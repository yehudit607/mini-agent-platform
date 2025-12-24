from uuid import UUID

from fastapi import APIRouter, Depends, Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.database import get_async_session
from app.dependencies import get_current_tenant
from app.schemas.execution import ExecutionRequest, ExecutionResponse
from app.services.execution_service import ExecutionService
from app.services.rate_limiter import get_rate_limiter

settings = get_settings()
router = APIRouter()


def get_execution_service(
    session: AsyncSession = Depends(get_async_session),
) -> ExecutionService:
    return ExecutionService(session)


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

    rate_limiter = await get_rate_limiter()
    rate_result = await rate_limiter.check_and_consume(tenant_id)

    response.headers["X-RateLimit-Limit"] = str(settings.rate_limit_requests)
    response.headers["X-RateLimit-Remaining"] = str(max(0, rate_result.remaining))
    response.headers["X-RateLimit-Window"] = str(settings.rate_limit_window_seconds)

    return result
