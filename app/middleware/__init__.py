"""Middleware components."""

from app.middleware.auth import TENANT_REGISTRY
from app.middleware.error_handler import add_exception_handlers

__all__ = [
    "TENANT_REGISTRY",
    "add_exception_handlers",
]
