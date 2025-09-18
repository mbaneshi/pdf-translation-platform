# Frontend UX/UI Enhancement & Test Coverage Plan

Date: 2025-09-18
Owner: PDF Translation Platform

## Context
Based on doc/SYSTEM_STATUS_AND_USER_GUIDE.md, the platform is production‑ready with:
- Upload (basic/enhanced), semantic analysis, sample translate, gradual translate
- Real‑time progress with tokens/costs
- Export (Markdown)
- Monitoring/health endpoints

Frontend currently offers upload, document view, progress polling, test translate, and export.
Our goals: improve operator/user ergonomics, add review affordances, and widen test coverage to match backend guarantees.

## UX Principles
- Clarity: show document state, costs, and next actions prominently.
- Feedback: instant affordances (toasts, inline messages, skeletons) for all async ops.
- Safety: guard rails around potentially costly actions (confirmations, budget hints).
- Accessibility: WCAG AA color contrast, keyboard navigation, ARIA role coverage.
- RTL readiness: ensure Persian rendering and layout mirror where applicable.

## UI Enhancements (Prioritized)
1) Translation Review (Side‑by‑Side)
- Page panel with Original (left) vs Translated (right); sticky toolbar with actions.
- Actions: copy translated, “Mark as sample approved,” retest page.
- Diff view toggle (inline highlights) for quick visual comparison.

2) Progress & Cost Visibility
- In document header: model name, progress bar, ETA, total cost (actual), tokens in/out.
- Per‑page: badges for tokens in/out and cost; tooltip with complexity.
- Auto‑refresh indicator and pause/resume polling button.

3) Upload & Error UX
- Drag‑n‑drop refinements: show file info and pre‑validation messages.
- Clear server/network error banners with retry.
- Soft‑limit notice for 100MB; link to “optimize PDF” tips.

4) Export & Share
- Export menu: Markdown (now), JSON (future), Copy to clipboard.
- Filenames sanitized; progress while generating; success toast with size.

5) Accessibility & Theming
- Audit interactive elements for aria‑labels/roles, keyboard traps, focus rings.
- High‑contrast theme toggle option.

6) Performance
- Virtualize page list for large docs.
- Debounce polling, backoff on 429/5xx from progress endpoint.

## Test Coverage Additions

Unit/Component (Jest + Testing Library)
- API client
  - progress: ok path returns totals, UI renders tokens/cost/percent
  - export: successful body triggers client download; error shows toast
  - upload: FormData request without manual content‑type; error branches (413/500/network)
- Hooks
  - useDocument: happy path; partial failure (doc ok, pages fail) preserves doc and sets error
  - useTranslation: start translation sets translating, resolves, handles error
  - useFileUpload: success, error, unknown throw, concurrent uploads
- Components
  - FileUpload: validation (type/size/empty), network/server errors, onUploadError callback
  - DocumentViewer: progress polling renders; pause polling, test translate action; export button flow
  - Review Panel (new): renders both panes, toggles diff, approve sample POST
- Accessibility
  - Basic a11y smoke via role queries (buttons, headings, lists) and keyboard tab order for key views

Integration (Jest + MSW)
- Mock API routes (/api/documents/*, /api/enhanced/*) to simulate:
  - Real‑time progress updates with token/cost accumulation
  - Export payloads and failures
  - Rate limit (429) and retry/backoff observations (UI messaging)

Optional E2E (Playwright) [future]
- Upload → extract → test translate → progress visible → export download
- Mobile viewport smoke and keyboard navigation checks

## Implementation Steps
1) Add ReviewPanel component and route/state wiring
- New component `components/ReviewPanel.tsx`; integrate into DocumentViewer row action “Open Review”.
- API: GET page content; POST approve sample.

2) Enhance DocumentViewer header
- Add model name, ETA (derived from pages processed / elapsed), totals.
- Pause/resume polling button; UI indicator for polling state.

3) Improve FileUpload
- Inline hints for size/type; show selected file name before send; retry button.

4) Tests & Mocks
- Introduce MSW server in tests with per‑suite handlers for progress/export.
- Add tests for new ReviewPanel and expanded DocumentViewer states.

5) Accessibility pass
- Add ARIA labels, role assertions, and keyboard focus tests on critical controls.

## Milestones & Owners
- Week 1: Review UI + progress header + tests (component/hook/api) [Frontend]
- Week 2: MSW integration tests + accessibility tests + performance tweaks [Frontend]

## Success Criteria
- Jest suites ≥ 90% pass with global coverage ≥ 80% (threshold retained).
- Green runs for: upload flows (happy/error), progress rendering, export, translation actions.
- Review Panel usable and accessible (keyboard/aria checks pass).
- No regressions in existing components/pages.

## Risks & Mitigations
- Flaky polling tests → MSW with deterministic timers; use fake timers and act/waitFor.
- Large DOM in page list → virtualization to maintain test performance.
- Diff rendering complexity → start with lightweight inline diff (word‑level) and snapshot test basic structure only.

## Tracking
- Create issues:
  - Frontend: ReviewPanel, Progress header enhancements, MSW tests, A11y improvements, Virtualized list.
  - Label: `frontend`, `ux`, `p0`, `testing`.

