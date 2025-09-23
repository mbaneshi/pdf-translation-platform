# Provider router for selecting and managing translation providers
from typing import Optional, Dict, List
import logging

from app.core.config import settings
from .providers.base import BaseProvider
from .providers.openai_provider import OpenAIProvider
from .providers.argos_provider import ArgosProvider
from .providers.openai_compatible_provider import OpenAICompatibleProvider
from .providers.deep_translator_provider import DeepTranslatorProvider

logger = logging.getLogger(__name__)


class ProviderRouter:
    """Router for selecting and managing translation providers"""
    
    def __init__(self, default: Optional[str] = None):
        self.providers: Dict[str, BaseProvider] = {}
        self.default_provider = default or getattr(settings, 'TRANSLATION_PROVIDER', 'openai')
        self._initialize_providers()
    
    def _initialize_providers(self):
        """Initialize available providers"""
        # OpenAI provider
        try:
            openai_provider = OpenAIProvider()
            if openai_provider.is_available():
                self.providers["openai"] = openai_provider
                logger.info("OpenAI provider initialized")
            else:
                logger.warning("OpenAI provider not available - missing API key")
        except Exception as e:
            logger.error(f"Failed to initialize OpenAI provider: {e}")
        
        # Argos provider (offline)
        try:
            argos_provider = ArgosProvider()
            if argos_provider.is_available():
                self.providers["argos"] = argos_provider
                logger.info("Argos provider initialized")
            else:
                logger.warning("Argos provider not available - not installed")
        except Exception as e:
            logger.error(f"Failed to initialize Argos provider: {e}")
        
        # OpenAI-compatible provider
        try:
            compatible_provider = OpenAICompatibleProvider()
            if compatible_provider.is_available():
                self.providers["openai_compatible"] = compatible_provider
                logger.info("OpenAI-compatible provider initialized")
            else:
                logger.warning("OpenAI-compatible provider not available")
        except Exception as e:
            logger.error(f"Failed to initialize OpenAI-compatible provider: {e}")
        
        # Deep Translator provider
        try:
            deep_provider = DeepTranslatorProvider()
            if deep_provider.is_available():
                self.providers["deep_translator"] = deep_provider
                logger.info("Deep Translator provider initialized")
            else:
                logger.warning("Deep Translator provider not available")
        except Exception as e:
            logger.error(f"Failed to initialize Deep Translator provider: {e}")
        
        # Validate default provider
        if self.default_provider not in self.providers:
            available_providers = list(self.providers.keys())
            if available_providers:
                self.default_provider = available_providers[0]
                logger.warning(f"Default provider '{self.default_provider}' not available, using '{available_providers[0]}'")
            else:
                raise RuntimeError("No translation providers available")
    
    def get(self, name: Optional[str] = None) -> BaseProvider:
        """Get a provider by name, or default if not specified"""
        provider_name = name or self.default_provider
        
        if provider_name not in self.providers:
            logger.warning(f"Provider '{provider_name}' not found, using default '{self.default_provider}'")
            provider_name = self.default_provider
        
        return self.providers[provider_name]
    
    def get_available_providers(self) -> List[str]:
        """Get list of available provider names"""
        return list(self.providers.keys())
    
    def get_provider_info(self, name: Optional[str] = None) -> Dict:
        """Get information about a provider"""
        provider = self.get(name)
        capabilities = provider.get_capabilities()
        
        return {
            "name": provider.name,
            "available": provider.is_available(),
            "capabilities": capabilities,
            "is_default": provider.name == self.default_provider
        }
    
    def get_all_providers_info(self) -> Dict[str, Dict]:
        """Get information about all providers"""
        return {
            name: self.get_provider_info(name) 
            for name in self.providers.keys()
        }
    
    def select_best_provider(
        self, 
        text_length: int, 
        quality_requirement: str = "medium",
        cost_sensitivity: str = "medium"
    ) -> BaseProvider:
        """Select the best provider based on requirements"""
        available_providers = [
            (name, provider) for name, provider in self.providers.items()
            if provider.is_available()
        ]
        
        if not available_providers:
            raise RuntimeError("No available providers")
        
        # Simple selection logic
        if quality_requirement == "high":
            # Prefer OpenAI providers for high quality
            for name, provider in available_providers:
                if "openai" in name:
                    return provider
        
        if cost_sensitivity == "high":
            # Prefer free providers
            for name, provider in available_providers:
                if name in ["argos", "deep_translator"]:
                    return provider
        
        if text_length > 10000:
            # For long texts, prefer providers with higher limits
            for name, provider in available_providers:
                capabilities = provider.get_capabilities()
                if capabilities.get("max_text_length", 0) >= text_length:
                    return provider
        
        # Default to first available provider
        return available_providers[0][1]
    
    def health_check(self) -> Dict[str, bool]:
        """Check health of all providers"""
        return {
            name: provider.is_available() 
            for name, provider in self.providers.items()
        }
