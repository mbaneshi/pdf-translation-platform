# Frontend Modernization & UX Strategy

This document outlines a focused plan to evolve our Next.js frontend into a modern, eye‑catching interface with first‑class UX tailored to a PDF translation platform.

## Product UX Principles
- Clarity first: show where the user is in the doc and translation state per page.
- Progressive disclosure: simple happy path; advanced controls only when needed.
- Speed by perception: optimistic UI, instant feedback, skeletons, toasts.
- Continuity: preserve reading flow; never block navigation while background tasks run.
- Trust: transparent costs, model/provider indicators, reproducible history.

## Signature Experiences (Tailored to PDFs)
- Side‑by‑Side Reader
  - Original left, translation right, synced scroll, unified zoom.
  - Page mini‑map with per‑page status dots: pending/processing/done/failed.
  - Lazy translate on view; background prefetch ±2 pages.
- Review & Improve
  - Inline segment selection with suggested alternatives, accept/edit buttons.
  - Glossary enforcement badge; highlight terms with hover definition.
  - Quick feedback chips: Accurate/Awkward/Missing → feeds learning queue.
- Cost & Progress
  - Header progress bar: pages done/total, ETA, tokens/$ estimate.
  - Provider badge (OpenAI/Offline/Custom) per page; switch with confirm.
- Resilient Uploads
  - Drag‑drop with large file guidance, chunked upload, resumable.
  - Immediate text extract preview; choose OCR fallback if text is sparse.

## Modern Stack & Patterns
- Next.js App Router + RSC
  - Adopt `app/` directory, Server Components by default.
  - Server Actions for mutations (start/stop translation, glossary updates).
  - Streaming responses for long tasks; progressively hydrate client UI.
- TypeScript Everywhere
  - Strict mode, shared `types/` for Document, Page, Layout, TranslationStatus.
- Data Layer
  - TanStack Query for client data (page status/polling), dehydrate on server.
  - WebSocket/SSE for live page updates; fallback to polling with backoff.
- UI System
  - Tailwind CSS with CSS variables for themes.
  - Radix UI + shadcn/ui primitives for accessible components.
  - Framer Motion for subtle transitions (page change, toasts, progress).
- State Management
  - Local: Zustand for UI state (viewer controls, selections).
  - Global server state via Query cache; avoid prop drilling.
- Forms & Validation
  - React Hook Form + Zod; accessible inputs, inline errors.

## Information Architecture
- App Shell
  - Top: file name, progress, provider menu, actions (export/report/share).
  - Left: mini‑map + page list with statuses and search.
  - Center: dual viewer (canvas/pdf.js) with toolbar.
  - Right (collapsible): Review Panel (edits, glossary, history).
- Key Routes
  - `/upload` → `/doc/[id]` (reader)
  - `/doc/[id]/review` (bulk edits, QA metrics)
  - `/settings` (providers, budget caps, shortcuts)

## Component Blueprint
- Reader
  - `PdfCanvas` (pdf.js + virtualization), `TranslatePane` (rich text with anchors), `SyncScroller`.
  - `PageStatusDot`, `MiniMap`, `Toolbar` (zoom, fit, split ratio, theme).
- Review
  - `SegmentList` with diff view, `SuggestionCard`, `GlossaryBadge`.
- System
  - `UploadDropzone` (chunked, resumable), `Toast`, `Dialog`, `ProgressBar`.

## Accessibility (WCAG 2.2 AA)
- Keyboard: full navigation (J/K next/prev page, G go to page, T translate page).
- Focus management: visible outlines, restore focus after dialogs.
- Landmarks: semantic regions, aria labels for viewer panes and mini‑map.
- Color contrast: enforce via tokens; support high‑contrast theme.
- Reduced motion: honor `prefers-reduced-motion`.

## Performance Targets
- TTI < 2.0s on mid devices for reader route.
- Initial viewer bundle < 120KB gz (code split pdf.js worker).
- LCP < 1.8s on cached nav; CLS ~0.
- Smooth scroll/zoom at 60fps; canvas virtualization for large PDFs.

## Visual Design
- Themes: Light/Dark/System; seamless theme switch.
- Tokens: spacing, radii, shadows; design tokens in CSS vars.
- Motion: micro‑interactions only (status dot ripple, toast enter).
- Empty/loading states with illustrations; consistent iconography (Lucide/Remix).

## Internationalization
- App i18n (en/fa) using `next-intl` or `@lingui`; RTL support.
- Number/date localization, Persian typography for translations.

## Observability & Quality
- UX metrics: client spans for translate latency per page, error rates.
- Analytics: privacy‑preserving events (page_view, translate_click, edit_accept).
- Testing: React Testing Library, Playwright e2e for reader flows.
- Visual regression: Storybook + Chromatic (or Loki) for core components.

## Security & Privacy
- Content handling: never log page text by default; redact in analytics.
- CSRF/XSS: sanitize rendered translation; strict CSP.
- Uploads: client‑side file type checks; size limits with clear errors.

## Progressive Web App (Optional)
- Installable app, offline cache for assets and recent pages.
- Background sync to resume uploads and pending translations.

## Implementation Roadmap
- Phase 1: Foundations
  - Migrate to App Router + TS strict; introduce Query + Zustand; set up shadcn/radix.
  - Add `types/` and API hooks (`useDocument`, `usePage`, `useTranslatePage`).
- Phase 2: Reader & Lazy Translation
  - Build dual‑pane reader, mini‑map, status dots, optimistic translate per page.
  - WebSocket/SSE updates with fallback polling.
- Phase 3: Review & Glossary
  - Inline editing, suggestions, glossary highlighting & enforcement UI.
  - Cost/ETA surfaces; provider switch flow.
- Phase 4: Polish & A11y
  - Keyboard shortcuts, reduced motion, visual QA, performance budgets.

## Concrete Tickets (Examples)
- Build `PdfCanvas` with pdf.js worker, virtualization, and sync controls.
- Implement `MiniMap` with status indicators and quick navigation.
- `useTranslatePage(pageId)` hook with optimistic status and cancellation.
- Provider badge and switcher with graceful degradation.
- Glossary highlighting component with hover card definitions.
- UploadDropzone with chunked/resumable uploads and pre‑OCR density check.

## Tech Choices (Recommended)
- Next.js (latest), App Router, RSC, Server Actions.
- Tailwind CSS + shadcn/ui + Radix UI.
- TanStack Query, Zustand, React Hook Form, Zod.
- pdf.js for rendering; react‑virtuoso for lists/mini‑map.
- Framer Motion (optional micro‑interactions).

## Success Criteria
- Time to translate first viewed page < 3s (p95) after click.
- Reader route interaction readiness < 1s on warm nav.
- A11y score ≥ 95, Lighthouse perf ≥ 90 on reader.
- User task success: upload → translate selected pages → export ≤ 3 clicks.

