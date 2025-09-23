# Inspiration Review and Stack Enhancement Report

This report compares the inspiration projects under `inspiration/` with our current workspace and outlines actionable enhancements.

## Sources Reviewed
- `inspiration/pdf-translator/` — WebUI + API that translates PDFs EN→JA with layout preservation using DiT (layout), PaddleOCR (text), and a HF MT model. GPU-first, Dockerized, CLI and GUI.
- `inspiration/pdf-translator-for-human/` — Streamlit app focused on side-by-side reading and on-demand, per-page translation. Supports OpenAI-compatible LLMs, local LLMs (ollama/llama.cpp/mlx_lm), and Google translator. Emphasizes incremental translation while reading.
- `inspiration/argos-translate/` — Offline, open-source MT (OpenNMT/CTranslate2). CLI/GUI/library with installable language packages and optional GPU via CTranslate2.

## Our Current Workspace (Summary)
- Backend: FastAPI (`backend/app`) with services for PDF parsing and translation.
  - `backend/app/services/pdf_service.py`: PyMuPDF + pdfplumber for text extraction and basic layout analysis (headers/footers/columns/tables, blocks, dimensions).
  - `backend/app/services/translation_service.py`: OpenAI-driven translation with Persian-focused prompts, caching, cost estimate, quality checks, and optional chunked mode.
  - `backend/app/services/translator.py`, `llm_client.py`, `chunker.py`, `semantic_analyzer.py` present for advanced flows.
- Frontend: Next.js (`frontend/`) with components like `DocumentViewer.js`, `FileUpload.js`, `ThemeSelector.js`, and TS-based components `SmartProgressHeader.tsx`, `ReviewPanel.tsx`.
- Infra: Dockerfiles, `start.sh`, monitoring, docs, and CI scripts.

## Key Comparisons and Gaps
- Layout and OCR
  - Inspiration uses vision models (DiT) and PaddleOCR ONNX for robust OCR and layout, enabling scanned PDFs and better structure retention.
  - We rely on selectable-text extraction via PyMuPDF/pdfplumber; OCR for scanned PDFs isn’t integrated.

- Translation Engines
  - Inspiration includes fully offline MT (Argos) and flexible backends (OpenAI-compatible, local LLMs, Google) with easy switching.
  - We primarily use OpenAI. No offline fallback or multi-provider abstraction exposed at API level.

- Interaction Model
  - “For Human” app translates lazily per page on navigation, minimizing token/cost and improving UX for long PDFs.
  - We process pages in batch or chunked modes; page-on-demand translation pattern is not a first-class UX/API capability.

- Delivery/UI
  - Inspiration showcases side-by-side original/translated pages with synchronized navigation.
  - Our frontend has `DocumentViewer` and `ReviewPanel`, but dedicated side-by-side page-level translation preview and lazy translation trigger could be deeper.

- Packaging and Ops
  - Inspiration provides Dockerized GPU flows and simple CLIs.
  - We have Docker and Celery worker infra, but no user-facing translation CLI or GPU OCR pipeline.

## Recommended Enhancements
1) Add OCR Pipeline for Scanned PDFs
   - Integrate ONNXRuntime with the included PaddleOCR ONNX models in `inspiration/pdf-translator/models/paddle-ocr/`.
   - API: expose an “ocr=true” processing flag. Fallback to OCR if extracted text is too sparse.
   - Store OCR usage and confidence in `page_metadata` for observability.

2) Layout-Aware Segmentation
   - Adopt layout-informed segmentation (columns/regions/tables) similar to DiT output to guide chunking and translation order.
   - Start lightweight: use existing `pdf_service` regions/blocks to build chunk units; add heuristics to retain reading order and figure/table captions.

3) Multi-Provider Translation Abstraction
   - Add providers: Argos (offline), Google/free via deep-translator, OpenAI-compatible endpoints (DeepSeek/Qwen).
   - Selection via config/env per document or per request. Implement retry/fallback chain: offline → paid API.
   - Add per-provider cost/latency metrics in `metrics_enhanced.py`.

4) On-Demand Per-Page Translation Flow
   - Backend: endpoint to translate a single page lazily, idempotent, cached by page hash.
   - Frontend: side-by-side viewer that triggers translation on page view, with progress, cancel, and retry.
   - Persist translation status per page (already present) and surface ETA/cost estimate in UI.

5) Side-by-Side Reader UX
   - Enhance `DocumentViewer.js` + `ReviewPanel.tsx` to support synchronized original/translated canvases, toggle original/translation overlay, and quick feedback on quality.
   - Add “Translate up to current page” and “Translate section” controls.

6) CLI for Batch and Headless Use
   - Provide `backend/cli/translator_cli.py` mirroring inspiration CLIs: input file/dir, output path, provider selection, and JSONL progress.
   - Useful for scripted runs and CI validation.

7) Caching, Batching, and Cost Controls
   - Strengthen hash-based caching at block/page level pre-translation.
   - Batch small chunks where model allows; enforce max token budgets with `chunker.py` using layout-aware boundaries.
   - Add budget caps per doc with fail-fast and user prompts in UI.

8) GPU/Accelerated Paths (Optional)
   - If environment has GPU, enable OCR acceleration and (optionally) Argos/CTranslate2 GPU.
   - Feature-flag via env to keep CPU-first deployments simple.

9) Licensing and Model Governance
   - Keep CC BY-NC components out of production/commercial builds. Prefer Apache/MIT alternatives for production.
   - Document model/provide provenance in `doc/architecture-proposal.md` and env toggles.

## Concrete Next Steps
- Backend
  - Add `ocr_service.py` using ONNXRuntime + PaddleOCR models already present under `inspiration/pdf-translator/models/paddle-ocr/`.
  - Extend `pdf_service.py` to attempt OCR when text density is low; attach confidences and bounding boxes.
  - Introduce `translation_providers/` with adapters: `openai.py`, `argos.py`, `deep_translator.py`, `openai_compatible.py`.
  - New endpoints: `POST /documents/{id}/pages/{n}/translate` (lazy), `GET /documents/{id}/pages/{n}` returns both original/translated payloads and layout.

- Frontend
  - Build a side-by-side `PDFReader` view: page navigation + lazy translate button and auto-on-view option.
  - Show per-page status, cost estimate, and provider badge.

- Tooling
  - Add `backend/cli/translator_cli.py` and docs under `doc/` for batch usage.
  - Expose configs via `.env` for provider selection and OCR toggles.

## Potential Risks and Mitigations
- Model size and performance: gate OCR and MT provider choices behind flags, stream results, and paginate work.
- Licensing: default to permissive stacks in production; keep research models optional.
- Complexity creep: implement in phases (OCR → provider abstraction → lazy per-page → UI polish).

## Summary
The inspiration projects validate three high-value directions: robust OCR + layout, flexible translation backends (including offline), and per-page, side-by-side UX. We can integrate these incrementally with minimal disruption by enhancing our services, adding provider adapters, and extending the viewer for on-demand translation.

