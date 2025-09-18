# Project Status Report

Date: 2025-09-18
Owner: PDF Translation Platform

## Where We Are (Snapshot)

- Infra
  - Traefik integrated (Cloudflare DNS/ACME). API/WEB healthy. Flower behind basic auth.
  - Compose updated: services on `traefik-proxy`, no public ports for internal services.
- Backend
  - Legacy per‑page translation (OpenAI completions) fully working.
  - Phase 1 scaffolding added and piloted behind flag:
    - Token‑aware Chunker (tiktoken) → splits paragraphs to meet token budgets.
    - Translator (chat API orchestrator) → aggregates usage and cost.
    - LLM chat client wrapper (retries + usage capture) and cost estimator.
    - Feature flag `USE_CHUNKING` wired (enabled for pilot).
  - Metrics exposed at `/metrics` (Prometheus counters + latency histograms).
  - Job cost accumulation: updates `TranslationJob.actual_cost` as pages complete.
- Frontend
  - Next.js app up; minimal viewer present. UI enhancements planned (not implemented yet).
- Tests
  - Unit: chunker, translator, cost estimator.
  - Integration: chunked flag path (translator stubbed to avoid network).
  - Global pytest/jest harness in place; coverage gates configured.
- Smoke Pilot
  - Chunked translation path exercised on a test PDF (page 1) via internal network; returns translated text and a small cost.

## What’s Next (Immediate P0)

- Persist Usage and Costs per Page
  - Capture prompt/completion tokens from chat client and store on `PDFPage` (add columns or metadata field via migration).
  - Aggregate to `TranslationJob` (actual_cost, tokens_in/out).
- API Enhancements
  - Extend progress/status endpoint to include tokens, costs, elapsed times, and model info.
  - Add export endpoint skeleton (Markdown) to prepare for V2 structure‑aware prompts.
- Minimal UI (Operator Visibility)
  - Document detail + pages table (status, cost, tokens) with polling.
  - Actions: sample translate, open page preview (side‑by‑side stub).
  - Tests with MSW for hooks/components.
- Metrics & Dashboard
  - Add histograms for tokens_in/out and page duration.
  - Provide a basic Grafana dashboard JSON (routers, latencies, error rate, tokens, cost).
- Hardening
  - Improve retry/backoff for 429/5xx; add Redis token bucket (rate limiter) skeleton (disabled by default).

## Remaining (By Phase)

- Phase A (in progress; target: week 1–2)
  - [P0] Persist usage and per‑page metrics; API status extension.
  - [P0] Minimal UI visibility and actions.
  - [P0] Metrics histograms + sample dashboard.
  - [P0] Tests for API contract and UI hooks.
- Phase B (week 2–3)
  - [P1] Structure‑aware prompts for lists/tables/headers; snapshot tests.
  - [P1] Reviewer pass (optional) with quality scores; store in page metadata.
  - [P1] Redis cache for dedupe; rate limiter (token bucket).
  - [P1] Side‑by‑side viewer + review queue (accept/reject edits).
- Phase C (week 3–4)
  - [P2] Glossary model + CRUD; glossary in prompts and QA.
  - [P2] Exporters (Markdown→HTML/DOCX) for full doc.
  - [P2] Celery groups/chords and resume logic; budget caps.
  - [P3] Optional thin agent layer (Orchestrator + Chunker) pilot.

## Priority (P0 → P3)

- P0: Usage persistence, status API, minimal UI, metrics dashboard.
- P1: Structure‑aware prompts, reviewer, cache, rate limiter.
- P2: Glossary, exporters, robust Celery orchestration/resume.
- P3: Agent layer and multi‑model strategies.

## Risks & Mitigations

- Cost Overruns → real‑time usage capture + job budget caps; alerts; operator pause/resume.
- Rate Limits → exponential backoff + Redis token bucket; limit parallelism.
- Prompt Regressions → snapshot tests; prompt versioning; easy rollback.
- Schema Mismatch → run migrations before enabling new fields; feature flags guard rollouts.

## Timeline (Target)

- Sprint A (1–2 weeks): P0 items above; pilot chunked path on 20 pages; baseline dashboard live.
- Sprint B (1–2 weeks): P1 quality features; review workflow; rate control; operator UI improves.
- Sprint C (1–2 weeks): P2 delivery (glossary, exporters, resilience); optional agent pilot.

## Commit & Documentation Cadence

- Frequent, descriptive commits (Conventional Commits) per small step.
- Docs updated each step: CHANGELOG (Unreleased), CURRENT_STATE (snapshot), EXECUTION_PLAN/PHASING (if timeline shifts).
- Weekly summary links to PRs and this report.

## Immediate Actions Checklist

- [ ] Add `tokens_in`, `tokens_out`, `cost_actual` fields to `PDFPage` (alembic migration) or a JSON metadata container.
- [ ] Update status API to include tokens/cost/time/model at page/job scope.
- [ ] Implement minimal UI (document detail + pages table + polling + sample translate).
- [ ] Add token/cost histograms and publish a basic Grafana dashboard JSON.
- [ ] Create tracking issues and mark them P0.

