"""Abstract interface for LLM providers."""

from abc import ABC, abstractmethod
from typing import Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from app.models.agent import Agent


class LLMProvider(ABC):
    """Abstract base class for LLM provider implementations.

    Enables swapping between mock, OpenAI, Claude, etc. without
    modifying dependent services (Dependency Inversion Principle).
    """

    @abstractmethod
    async def generate(
        self,
        agent: "Agent",
        prompt: str,
        model: str,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
    ) -> str:
        """Generate a response from the LLM.

        Args:
            agent: The agent configuration to use
            prompt: The user's prompt/request
            model: The model identifier (e.g., "gpt-4o-mini")
            temperature: Controls randomness (0.0-2.0)
            max_tokens: Maximum tokens in response (None = model default)

        Returns:
            The generated response text
        """
        pass
