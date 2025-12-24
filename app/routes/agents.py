from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_async_session
from app.dependencies import get_current_tenant
from app.schemas.agent import AgentCreate, AgentUpdate, AgentResponse, AgentListResponse
from app.schemas.tool import ToolResponse
from app.services.agent_service import AgentService

router = APIRouter()


def get_agent_service(session: AsyncSession = Depends(get_async_session)) -> AgentService:
    return AgentService(session)


def agent_to_response(agent) -> AgentResponse:
    tools = [
        ToolResponse(
            id=link.tool.id,
            name=link.tool.name,
            description=link.tool.description,
            created_at=link.tool.created_at,
            updated_at=link.tool.updated_at,
        )
        for link in agent.tool_links
    ]
    return AgentResponse(
        id=agent.id,
        name=agent.name,
        role=agent.role,
        description=agent.description,
        tools=tools,
        created_at=agent.created_at,
        updated_at=agent.updated_at,
    )


@router.post(
    "/agents",
    response_model=AgentResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new agent",
)
async def create_agent(
    data: AgentCreate,
    tenant_id: UUID = Depends(get_current_tenant),
    service: AgentService = Depends(get_agent_service),
) -> AgentResponse:
    agent = await service.create_agent(tenant_id, data)
    return agent_to_response(agent)


@router.get(
    "/agents",
    response_model=AgentListResponse,
    summary="List all agents",
)
async def list_agents(
    tool_name: Optional[str] = None,
    tenant_id: UUID = Depends(get_current_tenant),
    service: AgentService = Depends(get_agent_service),
) -> AgentListResponse:
    agents = await service.list_agents(tenant_id, tool_name)
    return AgentListResponse(
        items=[agent_to_response(a) for a in agents],
        total=len(agents),
    )


@router.get(
    "/agents/{agent_id}",
    response_model=AgentResponse,
    summary="Get an agent by ID",
)
async def get_agent(
    agent_id: UUID,
    tenant_id: UUID = Depends(get_current_tenant),
    service: AgentService = Depends(get_agent_service),
) -> AgentResponse:
    agent = await service.get_agent(tenant_id, agent_id)
    return agent_to_response(agent)


@router.put(
    "/agents/{agent_id}",
    response_model=AgentResponse,
    summary="Update an agent",
)
async def update_agent(
    agent_id: UUID,
    data: AgentUpdate,
    tenant_id: UUID = Depends(get_current_tenant),
    service: AgentService = Depends(get_agent_service),
) -> AgentResponse:
    agent = await service.update_agent(tenant_id, agent_id, data)
    return agent_to_response(agent)


@router.delete(
    "/agents/{agent_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete an agent",
)
async def delete_agent(
    agent_id: UUID,
    tenant_id: UUID = Depends(get_current_tenant),
    service: AgentService = Depends(get_agent_service),
) -> None:
    await service.delete_agent(tenant_id, agent_id)
