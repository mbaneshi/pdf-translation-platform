# Priority Matrix (Impact × Effort)

Legend: Impact (H/M/L), Effort (H/M/L). Priorities based on unlocking value early while controlling risk and cost.

| Item | Impact | Effort | Priority | Rationale |
|------|--------|--------|----------|-----------|
| LLMClient (chat) + usage capture | H | M | P0 | Foundation for quality/cost accuracy; replaces legacy completions. |
| Token‑aware Chunker | H | M | P0 | Controls tokens/cost and improves coherence; prerequisite for scale. |
| Translator Orchestrator | H | M | P0 | Wires chunker + client; enables pilot behind flag. |
| Minimal UI (doc detail, pages, progress) | M | M | P0 | Essential visibility; enables quick operator validation. |
| Metrics (Prometheus) | M | S | P0 | Observability to tune throughput and detect failures. |
| Structure‑aware prompts | H | M | P1 | Boosts fidelity for lists/tables/headers; improves perceived quality. |
| Reviewer (optional pass) | M | M | P1 | Quality uplift with moderate cost; optional toggle. |
| Redis cache (dedupe) | M | S/M | P1 | Saves cost/time on repeats; simple to add. |
| Rate limiter (token bucket) | M | S/M | P1 | Prevents 429s; stabilizes throughput. |
| Glossary + CRUD | M | M | P2 | Consistency for domain terms; UI work required. |
| Exporters (MD→HTML/DOCX) | M | M | P2 | Delivers usable artifacts; downstream formatting. |
| Celery groups/chords + resume | H | M/H | P2 | Resilience and speed for large docs; adds complexity. |
| Agent layer (Orchestrator + Chunker) | M | M | P3 | Planning clarity; optional once core pipeline is stable. |
| Multi‑model strategies | M | M | P3 | Cost/quality tuning after baseline stable. |

Notes
- P0 targets Sprint A; P1 targets Sprint B; P2 targets Sprint C; P3 optional/pilot.
- Items are feature‑flagged or config‑driven to reduce rollout risk.

