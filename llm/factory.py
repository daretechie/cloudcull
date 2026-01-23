import logging
from typing import Dict, Type
from llm.base import BaseLLM

logger = logging.getLogger("CloudCull.LLM")

class LLMFactory:
    """
    Simplified Registry/Factory for LLM Providers.
    """
    @staticmethod
    def get_provider(provider_type: str, simulated: bool = False) -> BaseLLM:
        provider_type = provider_type.lower()
        
        if simulated:
            from llm.providers.mock import MockProvider
            return MockProvider(model=f"mock-{provider_type}")

        if provider_type == "claude" or provider_type == "anthropic":
            from llm.providers.anthropic import AnthropicProvider
            return AnthropicProvider()
        elif provider_type == "gemini" or provider_type == "google":
            from llm.providers.google import GoogleProvider
            return GoogleProvider()
        elif provider_type == "llama" or provider_type == "groq":
            from llm.providers.groq import GroqProvider
            return GroqProvider()
        elif provider_type == "openai" or provider_type == "gpt4":
            from llm.providers.openai import OpenAIProvider
            return OpenAIProvider()
        else:
            logger.warning("Unknown provider '%s', defaulting to Claude", provider_type)
            from llm.providers.anthropic import AnthropicProvider
            return AnthropicProvider()
