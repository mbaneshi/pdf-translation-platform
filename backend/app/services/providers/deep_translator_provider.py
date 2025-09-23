# Deep Translator provider implementation
from typing import Iterator, Optional, Dict, Any
import logging
import requests
import time

from .base import BaseProvider, TranslationResult, TranslationOptions

logger = logging.getLogger(__name__)


class DeepTranslatorProvider(BaseProvider):
    """Deep Translator API provider (free translation service)"""
    
    name = "deep_translator"
    
    def __init__(self):
        self.base_url = "https://api-free.deepl.com/v2/translate"
        self._available = True  # Free service, always available
        self._rate_limit_delay = 1.0  # Rate limiting
    
    def translate(
        self, 
        text: str, 
        src: str, 
        tgt: str, 
        options: Optional[TranslationOptions] = None
    ) -> TranslationResult:
        """Translate text using Deep Translator"""
        if not self.is_available():
            raise RuntimeError("Deep Translator provider not available")
        
        # Rate limiting
        time.sleep(self._rate_limit_delay)
        
        try:
            # Map language codes to Deep Translator format
            src_lang = self._map_language_code(src)
            tgt_lang = self._map_language_code(tgt)
            
            payload = {
                "text": text,
                "source_lang": src_lang,
                "target_lang": tgt_lang
            }
            
            response = requests.post(
                self.base_url,
                data=payload,
                timeout=30
            )
            
            if response.status_code != 200:
                raise RuntimeError(f"Deep Translator API error: {response.status_code}")
            
            result = response.json()
            translated_text = result.get("data", {}).get("translations", [{}])[0].get("text", "")
            
            if not translated_text:
                raise RuntimeError("No translation returned from Deep Translator")
            
            return TranslationResult(
                text=translated_text,
                tokens_used=len(text.split()),  # Rough estimation
                cost=0.0,  # Free service
                provider=self.name,
                model="deep-translator",
                metadata={
                    "source_lang": src_lang,
                    "target_lang": tgt_lang,
                    "free_service": True
                }
            )
            
        except requests.RequestException as e:
            logger.error(f"Deep Translator request failed: {e}")
            raise RuntimeError(f"Translation request failed: {str(e)}")
        except Exception as e:
            logger.error(f"Deep Translator translation failed: {e}")
            raise RuntimeError(f"Translation failed: {str(e)}")
    
    def stream_translate(
        self, 
        text: str, 
        src: str, 
        tgt: str, 
        options: Optional[TranslationOptions] = None
    ) -> Iterator[TranslationResult]:
        """Stream translation (Deep Translator doesn't support streaming)"""
        result = self.translate(text, src, tgt, options)
        
        # Simulate streaming by yielding the complete result
        yield TranslationResult(
            text=result.text,
            tokens_used=result.tokens_used,
            cost=result.cost,
            provider=result.provider,
            model=result.model,
            metadata={**result.metadata, "streaming": True, "simulated": True}
        )
    
    def estimate_cost(
        self, 
        text: str, 
        src: str, 
        tgt: str, 
        options: Optional[TranslationOptions] = None
    ) -> Dict[str, Any]:
        """Estimate cost (always free for Deep Translator)"""
        estimated_tokens = len(text.split())
        
        return {
            "estimated_tokens": estimated_tokens,
            "estimated_cost": 0.0,
            "currency": "USD",
            "provider": self.name,
            "model": "deep-translator",
            "free_service": True
        }
    
    def is_available(self) -> bool:
        """Check if Deep Translator is available"""
        return self._available
    
    def get_capabilities(self) -> Dict[str, Any]:
        """Get Deep Translator provider capabilities"""
        return {
            "streaming": False,  # Not supported
            "max_text_length": 5000,  # API limit
            "supported_languages": [
                "en", "es", "fr", "de", "it", "pt", "ru", "zh", "ja", "ko", "ar", "fa"
            ],
            "cost_per_token": 0.0,
            "latency_ms": 3000,  # Slower due to rate limiting
            "quality": "medium",
            "free_service": True,
            "rate_limited": True
        }
    
    def _map_language_code(self, lang_code: str) -> str:
        """Map standard language codes to Deep Translator format"""
        mapping = {
            "en": "EN",
            "es": "ES", 
            "fr": "FR",
            "de": "DE",
            "it": "IT",
            "pt": "PT",
            "ru": "RU",
            "zh": "ZH",
            "ja": "JA",
            "ko": "KO",
            "ar": "AR",
            "fa": "FA"  # Persian
        }
        return mapping.get(lang_code.lower(), lang_code.upper())
