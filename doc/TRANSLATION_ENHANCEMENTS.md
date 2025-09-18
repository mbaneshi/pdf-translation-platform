# Translation Pipeline: Deep-Dive Findings and Proposal

This document summarizes the current implementation, key gaps, and a pragmatic enhancement plan to improve translation quality, cost control, robustness, and throughput for English → Persian (Farsi).

## Current State (Quick Summary)

- Pipeline
  - PDF ingestion via PyMuPDF + pdfplumber (`PDFService`), pages stored in DB (`PDFPage`).
  - Optional semantic analysis (`SemanticAnalyzer`) populates sentences/paragraphs/sections (placeholder-heavy).
  - Translation handled by `TranslationService` using OpenAI “completions” API with a single prompt and large `max_tokens` per page.
  - Background processing with Celery (`process_document_translation`, `translate_page_task`).
- Persian handling
  - `PersianTextProcessor` reshapes Arabic script, enforces RTL and basic punctuation mapping, provides lightweight validation.
- Costing
  - Heuristic cost estimation using tiktoken on raw input text and static GPT‑3.5 Turbo prices.
- Observability
  - Flower is enabled; no explicit metrics for translation throughput, costs, or failures.

## Key Gaps Identified

- Model/API usage
  - Uses legacy completions API; modern chat API and newer models (e.g., gpt‑4o‑mini) yield better quality/cost and richer usage data.
  - Single-shot page translation risks token overflows, higher costs, and inconsistent structure preservation.
- Chunking/structure
  - No token‑aware chunker; limited use of semantic structure and layout boundaries to segment content.
  - Tables/lists/headers/footers are not explicitly handled during translation.
- Quality and consistency
  - Limited QA: basic checks only; no terminology consistency across document or user glossary support.
- Cost and rate control
  - Pricing hardcoded; no dynamic model selection; limited retry/backoff and no concurrency/rate limiting at worker level.
- Caching and deduplication
  - No cross‑page deduplication for repeated paragraphs (e.g., headers, disclaimers, repeated footers).
- Observability
  - No Prometheus metrics (duration, token counts, errors, costs) or job‑level progress beyond counts.

## Proposed Enhancements (Prioritized)

### 1) Modernize translation client (quick win)

- Switch to Chat Completions API with system/user messages and deterministic settings.
- Default model: `gpt-4o-mini` (cost‑effective), configurable via `OPENAI_MODEL`.
- Implement robust retry/backoff for 429/5xx with jitter; bounded timeouts.
- Capture `usage` (prompt/output tokens) and persist to `PDFPage` and `TranslationJob` for accurate cost tracking.
- Add connection pooling (reuse client) and short circuit on empty/short inputs.

Why: better quality/cost, reliable usage data, fewer failures.

Implementation outline (no code change yet):
- Create `app/services/openai_client.py` with a reusable `TranslationClient` that wraps `client.chat.completions.create()` and centralizes retries, timeouts, and pricing math.
- Update `TranslationService.translate_text()` to use this client and handle structured prompts.

### 2) Token‑aware, layout‑aware chunking

- Add chunker that:
  - Uses tiktoken to target chunk size (e.g., 1,000–1,500 tokens per chunk).
  - Respects semantic boundaries: paragraphs, headings; avoids splitting tables/code blocks.
  - Collapses headers/footers and deduplicates repeated segments (hashing).
- Maintain per‑page chunk order and IDs for deterministic reassembly.

Why: reduces token overflow, improves coherence and format preservation, lowers cost.

Implementation outline:
- New `Chunker` in `app/services/chunker.py` that accepts page text + optional layout metadata, returns `List[Chunk]` with type (paragraph/table/list), source offsets, and token counts.
- Store chunk metadata in `PDFPage.metadata` (or a new table `page_chunks` via Alembic) and persist translated chunks for resume/retry.

### 3) Structure‑preserving prompts + format strategies

- Use different prompt templates per chunk type:
  - Title/headers: keep capitalization rules and brevity.
  - Paragraphs: preserve meaning, academic tone, maintain citation brackets (e.g., [1]).
  - Lists: preserve bullets and nesting.
  - Tables: return Markdown table preserving cell structure; do not paraphrase numeric content.
- Mark structure with minimal, deterministic tags (e.g., markdown) to ease reassembly.
- Post‑process with `PersianTextProcessor` only on text chunks (skip tables/code).

Why: higher fidelity, easier to render and export (HTML/PDF/docx) while maintaining structure.

Implementation outline:
- Add `PromptLibrary` with templates and small guardrails (e.g., “do not add commentary”).
- `TranslationService` selects template based on chunk type and passes constraints to the chat model.

### 4) Terminology and glossary support

- Add optional user glossary (English → Persian) at document/job scope.
- Inject glossary into system prompt; enforce via reviewer step (discussed below).
- Detect and report inconsistent usage of glossary terms.

Why: domain consistency across document; essential for academic texts.

Implementation outline:
- New DB model `GlossaryTerm(document_id, source, target, notes)` and CRUD endpoints.
- `TranslationService` merges glossary into prompt context; QA step validates term usage.

### 5) Two‑pass QA (LLM‑assisted review)

