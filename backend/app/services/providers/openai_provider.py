# OpenAI provider implementation
from typing import Iterator, Optional, Dict, Any
import openai
from openai import OpenAI
import logging

from app.core.config import settings
from .base import BaseProvider, TranslationResult, TranslationOptions

logger = logging.getLogger(__name__)


class OpenAIProvider(BaseProvider):
    """OpenAI GPT-based translation provider"""
    
    name = "openai"
    
    def __init__(self):
        self.client = OpenAI(api_key=settings.OPENAI_API_KEY)
        self.model = settings.OPENAI_MODEL
        self._available = bool(settings.OPENAI_API_KEY)
    
    def translate(
        self, 
        text: str, 
        src: str, 
        tgt: str, 
        options: Optional[TranslationOptions] = None
    ) -> TranslationResult:
        """Translate text using OpenAI chat completions"""
        if not self.is_available():
            raise RuntimeError("OpenAI provider not available - missing API key")
        
        options = options or TranslationOptions()
        
        # Build system message with context
        system_message = self._build_system_message(src, tgt, options)
        user_message = f"Translate the following text from {src} to {tgt}:\n\n{text}"
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_message},
                    {"role": "user", "content": user_message}
                ],
                max_tokens=options.max_tokens or 4000,
                temperature=options.temperature
            )
            
            translated_text = response.choices[0].message.content.strip()
            
            # Calculate cost (approximate)
            tokens_used = response.usage.total_tokens if response.usage else None
            cost = self._calculate_cost(tokens_used) if tokens_used else None
            
            return TranslationResult(
                text=translated_text,
                tokens_used=tokens_used,
                cost=cost,
                provider=self.name,
                model=self.model,
                metadata={
                    "finish_reason": response.choices[0].finish_reason,
                    "usage": response.usage.dict() if response.usage else None
                }
            )
            
        except Exception as e:
            logger.error(f"OpenAI translation failed: {e}")
            raise RuntimeError(f"Translation failed: {str(e)}")
    
    def stream_translate(
        self, 
        text: str, 
        src: str, 
        tgt: str, 
        options: Optional[TranslationOptions] = None
    ) -> Iterator[TranslationResult]:
        """Stream translation using OpenAI chat completions"""
        if not self.is_available():
            raise RuntimeError("OpenAI provider not available - missing API key")
        
        options = options or TranslationOptions()
        
        system_message = self._build_system_message(src, tgt, options)
        user_message = f"Translate the following text from {src} to {tgt}:\n\n{text}"
        
        try:
            stream = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_message},
                    {"role": "user", "content": user_message}
                ],
                max_tokens=options.max_tokens or 4000,
                temperature=options.temperature,
                stream=True
            )
            
            accumulated_text = ""
            for chunk in stream:
                if chunk.choices[0].delta.content:
                    content = chunk.choices[0].delta.content
                    accumulated_text += content
                    
                    yield TranslationResult(
                        text=content,
                        provider=self.name,
                        model=self.model,
                        metadata={"streaming": True, "partial": True}
                    )
            
            # Final result with complete text
            yield TranslationResult(
                text=accumulated_text,
                provider=self.name,
                model=self.model,
                metadata={"streaming": True, "partial": False, "complete": True}
            )
            
        except Exception as e:
            logger.error(f"OpenAI streaming translation failed: {e}")
            raise RuntimeError(f"Streaming translation failed: {str(e)}")
    
    def estimate_cost(
        self, 
        text: str, 
        src: str, 
        tgt: str, 
        options: Optional[TranslationOptions] = None
    ) -> Dict[str, Any]:
        """Estimate cost and token usage"""
        # Rough estimation based on text length
        estimated_tokens = len(text.split()) * 1.3  # Rough token estimation
        estimated_cost = self._calculate_cost(int(estimated_tokens))
        
        return {
            "estimated_tokens": int(estimated_tokens),
            "estimated_cost": estimated_cost,
            "currency": "USD",
            "provider": self.name,
            "model": self.model
        }
    
    def is_available(self) -> bool:
        """Check if OpenAI provider is available"""
        return self._available
    
    def get_capabilities(self) -> Dict[str, Any]:
        """Get OpenAI provider capabilities"""
        return {
            "streaming": True,
            "max_text_length": 50000,  # Approximate
            "supported_languages": ["en", "fa", "ar", "es", "fr", "de", "it", "pt", "ru", "zh", "ja", "ko"],
            "cost_per_token": 0.0005,  # Approximate for GPT-3.5-turbo
            "latency_ms": 2000,
            "quality": "high"
        }
    
    def _build_system_message(self, src: str, tgt: str, options: TranslationOptions) -> str:
        """Build system message with context and instructions"""
        base_message = f"You are an expert translator specializing in {src} to {tgt} translation. "
        base_message += "Maintain academic tone and precision. Preserve formatting and structure. "
        
        if options.glossary:
            base_message += f"\n\nUse this glossary for consistent terminology:\n"
            for term, translation in options.glossary.items():
                base_message += f"- {term}: {translation}\n"
        
        if options.custom_instructions:
            base_message += f"\n\nAdditional instructions: {options.custom_instructions}"
        
        if options.domain:
            base_message += f"\n\nDomain context: {options.domain}"
        
        return base_message
    
    def _calculate_cost(self, tokens: int) -> float:
        """Calculate approximate cost based on token usage"""
        # GPT-3.5-turbo pricing (approximate)
        cost_per_1k_tokens = 0.002
        return (tokens / 1000) * cost_per_1k_tokens
