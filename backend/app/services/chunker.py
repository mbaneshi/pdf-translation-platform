from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, List

import tiktoken


@dataclass
class Chunk:
    kind: str  # paragraph|list|table|generic
    text: str
    order: int
    token_count: int


class Chunker:
    """Token-aware chunker that prefers paragraph boundaries.

    Strategy (v1):
    - Split on blank lines (\n\n) as paragraph candidates.
    - Pack consecutive paragraphs until token budget is reached.
    - Avoid empty/whitespace chunks.
    """

    def __init__(self, model_name: str = "cl100k_base", target_tokens: int = 1200):
        self.enc = tiktoken.get_encoding(model_name)
        self.target_tokens = max(200, target_tokens)

    def chunk_paragraphs(self, text: str) -> List[Chunk]:
        paras = [p for p in text.split("\n\n") if p.strip()]
        chunks: List[Chunk] = []
        buf: List[str] = []
        tok_sum = 0
        order = 0

        def flush():
            nonlocal order, tok_sum, buf
            if not buf:
                return
            s = "\n\n".join(buf)
            tokens = len(self.enc.encode(s))
            chunks.append(Chunk(kind="paragraph", text=s, order=order, token_count=tokens))
            order += 1
            buf = []
            tok_sum = 0

        for p in paras:
            ptoks = len(self.enc.encode(p))
            if tok_sum + ptoks > self.target_tokens and buf:
                flush()
            buf.append(p)
            tok_sum += ptoks
            if tok_sum >= self.target_tokens:
                flush()
        flush()
        if not chunks and text.strip():
            # Fallback single chunk
            tokens = len(self.enc.encode(text))
            chunks.append(Chunk(kind="generic", text=text, order=0, token_count=tokens))
        return chunks

