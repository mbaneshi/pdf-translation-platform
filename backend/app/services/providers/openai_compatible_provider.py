# OpenAI-compatible provider for custom endpoints
from typing import Iterator, Optional, Dict, Any
import httpx
import logging
import json

from app.core.config import settings
from .base import BaseProvider, TranslationResult, TranslationOptions

logger = logging.getLogger(__name__)


class OpenAICompatibleProvider(BaseProvider):
    """OpenAI-compatible provider for custom endpoints (e.g., local LLM servers)"""
    
    name = "openai_compatible"
    
    def __init__(self):
        self.base_url = getattr(settings, 'OPENAI_COMPATIBLE_URL', 'http://localhost:8000/v1')
        self.api_key = getattr(settings, 'OPENAI_COMPATIBLE_API_KEY', None)
        self.model = getattr(settings, 'OPENAI_COMPATIBLE_MODEL', 'gpt-3.5-turbo')
        self._available = bool(self.base_url)
    
    def translate(
        self, 
        text: str, 
        src: str, 
        tgt: str, 
        options: Optional[TranslationOptions] = None
    ) -> TranslationResult:
        """Translate text using OpenAI-compatible endpoint"""
        if not self.is_available():
            raise RuntimeError("OpenAI-compatible provider not available")
        
        options = options or TranslationOptions()
        
        system_message = self._build_system_message(src, tgt, options)
        user_message = f"Translate the following text from {src} to {tgt}:\n\n{text}"
        
        try:
            response = self._make_request({
                "model": self.model,
                "messages": [
                    {"role": "system", "content": system_message},
                    {"role": "user", "content": user_message}
                ],
                "max_tokens": options.max_tokens or 4000,
                "temperature": options.temperature
            })
            
            translated_text = response["choices"][0]["message"]["content"].strip()
            
            # Calculate cost (if usage info available)
            tokens_used = response.get("usage", {}).get("total_tokens")
            cost = self._calculate_cost(tokens_used) if tokens_used else None
            
            return TranslationResult(
                text=translated_text,
                tokens_used=tokens_used,
                cost=cost,
                provider=self.name,
                model=self.model,
                metadata={
                    "finish_reason": response["choices"][0].get("finish_reason"),
                    "usage": response.get("usage"),
                    "endpoint": self.base_url
                }
            )
            
        except Exception as e:
            logger.error(f"OpenAI-compatible translation failed: {e}")
            raise RuntimeError(f"Translation failed: {str(e)}")
    
    def stream_translate(
        self, 
        text: str, 
        src: str, 
        tgt: str, 
        options: Optional[TranslationOptions] = None
    ) -> Iterator[TranslationResult]:
        """Stream translation using OpenAI-compatible endpoint"""
        if not self.is_available():
            raise RuntimeError("OpenAI-compatible provider not available")
        
        options = options or TranslationOptions()
        
        system_message = self._build_system_message(src, tgt, options)
        user_message = f"Translate the following text from {src} to {tgt}:\n\n{text}"
        
        try:
            stream_response = self._make_streaming_request({
                "model": self.model,
                "messages": [
                    {"role": "system", "content": system_message},
                    {"role": "user", "content": user_message}
                ],
                "max_tokens": options.max_tokens or 4000,
                "temperature": options.temperature,
                "stream": True
            })
            
            accumulated_text = ""
            for chunk in stream_response:
                if chunk.get("choices", [{}])[0].get("delta", {}).get("content"):
                    content = chunk["choices"][0]["delta"]["content"]
                    accumulated_text += content
                    
                    yield TranslationResult(
                        text=content,
                        provider=self.name,
                        model=self.model,
                        metadata={"streaming": True, "partial": True}
                    )
            
            # Final result
            yield TranslationResult(
                text=accumulated_text,
                provider=self.name,
                model=self.model,
                metadata={"streaming": True, "partial": False, "complete": True}
            )
            
        except Exception as e:
            logger.error(f"OpenAI-compatible streaming translation failed: {e}")
            raise RuntimeError(f"Streaming translation failed: {str(e)}")
    
    def estimate_cost(
        self, 
        text: str, 
        src: str, 
        tgt: str, 
        options: Optional[TranslationOptions] = None
    ) -> Dict[str, Any]:
        """Estimate cost and token usage"""
        estimated_tokens = len(text.split()) * 1.3
        estimated_cost = self._calculate_cost(int(estimated_tokens))
        
        return {
            "estimated_tokens": int(estimated_tokens),
            "estimated_cost": estimated_cost,
            "currency": "USD",
            "provider": self.name,
            "model": self.model,
            "endpoint": self.base_url
        }
    
    def is_available(self) -> bool:
        """Check if OpenAI-compatible provider is available"""
        if not self._available:
            return False
        
        # Try to ping the endpoint
        try:
            with httpx.Client(timeout=5.0) as client:
                response = client.get(f"{self.base_url}/models")
                return response.status_code == 200
        except Exception:
            return False
    
    def get_capabilities(self) -> Dict[str, Any]:
        """Get OpenAI-compatible provider capabilities"""
        return {
            "streaming": True,
            "max_text_length": 50000,
            "supported_languages": ["en", "fa", "ar", "es", "fr", "de", "it", "pt", "ru", "zh", "ja", "ko"],
            "cost_per_token": 0.0001,  # Usually cheaper than OpenAI
            "latency_ms": 1500,
            "quality": "high",
            "custom_endpoint": True
        }
    
    def _make_request(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Make HTTP request to OpenAI-compatible endpoint"""
        headers = {
            "Content-Type": "application/json"
        }
        
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        
        with httpx.Client(timeout=30.0) as client:
            response = client.post(
                f"{self.base_url}/chat/completions",
                headers=headers,
                json=payload
            )
            response.raise_for_status()
            return response.json()
    
    def _make_streaming_request(self, payload: Dict[str, Any]) -> Iterator[Dict[str, Any]]:
        """Make streaming HTTP request to OpenAI-compatible endpoint"""
        headers = {
            "Content-Type": "application/json"
        }
        
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        
        with httpx.stream(
            "POST",
            f"{self.base_url}/chat/completions",
            headers=headers,
            json=payload,
            timeout=30.0
        ) as response:
            response.raise_for_status()
            
            for line in response.iter_lines():
                if line.startswith("data: "):
                    data = line[6:]  # Remove "data: " prefix
                    if data.strip() == "[DONE]":
                        break
                    try:
                        yield json.loads(data)
                    except json.JSONDecodeError:
                        continue
    
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
        # Custom endpoint pricing (usually cheaper)
        cost_per_1k_tokens = 0.0001
        return (tokens / 1000) * cost_per_1k_tokens
