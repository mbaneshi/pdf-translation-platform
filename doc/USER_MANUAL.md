# PDF Translation Platform — User Manual and Onboarding

This guide explains how to use the platform end‑to‑end, what each screen does, how to monitor progress, and how to troubleshoot common issues. It also summarizes current functionality and the most impactful enhancements for reliability, correctness, and UX.

---

## What You Can Do

- Upload PDF files for translation (English → Persian).
- Run a sample translation on a page to validate quality/cost.
- Start a full translation job and monitor progress live.
- See token usage and estimated costs per page and in total.
- Download the translated output as Markdown (API; UI button if enabled).
- Observe system metrics via Prometheus/Grafana and track background jobs in Flower.

---

## URLs and Access

- App (frontend): https://pdf.edcopo.info
- API (backend): https://apipdf.edcopo.info
- Metrics: `GET https://apipdf.edcopo.info/metrics` (Prometheus format)
- Celery monitoring (Flower): https://flower.edcopo.info

Notes:
- Flower may be protected by Traefik basic auth in your Traefik stack. If you see a login prompt, use the credentials configured in Traefik `dynamic.yml` or in compose labels. Rotate to a strong password in production.

---

## Quick Start (Operators)

Prerequisites
- Docker, Docker Compose
- External network `traefik-proxy` exists: `docker network create traefik-proxy || true`
- A valid `OPENAI_API_KEY` in `.env` (do not commit secrets)

Launch
1) Copy `.env.example` to `.env` and set variables (at minimum `OPENAI_API_KEY`).
2) Start the stack:
   - `docker compose up -d`
3) Run migrations inside the API container (first time):
   - `docker compose exec api alembic upgrade head`
4) Verify health:
   - `curl -s https://apipdf.edcopo.info/health`
   - Open https://pdf.edcopo.info and ensure the UI loads.
5) Confirm routing in Traefik dashboard of your existing Traefik stack (routers: pdftr-api, pdftr-web, pdftr-flower).

Zero‑downtime updates
- `docker compose pull && docker compose up -d`

Rollback
- Switch image/tag back and `docker compose up -d`.

---

## Using the App (End Users)

1) Open https://pdf.edcopo.info.
2) Upload a PDF. After upload, you will see the document details page with:
   - Total pages and file size
   - Status badge (uploaded/processing/completed)
   - Progress widgets (percentage, total input/output tokens, total page costs)
   - A list of pages showing characters, tokens (in/out), and per-page cost.
3) Try a page (optional):
   - Click “Test Translate” on a page to translate just that page. This is useful to preview quality and cost before a full run.
4) Start full translation:
   - Click “Start Full Translation”. Background workers process each page. The progress area updates every few seconds.
5) Export Markdown:
   - Use the “Download Markdown” button (if present), or call the API endpoint `GET /api/enhanced/export/{document_id}` and save the `content`.

---

## Feature Details

- Chunked translation (for correctness and cost control)
  - Content is split into token‑bounded, paragraph‑aware chunks.
  - Each chunk is translated via Chat Completions; results are re‑assembled and stored per page.
  - Token usage and estimated costs are captured per page and rolled up for the document.

- Progress and cost visibility
  - `/api/enhanced/translation-progress/{document_id}` returns:
    - `progress_percentage`, `pages_processed/total_pages`
    - `tokens_in_total`, `tokens_out_total`, `pages_cost_total`
  - UI polls this endpoint to update progress widgets.

- Monitoring
  - Backend exposes `/metrics` (Prometheus). A Grafana dashboard JSON is provided in `monitoring/grafana-dashboard.json`.
  - Flower shows queue, tasks, and worker health at https://flower.edcopo.info.

---

## Reliability and Correctness

Current status
- Stable compose with healthchecks and Traefik routing.
- Metrics in place for translation latency, tokens, and cost. Dashboard JSON provided.
- Token/cost accounting per page and aggregated at document level.

Recommended enhancements
- Rate limiting (high impact):
  - Add a Redis‑backed token bucket to the LLM client to cap TPM/RPM and respect `Retry-After` headers. Configure env knobs like `OPENAI_TPM_BUDGET`, `OPENAI_RPM_BUDGET`.
  - Set Celery task `rate_limit` on translate tasks and reduce `worker` concurrency during peak.
- Chunk sizing adjustments:
  - Reduce per‑chunk `max_tokens` and chunk target to mitigate bursty TPM usage and improve latency predictability.
- Structure‑aware prompts:
  - Differentiate lists/tables/headers to preserve formatting better; add snapshot tests for invariant formatting.
- Quality gate (optional):
  - Add a reviewer pass for high‑importance pages; store results and allow override.

Operational checks
- SLOs to monitor:
  - Queue latency (Flower/Grafana)
  - Page translation duration histogram (Prometheus)
  - Error rates/429s from provider
- Alerts:
  - 5xx spikes, job stalls, and queue length growth trends.

---

## Troubleshooting

- Upload fails
  - Ensure the file is a non‑empty PDF and below `MAX_FILE_SIZE` (100 MB default).
  - Check API logs: `docker compose logs -f api`

- Page stays in “processing”
  - Verify worker logs: `docker compose logs -f worker`
  - Check Redis connectivity and queue depth (Flower).

- 429 rate limit errors
  - Lower concurrency and chunk sizes; implement the rate limiter as above.
  - Retry later; provider may enforce RPM/TPM caps.

- Can’t access Flower
  - If prompted for basic auth, use the credentials configured in Traefik or enable labels in `docker-compose.yml` under the `monitor` service. Rotate to a strong bcrypt hash.

- CORS/browser errors
  - Confirm `NEXT_PUBLIC_API_URL` and allowed origins match your domains.

---

## API Reference (Selected)

- Upload: `POST /api/documents/upload` (multipart form: `file`)
- Document: `GET /api/documents/{document_id}`
- Pages: `GET /api/documents/{document_id}/pages`
- Start full translation: `POST /api/documents/{document_id}/translate`
- Test translate page: `POST /api/documents/{document_id}/pages/{page_number}/test`
- Progress rollups: `GET /api/enhanced/translation-progress/{document_id}`
- Export Markdown: `GET /api/enhanced/export/{document_id}`
- Health: `GET /health`
- Metrics: `GET /metrics`

---

## Safety and Credentials

- Never commit `.env` with real secrets. Use `.env.example` for placeholders.
- Rotate Flower/Traefik basic auth credentials periodically. Use bcrypt hashes for Traefik `basicauth.users`.

---

## Roadmap Highlights for UX

- Add a visible “Download Markdown” action and DOCX/HTML exporters.
- Side‑by‑side preview (original vs translated) with per‑page navigation and search.
- Progress toasts and better empty/loading states.
- Frontend tests for polling/UI states (MSW + Testing Library).

---

## Appendix: Run Commands

- Backend (dev):
  - `cd backend && pip install -r requirements.txt && uvicorn app.main:app --reload`
- Frontend (dev):
  - `cd frontend && npm install && npm run dev`
- Docker stack:
  - `./start.sh` or `docker compose up -d`
- Backend tests:
  - `cd backend && python -m pytest -v`
- Frontend tests:
  - `cd frontend && npm test`

