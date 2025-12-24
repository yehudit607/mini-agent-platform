from datetime import datetime
from typing import List, Optional
from uuid import UUID

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.agent import Agent, AgentToolLink
from app.models.tool import Tool


class AgentRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(
        self,
        tenant_id: UUID,
        name: str,
        role: str,
        description: str,
        tool_ids: List[UUID],
    ) -> Agent:
        agent = Agent(
            tenant_id=tenant_id,
            name=name,
            role=role,
            description=description,
        )
        self.session.add(agent)
        await self.session.flush()

        for tool_id in tool_ids:
            link = AgentToolLink(agent_id=agent.id, tool_id=tool_id)
            self.session.add(link)

        await self.session.flush()
        await self.session.refresh(agent)

        return await self.get_by_id(tenant_id, agent.id)

    async def get_by_id(self, tenant_id: UUID, agent_id: UUID) -> Optional[Agent]:
        statement = (
            select(Agent)
            .options(selectinload(Agent.tool_links).selectinload(AgentToolLink.tool))
            .where(
                Agent.tenant_id == tenant_id,
                Agent.id == agent_id,
            )
        )
        result = await self.session.execute(statement)
        return result.scalar_one_or_none()

    async def get_by_name(self, tenant_id: UUID, name: str) -> Optional[Agent]:
        statement = select(Agent).where(
            Agent.tenant_id == tenant_id,
            Agent.name == name,
        )
        result = await self.session.execute(statement)
        return result.scalar_one_or_none()

    async def list_all(self, tenant_id: UUID) -> List[Agent]:
        statement = (
            select(Agent)
            .options(selectinload(Agent.tool_links).selectinload(AgentToolLink.tool))
            .where(Agent.tenant_id == tenant_id)
        )
        result = await self.session.execute(statement)
        return list(result.scalars().all())

    async def list_by_tool_name(self, tenant_id: UUID, tool_name: str) -> List[Agent]:
        statement = (
            select(Agent)
            .options(selectinload(Agent.tool_links).selectinload(AgentToolLink.tool))
            .join(AgentToolLink, Agent.id == AgentToolLink.agent_id)
            .join(Tool, AgentToolLink.tool_id == Tool.id)
            .where(
                Agent.tenant_id == tenant_id,
                Tool.name == tool_name,
            )
        )
        result = await self.session.execute(statement)
        return list(result.scalars().unique().all())

    async def update(
        self,
        tenant_id: UUID,
        agent_id: UUID,
        name: Optional[str] = None,
        role: Optional[str] = None,
        description: Optional[str] = None,
        tool_ids: Optional[List[UUID]] = None,
    ) -> Optional[Agent]:
        agent = await self.get_by_id(tenant_id, agent_id)
        if agent is None:
            return None

        if name is not None:
            agent.name = name
        if role is not None:
            agent.role = role
        if description is not None:
            agent.description = description
        agent.updated_at = datetime.utcnow()

        if tool_ids is not None:
            for link in agent.tool_links:
                await self.session.delete(link)
            for tool_id in tool_ids:
                link = AgentToolLink(agent_id=agent.id, tool_id=tool_id)
                self.session.add(link)

        await self.session.flush()
        return await self.get_by_id(tenant_id, agent_id)

    async def delete(self, tenant_id: UUID, agent_id: UUID) -> bool:
        agent = await self.get_by_id(tenant_id, agent_id)
        if agent is None:
            return False

        await self.session.delete(agent)
        await self.session.flush()
        return True

    async def count(self, tenant_id: UUID) -> int:
        statement = select(func.count()).select_from(Agent).where(
            Agent.tenant_id == tenant_id
        )
        result = await self.session.execute(statement)
        return result.scalar_one()
