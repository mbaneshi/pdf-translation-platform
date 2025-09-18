# Development Process (TDD + Delivery)

## Principles
- TDD by default; write tests first for new modules and APIs.
- Small, frequent commits and merges; keep main always green.
- Conventional Commits; clear PR descriptions and checklists.
- Infrastructure as code; update docs alongside changes.

## Branching & Commits
- Branch naming: `feat/<area>-<short-desc>`, `fix/<area>-<short-desc>`, `chore/infra-...`.
- Commits: Conventional Commits (subject ≤72 chars), context in body.
- Examples:
  - `feat(translation): add token-aware chunker with tests`
  - `refactor(services): extract OpenAIClient interface`
  - `docs(roadmap): add V3 TDD plan and timeline`

## Pull Requests
- Required: description, linked issue, screenshots for UI, test notes, migration steps.
- CI must pass: `./check-quality.sh` runs pytest and jest.
- Review checklist:
  - Tests cover success/edge/error paths and avoid real network.
  - No secrets; env driven config.
  - Backwards compatible or feature-flagged.
  - Docs updated (CHANGELOG, relevant doc/* files).

## Testing
- Backend: `python -m pytest -m "not e2e" -v` (coverage gate 80%, new modules 90%).
- Frontend: `npm run test:ci` (coverage 80%).
- E2E (optional nightly): smoke via small PDF fixture; background job completes; export present.

## Releases
- Tag milestones (e.g., v2.1.0-m1) and generate release notes from CHANGELOG.
- Keep release artifacts/notes in GitHub Releases; attach doc links.

## Operational Readiness
- Runbook updated (Traefik, credentials, endpoints).
- Dashboards: translation throughput, latency, errors, costs.
- Alerts: rate limit spikes, job failures, budget overages.

## Documentation Discipline
- Update:
  - CHANGELOG.md (Unreleased → release)
  - MASTER_PLAN.md (status block)
  - doc/CURRENT_STATE.md
  - doc/EXECUTION_PLAN.md (timeline adjustments)
  - Feature-specific docs under doc/
