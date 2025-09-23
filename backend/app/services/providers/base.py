# Base provider interface for translation services
from abc import ABC, abstractmethod
from typing import Iterator, Optional, Dict, Any
from dataclasses import dataclass


@dataclass
class TranslationResult:
    """Result of a translation operation"""
    text: str
    tokens_used: Optional[int] = None
    cost: Optional[float] = None
    provider: Optional[str] = None
    model: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


@dataclass
class TranslationOptions:
    """Options for translation requests"""
    temperature: float = 0.1
    max_tokens: Optional[int] = None
    preserve_formatting: bool = True
    domain: Optional[str] = None
    glossary: Optional[Dict[str, str]] = None
    custom_instructions: Optional[str] = None


class BaseProvider(ABC):
    """Base class for all translation providers"""
    
    name: str = "base"
    
    @abstractmethod
    def translate(
        self, 
        text: str, 
        src: str, 
        tgt: str, 
        options: Optional[TranslationOptions] = None
    ) -> TranslationResult:
        """Translate text synchronously"""
        raise NotImplementedError
    
    @abstractmethod
    def stream_translate(
        self, 
        text: str, 
        src: str, 
        tgt: str, 
        options: Optional[TranslationOptions] = None
    ) -> Iterator[TranslationResult]:
        """Translate text with streaming support"""
        raise NotImplementedError
    
    @abstractmethod
    def estimate_cost(
        self, 
        text: str, 
        src: str, 
        tgt: str, 
        options: Optional[TranslationOptions] = None
    ) -> Dict[str, Any]:
        """Estimate cost and token usage for translation"""
        raise NotImplementedError
    
    @abstractmethod
    def is_available(self) -> bool:
        """Check if provider is available and configured"""
        raise NotImplementedError
    
    def get_capabilities(self) -> Dict[str, Any]:
        """Get provider capabilities and limits"""
        return {
            "streaming": False,
            "max_text_length": 10000,
            "supported_languages": [],
            "cost_per_token": 0.0,
            "latency_ms": 1000
        }
