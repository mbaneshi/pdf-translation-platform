# GitHub‑Like UX Plan + PDF Viewing & Semantic Translation

This document outlines the UX, data model, APIs, and implementation plan to deliver a GitHub‑like experience with side‑by‑side PDF viewing, semantic (sentence/paragraph/section) translation, tables/figures handling, and export of a translated PDF.

## Goals
- Persistent header + sidebar, route-driven content (GitHub feel).
- View original PDF in the browser and overlay semantic blocks (sentences, paragraphs, sections).
- Side‑by‑side compare: original vs translated with synced scroll and live edit.
- Handle tables, images, figures with coordinates; preserve layout in exported PDF.
- URL reflects state (selected doc, page, filters, review mode).

## Information Architecture (Routes)
- `/documents` — List all documents.
- `/documents/[id]` — Overview (meta, actions, export).
- `/documents/[id]/pages` — Pages list (status, filters, quick actions).
- `/documents/[id]/progress` — Translation progress and timeline.
- `/documents/[id]/review?page=3&mode=side-by-side` — Original vs translation, live edit.

## Layout & Navigation
- Header: logo, global search, quick actions (upload), theme/user menu.
- Sidebar: sections (Home, Documents, Translations→active doc, History, Settings), Recent documents.
- Page header: breadcrumbs, title, tabs (Overview | Pages | Progress | Reviews), primary CTA.

## State & Data Flow
- Global state (client): `currentDocumentId`, `useEnhancedMode`, recents, layout prefs (localStorage).
- Data fetching via React Query; each route has its own queries and cache keys.
- URL params control pagination, filters, review mode, selected page.

## Semantic Model
Represent document content as a hierarchy with positional anchors for overlays:
- Document → Pages → Blocks → Segments
- Block types: `heading`, `paragraph`, `table`, `figure`, `caption`, `list`, `code`.
- Segment granularity: sentence-level within `paragraph`; cell-level within `table`.
- Every node carries: `id`, `type`, `bbox` (x, y, w, h), `page_number`, `text`, `tokens`, and (if translated) `translated_text`.

## Backend APIs
Existing (from `enhanced_documents.py` and `documents.py`):
- `POST /api/enhanced/upload` or `/api/enhanced/upload-enhanced` — upload PDF (returns document_id, total_pages, file_size_bytes).
- `GET /api/documents/{document_id}` — document summary (status, total_pages, total_characters).
- `GET /api/documents/{document_id}/pages` — page list with status flags.
- `POST /api/documents/{document_id}/translate` — start translation via Celery.
- `POST /api/documents/{document_id}/pages/{page_number}/test` — translate a specific page sample.
- `GET /api/enhanced/translation-progress/{document_id}` — progress (completed/total/percentage).
- `GET /api/enhanced/export/{document_id}` — export (e.g., Markdown).

To add (for full review workflow):
- `GET /api/pages/{page_id}` → Page detail with original/translated text and per‑segment structure:
  - `{ id, document_id, page_number, blocks: [{ id, type, bbox, text, segments: [{ id, bbox, text, translated_text }] }] }`
- `PATCH /api/pages/{page_id}` → Update translated text at page or segment level:
  - Body: `{ translated_text?: string, segments?: [{ id, translated_text }] }`
- `POST /api/pages/{page_id}/approve` and `/reject` → Review status.
- `GET /api/enhanced/semantic-structure/{document_id}` → Optional: full-doc structure for prefetching.

## Extraction & Structure (Backend)
- Libraries: `pdfplumber`/`pdfminer.six` for text + layout; `PyMuPDF` (pymupdf) for images and coordinates; `reportlab` for composition; existing stack already includes these.
- Steps per page:
  1) Extract text runs with font/size/coords; merge into lines/paragraphs.
  2) Segment sentences (e.g., regex + language model hints) within paragraphs.
  3) Detect headings via font size/weight heuristics to form sections/subsections.
  4) Detect tables (pdfplumber `extract_tables`, ruling lines, grid heuristics); produce cell-level text with bounding boxes.
  5) Extract images/figures (PyMuPDF) with bbox and resource id.
  6) Persist structure in DB tables (`pdf_pages`, `pdf_blocks`, `pdf_segments`).

