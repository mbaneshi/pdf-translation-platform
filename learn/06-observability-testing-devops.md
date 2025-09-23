# Observability, Testing, and DevOps

Deliver reliable features with metrics, tracing, tests, and smooth deploys.

## Observability
- Metrics: request latency, error rates, translation costs, provider errors
- Tracing: end-to-end across frontend → API → workers → provider
- Logs: structured, redacted; correlation ids

## Testing
- Backend: pytest (unit, integration). Coverage ≥ 80% (see `backend/pytest.ini`)
- Frontend: RTL + Jest; e2e via Playwright for reader flows
- Load: k6/Gatling for WS rooms and translate throughput

## CI
- Run `./check-quality.sh` on PR; block if failing
- Artifacts: store coverage reports; post summaries

## Deploy
- Dockerize API and web; use blue/green or canary where possible
- Secrets via env; never commit secrets

## SLOs
- API p95 < 150ms (reads), WS echo < 150ms in-region, first-token < 500ms p95

## Runbooks
- Provider outage → switch router default; trigger n8n fallback workflow
- DB latency spikes → analyze slow queries; add indexes

