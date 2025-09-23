# n8n Strategy: Automation, Orchestration, and Human‑in‑the‑Loop Workflows

This document explains how a self‑hosted n8n can power automation, orchestration, and integrations for our AI translation platform. It includes concrete webhook payloads, nodes, and recipes optimized for humans and AI coding tools.

## Why n8n (Self‑Hosted)
- Visual, versionable workflows with 400+ integrations; self‑host to keep data private.
- Great for glue tasks: notifications, QA checks, batch operations, analytics syncs.
- Human‑in‑the‑loop approvals and resumable flows.

## High‑Impact Use Cases
- Translation Job Orchestration
  - Receive webhook when a page starts/finishes translating; post updates to Slack/Email.
  - If provider fails, auto‑retry with fallback provider; escalate if SLA violated.
- Glossary Enforcement Pipeline
  - Nightly job fetches changed pages; runs enforcement; opens suggestions via API.
- QA Sampling
  - Sample 5% of pages; assign to reviewers; send reminders if idle > 48h.
- Cost & Usage Analytics
  - Aggregate tokens/time by doc and provider; push to BigQuery/ClickHouse.
- User Lifecycle
  - On invite → send onboarding emails, create default glossaries, seed instructions.

## Core Integration Points
- Webhooks from our backend:
  - `POST /hooks/n8n/page-status` → payload `{docId, pageNumber, status, provider, latencyMs, cost}`
  - `POST /hooks/n8n/suggestion` → payload `{docId, pageId, suggestionId, status}`
- n8n calls our API:
  - `POST /api/suggestions/:id/accept`
  - `POST /api/documents/:id/pages/:n/translate`
  - `GET /api/quality/:docId`

## Example Workflow: Provider Fallback & Notification
- Trigger: Webhook node on `/hooks/n8n/page-status`.
- If status == failed
  - HTTP node: POST to `/api/documents/{id}/pages/{n}/translate` with `{ provider: 'argos' }`.
  - Slack node: notify channel with diagnostic id.
  - If retry fails: create task in Linear/Jira via node; email owner.

Payload example
```json
{
  "docId": 101,
  "pageNumber": 12,
  "status": "failed",
  "provider": "openai",
  "latencyMs": 4321,
  "cost": 0.0023,
  "error": "rate_limited"
}
```

## Example Workflow: Nightly Glossary Enforcement
- Trigger: Cron node daily at 02:00.
- HTTP node: `GET /api/documents/changed?since=${yesterday}`.
- For each document:
  - HTTP node: `POST /api/enforce-glossary?docId=${doc.id}`.
  - Wait node: backoff, then poll `GET /api/enforce-status?jobId=...`.
  - On completion: Slack summary with counts; create review task if violations > threshold.

## Example Workflow: QA Sampling
- Trigger: Cron node hourly.
- HTTP node: `GET /api/pages?status=completed&sample=5%`.
- For each page:
  - Create suggestion review assignment via `POST /api/assignments`.
  - If not reviewed in 48h: send reminder via Email/Slack.

## Design Tips
- Keep workflows idempotent by using external ids and checking status before acting.
- Use n8n credentials with least privilege; rotate regularly.
- Prefer event‑driven webhooks over polling; throttle to avoid storms.

## Error Handling Patterns
- Circuit breaker for provider retries to avoid cascading failures.
- Dead letter queue: send failed events to S3/object storage for later replay.
- Alerting: PagerDuty/Slack notifications with severity mapping.

## Version Control & Promotion
- Export workflow JSON to repo under `ops/n8n/`.
- Use environment vars in n8n for API base URLs and keys.
- Promote workflows across `dev` → `staging` → `prod` via CI job.

## Security
- IP allowlist on webhook endpoint; HMAC signature validation.
- Encrypt creds at rest; audit access.

## Actionable Tickets
- Deploy n8n with Postgres and redis queue; enable basic auth and HTTPS.
- Implement `/hooks/n8n/*` endpoints in FastAPI with HMAC verification.
- Build “provider fallback” and “nightly enforcement” base workflows.
- Add Linear/Jira, Slack, and Email creds; create templates.

