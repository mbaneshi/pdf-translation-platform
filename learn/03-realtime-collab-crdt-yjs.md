# Realtime Collaboration: Presence, Yjs, and WebSockets

Implement realtime features incrementally: start with presence and status, grow to CRDT-backed editing.

## Levels of Realtime
1) Status updates (pages translate, suggestions appear)
2) Presence (who’s here, cursors)
3) Comments/threads
4) Suggestions and locks
5) Live editing via CRDT (Yjs)

## Minimal WS Echo (backend)
- See `enh/SCAFFOLD_COLLAB_AND_PROVIDERS.md` collab WS example
- Route: `WS /collab/{pageId}` broadcasts messages in a room

## Presence Payload
```json
{ "t":"presence", "user": {"id":"u1","name":"Alice"}, "cursor": {"x":0.5,"y":0.2} }
```

## Adding Yjs (plan)
- Use TipTap or Lexical editor bound to Yjs for the translate pane
- Each segment maps to `Y.Text`; page maps to `Y.Map`
- Awareness for presence; throttle updates; store snapshots periodically

## Conflict Handling
- CRDT merges automatically; surface diffs when merges change visible text
- Soft locks show who is editing; allow override by leads

## Persistence
- Snapshot store writes `Y.Doc` to object storage
- Ops log persisted (Redis Streams or Postgres logical table) for recovery

## Security
- Short-lived WS tokens scoped to pageId and role
- Validate tokens server-side; drop unauthenticated sockets

## Frontend Wiring
- `frontend/lib/ws.ts`: small client managing (re)connect
- `frontend/hooks/usePageChannel.ts`: hook to subscribe to WS events

## Metrics
- Echo latency, reconnects, dropped ops, room sizes

## Next
- Implement presence + comments first; add Yjs once suggestion flow stabilizes

