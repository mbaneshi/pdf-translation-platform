# Insights on FRONTEND_ENHANCEMENT_ROADMAP.md

Date: 2025-09-18
Owner: PDF Translation Platform

## Snapshot Assessment
- The roadmap is ambitious and aligned with backend capabilities (enhanced upload, semantic analysis, progress, export).
- Priority correctly emphasizes test stability first, then feature depth.
- Some targets are overstated (100% tests); maintaining ≥80–90% with critical-path integration tests is more sustainable.

## What Looks Strong
- Tight coupling to backend features: progress metrics (tokens/cost), enhanced upload, export.
- Early investment in test primitives (robust response parsing, FormData handling) to stabilize CI.
- Clear phasing: foundation → integration → UX polish → advanced flows.

## Gaps / Refinements
- Test realism
  - Add MSW for API route simulation; avoid brittle hand‑rolled fetch stubs.
  - Use fake timers for polling tests; assert debounce/backoff behavior on 429/5xx.
- Accessibility & RTL
  - Formalize RTL snapshots for Persian: verify punctuation shaping and alignment in UI blocks.
  - Add keyboard navigation tests (Tab flow) for the Review Panel and dialogs.
- Performance
  - Virtualize large page lists (react‑window) and include interaction tests for virtualization boundaries.
- State management
  - Consider a thin store (Zustand/Context) for document/progress state to reduce prop drilling and make polling pausable/persistent across views; add unit tests for store actions.
- Export UX
  - Validate file naming and blob creation under various browsers; add unit tests for download fallback.
- Error taxonomy
  - Standardize API error mapping (network, 4xx, 5xx, rate‑limit). Add snapshot tests for error banners and retry buttons.

## Sequenced Plan (Refined)
1) Test Stability & Infra
- Introduce MSW server and fixtures for: upload (basic/enhanced), progress, export, test translate.
- Harden apiFetch once (headers for FormData, resilient parsing) and add api unit tests per route.

2) Core UX Hooks & Components
- useDocument/useTranslation/useFileUpload tests: success, partial failure, concurrency.
- DocumentViewer header: ETA calc, model display, aggregated tokens/costs with tests.

3) Review Experience
- Implement ReviewPanel (side‑by‑side), approve sample action, diff toggle.
- Tests: render states, diff toggle, approve action success/error.

4) Accessibility & RTL
- Add role/aria assertions and keyboard navigation tests.
- Snapshot RTL rendering for Persian excerpts in components (no backend call needed).

5) Performance & Observability
- Virtualize page table and provide MSW-driven long document test.
- Add lightweight perf marks in dev; no test gate on perf numbers.

## Concrete Deliverables
- Components: ReviewPanel, ProgressHeader.
- Testing:
  - MSW setup + per-suite handlers.
  - Unit tests for api, hooks, components.
  - Integration tests for polling/export flows.
  - Basic a11y/RTL tests.
- Docs: Update USER_MANUAL with review flow; add DEV_GUIDE for MSW usage.

## Success Criteria
- CI green, global coverage ≥80%.
- Stable tests for: upload, progress, export, review approve, error branches.
- No flakiness in polling tests (fake timers + MSW verified).

## Risks & Mitigations
- Flaky network tests → MSW + deterministic timers.
- Large DOM → virtualization + focused queries in tests.
- Diff complexity → start simple (word‑level), expand if time permits.

