from typing import Any, Dict, Optional


class APIException(Exception):
    def __init__(
        self,
        error_code: str,
        message: str,
        status_code: int = 400,
        details: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
    ):
        self.error_code = error_code
        self.message = message
        self.status_code = status_code
        self.details = details or {}
        self.headers = headers
        super().__init__(message)


class AuthenticationError(APIException):
    def __init__(
        self,
        error_code: str = "AUTHENTICATION_FAILED",
        message: str = "Authentication failed",
        details: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(
            error_code=error_code,
            message=message,
            status_code=401,
            details=details,
        )


class ForbiddenError(APIException):
    def __init__(
        self,
        error_code: str = "FORBIDDEN",
        message: str = "Access denied",
        details: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(
            error_code=error_code,
            message=message,
            status_code=403,
            details=details,
        )


class NotFoundError(APIException):
    def __init__(
        self,
        error_code: str = "NOT_FOUND",
        message: str = "Resource not found",
        details: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(
            error_code=error_code,
            message=message,
            status_code=404,
            details=details,
        )


class ValidationError(APIException):
    def __init__(
        self,
        error_code: str = "VALIDATION_ERROR",
        message: str = "Validation failed",
        details: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(
            error_code=error_code,
            message=message,
            status_code=400,
            details=details,
        )


class DuplicateError(APIException):
    def __init__(
        self,
        error_code: str = "DUPLICATE_RESOURCE",
        message: str = "Resource already exists",
        details: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(
            error_code=error_code,
            message=message,
            status_code=400,
            details=details,
        )


class DependencyError(APIException):
    def __init__(
        self,
        error_code: str = "DEPENDENCY_ERROR",
        message: str = "Resource has dependencies",
        details: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(
            error_code=error_code,
            message=message,
            status_code=400,
            details=details,
        )


class RateLimitExceededError(APIException):
    def __init__(
        self,
        retry_after: int,
        limit: int = 100,
        window_seconds: int = 60,
    ):
        super().__init__(
            error_code="RATE_LIMIT_EXCEEDED",
            message="Rate limit exceeded. Please try again later.",
            status_code=429,
            details={
                "limit": limit,
                "window_seconds": window_seconds,
                "retry_after_seconds": retry_after,
            },
            headers={"Retry-After": str(retry_after)},
        )


class ServiceUnavailableError(APIException):
    def __init__(
        self,
        error_code: str = "SERVICE_UNAVAILABLE",
        message: str = "Service temporarily unavailable",
        details: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(
            error_code=error_code,
            message=message,
            status_code=503,
            details=details,
        )
