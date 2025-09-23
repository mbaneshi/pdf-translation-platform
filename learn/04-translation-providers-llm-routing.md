# Translation Providers and LLM Routing

Abstract and route between multiple translation backends (OpenAI, Argos offline, OpenAI-compatible, deep-translator) with streaming and fallbacks.

## Why Abstraction
- Swap providers without changing business logic
- Apply policies: cost, latency, quality tiers
- Add streaming UI with minimal coupling

## Files (planned)
- `backend/app/services/providers/base.py` (interface)
- `backend/app/services/providers/openai_provider.py`
- `backend/app/services/provider_router.py`

## Interface (sketch)
```python
class BaseProvider:
    def translate(self, text: str, src: str, tgt: str, options=None) -> str: ...
    def stream_translate(self, text: str, src: str, tgt: str, options=None) -> Iterator[str]: ...
```

## Router Policy
- Default provider via env `TRANSLATION_PROVIDER`
- Fallback chain when provider fails (e.g., 429 → Argos)

## Streaming UI Hooks
- Start job → show `processing`
- Stream chunks → append into pane with backpressure
- Complete → persist translated text; revalidate queries

## Pricing & Tokens
- Estimate tokens with `tiktoken`; compute budget per page
- Warn user when exceeding thresholds; enforce caps per document

## Quality Signals
- Track suggestion acceptance rate by provider; route hard cases to stronger models

## Next
- Implement OpenAI provider first; add Argos when offline path is needed

