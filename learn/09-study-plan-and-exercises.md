# Study Plan and Exercises (4–6 Weeks)

A structured path to mastery with weekly goals, exercises, and checkpoints. No implementation required in the repo; use mocks and snippets.

## Week 1 — Backend & Services Fundamentals
- Concepts
  - FastAPI patterns, dependency injection, service layer design, error handling.
  - SQLAlchemy models and transactions; idempotent updates for page status.
- Exercises
  - Write a pseudo-endpoint spec to translate text with cost estimates and error mapping.
  - Design a `TranslationJob` state machine diagram: pending → processing → completed|failed.
  - Draft Pydantic response models for page payloads with typed metadata.
- Code Samples (pseudo)
  - Endpoint contract with request/response types.
  - Service method signatures and error envelopes.
- Checkpoint
  - Explain pros/cons of thin controllers + rich services and where to put caching.

## Week 2 — Frontend Reader & State Management
- Concepts
  - App Router, Server vs Client components, TanStack Query patterns, Zustand for UI state.
  - Virtualization, pdf.js worker separation, accessibility and motion controls.
- Exercises
  - Sketch a component tree for the dual‑pane reader with data dependencies.
  - Model a Query cache key strategy for doc/page/suggestions.
  - Write keyboard shortcut maps and announce patterns for screen readers.
- Code Samples
  - Custom hooks for page data and lazy translate mutations (mock fetch).
  - MiniMap prop contracts and micro-interaction notes.
- Checkpoint
  - Defend a decision to keep page status in server state and split UI state to Zustand.

## Week 3 — Collaboration, Presence, and Comments
- Concepts
  - WebSockets vs SSE vs polling, presence semantics, message envelopes.
  - Yjs basics, awareness, snapshots; when to choose CRDTs.
- Exercises
  - Define WS message schemas for presence, comments, and suggestions.
  - Draw a reconnection flow diagram with backoff and state resync.
  - Design a snapshot frequency policy based on ops/sec and room size.
- Code Samples
  - WS client reconnection helper; presence update throttling pattern.
- Checkpoint
  - Explain the tradeoffs of CRDTs vs server-serialized diffs in this app.

## Week 4 — Providers, Routing, and Streaming UX
- Concepts
  - Strategy pattern for providers; routing based on cost/quality/latency.
  - Streaming translation to UI; backpressure and buffering strategies.
- Exercises
  - Define a provider adapter interface and routing policy in pseudocode.
  - Map UI states for streaming: idle → processing → partial → complete|failed.
- Code Samples
  - Mock stream generator yielding chunks and a consumer rendering line by line.
- Checkpoint
  - Compare streaming via WebSocket, HTTP chunked, and SSE for this product.

## Week 5 — Glossary, Suggestions, and Quality
- Concepts
  - Glossary models, enforcement rules, suggestion lifecycle.
  - Quality metrics and acceptance loops.
- Exercises
  - Model glossary enforcement rules and exceptions as data + finite states.
  - Propose quality KPIs and how to compute them from events.
- Code Samples
  - Diff rendering strategies for segments (word-level vs char-level).
- Checkpoint
  - Justify batch acceptance policies and safeguards.

## Week 6 — Supabase, n8n, and Ops
- Concepts
  - RLS policies, realtime channels, storage flows, webhook security (HMAC).
  - n8n orchestration: retries, alerts, and idempotency.
- Exercises
  - Author RLS read policies that isolate tenants and docs.
  - Draft a provider-fallback n8n workflow JSON with Slack alerts.
- Code Samples
  - JWT validation flow diagrams; signed URL issuance sketch.
- Checkpoint
  - Pick “Supabase as sidecar vs primary” and defend with tradeoffs.

## Capstone (Optional)
- Design a vertical slice: upload → parse → view → translate → suggest → accept → export.
- Produce contracts, mock JSON payloads, component props, and state diagrams.

