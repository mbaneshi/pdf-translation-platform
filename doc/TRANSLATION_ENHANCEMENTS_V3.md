# Translation Platform – Version 3 Plan

Focus: test‑driven development, SOLID architecture, and scale readiness. Builds on V1/V2 docs and current codebase.

## Objectives

- Quality: adopt TDD with clear test layers and fast feedback.
- Design: refactor toward SOLID principles and clean boundaries.
- Scale: handle larger documents, concurrent jobs, and stable costs.

## Architecture Principles (SOLID)

- Single Responsibility
  - Split `TranslationService` into: `OpenAIClient` (I/O), `PromptLibrary` (templates), `Chunker` (segmentation), `Translator` (orchestration), `Reviewer` (QA), `CostModel` (pricing), `Cache` (dedupe), `Metrics` (telemetry).
- Open/Closed
  - Add new models/prompts/chunk strategies via config without modifying core orchestrator.
- Liskov Substitution
  - Define `LLMClient` interface; allow swapping OpenAI/other providers in tests and at runtime.
- Interface Segregation
  - Separate read APIs (stats/progress) from write/exec APIs (start/stop jobs) to keep controllers lean.
- Dependency Inversion
  - Inject `LLMClient`, `RateLimiter`, and `Cache` into services; wire in `app.main` and worker init.

## Testing Strategy (TDD)

Test pyramid and patterns using existing `backend/tests` structure.

- Unit (fast, no network)
  - Chunker: property tests for token budgets; boundaries at paragraph/table; never split inside table rows.
  - PromptLibrary: snapshot tests for each chunk type with glossary/context.
  - CostModel: deterministic pricing from token usage.
  - OpenAIClient: retry/backoff decisions (simulate 429/5xx) with clocks.
  - PersianTextProcessor: punctuation/RTL invariants.
- Service/Integration (uses DB/Redis, mocks LLM)
  - Translator: end‑to‑end page → chunks → translations → reassembly; verify persisted usage/cost.
  - Reviewer: flags glossary violations; applies minimal edits.
  - Celery: group/chord pipeline over chunks; idempotent retries by chunk hash.
- API (FastAPI TestClient)
  - Start translation with options; poll progress; fetch export.
  - Glossary CRUD.
- E2E (optional in CI nightly)
  - Minimal PDF fixture; full background job; assert final artifact exists and metrics recorded.
- Frontend
  - Hooks: `useJobStatus`, `useTranslateSample` with MSW.
  - Components: DocumentDetail, PagesTable, SideBySide viewer, basic snapshots.
  - E2E UI (optional): Playwright smoke (upload, translate sample, see progress).

Coverage gates
- Backend: keep 80% global; new modules ≥90%.
- Frontend: keep 80%; critical hooks/components ≥90%.

## Scale Readiness

- Chunking and Throughput
  - Token‑aware chunking (1–1.5k tokens) with semantic boundaries.
  - Celery: use `group` per page (parallel chunks), `chord` to merge results; configurable concurrency.
  - Prefetch limit per worker; per‑queue priorities (sample vs batch jobs).
- Rate Limiting & Backoff
  - Redis token bucket (global calls/sec per model); exponential backoff with jitter on 429/5xx.
- Idempotency & Resume
  - Chunk id = blake3(model+promptVersion+content). Persist status; safe to retry.
  - Resume picks pending/failed chunks; page and job roll‑up recomputed.
- Cost Control
  - Real usage accounting from API response; budget caps per job; stop/alert when budget exceeded.
- Storage & Exports
  - Store uploads and exports on disk now; optionally move to S3-compatible storage later.
  - Export Markdown (canonical), derive HTML/DOCX in worker.
- Data Model
  - Option A: store chunk metadata under `PDFPage.metadata['chunks']`.
  - Option B (preferred for scale): new `page_chunks` table with status, usage, cost, and hashes.
- Observability
  - Prometheus metrics (translation latency, tokens in/out, errors, budgets, queue lengths).
  - Structured logs with job_id/page_id/chunk_id; Grafana dashboards and alerts.

## Concrete Work Items (TDD‑first)

1) LLM Client + Pricing
- Add `app/services/llm_client.py` with `LLMClient` interface and `OpenAIClient(chat)` impl.
- Tests: retries, timeouts, usage capture, error mapping, pricing.

2) Chunker
- Add `app/services/chunker.py` with token‑aware segmentation (paragraph‑first) + table/list guards.
- Tests: property tests on token budgets and boundary rules.

3) Translator Orchestrator
- Add `app/services/translator.py` that uses Chunker + LLMClient + PromptLibrary + Cache.
- Persist chunk usage/cost; reassemble page text (markdown for tables/lists).
- Tests: end‑to‑end with mocked LLM.

4) Reviewer (optional flag)
- Add `app/services/reviewer.py` with quick QA prompt and safe edits.
- Tests: glossary adherence, punctuation fixes.

5) Cache & RateLimiter
- Add `app/services/cache.py` (Redis or in‑DB) and `app/services/rate_limiter.py`.
- Tests: dedupe by hash; enforce call budgets.

6) Celery Flow
- Update worker: chunk group per page; chord to finalize page; job aggregator to roll up stats.
- Tests: simulate chunk failures, retries, and resume logic.

7) API Extensions
- Start translation with options (model, chunk_size, review, budget, glossary_id);
- Progress includes tokens/cost; export endpoint.
- Tests: contract tests for responses.

8) UI Minimal
- Document detail + pages table + sample translate; Side‑by‑side viewer.
- Tests: hooks/components with MSW; snapshots.

## Definition of Done (Phase 1/2)

- Backend
  - Unit/service tests pass; coverage ≥90% for new modules.
  - Integration tests verify chunk pipeline; no real network (LLM mocked).
  - API contract tests updated; CI green.
- Worker
  - Processes chunk groups; safe retry; rate limits enforced.
  - Metrics exported; basic Grafana panel shows throughput and latency.
- Frontend
  - Document detail shows progress; sample translate works; basic RTL viewer.
  - Jest tests pass with ≥80% coverage.
- Ops
  - Config via env: model, pricing, chunk size, budgets, rate limits.
  - Rollback: feature flag to fall back to legacy per‑page translation.

## Risks & Mitigations

- Prompt regressions → snapshot tests; prompt versions; quick rollback.
- API limits → token bucket + backoff; reduce concurrency.
- Cost spikes → job budget caps and alerts; pause/resume controls.
- Complexity → keep agents thin; Celery does execution; add components incrementally.

## Quick Pilot (today)

- Keep current endpoints; add a feature flag `USE_CHUNKING=false`.
- Implement LLMClient + Chunker + Translator with tests.
- Flip `USE_CHUNKING=true` for a single document; run 20‑page trial from V2 doc; compare cost/time/quality.

## CI/CD & Tooling

- Extend `./check-quality.sh` to run `python -m pytest -m "not e2e"` and `npm run test:ci`.
- Add a Makefile target `make bench20 DOC_ID=...` for the quick trial script.
- Optional: pre-commit hooks ensure no real API calls in tests (guard by env flag).

---

If you approve, I’ll scaffold LLMClient + Chunker with tests under `backend/tests/unit/service_*` and wire a feature flag to switch per‑page translation to chunked translation for a pilot.
