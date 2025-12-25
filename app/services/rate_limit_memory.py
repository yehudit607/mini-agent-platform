"""In-memory rate limit backend for testing without Redis."""

import time
from collections import defaultdict

from app.services.rate_limit_backend import RateLimitBackend, RateLimitResult


class InMemoryRateLimitBackend(RateLimitBackend):
    """In-memory sliding window rate limiter for testing.

    Uses the same algorithm as Redis but stores timestamps in memory.
    Not suitable for production (single-instance, no persistence).
    """

    def __init__(self):
        # key -> list of request timestamps (in milliseconds)
        self._requests: dict[str, list[float]] = defaultdict(list)

    def _cleanup_expired(self, key: str, window_ms: float, now: float) -> None:
        """Remove timestamps outside the current window."""
        window_start = now - window_ms
        self._requests[key] = [
            ts for ts in self._requests[key] if ts > window_start
        ]

    async def check_and_consume(
        self,
        key: str,
        limit: int,
        window_seconds: int,
    ) -> RateLimitResult:
        now = time.time() * 1000  # Convert to milliseconds
        window_ms = window_seconds * 1000

        # Clean up expired entries
        self._cleanup_expired(key, window_ms, now)

        count = len(self._requests[key])

        if count < limit:
            # Allow request, add timestamp
            self._requests[key].append(now)
            return RateLimitResult(
                allowed=True,
                remaining=limit - count - 1,
                retry_after=0,
            )
        else:
            # Calculate retry_after from oldest entry
            if self._requests[key]:
                oldest = min(self._requests[key])
                retry_after = int((oldest + window_ms - now) / 1000)
                retry_after = max(1, retry_after)  # At least 1 second
            else:
                retry_after = window_seconds

            return RateLimitResult(
                allowed=False,
                remaining=0,
                retry_after=retry_after,
            )

    async def get_remaining(
        self,
        key: str,
        limit: int,
        window_seconds: int,
    ) -> int:
        now = time.time() * 1000
        window_ms = window_seconds * 1000

        self._cleanup_expired(key, window_ms, now)
        count = len(self._requests[key])

        return max(0, limit - count)

    async def close(self) -> None:
        """Clear all stored data."""
        self._requests.clear()

    def reset(self) -> None:
        """Reset all rate limits (useful for testing)."""
        self._requests.clear()
