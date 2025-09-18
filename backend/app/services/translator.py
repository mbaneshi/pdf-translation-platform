from __future__ import annotations

from typing import Dict, Tuple

from sqlalchemy.orm import Session

from app.models.models import PDFPage
from app.services.chunker import Chunker
from app.services.llm_client import LLMClient, OpenAIChatClient, estimate_cost_usd
from app.metrics import translation_requests, translation_latency, translation_errors
from app.services.prompt_library import PARAGRAPH_SYSTEM, paragraph_user


class Translator:
    def __init__(self, llm: LLMClient | None = None, chunk_tokens: int = 1200):
        self.llm = llm or OpenAIChatClient()
        self.chunker = Chunker(target_tokens=chunk_tokens)

    def translate_text(self, text: str) -> Dict:
        """Translate text using chunking and chat API; returns dict with text and usage."""
        if not text.strip():
            return {"text": "", "prompt_tokens": 0, "completion_tokens": 0, "cost_usd": 0.0}

        chunks = self.chunker.chunk_paragraphs(text)
        out_parts: list[str] = []
        ptoks = 0
        ctoks = 0

        for ch in chunks:
            translation_requests.labels(path="translator.translate_text", mode="chat").inc()
            with translation_latency.labels(path="translator.translate_text", mode="chat").time():
                try:
                    res = self.llm.chat(PARAGRAPH_SYSTEM, paragraph_user(ch.text), temperature=0.1, max_tokens=800)
                except Exception as e:  # pragma: no cover
                    translation_errors.labels(path="translator.translate_text", mode="chat", reason=type(e).__name__).inc()
                    raise
            out_parts.append(res.text)
            ptoks += res.prompt_tokens
            ctoks += res.completion_tokens

        total_cost = estimate_cost_usd(ptoks, ctoks)
        return {
            "text": "\n\n".join(out_parts).strip(),
            "prompt_tokens": ptoks,
            "completion_tokens": ctoks,
            "cost_usd": total_cost,
        }

    def translate_page_chunked(self, db: Session, page_id: int) -> PDFPage:
        page = db.query(PDFPage).filter(PDFPage.id == page_id).first()
        if not page:
            raise ValueError("Page not found")

        result = self.translate_text(page.original_text or "")
        page.translated_text = result["text"]
        page.translation_status = "completed"
        page.translation_model = "chat:"  # model captured internally; optional to expose here
        page.cost_estimate = result["cost_usd"]
        db.commit()
        return page
