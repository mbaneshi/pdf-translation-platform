# Platform Architecture & Scalability Blueprint

This document outlines a production‑grade architecture to support real‑time collaboration, streaming translation, offline/online providers, quality systems, and enterprise‑ready ops.

## High‑Level Components
- API (FastAPI): documents, pages, translation jobs, glossary, suggestions, quality.
- Collab Service: WebSocket edge, CRDT rooms, snapshots, ops persistence.
- Workers: translation pipelines, OCR, enforcement, quality scoring, exports.
- Storage: Postgres (primary), Redis/NATS (realtime), object store (snapshots, exports).
- Frontend (Next.js App Router): reader, review, settings, analytics.
- Observability: tracing, metrics, logs, alerting, SLO dashboards.

## Data Flow: Upload → Read → Translate → Review → Export
- Upload: chunked, resumable; virus scan; metadata extraction; enqueue processing.
- Parse: layout analysis; segment extraction; anchors; index for search.
- Translate: provider routing; streaming; store drafts; apply on accept.
- Review: suggestions, comments, glossary enforcement; quality scoring.
- Export: PDF/HTML/JSONL with audits; sign artifacts.

## Translation Pipeline
- Steps: segment batching → provider call (stream) → post‑process → store draft → notify collab.
- Policies: budget caps, retry/backoff, fallback provider.
- Observability: per‑segment latency, token spend, provider error rates.

## Provider Abstraction
- Interface: `translate(text, src, tgt, options) -> stream|result`.
- Providers: OpenAI‑compatible, Argos (offline), custom NMT.
- Router: rules by project, page difficulty, cost/latency SLOs.

## Collab Architecture
- Rooms pinned to pageId; sticky routing via consistent hashing.
- Ops stream persisted with sequence numbers; snapshots every N ops.
- Rehydration on failover from last snapshot + ops tail.

## Scaling & Capacity Planning
- Stateless API scale out; rate limit per tenant.
- Collab nodes scale by room count and ops throughput.
- Worker autoscaling by queue depth and time‑to‑empty SLO.

## Storage Strategy
- Postgres: normalized core entities + JSONB for flexible metadata.
- Object store: PDFs, previews, exports, CRDT snapshots.
- Caching: Redis for hot lookups; CDN for static assets.

## Security & Compliance
- JWT/OIDC auth; RBAC; short‑lived WS tokens.
- Encryption at rest and in transit; per‑tenant keys.
- Audit logging and export; retention policies; legal hold support.

## Disaster Recovery
- Backups: PITR for Postgres; versioned object storage; infra as code.
- DR runbooks; RPO/RTO targets; region failover drills.

## Observability
- Metrics: API p95, WS uptime, worker throughput, provider errors.
- Tracing: end‑to‑end across upload → export; provider spans.
- Logs: structured, redacted; correlation ids across services.

## Cost Management
- Track per‑doc costs: tokens, compute time, storage.
- Idle shutdown for warm workers; queue consolidation windows.
- Data lifecycle: archive old ops/snapshots.

## Migrations & Backwards Compatibility
- Version APIs; deprecate with headers; feature flags for new behaviors.
- Data migration jobs with progress reporting and safe backout.

## SLOs
- API p95 < 150ms for metadata reads; < 500ms for mutations.
- Collab echo < 150ms in‑region; reconnect within 3s p95.
- Translation first‑token < 500ms p95 with streaming provider.

## Deployment
- Containers per service; minimal base images; compilers cached.
- Blue‑green or canary deploys; feature flags per tenant.
- IaC with Terraform; secrets via Vault/KMS; GitOps pipelines.

## Testing Strategy
- Unit: services and adapters; property tests for merge/CRDT.
- Integration: API + DB; collab snapshot/rehydrate; provider mocks.
- E2E: upload→translate→review→export happy path and failure cases.
- Load: k6/Gatling profiles; chaos monkey for room nodes.

## Roadmap
- Milestone 1: provider abstraction + streaming; basic collab.
- Milestone 2: suggestions + glossary enforcement; quality metrics.
- Milestone 3: enterprise controls; DR drills; multi‑region.