- Pass 1: translate chunks deterministically (low temperature, structure preserved).
- Pass 2: reviewer prompt validates style, punctuation, numerals, glossary adherence, and suggests minimal edits; optionally auto‑apply safe edits.
- Maintain a quality score per chunk/page with reasons and suggested fixes (persist in `metadata`).

Why: improved quality and consistency with limited extra cost; targeted improvements.

Implementation outline:
- Add `ReviewService` using the same or higher‑quality model for short review prompts.
- Persist results under `PDFPage.metadata['review']`.

### 6) Accurate costing + pricing config

- Price catalog in settings (env):
  - `OPENAI_PRICING_INPUT_PER_M`: `$`/1M tokens
  - `OPENAI_PRICING_OUTPUT_PER_M`
- Compute cost from `usage.prompt_tokens` + `usage.completion_tokens` for each chunk.
- Aggregate to page/job; store `actual_cost` in `TranslationJob` and `cost_estimate` in `PDFPage`.

Why: real numbers to track costs and set budgets.

### 7) Caching and deduplication

- Content fingerprinting (e.g., blake3) for chunks; Redis/DB cache of translations by hash + model + prompt version.
- Reuse cached translations across pages/documents.

Why: eliminates rework (common for headers/footers, repeated notices); reduces cost and latency.

### 8) Worker throughput, rate limiting, and resilience

- Celery tuning: set prefetch limits, concurrency controls, and job chunking (use `group/chord`) per document.
- Global rate limiter for OpenAI calls (token bucket in Redis) to avoid 429s.
- Idempotency: safe retries per chunk based on chunk hash and persisted status.
- Resume: a stalled/failed job picks up unprocessed chunks.

Why: stable throughput under load, fewer failures, simpler restarts.

### 9) Export options and format preservation

- Reconstruct translated output as:
  - Markdown (recommended) -> easy to render to HTML/PDF/docx.
  - Optionally DOCX/PDF generation preserving layout approximations (e.g., WeasyPrint, Pandoc pipeline).
- Include tables as Markdown tables; keep images/figures references.

Why: deliverable formats beyond plain text; better UX.

### 10) Observability and SLOs

- Prometheus metrics (via `prometheus_client`):
  - `translation_requests_total`, `translation_tokens_total`, `translation_latency_seconds{stage=translate|review}`, `translation_errors_total{code}`
  - `openai_rate_limited_total`
  - `job_pages_processed`, `job_cost_usd_total`
- Logs: structured logs with job_id/document_id/chunk_id.
- Grafana dashboards; alerting on error rate spikes.

Why: measure, tune, and catch regressions.

## Suggested API/DB Changes (Minimal Surface)

- Endpoints
  - POST `/api/enhanced/translate/start` → accept options: model, chunk_size, use_review, glossary_id.
  - GET `/api/enhanced/translate/{document_id}/status` → include tokens/cost metrics.
  - Glossary CRUD under `/api/enhanced/glossary`.
  - Export endpoint `/api/enhanced/export/{document_id}?format=markdown|html|docx`.
- DB
  - Add `glossary_terms` table (Alembic migration).
  - Optional `page_chunks` table for durable chunk status (or embed under `PDFPage.metadata['chunks']`).

## Implementation Plan (Phased)

Phase 1 (1–2 days)
- Introduce `TranslationClient` (chat API, retries, usage capture) and wire into `TranslationService`.
- Add token‑aware chunker for pages (paragraph‑first); translate sequentially per page; reassemble.
- Record usage and actual cost per page/job.

Phase 2 (2–4 days)
- Structure‑aware prompts per chunk type; format preservation to Markdown (tables/lists/headings).
- Add review pass (optional flag) with quality metrics stored in page metadata.
- Add deduplication cache (Redis key: hash(model+prompt+content)).

Phase 3 (2–4 days)
- Glossary model + endpoints; glossary enforcement in prompts; QA check.
- Prometheus metrics and basic Grafana dashboard.
- Improve Celery orchestration (groups/chords), rate limiter (Redis token bucket).

Phase 4 (optional, 3–5 days)
- Exporters (Markdown → HTML/PDF/docx).
- Enhance semantic analyzer to feed chunker with robust boundaries (reduce placeholders).
- Model‑tiering (fallback/escalation logic) and budget caps per job.

## Risks and Mitigations

- Token limits: Mitigate with strict chunking, enforce headroom in prompts.
- Cost overruns: Real‑time usage capture, budget checks before starting jobs.
- Quality regressions: Two‑pass review, terminology QA, maintain prompt versions.
- Latency spikes / 429s: Backoff + rate limiter; Celery prefetch tuning.

## Appendix: Example Prompt Sketches

System (generic):
- “You are an expert English→Persian translator for academic texts. Preserve meaning and structure. Do not add commentary. Use Persian punctuation. Keep citations [..] intact.”

User (paragraph chunk):
- Includes paragraph text + brief context (document title/section) + glossary terms array when available.

User (table chunk):
- “Translate headers and cells faithfully. Return a Markdown table with same columns/rows. Preserve numeric formats. Do not paraphrase.”

Reviewer pass:
- “Review the Persian translation for: terminology consistency (use glossary), punctuation, numerals, citations, and brevity of headings. Suggest minimal edits. Output: edited text.”

---

If you want, I can start with Phase 1 by adding the TranslationClient (chat API), a basic chunker, and wiring usage/cost into the DB, then open a PR for review.
