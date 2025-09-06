from openai import OpenAI
import time
from typing import Optional
from core.config import settings
import tqdm
from sqlalchemy.orm import Session
from models import PDFPage
import logging

logger = logging.getLogger(__name__)

class TranslationService:
    def __init__(self):
        self.client = OpenAI(api_key=settings.OPENAI_API_KEY)
        self.model = settings.OPENAI_MODEL
        self.translation_cache = {}

    def estimate_cost(self, text: str) -> float:
        """Estimate translation cost"""
        char_count = len(text)
        # GPT-3.5 Turbo pricing: $1.50 per 1M tokens (~4 chars per token)
        cost_per_char = 1.50 / (1_000_000 * 4)
        return char_count * cost_per_char

    def translate_text(self, text: str, max_retries: int = 3) -> str:
        """Translate text using OpenAI API"""
        if not text.strip():
            return ""
        
        # Check cache
        if text in self.translation_cache:
            return self.translation_cache[text]
        
        for attempt in range(max_retries):
            try:
                response = self.client.completions.create(
                    model=self.model,
                    prompt=f"""Translate the following English text to Persian accurately. 
                    Maintain the original structure, formatting, and meaning. 
                    Use precise technical terms where appropriate.
                    
                    English Text:
                    {text}
                    
                    Persian Translation:""",
                    max_tokens=4000,
                    temperature=0.1
                )
                
                translated_text = response.choices[0].text.strip()
                self.translation_cache[text] = translated_text
                return translated_text
                
            except Exception as e:
                if attempt == max_retries - 1:
                    logger.error(f"Translation failed after {max_retries} attempts: {e}")
                    raise
                logger.warning(f"Attempt {attempt + 1} failed, retrying...")
                time.sleep(2 ** attempt)
        
        return text

    def translate_page(self, db: Session, page_id: int) -> PDFPage:
        """Translate a single page and update database"""
        page = db.query(PDFPage).filter(PDFPage.id == page_id).first()
        if not page:
            raise ValueError("Page not found")
        
        try:
            page.translation_status = "processing"
            db.commit()
            
            start_time = time.time()
            translated_text = self.translate_text(page.original_text)
            translation_time = time.time() - start_time
            
            page.translated_text = translated_text
            page.translation_status = "completed"
            page.translation_time = translation_time
            page.cost_estimate = self.estimate_cost(page.original_text)
            page.translation_model = self.model
            
            db.commit()
            return page
            
        except Exception as e:
            page.translation_status = "failed"
            db.commit()
            raise e
