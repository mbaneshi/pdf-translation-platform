# Project Management

Clear cadence, artifacts, and responsibilities to keep delivery predictable.

## Cadence
- Sprints: 1–2 weeks, timeboxed; end with a demo and doc updates.
- Standups: async daily notes in tracking issue/PR; blockers flagged early.
- Planning: backlog grooming mid‑sprint; sprint planning with priority matrix.
- Retrospective: brief written retro per sprint; capture actions in backlog.

## Roles (RACI)
- Product/Owner: priorities, acceptance criteria (A)
- Tech Lead: architecture, code quality, estimates (A)
- Backend: services, workers, tests (R)
- Frontend: UI, hooks, tests (R)
- DevOps: infra, CI/CD, observability (R)
- Reviewers: code reviews, test coverage (C)
- Stakeholders: feedback on demos (I)

## Artifacts
- Backlog: GitHub issues with labels: area (backend/frontend/infra), type (feat/fix/docs/test/chore), size (S/M/L).
- Roadmap: doc/ROADMAP.md
- Execution plan: doc/EXECUTION_PLAN.md
- Current state: doc/CURRENT_STATE.md
- Process: doc/DEVELOPMENT_PROCESS.md
- Enhancements: doc/TRANSLATION_ENHANCEMENTS_V1–V3.md
- Risks: tracked in issues, summarized in EXECUTION_PLAN.

## Definitions
- Definition of Ready (DoR)
  - Problem, scope, acceptance criteria, test approach, dependencies, estimate.
- Definition of Done (DoD)
  - Code + tests + docs + changelog; CI green; feature flag/config documented; demoable.

## Estimation
- Relative sizing (S/M/L) mapped to sprint capacity; re‑estimate after spikes.
- Track throughput (# items/sprint) to forecast.

## Change Control
- Any major scope/date change → updated ROADMAP and EXECUTION_PLAN; CHANGELOG “Unreleased” updated.

## Commit & PR Hygiene
- Conventional Commits; small PRs with focused scope.
- PR checklist: tests added/updated, CI passing, docs updated, risks noted.

## Risk Management
- Maintain a visible risk list with severity/likelihood and mitigations.
- Common risks: cost spikes, rate limits, model regressions, infra changes.

