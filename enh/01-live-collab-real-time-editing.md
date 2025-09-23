# Live Collaboration & Real‑Time Editing Blueprint

This document presents a comprehensive plan for implementing live collaboration and real‑time editing for a side‑by‑side PDF translation experience. It details product UX, data flow, conflict resolution, operational concerns, and quality instrumentation tailored to a PDF translation platform targeting a best‑in‑class AI assistance experience.

## Goals
- Real‑time, low‑latency collaborative editing of translated content, per segment and per page.
- Presence, cursor/selection sharing, and granular permissions for teams.
- Robust offline‑first behavior with conflict‑free merges on reconnection.
- Scalable signaling, persistence, and audit trails suitable for enterprise use.

## Core Use Cases
- Multiple editors refine translations live while a background translator streams results.
- SME/reviewer annotates or proposes edits; translator accepts with one click.
- Lead linguist locks a segment for a short window (soft lock) to apply critical fixes.
- Comment threads on segments with resolve/reopen lifecycle and task assignment.

## Collaboration Model: CRDT First
- Choose CRDT (e.g., Yjs) for conflict‑free, offline‑capable rich‑text editing.
- Map per‑segment content to a Y.Text; page state is a Y.Map of segments.
- Maintain lightweight metadata (author, timestamps, glossary flags) parallel to content.
- Use awareness protocol for presence cursors, color badges, and typing indicators.

## Data Structures
- Document
  - id, title, ownerId, createdAt, updatedAt, settings
  - languages: sourceLang, targetLang
  - providers: activeProvider, providerHistory
  - permissions: role mapping (owner, editor, reviewer, viewer)
- Page
  - id, docId, pageNumber, status (pending, processing, done, failed)
  - layout: blocks, regions, tables, anchors
  - translation: segments[], provider, quality, costEstimate
- Segment
  - id, pageId, anchor (bbox or token span), sourceText, targetText
  - glossaryFlags[], comments[], suggestions[]
  - locks: userId?, until?
  - history: versions[], acceptedSuggestionId?

## Transport & Topology
- Client ↔ Collaboration Edge via WebSocket (primary), SSE fallback, polling last resort.
- Edge ↔ State Service via durable room process (e.g., Redis Streams or nats‑jetstream backed).
- Persist snapshots and ops deltas to Postgres + object store (periodic compaction).
- Horizontal scale using sticky sessions by roomId and autoscaling room processes.

## Presence & Awareness
- Track participants per room: userId, role, color, cursor position, selection ranges, activity heartbeat.
- Soft‑timeouts for stale presence; visual indicators fade after 10s inactivity.
- Privacy: redact exact cursor position when viewer role is set to “anonymous share.”

## Permissions & Roles
- Owner: full control; manage roles; export audits.
- Editor: live edit segments; accept/reject suggestions.
- Reviewer: comment, propose suggestions, resolve threads.
- Viewer: read‑only; can request changes.
- Guest: temporary access links scoped to specific pages, time‑boxed.

## Locking Strategy
- Default optimistic editing (no hard locks) backed by CRDT conflict resolution.
- Soft locks: a segment shows “editing by” when user actively types; respectful UI nudges others.
- Escalation: lead can apply a 60s hard lock for critical fixes; lock events recorded and visible.

## Comments & Threads
- Per‑segment threaded comments with mentions `@user` and statuses (open, resolved, reopened).
- Quick actions: “create task,” “assign to…,” “convert to suggestion.”
- Smart filters: unresolved only, by assignee, by page, by glossary term.

## Suggestions Workflow
- Any user can propose a suggestion; suggestions are diffed against current segment.
- Editors/Reviewers can accept/reject; acceptance creates a new version and closes the suggestion.
- Batch operations: accept all of a page/from glossary enforcement batch.
- AI‑generated suggestions are tagged with provider/model for traceability.

## Versioning & Audit
- Each accepted edit yields a new immutable version (delta + metadata).
- Auditable trail: who changed what/when/why (comment link), signature hash for export.
- Time‑travel: view and restore any version; compare versions side‑by‑side.
- Export audit in JSONL and human‑readable PDF.

## Offline & Intermittent Connectivity
- Local CRDT updates persist and merge when reconnected.
- UI surfaces “offline mode” banner with retry/backoff state for translations.
- Conflict visualization: when merges alter visible text, show a compact diff tooltip.

## Latency Budgets
- Keystroke → peer echo: < 150ms p95 in‑region; < 350ms cross‑region.
- Presence updates: 1s heartbeat; collapse bursts with 100ms debounce.
- Initial page join: snapshot + ops hydrate < 1s on typical networks.

## Scalability Targets
- Rooms: 10k concurrent rooms per cluster; 50 active users per room typical.
- Messages: sustain 5k ops/sec per node with backpressure and batching.
- Storage: snapshot every N ops or 10s; compact nightly; retain full history 90 days.

