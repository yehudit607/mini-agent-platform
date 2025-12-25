"""Abstract interface for rate limiting storage backends."""

from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass
class RateLimitResult:
    """Result of a rate limit check."""

    allowed: bool
    remaining: int
    retry_after: int


class RateLimitBackend(ABC):
    """Abstract base class for rate limit storage backends.

    Enables swapping between Redis, in-memory, etc. without
    modifying the RateLimiter service (Dependency Inversion Principle).
    """

    @abstractmethod
    async def check_and_consume(
        self,
        key: str,
        limit: int,
        window_seconds: int,
    ) -> RateLimitResult:
        """Check rate limit and consume a token if allowed.

        Args:
            key: Unique identifier for the rate limit bucket
            limit: Maximum requests allowed in the window
            window_seconds: Time window in seconds

        Returns:
            RateLimitResult with allowed status and remaining tokens
        """
        pass

    @abstractmethod
    async def get_remaining(
        self,
        key: str,
        limit: int,
        window_seconds: int,
    ) -> int:
        """Get remaining tokens without consuming.

        Args:
            key: Unique identifier for the rate limit bucket
            limit: Maximum requests allowed in the window
            window_seconds: Time window in seconds

        Returns:
            Number of remaining tokens
        """
        pass

    @abstractmethod
    async def close(self) -> None:
        """Clean up any resources (connections, etc.)."""
        pass
