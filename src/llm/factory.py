import logging
from .base import BaseLLM

logger = logging.getLogger("CloudCull.LLM")

class LLMFactory:
    """
    Simplified Registry/Factory for LLM Providers.
    """
    @staticmethod
    def get_provider(provider_type: str, simulated: bool = False) -> BaseLLM:
        provider_type = provider_type.lower()
        
        if simulated:
            from .providers.simulated import SimulatedProvider
            return SimulatedProvider(model=f"simulated-{provider_type}")

        if provider_type == "claude" or provider_type == "anthropic":
            from .providers.anthropic import AnthropicProvider
            return AnthropicProvider()
        elif provider_type == "gemini" or provider_type == "google":
            from .providers.google import GoogleProvider
            return GoogleProvider()
        elif provider_type == "llama" or provider_type == "groq":
            from .providers.groq import GroqProvider
            return GroqProvider()
        elif provider_type == "openai" or provider_type == "gpt4":
            from .providers.openai import OpenAIProvider
            return OpenAIProvider()
        else:
            logger.warning("Unknown provider '%s', defaulting to Claude", provider_type)
            from .providers.anthropic import AnthropicProvider
            return AnthropicProvider()
