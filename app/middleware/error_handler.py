"""Global exception handlers for structured error responses."""

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app.exceptions import (
    APIException,
    AuthenticationError,
    ForbiddenError,
    NotFoundError,
    ValidationError,
    RateLimitExceededError,
    ServiceUnavailableError,
)
from app.logging_config import setup_logger

logger = setup_logger(__name__)


def add_exception_handlers(app: FastAPI) -> None:

    @app.exception_handler(APIException)
    async def api_exception_handler(request: Request, exc: APIException) -> JSONResponse:
        """Handle custom API exceptions."""
        logger.warning(
            f"API exception: {exc.error_code} - {exc.message} "
            f"(path={request.url.path}, status={exc.status_code})"
        )
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "error_code": exc.error_code,
                "message": exc.message,
                "details": exc.details,
            },
            headers=exc.headers,
        )

    @app.exception_handler(Exception)
    async def generic_exception_handler(request: Request, exc: Exception) -> JSONResponse:
        """Handle unexpected exceptions."""
        logger.exception(
            f"Unexpected error handling request to {request.url.path}"
        )
        return JSONResponse(
            status_code=500,
            content={
                "error_code": "INTERNAL_SERVER_ERROR",
                "message": "An unexpected error occurred",
                "details": {},
            },
        )
