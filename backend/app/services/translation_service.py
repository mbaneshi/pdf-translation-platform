import time
from typing import Optional, Dict, List, Iterator
from app.core.config import settings
from sqlalchemy.orm import Session
from app.models.models import PDFPage
import logging
from app.services.persian_text_processor import PersianTextProcessor
from app.services.translator import Translator
from app.services.provider_router import ProviderRouter
from app.services.providers.base import TranslationOptions
import tiktoken

logger = logging.getLogger(__name__)

class TranslationService:
    def __init__(self):
        self.provider_router = ProviderRouter()
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

    def estimate_cost(
        self, 
        text: str, 
        src: str = "en", 
        tgt: str = "fa", 
        provider_name: Optional[str] = None
    ) -> float:
        """Estimate translation cost using provider abstraction"""
        try:
            # Get provider
            provider = self.provider_router.get(provider_name)
            
            # Build translation options
            options = TranslationOptions(
                temperature=0.1,
                max_tokens=4000,
                preserve_formatting=True,
                domain="academic"
            )
            
            # Get cost estimate from provider
            estimate = provider.estimate_cost(text, src, tgt, options)
            return estimate.get("estimated_cost", 0.0)
            
        except Exception as e:
            logger.warning(f"Error in cost estimation, using fallback: {e}")
            # Fallback to character-based estimation
            char_count = len(text)
            cost_per_char = 1.50 / (1_000_000 * 4)
            return char_count * cost_per_char * 1.3  # Persian expansion factor

    def translate_text(
        self, 
        text: str, 
        src: str = "en", 
        tgt: str = "fa", 
        provider_name: Optional[str] = None,
        max_retries: int = 3
    ) -> str:
        """Translate text using provider abstraction with Persian optimization"""
        if not text.strip():
            return ""
        
        # Check cache
        cache_key = f"{src}_{tgt}_{hash(text)}"
        if cache_key in self.translation_cache:
            return self.translation_cache[cache_key]
        
        # Get provider
        provider = self.provider_router.get(provider_name)
        
        # Build translation options
        options = TranslationOptions(
            temperature=0.1,
            max_tokens=4000,
            preserve_formatting=True,
            domain="academic",
            custom_instructions="Maintain academic tone and precision. Use proper Persian terminology for philosophical concepts."
        )
        
        for attempt in range(max_retries):
            try:
                # Translate using provider
                result = provider.translate(text, src, tgt, options)
                translated_text = result.text
                
                # Process Persian text for proper RTL and shaping
                if tgt == "fa":  # Persian
                    processed_text = self.persian_processor.format_persian_text(translated_text)
                else:
                    processed_text = translated_text
                
                # Cache the result
                self.translation_cache[cache_key] = processed_text
                
                return processed_text
                
            except Exception as e:
                # Handle provider-specific errors
                if "quota" in str(e).lower() or "limit" in str(e).lower():
                    logger.error(f"Provider quota exceeded: {e}")
                    raise ValueError("Translation service quota exceeded. Please try a different provider or check billing settings.")
                elif "auth" in str(e).lower() or "key" in str(e).lower():
                    logger.error(f"Provider authentication failed: {e}")
                    raise ValueError("Translation service authentication failed. Please check your API key.")
                elif "unavailable" in str(e).lower():
                    logger.error(f"Provider temporarily unavailable: {e}")
                    raise ValueError("Translation service temporarily unavailable. Please try again later.")
                
                if attempt == max_retries - 1:
                    logger.error(f"Translation failed after {max_retries} attempts: {e}")
                    raise ValueError(f"Translation failed: {str(e)}")
                logger.warning(f"Attempt {attempt + 1} failed, retrying...")
                time.sleep(2 ** attempt)
        
        return text
    
    def stream_translate_text(
        self, 
        text: str, 
        src: str = "en", 
        tgt: str = "fa", 
        provider_name: Optional[str] = None
    ) -> Iterator[str]:
        """Stream translation using provider abstraction"""
        if not text.strip():
            yield ""
            return
        
        # Get provider
        provider = self.provider_router.get(provider_name)
        
        # Build translation options
        options = TranslationOptions(
            temperature=0.1,
            max_tokens=4000,
            preserve_formatting=True,
            domain="academic",
            custom_instructions="Maintain academic tone and precision. Use proper Persian terminology for philosophical concepts."
        )
        
        try:
            # Stream translation using provider
            for result in provider.stream_translate(text, src, tgt, options):
                if result.text:
                    # Process Persian text for proper RTL and shaping
                    if tgt == "fa":  # Persian
                        processed_text = self.persian_processor.format_persian_text(result.text)
                    else:
                        processed_text = result.text
                    
                    yield processed_text
                    
        except Exception as e:
            logger.error(f"Streaming translation failed: {e}")
            raise ValueError(f"Streaming translation failed: {str(e)}")

    def translate_page(self, db: Session, page_id: int) -> PDFPage:
        """Translate a single page and update database with Persian optimization"""
        page = db.query(PDFPage).filter(PDFPage.id == page_id).first()
        if not page:
            raise ValueError("Page not found")
        # Feature-flagged chunked path using chat API
        if settings.USE_CHUNKING:
            translator = Translator()
            return translator.translate_page_chunked(db, page_id)

        try:
            page.translation_status = "processing"
            db.commit()
            
            start_time = time.time()
            translated_text = self.translate_text(page.original_text, "en", "fa")
            translation_time = time.time() - start_time
            
            # Validate Persian translation quality
            validation_result = self.persian_processor.validate_persian_translation(
                page.original_text, translated_text
            )
            
            page.translated_text = translated_text
            page.translation_status = "completed"
            page.translation_time = translation_time
            page.cost_estimate = self.estimate_cost(page.original_text, "en", "fa")
            page.translation_model = self.provider_router.get().name
            
            # Store validation results in metadata
            # Store validation results in page_metadata (avoid SQLAlchemy reserved name)
            # Store validation summary transiently (not persisted in DB schema)
            page.validation_summary = validation_result
            
            db.commit()
            return page
            
        except Exception as e:
            page.translation_status = "failed"
            db.commit()
            raise e
    
    def translate_with_quality_check(
        self, 
        text: str, 
        src: str = "en", 
        tgt: str = "fa", 
        provider_name: Optional[str] = None
    ) -> Dict:
        """Translate text with quality validation"""
        try:
            translated_text = self.translate_text(text, src, tgt, provider_name)
            validation_result = self.persian_processor.validate_persian_translation(text, translated_text)
            
            return {
                'original_text': text,
                'translated_text': translated_text,
                'validation': validation_result,
                'cost_estimate': self.estimate_cost(text, src, tgt, provider_name),
                'token_count': len(self.tokenizer.encode(text)),
                'provider': self.provider_router.get(provider_name).name
            }
            
        except Exception as e:
            logger.error(f"Error in translate_with_quality_check: {e}")
            raise
    
    def get_translation_statistics(
        self, 
        text: str, 
        src: str = "en", 
        tgt: str = "fa", 
        provider_name: Optional[str] = None
    ) -> Dict:
        """Get detailed translation statistics"""
        try:
            tokens = self.tokenizer.encode(text)
            token_count = len(tokens)
            char_count = len(text)
            word_count = len(text.split())
            
            cost_estimate = self.estimate_cost(text, src, tgt, provider_name)
            provider = self.provider_router.get(provider_name)
            
            return {
                'char_count': char_count,
                'word_count': word_count,
                'token_count': token_count,
                'estimated_cost': cost_estimate,
                'persian_expansion_factor': 1.3,
                'estimated_persian_length': int(char_count * 1.3),
                'provider': provider.name,
                'provider_capabilities': provider.get_capabilities()
            }
            
        except Exception as e:
            logger.error(f"Error getting translation statistics: {e}")
            return {}
