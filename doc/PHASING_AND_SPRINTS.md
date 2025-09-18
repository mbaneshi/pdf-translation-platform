# Phasing and Sprints (Detailed)

This breaks the roadmap into sprint‑sized, test‑driven deliverables with exit criteria.

## Phase A – Foundations (Sprint A, week 1–2)

- Backend
  - LLMClient (chat) with retries/backoff; usage capture.
  - Chunker (token‑aware, paragraph‑first); unit property tests.
  - Translator orchestrator; persist usage/cost per page/job.
  - Feature flag: `USE_CHUNKING` off by default.
- Worker
  - Simple per‑page chunk loop (sequential) to validate pipeline.
- Frontend
  - Document detail and pages table; sample translate; progress polling.
- Observability
  - Initial Prometheus counters/histograms; basic Grafana board.
- Exit criteria
  - New modules ≥90% coverage; CI green; sample document runs via flag; cost/usage stored.

## Phase B – Quality & Control (Sprint B, week 2–3)

- Backend
  - Structure‑aware prompts (paragraph/list/table) + PromptLibrary snapshots.
  - Reviewer (optional) with quality score and suggestions.
  - Redis cache for dedupe; rate limiter (token bucket).
- Worker
  - Celery group per page; chord to reassemble; idempotent retries by chunk hash.
- Frontend
  - Side‑by‑side page viewer; review queue (accept/reject edits); glossary UI skeleton.
- Ops
  - Dashboard charts: throughput, latency, error rate, tokens, cost.
- Exit criteria
  - Background job stable on a 100‑page doc; review pipeline optional but working; dashboard shows live metrics.

## Phase C – Delivery & Resilience (Sprint C, week 3–4)

- Backend
  - Glossary model + CRUD; integration in prompts and QA checks.
  - Exporters (Markdown→HTML/DOCX) for full document.
- Worker
  - Resume logic for failed/pending chunks; budget caps per job.
- Frontend
  - Exports tab; glossary CRUD; review refinements.
- Optional
  - Thin agent layer (Orchestrator + Chunker) piloted in feature branch.
- Exit criteria
  - Full E2E from upload → translate → review → export; budget enforcement; resilience verified.

## Cross‑Cutting Acceptance Criteria

- TDD: tests precede implementations for all new modules.
- Documentation updated each sprint: ROADMAP, EXECUTION_PLAN, CHANGELOG, CURRENT_STATE.
- No secrets in repo; env‑driven config; runbooks current.

