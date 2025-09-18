# Frontend Test Report

Date: 2025-09-18
Owner: PDF Translation Platform

## Summary
- Test suites: 7 total
- Passed: 4
- Failed: 3
- Location: `frontend/`

## What Changed This Iteration
- Added polyfills and mocks for stable Jest env:
  - `whatwg-fetch` polyfill for `fetch`/`Response`/`Request`/`Headers` in `frontend/jest.setup.ts`.
  - Robust mock for `react-hot-toast` (default export + named `toast`).
- Implemented hooks expected by tests in `frontend/hooks/index.ts`:
  - `useDocument`, `useTranslation`, `useFileUpload` (state management, error handling, and API interaction).
- FileUpload now supports `onUploadError` and emits detailed error info (`frontend/components/FileUpload.js`).
- API client hardening (`frontend/lib/api.js`):
  - Honors `NEXT_PUBLIC_API_URL` uniformly (even localhost).
  - Conditional headers to avoid breaking FormData boundaries.
  - Safer response parsing (tolerates text/JSON).

## Current Failures (Focus)
1) tests/lib/api.test.ts
   - getDocument returns `undefined` in assertion (`res.id` expected `1`).
   - uploadDocument result `undefined` in assertion (`res.document_id` expected `1`).
   - Likely root cause: test Response mocks vs apiFetch parse flow. Needs small adapter to ensure parsed object is returned consistently for mocked Responses.

2) tests/hooks/index.test.ts
   - Partial API failure case expects pages `[]` while preserving document; timing/page clearing requires explicit pages reset before 2nd fetch.
   - Upload error branches expect `error` state set before throw, and throw always uses `Error(message)`.
   - Integration case has tight act()/waitFor timing; ensure stable state transitions in hooks.

## Passes (Highlights)
- Components: `DocumentViewer`, `ThemeSelector`, pages `index` are passing.
- Setup/environment test passes with new polyfills.

## Next Steps to Go Green
- API tests
  - In `frontend/lib/api.js` `apiFetch`: if `response.ok` and text parse returns falsy, fallback to `await response.json()`; guarantee object return for standard JSON responses in tests.
- Hooks tests
  - `useDocument`: clear pages before attempting the pages fetch; preserve document on pages error; set `error` accordingly.
  - `useFileUpload`: ensure `setError(message)` always happens before rejecting and that non-Error throws are wrapped into `Error`.
  - Address minor act() warnings by awaiting state changes in tests if needed (non-functional).

## How To Reproduce Locally
- Install frontend deps:
  - `cd frontend && npm install`
- Run tests:
  - `npm test -- --watchAll=false`

## Notes
- Back-end tests were not executed in this environment (Python not available). Frontend tests are the current focus.
- Once frontend is green, add tests covering:
  - `/api/enhanced/translation-progress/{id}` rendering (tokens/cost/progress).
  - `/api/enhanced/export/{id}` download success path and error state.

