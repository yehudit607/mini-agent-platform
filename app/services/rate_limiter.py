"""Rate limiter service with pluggable backend."""

from typing import Optional
from uuid import UUID

from app.config import get_settings
from app.logging_config import setup_logger
from app.services.rate_limit_backend import RateLimitBackend, RateLimitResult

settings = get_settings()
logger = setup_logger(__name__)


class RateLimiter:
    """Rate limiter service with configurable backend.

    Uses Dependency Injection to accept any RateLimitBackend implementation,
    enabling easy swapping between Redis (production) and InMemory (testing).
    """

    def __init__(self, backend: RateLimitBackend):
        self.backend = backend
        self.limit = settings.rate_limit_requests
        self.window_seconds = settings.rate_limit_window_seconds

    async def check_and_consume(self, tenant_id: UUID) -> RateLimitResult:
        """Check rate limit for tenant and consume a token if allowed."""
        key = f"ratelimit:{tenant_id}"

        result = await self.backend.check_and_consume(
            key=key,
            limit=self.limit,
            window_seconds=self.window_seconds,
        )

        if not result.allowed:
            logger.warning(
                f"Rate limit exceeded for tenant_id={tenant_id}, "
                f"retry_after={result.retry_after}s"
            )

        return result

    async def get_remaining(self, tenant_id: UUID) -> int:
        """Get remaining tokens for tenant without consuming."""
        key = f"ratelimit:{tenant_id}"

        return await self.backend.get_remaining(
            key=key,
            limit=self.limit,
            window_seconds=self.window_seconds,
        )

    async def close(self) -> None:
        """Close the backend connection."""
        await self.backend.close()


# Global instance management (for backward compatibility during transition)
_rate_limiter: Optional[RateLimiter] = None


def create_rate_limiter(backend: Optional[RateLimitBackend] = None) -> RateLimiter:
    """Create a RateLimiter with the specified or default backend."""
    if backend is None:
        from app.services.rate_limit_redis import RedisRateLimitBackend

        backend = RedisRateLimitBackend(settings.redis_url)

    return RateLimiter(backend)


async def get_rate_limiter() -> RateLimiter:
    """Get or create the global rate limiter instance."""
    global _rate_limiter
    if _rate_limiter is None:
        _rate_limiter = create_rate_limiter()
    return _rate_limiter