## Failure Modes & Resilience
- Client reconnection strategy with exponential backoff and jitter.
- Server hot failover of room processes; resume from last persisted op sequence.
- Graceful degradation: hide avatars at high churn; limit presence frequencies.

## Security & Compliance
- Auth: short‑lived WS tokens (JWT) minted by API; scope: roomId, role, ttl.
- E2E transport TLS; optional content encryption at rest with KMS keys per tenant.
- PII controls: redact names in exported public shares; configurable data retention.

## Integration With Translation Pipeline
- Streaming MT: as model tokens stream, CRDT sets a “shadow draft” layer.
- User edits operate on the main layer; reviewers can pull from shadow layer into suggestions.
- Segment freeze during streaming if user is editing; or stream into a parallel suggestion.

## Metrics & Observability
- Collab: room join latency, message rate, dropped ops, reconnects.
- Editing: characters per minute, segments touched, suggestion accept rate.
- Reliability: WS uptime, backpressure activations, snapshot size, compaction time.

## Testing Strategy
- Unit: CRDT transforms, permissions checks, serializers.
- Integration: room lifecycle, reconnect merge correctness, version audit integrity.
- Load: soak tests with scripted typing patterns and cursor churn.
- Chaos: kill room processes; verify hot restoration correctness.

## Frontend Implementation Details
- Editor: ProseMirror/TipTap or Lexical bound to Yjs via bridge.
- Presence: y‑protocol awareness → avatars, cursors, selections with color hashing.
- Rendering: virtualized segment list; reconcile minimal React nodes per op.
- Performance: requestIdleCallback to coalesce updates; keep main thread responsive.

## Cursor & Selection Rendering
- Draw overlay layers on both panes; ensure high‑contrast and unobtrusive labels.
- Smooth, throttled cursor position updates; lerp positions for micro‑motion.
- Selection ranges snap to segment boundaries in translate pane; freeform in comments.

## Edge Cases
- Large segment (>5k chars): split suggestion flows; hard cap on simultaneous cursors.
- Concurrent accept/reject: server side idempotent operations; UI resolves deterministically.
- Role change mid‑edit: downgrade permissions instantly; keep local buffer but block submit.

## API Sketches
- `POST /collab/rooms` → create or join token.
- `GET /documents/:id/pages/:n/collab-snapshot` → CRDT snapshot + metadata.
- `WS /collab/:roomId` → ops stream; subchannels for presence, comments, suggestions.

## Storage Layout
- tables
  - collab_rooms(id, doc_id, page_id, created_at, ttl)
  - collab_ops(room_id, seq, payload, created_at)
  - collab_snapshots(room_id, version, blob_uri, created_at)
  - segment_versions(segment_id, version, diff, author_id, ts, reason)

## Migration Plan
- Phase 1: single‑user CRDT w/ persistence.
- Phase 2: presence & cursors; comments.
- Phase 3: suggestions + roles.
- Phase 4: scaling, snapshots, audits, and enterprise features.

## Accessibility Considerations
- Announce presence joins/leaves non‑intrusively.
- Keyboard shortcuts for accepting suggestions, cycling comments, moving between diffs.
- High‑contrast colors for cursors; respect reduced motion.

## Privacy Modes
- Redacted share links: mask names, show anonymous colors.
- Private comments: visible only to reviewers; audit still records event types.

## Cost Controls
- Pause presence broadcasting in background tabs.
- Batch ops to reduce server load; compress payloads with CBOR.

## Example UI Interactions
- Hover a segment: reveal “Suggest,” “Comment,” “History.”
- Accept suggestion: micro‑diff animates merge; toast with undo (10s).
- Reviewer assigns: quick panel with user search; @mention notifies.

## Risks & Mitigations
- Editor performance under heavy ops → virtualization + coalescing + profiling.
- Data corruption → append‑only ops + checksums + regular snapshots.
- User confusion in conflicts → clear diffs, explainers, and safe undo.

## Roadmap KPIs
- p95 echo latency < 150ms in‑region.
- Suggestion acceptance > 60% for AI proposals.
- Recoverability: 0 data loss in chaos tests across 10k rooms.

## Open Questions
- Per‑tenant encryption boundaries and key rotation workflows.
- Long‑term archival format for CRDT snapshots.
- Legal holds and eDiscovery export needs.

## Appendix: Shortcut Map (Draft)
- J/K: next/prev segment
- G: go to page
- T: translate page
- A: accept suggestion
- R: reject suggestion
- C: new comment
- L: toggle lock (lead only)
- U: undo last accepted edit

## Appendix: Event Names
- collab.join, collab.leave
- collab.op.apply, collab.op.drop
- collab.snapshot.write, collab.snapshot.read
- comment.create, comment.resolve, comment.reopen
- suggestion.create, suggestion.accept, suggestion.reject
- version.create, version.restore

