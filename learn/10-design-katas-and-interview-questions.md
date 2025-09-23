# Design Katas and Interview-Style Questions

Sharpen intuition with focused design challenges and discussion prompts tailored to our platform.

## Katas
- Kata 1: Idempotent Page Translation
  - Problem: Ensure POST /translate is safe on retries without double work.
  - Deliverables: State diagram, idempotency key plan, response semantics.
- Kata 2: Scroll Sync for Dual-Pane
  - Problem: Keep panes aligned across zoom levels and dynamic content.
  - Deliverables: Ratio-based sync algorithm, hysteresis, performance plan.
- Kata 3: Presence Scalability
  - Problem: 1k rooms, 50 users/room; keep updates smooth.
  - Deliverables: Presence frequency, batching, backoff rules, UI degradation.
- Kata 4: Streaming Backpressure
  - Problem: Provider streams faster than UI can render.
  - Deliverables: Buffer strategy, chunk coalescing, frame budget.
- Kata 5: Glossary Enforcement UX
  - Problem: Batch replace suggestions with clear preview.
  - Deliverables: Diff preview design, undo plan, metrics.

## Deep Dives (Choose Any)
- CRDT vs Server-Serialized Diffs
- OpenAI-compatible vs offline MT routing policies
- RLS policy pitfalls and audit trails
- WebSockets auth and token rotation strategy

## Interview-Style Questions
- Describe a robust error taxonomy for provider failures and user display.
- How would you test scroll sync correctness under virtualization?
- What’s your plan to avoid realtime “notification storms” on busy docs?
- Explain a SLO set for this platform and how you’d measure it.
- Which component boundaries enable fast feature work with low regressions?

## Scoring Rubric (Self-Assessment)
- Clarity of diagrams, explicit tradeoffs, measurable outcomes, edge cases.

