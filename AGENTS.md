# Repository Guidelines

## Project Structure & Module Organization
- `backend/app`: FastAPI app. Routers in `app/api/endpoints/`, services in `app/services/`, models in `app/models/`.
- `backend/tests`: `unit/`, `integration/`, `e2e/` test suites.
- `frontend`: Next.js app. Pages in `pages/`, UI in `components/`, hooks in `hooks/`, tests in `tests/`.
- Infra: `docker-compose.yml`, `Caddyfile`, `start.sh`, `check-quality.sh`, `uploads/`, `logs/`, `backups/`.

## Build, Test, and Development Commands
- Backend (dev): `cd backend && pip install -r requirements.txt && uvicorn app.main:app --reload`
- Frontend (dev): `cd frontend && npm install && npm run dev`
- Docker stack: `./start.sh` (or `docker-compose up -d db cache api worker monitor web`)
- Backend tests: `cd backend && python -m pytest`
- Frontend tests: `cd frontend && npm test` (CI: `npm run test:ci`)
- All checks (CI parity): `./check-quality.sh`

## Coding Style & Naming Conventions
- Python: 4-space indent, Black (88 cols), isort (profile=black), Ruff, Flake8, MyPy, Bandit. Use type hints. `snake_case` for modules/functions/vars; `PascalCase` for classes.
- TS/React: 2-space indent, ESLint + Prettier, TypeScript. `camelCase` for vars/functions; `PascalCase` for components in `frontend/components/`. Prefer function components + hooks.
- Pre-commit: `pre-commit install` (auto Black/isort/Ruff/ESLint/Prettier on changed files).

## Testing Guidelines
- Backend: pytest with coverage gate 80% (see `backend/pytest.ini`). Name tests `test_*.py`. Use markers (`unit`, `integration`, `e2e`, `api`, `service`, `model`, `slow`). Run: `python -m pytest -v`.
- Frontend: Jest + Testing Library (`frontend/jest.config.ts`) with 80% global thresholds. Name `*.test.tsx`/`*.spec.tsx` under `frontend/tests/`.

## Commit & Pull Request Guidelines
- Use Conventional Commits: `feat:`, `fix:`, `docs:`, `refactor:`, `test:`, `chore:`. Imperative, concise subject; add context in body.
- PRs must include: clear description, linked issues, screenshots/GIFs for UI changes, test coverage notes, and any migration/config steps. Ensure `./check-quality.sh` passes.

## Security & Configuration Tips
- Do not commit secrets. Copy `env.example` to `.env` and set `OPENAI_API_KEY`, `DATABASE_URL`, `REDIS_URL`.
- Artifacts live in `uploads/` and `logs/` (gitignored). Review CORS in `backend/app/main.py` and env in `docker-compose.yml` before deploying.

