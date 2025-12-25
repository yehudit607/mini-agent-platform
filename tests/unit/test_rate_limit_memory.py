"""Unit tests for InMemoryRateLimitBackend."""

import asyncio
import pytest
import time

from app.services.rate_limit_memory import InMemoryRateLimitBackend


class TestInMemoryRateLimitBackend:
    """Tests for in-memory rate limit backend."""

    @pytest.fixture
    def backend(self):
        """Create a fresh backend for each test."""
        return InMemoryRateLimitBackend()

    @pytest.mark.asyncio
    async def test_allows_first_request(self, backend):
        """Should allow the first request."""
        result = await backend.check_and_consume("test-key", limit=10, window_seconds=60)

        assert result.allowed is True
        assert result.remaining == 9
        assert result.retry_after == 0

    @pytest.mark.asyncio
    async def test_allows_requests_up_to_limit(self, backend):
        """Should allow requests up to the limit."""
        for i in range(5):
            result = await backend.check_and_consume(
                "test-key", limit=5, window_seconds=60
            )

            if i < 5:
                assert result.allowed is True
                assert result.remaining == 5 - i - 1

    @pytest.mark.asyncio
    async def test_denies_request_at_limit(self, backend):
        """Should deny request when limit is reached."""
        # Consume all tokens
        for _ in range(5):
            await backend.check_and_consume("test-key", limit=5, window_seconds=60)

        # This should be denied
        result = await backend.check_and_consume("test-key", limit=5, window_seconds=60)

        assert result.allowed is False
        assert result.remaining == 0
        assert result.retry_after > 0

    @pytest.mark.asyncio
    async def test_different_keys_have_separate_limits(self, backend):
        """Should track rate limits separately for different keys."""
        # Exhaust limit for key1
        for _ in range(3):
            await backend.check_and_consume("key1", limit=3, window_seconds=60)

        # key1 should be denied
        result1 = await backend.check_and_consume("key1", limit=3, window_seconds=60)
        assert result1.allowed is False

        # key2 should still be allowed
        result2 = await backend.check_and_consume("key2", limit=3, window_seconds=60)
        assert result2.allowed is True

    @pytest.mark.asyncio
    async def test_get_remaining_returns_correct_count(self, backend):
        """Should return correct remaining count without consuming."""
        # Initially should have full limit
        remaining = await backend.get_remaining("test-key", limit=5, window_seconds=60)
        assert remaining == 5

        # Consume 3 tokens
        for _ in range(3):
            await backend.check_and_consume("test-key", limit=5, window_seconds=60)

        # Should have 2 remaining
        remaining = await backend.get_remaining("test-key", limit=5, window_seconds=60)
        assert remaining == 2

    @pytest.mark.asyncio
    async def test_get_remaining_does_not_consume(self, backend):
        """get_remaining should not consume a token."""
        await backend.check_and_consume("test-key", limit=5, window_seconds=60)

        # Call get_remaining multiple times
        for _ in range(10):
            await backend.get_remaining("test-key", limit=5, window_seconds=60)

        # Should still have 4 remaining (only 1 consumed)
        remaining = await backend.get_remaining("test-key", limit=5, window_seconds=60)
        assert remaining == 4

    @pytest.mark.asyncio
    async def test_close_clears_data(self, backend):
        """close() should clear all stored data."""
        # Add some requests
        await backend.check_and_consume("key1", limit=5, window_seconds=60)
        await backend.check_and_consume("key2", limit=5, window_seconds=60)

        # Close should clear data
        await backend.close()

        # Keys should be fresh
        remaining = await backend.get_remaining("key1", limit=5, window_seconds=60)
        assert remaining == 5

    @pytest.mark.asyncio
    async def test_reset_clears_data(self, backend):
        """reset() should clear all rate limits."""
        await backend.check_and_consume("test-key", limit=5, window_seconds=60)
        assert await backend.get_remaining("test-key", limit=5, window_seconds=60) == 4

        backend.reset()

        assert await backend.get_remaining("test-key", limit=5, window_seconds=60) == 5

    @pytest.mark.asyncio
    async def test_retry_after_is_positive(self, backend):
        """retry_after should be at least 1 second when denied."""
        # Exhaust limit
        for _ in range(3):
            await backend.check_and_consume("test-key", limit=3, window_seconds=60)

        result = await backend.check_and_consume("test-key", limit=3, window_seconds=60)

        assert result.allowed is False
        assert result.retry_after >= 1

    @pytest.mark.asyncio
    async def test_remaining_never_negative(self, backend):
        """remaining should never be negative."""
        for _ in range(10):
            result = await backend.check_and_consume(
                "test-key", limit=3, window_seconds=60
            )
            assert result.remaining >= 0

        remaining = await backend.get_remaining("test-key", limit=3, window_seconds=60)
        assert remaining >= 0

    @pytest.mark.asyncio
    async def test_concurrent_requests(self, backend):
        """Should handle concurrent requests correctly."""

        async def make_request():
            return await backend.check_and_consume(
                "test-key", limit=5, window_seconds=60
            )

        # Make 10 concurrent requests with limit of 5
        results = await asyncio.gather(*[make_request() for _ in range(10)])

        allowed_count = sum(1 for r in results if r.allowed)
        denied_count = sum(1 for r in results if not r.allowed)

        # Exactly 5 should be allowed, 5 denied
        assert allowed_count == 5
        assert denied_count == 5

    @pytest.mark.asyncio
    async def test_implements_abstract_interface(self, backend):
        """Should implement RateLimitBackend interface."""
        from app.services.rate_limit_backend import RateLimitBackend

        assert isinstance(backend, RateLimitBackend)


class TestInMemoryRateLimitBackendExpiry:
    """Tests for sliding window expiry behavior."""

    @pytest.fixture
    def backend(self):
        return InMemoryRateLimitBackend()

    @pytest.mark.asyncio
    async def test_expired_entries_cleaned_up(self, backend):
        """Should clean up expired entries."""
        # Use a very short window for testing
        window = 1  # 1 second

        # Exhaust limit
        for _ in range(3):
            await backend.check_and_consume("test-key", limit=3, window_seconds=window)

        # Should be denied
        result = await backend.check_and_consume(
            "test-key", limit=3, window_seconds=window
        )
        assert result.allowed is False

        # Wait for window to expire
        await asyncio.sleep(1.1)

        # Should be allowed again
        result = await backend.check_and_consume(
            "test-key", limit=3, window_seconds=window
        )
        assert result.allowed is True
        assert result.remaining == 2
