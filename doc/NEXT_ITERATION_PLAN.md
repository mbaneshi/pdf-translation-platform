# Next Iteration Plan (Sprint A — Hardening & Operator UX)

Date: 2025-09-18
Owner: PDF Translation Platform

## Objectives
- Ship a reliable, cost-aware chunked translation path in production.
- Persist fine-grained semantic structures to enable smarter prompts later.
- Provide minimal operator UI for visibility and basic QA.
- Ensure schema and migrations are fully aligned in deployed environments.

## Scope & Deliverables

- Chunked Chat Translation (Production-Ready)
  - Add resilient rate limiting/backoff:
    - Exponential backoff with jitter for 429/5xx.
    - Token-bucket limiter (Redis) with configurable RPS/TPM; disabled by default via env.
  - Circuit-breaker: temporary pause after sustained failures with health probe.
  - Config flags: `USE_CHUNKING`, `RATE_LIMIT_ENABLED`, `RATE_LIMIT_TPM`, `RATE_LIMIT_RPS`.
  - Metrics: per-error-type counters, retries, and backoff histograms.

- Semantic Analysis Persistence
  - Persist `SemanticStructure` rows per sentence/paragraph/section (not only JSON on `PDFPage`).
  - Batch inserts with pagination to avoid large transactions.
  - Add lightweight index on `semantic_structures(page_id, structure_type, structure_index)`.
  - API: `GET /api/enhanced/semantic-structure/{document_id}` to optionally stream or paginate.

- Frontend: Minimal Review UX
  - Pages table already displays status/tokens/cost.
  - Add side-by-side viewer for a page:
    - Original vs Translated with simple diff view.
    - Approve sample translation (hook to `/api/enhanced/approve-sample/{sample_id}`).
  - Export UX polish (filename, empty-state, progress).

- Database Migrations Assurance
  - Verify existing Alembic migrations cover:
    - `PDFPage.tokens_in`, `tokens_out`, `cost_estimate` fields.
    - All enhanced tables: `SemanticStructure`, `FormatPreservation`, etc.
  - Add missing migration(s) if gaps found; run `alembic upgrade head` in CI and deployment.

## Tasks & Sequencing

1) Backend – Chunked Path Hardening
- Implement retry/backoff wrapper in `LLMClient` for chat requests.
- Optional Redis-based token bucket (middleware) guarded by env flags.
- Wire retries and rate limiter into `Translator.translate_text` loop.
- Expand metrics: retries, rate-limited count, backoff seconds.

2) Backend – Semantic Persistence
- Update `SemanticAnalyzer` call path to write `SemanticStructure` entities per item.
- Add pagination and commit every N structures (e.g., 500) to avoid long transactions.
- Add index migration on (`page_id`, `structure_type`, `structure_index`).
- Extend retrieval endpoint to support `?type=sentence&limit=...&offset=...`.

3) Backend – Progress API Enrichment
- Extend `/api/enhanced/translation-progress/{id}` to include:
  - Job/model info, retry counts, rate-limit hits, recent errors.
  - Elapsed time and ETA (if total pages known).

4) Frontend – Review UI
- New route/screen: page review with split layout and sticky header.
- Actions: test translate (existing), approve sample (existing), copy Markdown.
- Poll progress to reflect live changes.

5) DB & CI
- Audit migrations vs models; add missing changesets.
- CI step: `alembic upgrade head` against ephemeral DB (or `--sql` dry run) to catch regressions.

6) Docs & Runbooks
- Update USER_MANUAL for operator flows.
- Update deployment guide with new env flags and rate-limiter notes.

## Success Criteria
- Chunked path stable under backoff; zero unhandled 429/5xx in smoke.
- Tokens/costs recorded per page; progress API aggregates correctly.
- Semantic structures persisted and queryable by page/type.
- Review UI shows side-by-side view and basic actions.
- Alembic migrations apply cleanly in CI and in staging.

## Risks & Mitigations
- OpenAI rate limits → limiter + backoff + small concurrency.
- Large PDFs → batch commits + streaming reads.
- Cost drift → real-time cost aggregation and budget caps (future).

## Timebox (Target)
- 3–5 days: backend hardening + semantic persistence + progress API.
- 2–3 days: frontend review UI + polish.
- 0.5 day: docs, runbooks, and staging verification.

