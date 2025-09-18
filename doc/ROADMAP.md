# Roadmap (Systematic View)

This roadmap aligns technical work with outcomes: reliable, cost‑efficient, high‑quality English→Persian translation at scale with clear UX and observability.

## Vision → Outcomes
- Quality: structure‑preserving translations suitable for academic texts; reviewable and correctable.
- Cost/Latency: predictable usage with token‑aware chunking; transparent accounting and budgets.
- Operability: clear runbooks, metrics, alerts, and safe rollbacks.
- UX: simple workflow to upload, monitor, review, and export.

## Milestones (Major Deliverables)
- M1. Chunked translation (feature‑flagged), usage/cost capture, basic metrics.
- M2. Structure‑aware prompts, optional review pass, minimal UI dashboard, rate limiting and cache.
- M3. Glossary, export pipeline (Markdown→HTML/DOCX), resilient Celery groups/chords, dashboards.
- M4 (optional). Thin agent layer (Orchestrator + Chunker) over Celery; multi‑model strategies.

## Scope by Area
- Backend
  - LLMClient (chat), Chunker, Translator, Reviewer, CostModel, RateLimiter, Cache, Exporters.
- Worker
  - Chunk orchestration with Celery groups/chords; idempotent retries; progress roll‑ups.
- Frontend
  - Document dashboard, pages table, side‑by‑side viewer, glossary UI, review queue, exports.
- Infra/Observability
  - Traefik, TLS, dashboards, alerts, runbooks; budget caps and job controls.

## Dependencies & Assumptions
- Stable OpenAI API access and pricing; long‑lived API key (rotatable).
- Traefik reverse proxy in place (done) with Cloudflare DNS.
- Redis for broker and rate‑limit/cache; Postgres for persistence.

## Non‑Goals (for now)
- Multi‑tenant RBAC, billing, and quotas per user (future enterprise track).
- Full WYSIWYG PDF reflow fidelity (focus on useful structure via Markdown/HTML first).

## References
- doc/EXECUTION_PLAN.md – sprint timeline and deliverables
- doc/TRANSLATION_ENHANCEMENTS_V3.md – SOLID + TDD plan
- doc/DEVELOPMENT_PROCESS.md – process, commits, PRs

