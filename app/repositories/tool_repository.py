from datetime import datetime
from typing import List, Optional
from uuid import UUID

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.tool import Tool
from app.models.agent import AgentToolLink


class ToolRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, tenant_id: UUID, name: str, description: str) -> Tool:
        tool = Tool(
            tenant_id=tenant_id,
            name=name,
            description=description,
        )
        self.session.add(tool)
        await self.session.flush()
        await self.session.refresh(tool)
        return tool

    async def get_by_id(self, tenant_id: UUID, tool_id: UUID) -> Optional[Tool]:
        statement = select(Tool).where(
            Tool.tenant_id == tenant_id,
            Tool.id == tool_id,
        )
        result = await self.session.execute(statement)
        return result.scalar_one_or_none()

    async def get_by_name(self, tenant_id: UUID, name: str) -> Optional[Tool]:
        statement = select(Tool).where(
            Tool.tenant_id == tenant_id,
            Tool.name == name,
        )
        result = await self.session.execute(statement)
        return result.scalar_one_or_none()

    async def list_all(self, tenant_id: UUID) -> List[Tool]:
        statement = select(Tool).where(Tool.tenant_id == tenant_id)
        result = await self.session.execute(statement)
        return list(result.scalars().all())

    async def list_by_agent_name(
        self, tenant_id: UUID, agent_name: str
    ) -> List[Tool]:
        from app.models.agent import Agent

        statement = (
            select(Tool)
            .join(AgentToolLink, Tool.id == AgentToolLink.tool_id)
            .join(Agent, AgentToolLink.agent_id == Agent.id)
            .where(
                Tool.tenant_id == tenant_id,
                Agent.name == agent_name,
            )
        )
        result = await self.session.execute(statement)
        return list(result.scalars().all())

    async def update(
        self,
        tenant_id: UUID,
        tool_id: UUID,
        name: Optional[str] = None,
        description: Optional[str] = None,
    ) -> Optional[Tool]:
        tool = await self.get_by_id(tenant_id, tool_id)
        if tool is None:
            return None

        if name is not None:
            tool.name = name
        if description is not None:
            tool.description = description
        tool.updated_at = datetime.utcnow()

        await self.session.flush()
        await self.session.refresh(tool)
        return tool

    async def delete(self, tenant_id: UUID, tool_id: UUID) -> bool:
        tool = await self.get_by_id(tenant_id, tool_id)
        if tool is None:
            return False

        await self.session.delete(tool)
        await self.session.flush()
        return True

    async def get_dependent_agents(self, tenant_id: UUID, tool_id: UUID) -> List[dict]:
        from app.models.agent import Agent

        statement = (
            select(Agent.id, Agent.name)
            .join(AgentToolLink, Agent.id == AgentToolLink.agent_id)
            .where(
                Agent.tenant_id == tenant_id,
                AgentToolLink.tool_id == tool_id,
            )
        )
        result = await self.session.execute(statement)
        return [{"id": str(row.id), "name": row.name} for row in result.all()]

    async def count(self, tenant_id: UUID) -> int:
        statement = select(func.count()).select_from(Tool).where(
            Tool.tenant_id == tenant_id
        )
        result = await self.session.execute(statement)
        return result.scalar_one()
