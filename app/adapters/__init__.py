"""External adapters."""

from app.adapters.llm_provider import LLMProvider
from app.adapters.mock_llm import MockLLMAdapter

__all__ = ["LLMProvider", "MockLLMAdapter"]
