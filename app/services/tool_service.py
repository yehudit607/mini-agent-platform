from typing import List, Optional
from uuid import UUID

from sqlalchemy.exc import IntegrityError

from app.exceptions import DuplicateError, NotFoundError, DependencyError, ForbiddenError
from app.models.tool import Tool
from app.repositories.tool_repository import ToolRepository
from app.schemas.tool import ToolCreate, ToolUpdate


class ToolService:
    """Service for tool CRUD operations with tenant isolation."""

    def __init__(self, tool_repository: ToolRepository):
        """Initialize with injected repository.

        Args:
            tool_repository: Repository for tool data access.
        """
        self.repository = tool_repository

    async def create_tool(self, tenant_id: UUID, data: ToolCreate) -> Tool:
        existing = await self.repository.get_by_name(tenant_id, data.name)
        if existing:
            raise DuplicateError(
                error_code="DUPLICATE_TOOL_NAME",
                message="A tool with this name already exists for your tenant",
                details={"name": data.name},
            )

        try:
            return await self.repository.create(
                tenant_id=tenant_id,
                name=data.name,
                description=data.description,
            )
        except IntegrityError:
            raise DuplicateError(
                error_code="DUPLICATE_TOOL_NAME",
                message="A tool with this name already exists for your tenant",
                details={"name": data.name},
            )

    async def get_tool(self, tenant_id: UUID, tool_id: UUID) -> Tool:
        tool = await self.repository.get_by_id(tenant_id, tool_id)
        if tool is None:
            raise NotFoundError(
                error_code="TOOL_NOT_FOUND",
                message="Tool with the specified ID does not exist",
                details={"tool_id": str(tool_id)},
            )
        return tool

    async def get_tool_or_forbidden(
        self, tenant_id: UUID, tool_id: UUID, check_exists: bool = True
    ) -> Tool:
        """Returns 403 instead of 404 to prevent tenant resource enumeration."""
        tool = await self.repository.get_by_id(tenant_id, tool_id)
        if tool is None:
            if check_exists:
                raise ForbiddenError(
                    error_code="TENANT_ISOLATION_VIOLATION",
                    message="Access denied to resource owned by another tenant",
                    details={"resource_type": "tool", "resource_id": str(tool_id)},
                )
            raise NotFoundError(
                error_code="TOOL_NOT_FOUND",
                message="Tool with the specified ID does not exist",
                details={"tool_id": str(tool_id)},
            )
        return tool

    async def list_tools(
        self, tenant_id: UUID, agent_name: Optional[str] = None
    ) -> List[Tool]:
        if agent_name:
            return await self.repository.list_by_agent_name(tenant_id, agent_name)
        return await self.repository.list_all(tenant_id)

    async def update_tool(
        self, tenant_id: UUID, tool_id: UUID, data: ToolUpdate
    ) -> Tool:
        await self.get_tool(tenant_id, tool_id)

        if data.name:
            existing = await self.repository.get_by_name(tenant_id, data.name)
            if existing and existing.id != tool_id:
                raise DuplicateError(
                    error_code="DUPLICATE_TOOL_NAME",
                    message="A tool with this name already exists for your tenant",
                    details={"name": data.name},
                )

        try:
            tool = await self.repository.update(
                tenant_id=tenant_id,
                tool_id=tool_id,
                name=data.name,
                description=data.description,
            )
            if tool is None:
                raise NotFoundError(
                    error_code="TOOL_NOT_FOUND",
                    message="Tool with the specified ID does not exist",
                    details={"tool_id": str(tool_id)},
                )
            return tool
        except IntegrityError:
            raise DuplicateError(
                error_code="DUPLICATE_TOOL_NAME",
                message="A tool with this name already exists for your tenant",
                details={"name": data.name},
            )

    async def delete_tool(self, tenant_id: UUID, tool_id: UUID) -> None:
        await self.get_tool(tenant_id, tool_id)

        dependent_agents = await self.repository.get_dependent_agents(
            tenant_id, tool_id
        )
        if dependent_agents:
            raise DependencyError(
                error_code="TOOL_IN_USE",
                message="Cannot delete tool that is associated with agents",
                details={"dependent_agents": dependent_agents},
            )

        deleted = await self.repository.delete(tenant_id, tool_id)
        if not deleted:
            raise NotFoundError(
                error_code="TOOL_NOT_FOUND",
                message="Tool with the specified ID does not exist",
                details={"tool_id": str(tool_id)},
            )
