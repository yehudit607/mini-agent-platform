from typing import List, Optional, Tuple
from uuid import UUID

from sqlalchemy import select, func, desc
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.execution_log import ExecutionLog
from app.models.agent import Agent


class ExecutionLogRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(
        self,
        tenant_id: UUID,
        agent_id: UUID,
        prompt: str,
        model: str,
        response: str,
    ) -> ExecutionLog:
        log = ExecutionLog(
            tenant_id=tenant_id,
            agent_id=agent_id,
            prompt=prompt,
            model=model,
            response=response,
        )
        self.session.add(log)
        await self.session.flush()
        await self.session.refresh(log)
        return log

    async def get_by_id(
        self, tenant_id: UUID, log_id: UUID
    ) -> Optional[ExecutionLog]:
        statement = (
            select(ExecutionLog)
            .options(selectinload(ExecutionLog.agent))
            .where(
                ExecutionLog.tenant_id == tenant_id,
                ExecutionLog.id == log_id,
            )
        )
        result = await self.session.execute(statement)
        return result.scalar_one_or_none()

    async def list_paginated(
        self,
        tenant_id: UUID,
        limit: int,
        offset: int,
    ) -> Tuple[List[ExecutionLog], int]:
        count_statement = select(func.count()).select_from(ExecutionLog).where(
            ExecutionLog.tenant_id == tenant_id
        )
        count_result = await self.session.execute(count_statement)
        total = count_result.scalar_one()

        statement = (
            select(ExecutionLog)
            .options(selectinload(ExecutionLog.agent))
            .where(ExecutionLog.tenant_id == tenant_id)
            .order_by(desc(ExecutionLog.created_at))
            .limit(limit)
            .offset(offset)
        )
        result = await self.session.execute(statement)
        logs = list(result.scalars().all())

        return logs, total

    async def count(self, tenant_id: UUID) -> int:
        statement = select(func.count()).select_from(ExecutionLog).where(
            ExecutionLog.tenant_id == tenant_id
        )
        result = await self.session.execute(statement)
        return result.scalar_one()
