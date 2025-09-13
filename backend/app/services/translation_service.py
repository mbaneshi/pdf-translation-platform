from openai import OpenAI
import time
from typing import Optional, Dict, List
from app.core.config import settings
import tqdm
from sqlalchemy.orm import Session
from app.models.enhanced_models import PDFPage
import logging
from app.services.persian_text_processor import PersianTextProcessor
import tiktoken

logger = logging.getLogger(__name__)

class TranslationService:
    def __init__(self):
        self.client = OpenAI(api_key=settings.OPENAI_API_KEY)
        self.model = settings.OPENAI_MODEL
        self.translation_cache = {}
        self.persian_processor = PersianTextProcessor()
        self.tokenizer = tiktoken.get_encoding("cl100k_base")
        
        # Persian-optimized translation prompts
        self.PERSIAN_TRANSLATION_PROMPT = """
You are an expert translator specializing in academic and philosophical texts from English to Persian (Farsi).

Guidelines:
1. Maintain academic tone and precision
2. Use proper Persian terminology for philosophical concepts
3. Preserve sentence structure and meaning
4. Handle proper nouns appropriately (keep names in original form)
5. Maintain paragraph breaks and formatting
6. Use proper Persian punctuation (، ؛ ؟)
7. Ensure cultural appropriateness for Persian readers
8. Maintain the original text's academic rigor

Text to translate: {text}

Persian Translation:
"""

    def estimate_cost(self, text: str) -> float:
        """Estimate translation cost using accurate token counting"""
        try:
            # Count tokens accurately
            tokens = self.tokenizer.encode(text)
            token_count = len(tokens)
            
            # GPT-3.5 Turbo pricing: $1.50 per 1M input tokens, $2.00 per 1M output tokens
            # Estimate output tokens as 1.3x input tokens for Persian (expansion factor)
            estimated_output_tokens = int(token_count * 1.3)
            
            input_cost = (token_count / 1_000_000) * 1.50
            output_cost = (estimated_output_tokens / 1_000_000) * 2.00
            
            return input_cost + output_cost
            
        except Exception as e:
            logger.warning(f"Error in token counting, using fallback: {e}")
            # Fallback to character-based estimation
            char_count = len(text)
            cost_per_char = 1.50 / (1_000_000 * 4)
            return char_count * cost_per_char * 1.3  # Persian expansion factor

    def translate_text(self, text: str, max_retries: int = 3) -> str:
        """Translate text using OpenAI API with Persian optimization"""
        if not text.strip():
            return ""
        
        # Check cache
        cache_key = f"persian_{hash(text)}"
        if cache_key in self.translation_cache:
            return self.translation_cache[cache_key]
        
        for attempt in range(max_retries):
            try:
                response = self.client.completions.create(
                    model=self.model,
                    prompt=self.PERSIAN_TRANSLATION_PROMPT.format(text=text),
                    max_tokens=4000,
                    temperature=0.1
                )
                
                translated_text = response.choices[0].text.strip()
                
                # Process Persian text for proper RTL and shaping
                processed_text = self.persian_processor.format_persian_text(translated_text)
                
                # Cache the result
                self.translation_cache[cache_key] = processed_text
                
                return processed_text
                
            except Exception as e:
                if attempt == max_retries - 1:
                    logger.error(f"Translation failed after {max_retries} attempts: {e}")
                    raise
                logger.warning(f"Attempt {attempt + 1} failed, retrying...")
                time.sleep(2 ** attempt)
        
        return text

    def translate_page(self, db: Session, page_id: int) -> PDFPage:
        """Translate a single page and update database with Persian optimization"""
        page = db.query(PDFPage).filter(PDFPage.id == page_id).first()
        if not page:
            raise ValueError("Page not found")
        
        try:
            page.translation_status = "processing"
            db.commit()
            
            start_time = time.time()
            translated_text = self.translate_text(page.original_text)
            translation_time = time.time() - start_time
            
            # Validate Persian translation quality
            validation_result = self.persian_processor.validate_persian_translation(
                page.original_text, translated_text
            )
            
            page.translated_text = translated_text
            page.translation_status = "completed"
            page.translation_time = translation_time
            page.cost_estimate = self.estimate_cost(page.original_text)
            page.translation_model = self.model
            
            # Store validation results in metadata
            if not hasattr(page, 'metadata') or page.metadata is None:
                page.metadata = {}
            page.metadata['persian_validation'] = validation_result
            
            db.commit()
            return page
            
        except Exception as e:
            page.translation_status = "failed"
            db.commit()
            raise e
    
    def translate_with_quality_check(self, text: str) -> Dict:
        """Translate text with quality validation"""
        try:
            translated_text = self.translate_text(text)
            validation_result = self.persian_processor.validate_persian_translation(text, translated_text)
            
            return {
                'original_text': text,
                'translated_text': translated_text,
                'validation': validation_result,
                'cost_estimate': self.estimate_cost(text),
                'token_count': len(self.tokenizer.encode(text))
            }
            
        except Exception as e:
            logger.error(f"Error in translate_with_quality_check: {e}")
            raise
    
    def get_translation_statistics(self, text: str) -> Dict:
        """Get detailed translation statistics"""
        try:
            tokens = self.tokenizer.encode(text)
            token_count = len(tokens)
            char_count = len(text)
            word_count = len(text.split())
            
            cost_estimate = self.estimate_cost(text)
            
            return {
                'char_count': char_count,
                'word_count': word_count,
                'token_count': token_count,
                'estimated_cost': cost_estimate,
                'persian_expansion_factor': 1.3,
                'estimated_persian_length': int(char_count * 1.3)
            }
            
        except Exception as e:
            logger.error(f"Error getting translation statistics: {e}")
            return {}
