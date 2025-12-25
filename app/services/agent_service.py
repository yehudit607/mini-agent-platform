from typing import List, Optional
from uuid import UUID

from sqlalchemy.exc import IntegrityError

from app.exceptions import DuplicateError, NotFoundError, ForbiddenError
from app.models.agent import Agent
from app.repositories.agent_repository import AgentRepository
from app.repositories.tool_repository import ToolRepository
from app.schemas.agent import AgentCreate, AgentUpdate


class AgentService:
    """Service for agent CRUD operations with tenant isolation."""

    def __init__(
        self,
        agent_repository: AgentRepository,
        tool_repository: ToolRepository,
    ):
        """Initialize with injected repositories.

        Args:
            agent_repository: Repository for agent data access.
            tool_repository: Repository for tool validation.
        """
        self.repository = agent_repository
        self.tool_repository = tool_repository

    async def create_agent(self, tenant_id: UUID, data: AgentCreate) -> Agent:
        existing = await self.repository.get_by_name(tenant_id, data.name)
        if existing:
            raise DuplicateError(
                error_code="DUPLICATE_AGENT_NAME",
                message="An agent with this name already exists for your tenant",
                details={"name": data.name},
            )

        for tool_id in data.tool_ids:
            tool = await self.tool_repository.get_by_id(tenant_id, tool_id)
            if tool is None:
                raise ForbiddenError(
                    error_code="CROSS_TENANT_TOOL",
                    message="Tool not found or belongs to another tenant",
                    details={"tool_id": str(tool_id)},
                )

        try:
            return await self.repository.create(
                tenant_id=tenant_id,
                name=data.name,
                role=data.role,
                description=data.description,
                tool_ids=data.tool_ids,
            )
        except IntegrityError:
            raise DuplicateError(
                error_code="DUPLICATE_AGENT_NAME",
                message="An agent with this name already exists for your tenant",
                details={"name": data.name},
            )

    async def get_agent(self, tenant_id: UUID, agent_id: UUID) -> Agent:
        agent = await self.repository.get_by_id(tenant_id, agent_id)
        if agent is None:
            raise NotFoundError(
                error_code="AGENT_NOT_FOUND",
                message="Agent with the specified ID does not exist",
                details={"agent_id": str(agent_id)},
            )
        return agent

    async def get_agent_for_execution(
        self, tenant_id: UUID, agent_id: UUID
    ) -> Agent:
        agent = await self.repository.get_by_id(tenant_id, agent_id)
        if agent is None:
            raise ForbiddenError(
                error_code="TENANT_ISOLATION_VIOLATION",
                message="Access denied to resource owned by another tenant",
                details={"resource_type": "agent", "resource_id": str(agent_id)},
            )
        return agent

    async def list_agents(
        self, tenant_id: UUID, tool_name: Optional[str] = None
    ) -> List[Agent]:
        if tool_name:
            return await self.repository.list_by_tool_name(tenant_id, tool_name)
        return await self.repository.list_all(tenant_id)

    async def update_agent(
        self, tenant_id: UUID, agent_id: UUID, data: AgentUpdate
    ) -> Agent:
        await self.get_agent(tenant_id, agent_id)

        if data.name:
            existing = await self.repository.get_by_name(tenant_id, data.name)
            if existing and existing.id != agent_id:
                raise DuplicateError(
                    error_code="DUPLICATE_AGENT_NAME",
                    message="An agent with this name already exists for your tenant",
                    details={"name": data.name},
                )

        if data.tool_ids is not None:
            for tool_id in data.tool_ids:
                tool = await self.tool_repository.get_by_id(tenant_id, tool_id)
                if tool is None:
                    raise ForbiddenError(
                        error_code="CROSS_TENANT_TOOL",
                        message="Tool not found or belongs to another tenant",
                        details={"tool_id": str(tool_id)},
                    )

        try:
            agent = await self.repository.update(
                tenant_id=tenant_id,
                agent_id=agent_id,
                name=data.name,
                role=data.role,
                description=data.description,
                tool_ids=data.tool_ids,
            )
            if agent is None:
                raise NotFoundError(
                    error_code="AGENT_NOT_FOUND",
                    message="Agent with the specified ID does not exist",
                    details={"agent_id": str(agent_id)},
                )
            return agent
        except IntegrityError:
            raise DuplicateError(
                error_code="DUPLICATE_AGENT_NAME",
                message="An agent with this name already exists for your tenant",
                details={"name": data.name},
            )

    async def delete_agent(self, tenant_id: UUID, agent_id: UUID) -> None:
        await self.get_agent(tenant_id, agent_id)

        deleted = await self.repository.delete(tenant_id, agent_id)
        if not deleted:
            raise NotFoundError(
                error_code="AGENT_NOT_FOUND",
                message="Agent with the specified ID does not exist",
                details={"agent_id": str(agent_id)},
            )
