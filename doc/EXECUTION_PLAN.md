# Execution Plan (Roadmap + Timeline)

Scope: Deliver chunked, quality‑controlled Persian translation with solid tests, clear UX, and stable ops.

## Timeline (target ranges)

- Sprint A (week 1–2)
  - Backend Phase 1: LLM chat client, token‑aware chunker, translator orchestration, usage/cost capture.
  - Tests: unit/service/integration; CI gates to 80%+ (90% new code).
  - Ops: feature flag `USE_CHUNKING` default off; pilot on demand.
- Sprint B (week 2–3)
  - Prompts per chunk type; optional review pass; redis cache; rate limiter.
  - Minimal UI: document detail, pages table, sample translate, progress polling.
  - Metrics: Prometheus counters/histograms; basic Grafana dashboard.
- Sprint C (week 3–4)
  - Glossary model + CRUD; export pipeline (Markdown→HTML/DOCX).
  - Celery groups/chords for chunks; resume/idempotency polish.
  - Optional: thin agent layer (Orchestrator + Chunker) over Celery.

## Milestones & Deliverables

- M1 (end Sprint A):
  - Chunked translation works via feature flag; accurate usage/cost persisted.
  - Tests at required coverage; CI green; docs updated.
- M2 (end Sprint B):
  - Structure‑preserving prompts; review option; minimal UI online; metrics visible.
- M3 (end Sprint C):
  - Glossary+exports; resilient Celery flow; optional agent pilot; dashboard in place.

## Ownership & Cadence

- Branching: feature branches → PRs to `main-consolidated`; small, frequent merges.
- Commits: Conventional Commits; descriptive subject + context body.
- Reviews: Require tests for new features; snapshot updates reviewed.
- Standups: brief daily notes in PR thread or tracking issue.
- Releases: tag minor releases per milestone; generate release notes from CHANGELOG.

## Risks & Mitigations

- Cost spikes → budget caps per job; alerts; pause/resume controls.
- Token limits → strict chunk budgets; headroom in prompts.
- Rate limits → redis token bucket; exponential backoff.
- Regression risk → TDD, CI gates, prompt versioning and snapshots.

## References

- doc/TRANSLATION_ENHANCEMENTS.md, V2, V3
- doc/INTEGRATE_WITH_EXISTING_TRAEFIK.md, doc/MIGRATING_FROM_CADDY_TO_TRAEFIK.md
