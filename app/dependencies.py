"""FastAPI dependency injection factories."""

from typing import Optional
from uuid import UUID

from fastapi import Depends, Header
from sqlalchemy.ext.asyncio import AsyncSession

from app.adapters.llm_provider import LLMProvider
from app.adapters.mock_llm import MockLLMAdapter
from app.database import get_async_session
from app.exceptions import AuthenticationError
from app.services.auth_service import AuthService
from app.services.rate_limiter import RateLimiter, get_rate_limiter


# === Auth Dependencies ===


def get_auth_service(
    session: AsyncSession = Depends(get_async_session),
) -> AuthService:
    """Dependency factory for AuthService."""
    return AuthService(session)


async def get_current_tenant(
    x_api_key: Optional[str] = Header(None, alias="X-API-KEY"),
    auth_service: AuthService = Depends(get_auth_service),
) -> UUID:
    """Dependency that validates API key and returns tenant UUID."""
    if x_api_key is None:
        raise AuthenticationError(
            error_code="MISSING_API_KEY",
            message="X-API-KEY header is required",
        )

    return await auth_service.validate_api_key(x_api_key)


# === LLM Provider Dependencies ===


def get_llm_provider() -> LLMProvider:
    """Dependency factory for LLM provider.

    Returns MockLLMAdapter by default. In production, this could be
    swapped to OpenAILLMProvider, ClaudeLLMProvider, etc.
    """
    return MockLLMAdapter()


# === Rate Limiter Dependencies ===
# get_rate_limiter is imported from rate_limiter module and re-exported here
__all__ = [
    "get_auth_service",
    "get_current_tenant",
    "get_llm_provider",
    "get_rate_limiter",
]
