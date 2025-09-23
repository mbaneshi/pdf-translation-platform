# Mastery Curriculum for This Platform

This curriculum turns you into a confident contributor to this PDF translation platform. It’s hands-on, repo-aware, and covers backend (FastAPI), frontend (Next.js), realtime collab, LLM providers, Supabase+n8n, testing/observability, and architecture patterns.

Read in order or jump to the topic you need:
- 01-backend-fastapi-mastery.md — Services, endpoints, DB, jobs
- 02-frontend-nextjs-mastery.md — App Router, components, hooks, tests
- 03-realtime-collab-crdt-yjs.md — Presence, Yjs, WS, conflicts
- 04-translation-providers-llm-routing.md — Providers, routing, streaming
- 05-supabase-n8n-mastery.md — Auth/RLS/realtime/storage + workflow automation
- 06-observability-testing-devops.md — Metrics, tracing, tests, CI, deploy
- 07-architecture-design-patterns.md — Modular design, patterns, pitfalls
- 08-hackable-recipes-and-snippets.md — Copy-ready snippets for common tasks

Prereqs
- Python 3.10+, Node 18+, Docker (optional), Postgres (via compose or cloud)
- Make sure env vars are set from `env.example`.

Quick Start
- Backend dev: `cd backend && pip install -r requirements.txt && uvicorn app.main:app --reload`
- Frontend dev: `cd frontend && npm install && npm run dev`
- Tests: `cd backend && python -m pytest -v`; `cd frontend && npm test`

