from functools import lru_cache

from app.config import get_settings
from app.providers.base import Completion, LLMProvider
from app.providers.mock import MockProvider
from app.providers.openai_provider import OpenAIProvider
from app.providers.anthropic_provider import AnthropicProvider

__all__ = ["Completion", "LLMProvider", "get_provider"]


@lru_cache
def get_provider() -> LLMProvider:
    s = get_settings()
    if s.llm_provider == "openai":
        return OpenAIProvider(api_key=s.openai_api_key, model=s.openai_model)
    if s.llm_provider == "anthropic":
        return AnthropicProvider(api_key=s.anthropic_api_key, model=s.anthropic_model)
    return MockProvider()
