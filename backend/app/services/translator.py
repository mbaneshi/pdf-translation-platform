from __future__ import annotations

from typing import Dict, Tuple

from sqlalchemy.orm import Session

from app.models.models import PDFPage
from app.services.chunker import Chunker
from app.services.llm_client import LLMClient, OpenAIChatClient, estimate_cost_usd
from app.metrics import MetricsCollector
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
            # Start metrics collection for chunk
            start_time = MetricsCollector.record_translation_start(
                "translator.translate_text", "chat", "gpt-4o-mini"
            )

            try:
                res = self.llm.chat(PARAGRAPH_SYSTEM, paragraph_user(ch.text), temperature=0.1, max_tokens=800)

                # Record success metrics for chunk
                MetricsCollector.record_translation_success(
                    start_time=start_time,
                    path="translator.translate_text",
                    mode="chat",
                    model="gpt-4o-mini",
                    tokens_in=res.prompt_tokens,
                    tokens_out=res.completion_tokens,
                    cost_usd=estimate_cost_usd(res.prompt_tokens, res.completion_tokens),
                    complexity=MetricsCollector.assess_text_complexity(ch.text)
                )

            except Exception as e:  # pragma: no cover
                MetricsCollector.record_translation_error(
                    "translator.translate_text", "chat", type(e).__name__, str(e)
                )
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

        # Start page-level metrics collection
        page_start_time = MetricsCollector.record_translation_start(
            "translator.translate_page_chunked", "chat", "gpt-4o-mini"
        )

        try:
            result = self.translate_text(page.original_text or "")
            page.translated_text = result["text"]
            page.translation_status = "completed"
            page.translation_model = "chat:gpt-4o-mini"
            page.cost_estimate = result["cost_usd"]

            # Store token usage
            try:
                page.tokens_in = int(result.get("prompt_tokens", 0))
                page.tokens_out = int(result.get("completion_tokens", 0))
            except Exception:
                pass

            db.commit()

            # Record page-level success metrics
            MetricsCollector.record_translation_success(
                start_time=page_start_time,
                path="translator.translate_page_chunked",
                mode="chat",
                model="gpt-4o-mini",
                tokens_in=page.tokens_in or 0,
                tokens_out=page.tokens_out or 0,
                cost_usd=page.cost_estimate or 0.0,
                complexity=MetricsCollector.assess_text_complexity(page.original_text or "")
            )

            return page

        except Exception as e:
            MetricsCollector.record_translation_error(
                "translator.translate_page_chunked", "chat", type(e).__name__, str(e)
            )
            raise
