from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_async_session
from app.dependencies import get_current_tenant
from app.schemas.tool import ToolCreate, ToolUpdate, ToolResponse, ToolListResponse
from app.services.tool_service import ToolService

router = APIRouter()


def get_tool_service(session: AsyncSession = Depends(get_async_session)) -> ToolService:
    return ToolService(session)


@router.post(
    "/tools",
    response_model=ToolResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new tool",
)
async def create_tool(
    data: ToolCreate,
    tenant_id: UUID = Depends(get_current_tenant),
    service: ToolService = Depends(get_tool_service),
) -> ToolResponse:
    tool = await service.create_tool(tenant_id, data)
    return ToolResponse.model_validate(tool)


@router.get(
    "/tools",
    response_model=ToolListResponse,
    summary="List all tools",
)
async def list_tools(
    agent_name: Optional[str] = None,
    tenant_id: UUID = Depends(get_current_tenant),
    service: ToolService = Depends(get_tool_service),
) -> ToolListResponse:
    tools = await service.list_tools(tenant_id, agent_name)
    return ToolListResponse(
        items=[ToolResponse.model_validate(t) for t in tools],
        total=len(tools),
    )


@router.get(
    "/tools/{tool_id}",
    response_model=ToolResponse,
    summary="Get a tool by ID",
)
async def get_tool(
    tool_id: UUID,
    tenant_id: UUID = Depends(get_current_tenant),
    service: ToolService = Depends(get_tool_service),
) -> ToolResponse:
    tool = await service.get_tool(tenant_id, tool_id)
    return ToolResponse.model_validate(tool)


@router.put(
    "/tools/{tool_id}",
    response_model=ToolResponse,
    summary="Update a tool",
)
async def update_tool(
    tool_id: UUID,
    data: ToolUpdate,
    tenant_id: UUID = Depends(get_current_tenant),
    service: ToolService = Depends(get_tool_service),
) -> ToolResponse:
    tool = await service.update_tool(tenant_id, tool_id, data)
    return ToolResponse.model_validate(tool)


@router.delete(
    "/tools/{tool_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a tool",
)
async def delete_tool(
    tool_id: UUID,
    tenant_id: UUID = Depends(get_current_tenant),
    service: ToolService = Depends(get_tool_service),
) -> None:
    await service.delete_tool(tenant_id, tool_id)
