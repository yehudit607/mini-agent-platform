"""Pydantic schemas for request/response validation."""

from app.schemas.common import ErrorResponse, PaginatedResponse

__all__ = [
    "ErrorResponse",
    "PaginatedResponse",
]
