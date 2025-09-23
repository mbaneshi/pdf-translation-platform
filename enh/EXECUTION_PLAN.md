# Execution Plan: Milestones, Tickets, and Acceptance Criteria

This plan prioritizes delivery of real‑time collaboration, multi‑provider translation, and a dual‑pane reader with suggestions. Each ticket includes scope, files, acceptance criteria, and notes to aid humans and AI coding tools.

## Milestone 1 — Foundations (Week 1–2)

- M1-T1: Define Provider Abstraction
  - Scope: Introduce provider interface and stub adapters.
  - Files
    - backend/app/services/providers/__init__.py
    - backend/app/services/providers/base.py
    - backend/app/services/providers/openai_provider.py
    - backend/app/services/providers/argos_provider.py
    - backend/app/services/providers/openai_compatible_provider.py
    - backend/app/services/providers/deep_translator_provider.py
    - backend/app/services/llm_client.py (light refactor to use interface)
  - Acceptance
    - `BaseProvider.translate(text, src, tgt, options)` sync + streaming API specs exist.
    - OpenAI provider implemented and used behind a flag in `translation_service.py`.
    - Unit tests for provider selection logic.

- M1-T2: API Contracts for Per‑Page Lazy Translation
  - Scope: Add endpoints for lazy translate and status fetch.
  - Files
    - backend/app/api/endpoints/enhanced_documents.py (extend)
    - backend/app/api/endpoints/documents.py (ensure parity)
    - backend/app/models/models.py (add fields if needed: provider, cost_estimate details)
  - Acceptance
    - POST `/documents/{id}/pages/{n}/translate` kicks a job and returns jobId/status.
    - GET `/documents/{id}/pages/{n}` returns source, translated, status, provider, cost.

- M1-T3: Collab Service Skeleton
  - Scope: Define WS endpoint, room model, and Yjs-compatible op envelope.
  - Files
    - backend/app/api/endpoints/collab.py
    - backend/app/services/collab/room_manager.py
    - backend/app/services/collab/models.py
  - Acceptance
    - WS `/collab/{pageId}` echoes pings and broadcasts messages to room.
    - Basic presence messages supported.

## Milestone 2 — Reader Prototype (Week 2–3)

- M2-T1: Dual‑Pane Reader Skeleton (Frontend)
  - Scope: Components and routes, no final polish.
  - Files
    - frontend/app/doc/[id]/page.tsx (App Router entry)
    - frontend/components/viewer/PdfCanvas.tsx
    - frontend/components/viewer/TranslatePane.tsx
    - frontend/components/viewer/MiniMap.tsx
    - frontend/components/viewer/Toolbar.tsx
    - frontend/hooks/useTranslatePage.ts
  - Acceptance
    - Renders original canvas and translated pane placeholders.
    - Button triggers lazy translate for current page via API.

- M2-T2: Suggestion Popovers
  - Scope: Context menu + popover with apply/cancel.
  - Files
    - frontend/components/suggestions/SuggestionPopover.tsx
    - frontend/hooks/useSuggestions.ts
  - Acceptance
    - Right‑click segment opens popover with placeholder suggestions.

- M2-T3: WebSocket Wiring
  - Scope: Hook up WS for page status/stream updates.
  - Files
    - frontend/lib/ws.ts
    - frontend/hooks/usePageChannel.ts
  - Acceptance
    - Page status updates reflect in UI without refresh.

## Milestone 3 — Suggestions, Glossary, and Quality (Week 3–4)

- M3-T1: Suggestions API
  - Files
    - backend/app/api/endpoints/suggestions.py
    - backend/app/services/suggestions_service.py
  - Acceptance
    - GET suggestions per page; POST accept/reject.

- M3-T2: Glossary Enforcement MVP
  - Files
    - backend/app/api/endpoints/glossary.py
    - backend/app/services/glossary_service.py
  - Acceptance
    - CRUD glossary; enforcement job produces suggestions.

- M3-T3: Quality Scoring MVP
  - Files
    - backend/app/services/quality_service.py
  - Acceptance
    - Compute page/document scores; API returns metrics.

## Milestone 4 — Collab Real‑Time Editing (Week 4–6)

- M4-T1: CRDT State and Snapshots
  - Files
    - backend/app/services/collab/snapshot_store.py
  - Acceptance
    - Snapshot/rehydrate works on restart; versioning endpoints exist.

- M4-T2: Comments/Threads
  - Files
    - backend/app/api/endpoints/comments.py
    - frontend/components/comments/CommentThread.tsx
  - Acceptance
    - Create/resolve/reopen threads tied to segment anchors.

- M4-T3: Soft Locks and Presence UI
  - Files
    - frontend/components/collab/PresenceLayer.tsx
  - Acceptance
    - Show cursors/avatars; soft lock badges on active edits.

## Global Non‑Functional Requirements
- A11y: Keyboard navigation, focus management, ARIA, reduced motion.
- Perf: LCP ≤ 1.8s reader; scroll/zoom 60fps; streaming first token ≤ 500ms p95.
- Security: JWT WS tokens; sanitize rendered HTML in translation pane.

## Ticket Template (Use for All New Items)
- Title
- Context
- Paths
- API/schema
- Steps
- Acceptance criteria
- Notes

