# Argos Translate provider implementation (offline/local)
from typing import Iterator, Optional, Dict, Any
import logging
import subprocess
import json
import os

from .base import BaseProvider, TranslationResult, TranslationOptions

logger = logging.getLogger(__name__)


class ArgosProvider(BaseProvider):
    """Argos Translate offline translation provider"""
    
    name = "argos"
    
    def __init__(self):
        self._available = self._check_argos_availability()
        self._supported_languages = self._get_supported_languages() if self._available else []
    
    def translate(
        self, 
        text: str, 
        src: str, 
        tgt: str, 
        options: Optional[TranslationOptions] = None
    ) -> TranslationResult:
        """Translate text using Argos Translate"""
        if not self.is_available():
            raise RuntimeError("Argos provider not available")
        
        if not self._is_language_supported(src, tgt):
            raise ValueError(f"Language pair {src}-{tgt} not supported by Argos")
        
        try:
            # Use argos-translate command line
            cmd = [
                "argos-translate",
                "--from-lang", src,
                "--to-lang", tgt,
                "--text", text
            ]
            
            result = subprocess.run(
                cmd, 
                capture_output=True, 
                text=True, 
                timeout=30
            )
            
            if result.returncode != 0:
                raise RuntimeError(f"Argos translation failed: {result.stderr}")
            
            translated_text = result.stdout.strip()
            
            return TranslationResult(
                text=translated_text,
                tokens_used=len(text.split()),  # Rough estimation
                cost=0.0,  # Free offline translation
                provider=self.name,
                model="argos-translate",
                metadata={
                    "offline": True,
                    "language_pair": f"{src}-{tgt}"
                }
            )
            
        except subprocess.TimeoutExpired:
            raise RuntimeError("Argos translation timed out")
        except Exception as e:
            logger.error(f"Argos translation failed: {e}")
            raise RuntimeError(f"Translation failed: {str(e)}")
    
    def stream_translate(
        self, 
        text: str, 
        src: str, 
        tgt: str, 
        options: Optional[TranslationOptions] = None
    ) -> Iterator[TranslationResult]:
        """Stream translation (Argos doesn't support streaming, so we simulate it)"""
        # For offline providers, we can't truly stream, so we yield the complete result
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
        """Estimate cost (always free for Argos)"""
        estimated_tokens = len(text.split())
        
        return {
            "estimated_tokens": estimated_tokens,
            "estimated_cost": 0.0,
            "currency": "USD",
            "provider": self.name,
            "model": "argos-translate",
            "offline": True
        }
    
    def is_available(self) -> bool:
        """Check if Argos Translate is available"""
        return self._available
    
    def get_capabilities(self) -> Dict[str, Any]:
        """Get Argos provider capabilities"""
        return {
            "streaming": False,  # Simulated only
            "max_text_length": 10000,
            "supported_languages": self._supported_languages,
            "cost_per_token": 0.0,
            "latency_ms": 5000,  # Slower than online providers
            "quality": "medium",
            "offline": True
        }
    
    def _check_argos_availability(self) -> bool:
        """Check if Argos Translate is installed and available"""
        try:
            result = subprocess.run(
                ["argos-translate", "--help"], 
                capture_output=True, 
                timeout=5
            )
            return result.returncode == 0
        except (subprocess.TimeoutExpired, FileNotFoundError):
            return False
    
    def _get_supported_languages(self) -> list:
        """Get list of supported language codes"""
        try:
            result = subprocess.run(
                ["argos-translate", "--list-languages"], 
                capture_output=True, 
                text=True, 
                timeout=10
            )
            if result.returncode == 0:
                # Parse language list from output
                lines = result.stdout.strip().split('\n')
                languages = []
                for line in lines:
                    if ':' in line:
                        lang_code = line.split(':')[0].strip()
                        languages.append(lang_code)
                return languages
        except Exception as e:
            logger.warning(f"Could not get Argos language list: {e}")
        
        # Fallback to common languages
        return ["en", "es", "fr", "de", "it", "pt", "ru", "zh", "ja", "ko", "ar", "fa"]
    
    def _is_language_supported(self, src: str, tgt: str) -> bool:
        """Check if language pair is supported"""
        return src in self._supported_languages and tgt in self._supported_languages
