"""Redis-based rate limit backend implementation."""

import time
from typing import Optional

import redis.asyncio as redis

from app.exceptions import ServiceUnavailableError
from app.logging_config import setup_logger
from app.services.rate_limit_backend import RateLimitBackend, RateLimitResult

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

# Script to check remaining without consuming
RATE_LIMIT_CHECK_SCRIPT = """
local key = KEYS[1]
local window = tonumber(ARGV[1]) * 1000
local limit = tonumber(ARGV[2])
local now = tonumber(ARGV[3])
local window_start = now - window

-- Remove expired entries
redis.call('ZREMRANGEBYSCORE', key, '-inf', window_start)

-- Count current requests in window
local count = redis.call('ZCARD', key)

return limit - count
"""


class RedisRateLimitBackend(RateLimitBackend):
    """Redis-based sliding window rate limiter using sorted sets."""

    def __init__(self, redis_url: str):
        self.redis_url = redis_url
        self._client: Optional[redis.Redis] = None

    async def _get_client(self) -> redis.Redis:
        if self._client is None:
            try:
                self._client = redis.from_url(
                    self.redis_url,
                    encoding="utf-8",
                    decode_responses=True,
                )
                await self._client.ping()
            except Exception:
                logger.exception("Redis connection failed")
                raise ServiceUnavailableError(
                    error_code="SERVICE_UNAVAILABLE",
                    message="Rate limiting service temporarily unavailable",
                    details={"reason": "redis_connection_failed"},
                )
        return self._client

    async def check_and_consume(
        self,
        key: str,
        limit: int,
        window_seconds: int,
    ) -> RateLimitResult:
        try:
            client = await self._get_client()
            now = int(time.time() * 1000)

            result = await client.eval(
                RATE_LIMIT_SCRIPT,
                1,  # Number of keys
                key,  # KEYS[1]
                window_seconds,  # ARGV[1]
                limit,  # ARGV[2]
                now,  # ARGV[3]
            )

            allowed, remaining, retry_after = result

            return RateLimitResult(
                allowed=bool(allowed),
                remaining=int(remaining),
                retry_after=int(retry_after),
            )

        except ServiceUnavailableError:
            raise
        except Exception:
            logger.exception("Redis rate limit error")
            raise ServiceUnavailableError(
                error_code="SERVICE_UNAVAILABLE",
                message="Rate limiting service temporarily unavailable",
                details={"reason": "redis_error"},
            )

    async def get_remaining(
        self,
        key: str,
        limit: int,
        window_seconds: int,
    ) -> int:
        try:
            client = await self._get_client()
            now = int(time.time() * 1000)

            remaining = await client.eval(
                RATE_LIMIT_CHECK_SCRIPT,
                1,  # Number of keys
                key,  # KEYS[1]
                window_seconds,  # ARGV[1]
                limit,  # ARGV[2]
                now,  # ARGV[3]
            )

            return max(0, int(remaining))

        except Exception:
            logger.exception("Redis get_remaining error")
            return 0  # Fail safe - report 0 remaining

    async def close(self) -> None:
        if self._client:
            await self._client.close()
            self._client = None
