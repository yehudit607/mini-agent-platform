"""Unit tests for RateLimiter service."""

import pytest
from uuid import uuid4
from unittest.mock import AsyncMock, MagicMock

from app.services.rate_limiter import RateLimiter
from app.services.rate_limit_backend import RateLimitBackend, RateLimitResult


class MockBackend(RateLimitBackend):
    """Mock backend for testing RateLimiter."""

    def __init__(self):
        self.check_and_consume_called = False
        self.get_remaining_called = False
        self.close_called = False
        self.mock_result = RateLimitResult(allowed=True, remaining=99, retry_after=0)

    async def check_and_consume(self, key: str, limit: int, window_seconds: int):
        self.check_and_consume_called = True
        self.last_key = key
        self.last_limit = limit
        self.last_window = window_seconds
        return self.mock_result

    async def get_remaining(self, key: str, limit: int, window_seconds: int):
        self.get_remaining_called = True
        return self.mock_result.remaining

    async def close(self):
        self.close_called = True


class TestRateLimiter:
    """Tests for RateLimiter with mocked backend."""

    def test_initialization_with_backend(self):
        """RateLimiter accepts backend via constructor."""
        backend = MockBackend()
        limiter = RateLimiter(backend)

        assert limiter.backend is backend
        assert limiter.limit == 100  # From config
        assert limiter.window_seconds == 60

    @pytest.mark.asyncio
    async def test_check_and_consume_calls_backend(self):
        """check_and_consume delegates to backend with correct parameters."""
        backend = MockBackend()
        limiter = RateLimiter(backend)
        tenant_id = uuid4()

        result = await limiter.check_and_consume(tenant_id)

        assert backend.check_and_consume_called
        assert backend.last_key == f"ratelimit:{tenant_id}"
        assert backend.last_limit == 100
        assert backend.last_window == 60
        assert result.allowed is True
        assert result.remaining == 99

    @pytest.mark.asyncio
    async def test_check_and_consume_with_denied_request(self):
        """check_and_consume handles denied requests."""
        backend = MockBackend()
        backend.mock_result = RateLimitResult(allowed=False, remaining=0, retry_after=30)
        limiter = RateLimiter(backend)
        tenant_id = uuid4()

        result = await limiter.check_and_consume(tenant_id)

        assert result.allowed is False
        assert result.remaining == 0
        assert result.retry_after == 30

    @pytest.mark.asyncio
    async def test_get_remaining_calls_backend(self):
        """get_remaining delegates to backend."""
        backend = MockBackend()
        limiter = RateLimiter(backend)
        tenant_id = uuid4()

        remaining = await limiter.get_remaining(tenant_id)

        assert backend.get_remaining_called
        assert remaining == 99

    @pytest.mark.asyncio
    async def test_close_calls_backend(self):
        """close delegates to backend."""
        backend = MockBackend()
        limiter = RateLimiter(backend)

        await limiter.close()

        assert backend.close_called

    @pytest.mark.asyncio
    async def test_different_tenants_get_different_keys(self):
        """Different tenant IDs generate different rate limit keys."""
        backend = MockBackend()
        limiter = RateLimiter(backend)
        tenant1 = uuid4()
        tenant2 = uuid4()

        await limiter.check_and_consume(tenant1)
        key1 = backend.last_key

        await limiter.check_and_consume(tenant2)
        key2 = backend.last_key

        assert key1 != key2
        assert key1 == f"ratelimit:{tenant1}"
        assert key2 == f"ratelimit:{tenant2}"


class TestRateLimiterFactory:
    """Tests for RateLimiter factory functions."""

    def test_create_rate_limiter_with_custom_backend(self):
        """create_rate_limiter accepts custom backend."""
        from app.services.rate_limiter import create_rate_limiter

        backend = MockBackend()
        limiter = create_rate_limiter(backend)

        assert limiter.backend is backend

    def test_create_rate_limiter_with_default_backend(self):
        """create_rate_limiter creates Redis backend by default."""
        from app.services.rate_limiter import create_rate_limiter
        from app.services.rate_limit_redis import RedisRateLimitBackend

        limiter = create_rate_limiter()

        assert isinstance(limiter.backend, RedisRateLimitBackend)

    @pytest.mark.asyncio
    async def test_get_rate_limiter_returns_singleton(self):
        """get_rate_limiter returns same instance."""
        from app.services.rate_limiter import get_rate_limiter, _rate_limiter

        # Reset global state
        import app.services.rate_limiter as rl_module
        rl_module._rate_limiter = None

        limiter1 = await get_rate_limiter()
        limiter2 = await get_rate_limiter()

        assert limiter1 is limiter2
