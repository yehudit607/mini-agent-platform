"""Agent execution route."""

from uuid import UUID

from fastapi import APIRouter, Depends, Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.adapters.llm_provider import LLMProvider
from app.config import get_settings
from app.database import get_async_session
from app.dependencies import get_current_tenant, get_llm_provider
from app.schemas.execution import ExecutionRequest, ExecutionResponse
from app.services.execution_service import ExecutionService
from app.services.rate_limiter import RateLimiter, get_rate_limiter

settings = get_settings()
router = APIRouter()


async def get_execution_service(
    session: AsyncSession = Depends(get_async_session),
    llm_provider: LLMProvider = Depends(get_llm_provider),
    rate_limiter: RateLimiter = Depends(get_rate_limiter),
) -> ExecutionService:
    """Dependency factory for ExecutionService with all dependencies injected."""
    return ExecutionService(
        session=session,
        llm_provider=llm_provider,
        rate_limiter=rate_limiter,
    )


@router.post(
    "/agents/{agent_id}/run",
    response_model=ExecutionResponse,
    summary="Execute an agent",
)
async def execute_agent(
    agent_id: UUID,
    data: ExecutionRequest,
    response: Response,
    tenant_id: UUID = Depends(get_current_tenant),
    service: ExecutionService = Depends(get_execution_service),
) -> ExecutionResponse:
    result = await service.execute_agent(tenant_id, agent_id, data)

    # Get remaining rate limit for headers (without consuming another token)
    remaining = await service.get_remaining_rate_limit(tenant_id)

    response.headers["X-RateLimit-Limit"] = str(settings.rate_limit_requests)
    response.headers["X-RateLimit-Remaining"] = str(remaining)
    response.headers["X-RateLimit-Window"] = str(settings.rate_limit_window_seconds)

    return result
