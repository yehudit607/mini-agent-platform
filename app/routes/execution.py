"""Agent execution route."""

from uuid import UUID

from fastapi import APIRouter, Depends, Response

from app.config import get_settings
from app.dependencies import get_current_tenant, get_execution_service
from app.schemas.execution import ExecutionRequest, ExecutionResponse
from app.services.execution_service import ExecutionService

settings = get_settings()
router = APIRouter()


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
    result, remaining = await service.execute_agent(tenant_id, agent_id, data)

    response.headers["X-RateLimit-Limit"] = str(settings.rate_limit_requests)
    response.headers["X-RateLimit-Remaining"] = str(remaining)
    response.headers["X-RateLimit-Window"] = str(settings.rate_limit_window_seconds)

    return result
