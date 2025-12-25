"""Unit tests for custom exceptions."""

import pytest

from app.exceptions import (
    APIException,
    AuthenticationError,
    ForbiddenError,
    NotFoundError,
    ValidationError,
    DuplicateError,
    RateLimitExceededError,
)


class TestAPIException:
    """Tests for base APIException."""

    def test_creates_with_required_fields(self):
        """Should create exception with error_code and message."""
        exc = APIException(error_code="TEST_ERROR", message="Test message")

        assert exc.error_code == "TEST_ERROR"
        assert exc.message == "Test message"
        assert exc.status_code == 400  # Default
        assert exc.details == {}
        assert exc.headers is None

    def test_creates_with_custom_status_code(self):
        """Should accept custom status code."""
        exc = APIException(
            error_code="CUSTOM", message="Custom error", status_code=418
        )

        assert exc.status_code == 418

    def test_creates_with_details(self):
        """Should store additional details."""
        details = {"field": "email", "reason": "invalid"}
        exc = APIException(
            error_code="VALIDATION", message="Invalid input", details=details
        )

        assert exc.details == details

    def test_creates_with_headers(self):
        """Should store custom headers."""
        headers = {"X-Custom-Header": "value"}
        exc = APIException(
            error_code="ERROR", message="Error", headers=headers
        )

        assert exc.headers == headers

    def test_str_representation(self):
        """Should have proper string representation."""
        exc = APIException(error_code="TEST", message="Test message")

        assert str(exc) == "Test message"


class TestAuthenticationError:
    """Tests for AuthenticationError."""

    def test_defaults_to_401(self):
        """Should default to 401 status code."""
        exc = AuthenticationError()

        assert exc.status_code == 401
        assert exc.error_code == "AUTHENTICATION_FAILED"

    def test_allows_custom_error_code(self):
        """Should accept custom error code."""
        exc = AuthenticationError(
            error_code="INVALID_TOKEN", message="Token expired"
        )

        assert exc.error_code == "INVALID_TOKEN"
        assert exc.message == "Token expired"
        assert exc.status_code == 401


class TestForbiddenError:
    """Tests for ForbiddenError."""

    def test_defaults_to_403(self):
        """Should default to 403 status code."""
        exc = ForbiddenError()

        assert exc.status_code == 403
        assert exc.error_code == "FORBIDDEN"

    def test_accepts_custom_message(self):
        """Should accept custom message."""
        exc = ForbiddenError(message="Access denied to this resource")

        assert exc.message == "Access denied to this resource"


class TestNotFoundError:
    """Tests for NotFoundError."""

    def test_defaults_to_404(self):
        """Should default to 404 status code."""
        exc = NotFoundError()

        assert exc.status_code == 404
        assert exc.error_code == "NOT_FOUND"


class TestValidationError:
    """Tests for ValidationError."""

    def test_defaults_to_400(self):
        """Should default to 400 status code."""
        exc = ValidationError()

        assert exc.status_code == 400
        assert exc.error_code == "VALIDATION_ERROR"


class TestDuplicateError:
    """Tests for DuplicateError."""

    def test_defaults_to_400(self):
        """Should default to 400 status code."""
        exc = DuplicateError()

        assert exc.status_code == 400
        assert exc.error_code == "DUPLICATE_RESOURCE"

    def test_includes_resource_details(self):
        """Should store resource identification details."""
        exc = DuplicateError(
            error_code="DUPLICATE_TOOL",
            message="Tool already exists",
            details={"name": "web_search"},
        )

        assert exc.details["name"] == "web_search"


class TestRateLimitExceededError:
    """Tests for RateLimitExceededError."""

    def test_defaults_to_429(self):
        """Should default to 429 status code."""
        exc = RateLimitExceededError(retry_after=30)

        assert exc.status_code == 429
        assert exc.error_code == "RATE_LIMIT_EXCEEDED"

    def test_includes_rate_limit_details(self):
        """Should include limit, window, and retry_after in details."""
        exc = RateLimitExceededError(retry_after=60, limit=100, window_seconds=60)

        assert exc.details["limit"] == 100
        assert exc.details["window_seconds"] == 60
        assert exc.details["retry_after_seconds"] == 60

    def test_includes_retry_after_header(self):
        """Should include Retry-After header."""
        exc = RateLimitExceededError(retry_after=45)

        assert exc.headers is not None
        assert exc.headers["Retry-After"] == "45"

    def test_uses_default_limit_and_window(self):
        """Should use default limit and window if not specified."""
        exc = RateLimitExceededError(retry_after=30)

        assert exc.details["limit"] == 100
        assert exc.details["window_seconds"] == 60
