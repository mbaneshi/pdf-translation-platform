# ADR Templates and Samples

Adopt Architecture Decision Records (ADRs) to capture rationale and enable safe iteration.

## ADR Template
```
ADR N: Title
Date: YYYY-MM-DD
Status: Proposed | Accepted | Deprecated | Superseded by ADR X
Context:
- What problem are we solving?
- Which constraints exist?
Decision:
- The choice made and why
Consequences:
- Positive
- Negative
- Follow-ups
References:
- Links to docs, issues, PRs
```

## Sample: Provider Abstraction (ADR 001)
- Context: Need to support multiple translation backends with streaming and fallback.
- Decision: Introduce `BaseProvider` interface and `ProviderRouter` with env-driven default.
- Consequences: Enables testing via fakes, decouples business logic; adds adapter maintenance cost.

## Sample: Presence via WS (ADR 002)
- Context: Need low-latency presence before full CRDT editing.
- Decision: Implement WS room endpoint and JSON envelopes; plan Yjs later.
- Consequences: Quick wins; migration path to CRDT.