## Translation Strategy
- Unit of work: sentence for paragraphs; cell for tables; caption for figures.
- Batch translate segments; maintain mapping {segment_id → translated_text}.
- For test translate: translate selected page segments only; store partial results.
- Track metrics per segment (tokens_in/out, cost_estimate) to aggregate at page/document.

## Frontend: PDF Viewing & Overlays
- Library: `pdfjs-dist` to render PDF page canvas.
- Overlay layer: absolutely positioned HTML elements on top of canvas using `bbox` coordinates scaled to viewport. Each overlay corresponds to a block/segment.
- Side‑by‑side layout:
  - Left: PDF canvas + overlay highlights (hover/selected segment).
  - Right: translation editor (per segment or aggregated paragraph), with live save and status badges.
- Synced interactions:
  - Click a sentence overlay → focus editor for that sentence.
  - Scroll sync: track viewport top page and align opposite pane to same page.
- Tables:
  - Overlay draws table grid; each cell clickable → editor shows cell text.
  - Option to preview “preserve format” rendering.

## Exporting Translated PDF
- Assemble new PDF preserving layout using `reportlab` or `PyMuPDF`:
  - Recompose text with translated content placed at segment bboxes (or use original text positions with substituted glyphs).
  - Draw images and figures at original coordinates.
  - For tables, render grid and cell contents.
- Alternative: generate high‑fidelity HTML with CSS Paged Media → print to PDF (for complex flows), but native PDF composition is preferred.

## Components to Build
- `components/Review/OriginalPane.tsx` — pdf.js viewer, page controls, overlay layer.
- `components/Review/EditorPane.tsx` — segment editor, list of sentences with status; save/approve buttons.
- `components/Documents/DocumentsTable.tsx` — list with filters/sorts (status, date, size, characters).
- `components/Common/Skeleton.tsx`, `EmptyState.tsx`, `InlineAlert.tsx`.
- `components/Layout/AppHeader.tsx`, `AppSidebar.tsx`, `PageHeader.tsx`.

## Frontend Data Contracts (TypeScript)
- `DocumentSummary`: `{ id, filename, status, pages, characters, sizeBytes, updatedAt }`
- `PageListItem`: `{ id, page_number, translation_status, is_test_page }`
- `PageDetail`: `{ id, document_id, page_number, blocks: Block[] }`
- `Block`: `{ id, type, bbox, text?, segments?: Segment[] }`
- `Segment`: `{ id, bbox, text, translated_text? }`

## Milestones
1) Layout shell (header/sidebar/tabs) and documents list.
2) Document detail tabs (Overview, Pages, Progress) and live polling.
3) Review side‑by‑side: pdf.js render + overlay + editor; GET/PATCH page endpoints.
4) Tables/figures overlay and editing; approve/reject actions.
5) Export translated PDF (backend composition) and on-demand side‑by‑side view.
6) Keyboard shortcuts, skeletons, optimistic updates, polish.

## Implementation Notes
- Coordinate mapping: pdf.js viewport scale factor × bbox from backend; keep a per-page scale to ensure overlays align.
- Performance: virtualize large lists (pages/segments); cache pdf.js pages; throttle scroll sync.
- Accessibility: keyboard navigation across segments; highlight focus; ARIA for editor.
- Resilience: all UI reads must guard for missing fields; default gracefully.

## Test Plan (E2E)
- Upload → extract → pages appear with correct counts.
- Start translation → progress increases; errors surface in a non-blocking alert.
- Test translate page → Review opens with translated content; edits can be saved and reflected back in Pages list.
- Export → download translated PDF; visual check tables/images.
- Cross-browser check (Chrome/Edge/Firefox) and responsive behavior.

## Libraries & References
- Frontend: `pdfjs-dist`, `@tanstack/react-query`, `framer-motion` (transitions), `zustand` (optional for local editor state).
- Backend: `pdfplumber`, `pdfminer.six`, `PyMuPDF` (pymupdf), `reportlab`, existing Celery pipeline.

---

This plan integrates a GitHub‑like product experience with a rigorous PDF semantics pipeline. It enumerates the endpoints to add, the data structures to exchange, and the UI components to build, along with concrete steps to implement and test the full review workflow.

