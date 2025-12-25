from dataclasses import dataclass
from typing import Optional
from uuid import UUID
import time

import redis.asyncio as redis

from app.config import get_settings
from app.exceptions import RateLimitExceededError, ServiceUnavailableError
from app.logging_config import setup_logger

settings = get_settings()
logger = setup_logger(__name__)

# Atomic Lua script ensures all rate limit operations (cleanup, count, add) happen
# in a single Redis transaction, preventing race conditions under concurrent requests
RATE_LIMIT_SCRIPT = """
local key = KEYS[1]
local window = tonumber(ARGV[1]) * 1000
local limit = tonumber(ARGV[2])
local now = tonumber(ARGV[3])
local window_start = now - window

-- Remove expired entries
redis.call('ZREMRANGEBYSCORE', key, '-inf', window_start)

-- Count current requests in window
local count = redis.call('ZCARD', key)

if count < limit then
    -- Allow request, add timestamp with random suffix for uniqueness
    redis.call('ZADD', key, now, now .. ':' .. math.random(1000000))
    redis.call('EXPIRE', key, ARGV[1] * 2)
    return {1, limit - count - 1, 0}
else
    -- Get oldest entry to calculate retry_after
    local oldest = redis.call('ZRANGE', key, 0, 0, 'WITHSCORES')
    local retry_after = 0
    if oldest[2] then
        retry_after = math.ceil((oldest[2] + window - now) / 1000)
    else
        retry_after = ARGV[1]
    end
    return {0, 0, retry_after}
end
"""


@dataclass
class RateLimitResult:
    allowed: bool
    remaining: int
    retry_after: int


class RateLimiter:
    def __init__(self, redis_url: Optional[str] = None):
        self.redis_url = redis_url or settings.redis_url
        self._client: Optional[redis.Redis] = None
        self._script_sha: Optional[str] = None

    async def _get_client(self) -> redis.Redis:
        if self._client is None:
            try:
                self._client = redis.from_url(
                    self.redis_url,
                    encoding="utf-8",
                    decode_responses=True,
                )
                await self._client.ping()
            except Exception as e:
                raise ServiceUnavailableError(
                    error_code="SERVICE_UNAVAILABLE",
                    message="Rate limiting service temporarily unavailable",
                    details={"reason": "redis_connection_failed"},
                )
        return self._client

    async def check_and_consume(self, tenant_id: UUID) -> RateLimitResult:
        """Fails closed - denies requests if Redis is unavailable."""
        try:
            client = await self._get_client()

            key = f"ratelimit:{tenant_id}"
            now = int(time.time() * 1000)

            result = await client.eval(
                RATE_LIMIT_SCRIPT,
                1,  # Number of keys
                key,  # KEYS[1]
                settings.rate_limit_window_seconds,  # ARGV[1]
                settings.rate_limit_requests,  # ARGV[2]
                now,  # ARGV[3]
            )

            allowed, remaining, retry_after = result

            if not allowed:
                logger.warning(
                    f"Rate limit exceeded for tenant_id={tenant_id}, "
                    f"retry_after={retry_after}s"
                )

            return RateLimitResult(
                allowed=bool(allowed),
                remaining=int(remaining),
                retry_after=int(retry_after),
            )

        except ServiceUnavailableError:
            raise
        except Exception as e:
            raise ServiceUnavailableError(
                error_code="SERVICE_UNAVAILABLE",
                message="Rate limiting service temporarily unavailable",
                details={"reason": "redis_error"},
            )

    async def close(self) -> None:
        if self._client:
            await self._client.close()
            self._client = None


_rate_limiter: Optional[RateLimiter] = None


async def get_rate_limiter() -> RateLimiter:
    global _rate_limiter
    if _rate_limiter is None:
        _rate_limiter = RateLimiter()
    return _rate_limiter
