"""FastAPI dependency injection factories.

This module centralizes all dependency injection factories for the application.
Services and repositories are created here and injected into route handlers.
"""

from typing import Optional
from uuid import UUID

from fastapi import Depends, Header
from sqlalchemy.ext.asyncio import AsyncSession

from app.adapters.llm_provider import LLMProvider
from app.adapters.mock_llm import MockLLMAdapter
from app.database import get_async_session
from app.exceptions import AuthenticationError
from app.repositories.agent_repository import AgentRepository
from app.repositories.execution_log_repository import ExecutionLogRepository
from app.repositories.tool_repository import ToolRepository
from app.services.agent_service import AgentService
from app.services.auth_service import AuthService
from app.services.execution_service import ExecutionService
from app.services.rate_limiter import RateLimiter, get_rate_limiter
from app.services.tool_service import ToolService


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


# === Repository Factories ===


def get_agent_repository(
    session: AsyncSession = Depends(get_async_session),
) -> AgentRepository:
    """Dependency factory for AgentRepository."""
    return AgentRepository(session)


def get_tool_repository(
    session: AsyncSession = Depends(get_async_session),
) -> ToolRepository:
    """Dependency factory for ToolRepository."""
    return ToolRepository(session)


def get_execution_log_repository(
    session: AsyncSession = Depends(get_async_session),
) -> ExecutionLogRepository:
    """Dependency factory for ExecutionLogRepository."""
    return ExecutionLogRepository(session)


# === Service Factories ===


def get_agent_service(
    agent_repository: AgentRepository = Depends(get_agent_repository),
    tool_repository: ToolRepository = Depends(get_tool_repository),
) -> AgentService:
    """Dependency factory for AgentService."""
    return AgentService(agent_repository, tool_repository)


def get_tool_service(
    tool_repository: ToolRepository = Depends(get_tool_repository),
) -> ToolService:
    """Dependency factory for ToolService."""
    return ToolService(tool_repository)


def get_execution_service(
    agent_service: AgentService = Depends(get_agent_service),
    log_repository: ExecutionLogRepository = Depends(get_execution_log_repository),
    llm_provider: LLMProvider = Depends(get_llm_provider),
    rate_limiter: RateLimiter = Depends(get_rate_limiter),
) -> ExecutionService:
    """Dependency factory for ExecutionService."""
    return ExecutionService(agent_service, log_repository, llm_provider, rate_limiter)


# === Rate Limiter Dependencies ===
# get_rate_limiter is imported from rate_limiter module and re-exported here


__all__ = [
    # Auth
    "get_auth_service",
    "get_current_tenant",
    # LLM
    "get_llm_provider",
    # Repositories
    "get_agent_repository",
    "get_tool_repository",
    "get_execution_log_repository",
    # Services
    "get_agent_service",
    "get_tool_service",
    "get_execution_service",
    # Rate Limiter
    "get_rate_limiter",
]
