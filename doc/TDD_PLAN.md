# Test-Driven Development Plan (Red → Green → Refactor)

This plan guides development for the GitHub-like UX, semantic PDF translation, review workflow, and exports, using a strict TDD loop.

## Scope of this TDD iteration
- Backend endpoints for page-level review
  - GET /api/pages/{page_id}
  - PATCH /api/pages/{page_id}
  - POST /api/pages/{page_id}/approve
  - POST /api/pages/{page_id}/reject
- Frontend review page behavior
  - Renders side-by-side (original | translation)
  - Loads page detail from API
  - Saves edited translation (optimistic update)
  - Approve/Reject triggers API and UI updates

## Red → Green Strategy
1) RED (this commit)
   - Add failing backend API tests that describe expected contract and behavior.
   - Add failing frontend tests (Jest/RTL) that define UI behavior and API calls.
2) GREEN (next commits)
   - Implement minimal backend (models/serializers/routes/services) to satisfy tests.
   - Implement frontend review components to satisfy tests.
3) REFACTOR
   - Consolidate duplication, naming, and error handling.
   - Improve test coverage and edge cases.

## Backend: Expected API Contract
- GET /api/pages/{page_id}
  - 200: { id, document_id, page_number, blocks: [ { id, type, bbox, text, segments: [ { id, bbox, text, translated_text } ] } ] }
  - 404: when page not found
- PATCH /api/pages/{page_id}
  - Body: { translated_text?: string, segments?: [{ id, translated_text }] }
  - 200: { message: 'updated', page_id }
  - 400: invalid payload
  - 404: page not found
- POST /api/pages/{page_id}/approve | /reject
  - 200: { message: 'approved' | 'rejected', page_id }
  - 404: page not found

## Frontend: Review Page Behavior
- Given a route `/documents/:id/review?page=:n` or `/review?documentId=:id&page=:n`
  - Loads page detail and renders:
    - OriginalPane (PDF/text placeholder) with segments overlay
    - EditorPane with segment list; shows translated_text and allows editing
  - On save:
    - Calls PATCH /api/pages/{page_id}
    - Shows success toast and updates UI
  - Approve/Reject buttons call their endpoints and reflect status

## Test Commands
- Backend: `cd backend && python -m pytest -v -m api`
- Frontend: `cd frontend && npm run test:ci`

## Notes
- Use realistic factories for PDFPage and related entities.
- Tests should not assume global state; isolate per test.
- Prefer small, focused tests; integration tests for end-to-end page review flow.

