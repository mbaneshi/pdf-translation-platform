from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Optional, Protocol, Tuple

from openai import OpenAI

from app.core.config import settings


@dataclass
class ChatResult:
    text: str
    prompt_tokens: int = 0
    completion_tokens: int = 0


class LLMClient(Protocol):
    def chat(self, system: str, user: str, *, temperature: float = 0.1, max_tokens: int = 800) -> ChatResult:
        ...


class OpenAIChatClient:
    """Thin wrapper over OpenAI chat completions with retries and usage capture."""

    def __init__(self, api_key: Optional[str] = None, model: Optional[str] = None):
        self._model = model or settings.OPENAI_CHAT_MODEL
        self._client = OpenAI(api_key=api_key or settings.OPENAI_API_KEY)

    def chat(
        self,
        system: str,
        user: str,
        *,
        temperature: float = 0.1,
        max_tokens: int = 800,
        max_retries: int = 3,
        retry_base_delay: float = 1.0,
    ) -> ChatResult:
        last_err: Optional[Exception] = None
        for attempt in range(max_retries):
            try:
                resp = self._client.chat.completions.create(
                    model=self._model,
                    messages=[
                        {"role": "system", "content": system},
                        {"role": "user", "content": user},
                    ],
                    temperature=temperature,
                    max_tokens=max_tokens,
                )
                text = (resp.choices[0].message.content or "").strip()
                usage = getattr(resp, "usage", None)
                return ChatResult(
                    text=text,
                    prompt_tokens=getattr(usage, "prompt_tokens", 0) or 0,
                    completion_tokens=getattr(usage, "completion_tokens", 0) or 0,
                )
            except Exception as e:  # pragma: no cover - exercised via unit tests with monkeypatch
                last_err = e
                if attempt == max_retries - 1:
                    raise
                time.sleep(retry_base_delay * (2**attempt))
        # Should not reach
        raise RuntimeError(str(last_err) if last_err else "chat failed")


def estimate_cost_usd(prompt_tokens: int, completion_tokens: int) -> float:
    """Estimate cost using configured pricing (per 1M tokens)."""
    in_cost = (prompt_tokens / 1_000_000) * settings.OPENAI_PRICING_INPUT_PER_M
    out_cost = (completion_tokens / 1_000_000) * settings.OPENAI_PRICING_OUTPUT_PER_M
    return round(in_cost + out_cost, 6)

