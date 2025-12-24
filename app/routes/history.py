from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.database import get_async_session
from app.dependencies import get_current_tenant
from app.exceptions import ValidationError
from app.repositories.execution_log_repository import ExecutionLogRepository
from app.schemas.execution import HistoryItem, HistoryListResponse

settings = get_settings()
router = APIRouter()


def get_log_repository(
    session: AsyncSession = Depends(get_async_session),
) -> ExecutionLogRepository:
    return ExecutionLogRepository(session)


@router.get(
    "/history",
    response_model=HistoryListResponse,
    summary="Get execution history",
)
async def get_history(
    limit: int = Query(
        default=settings.default_page_limit,
        ge=1,
        le=settings.max_page_limit,
        description="Number of records to return",
    ),
    offset: int = Query(
        default=0,
        ge=0,
        description="Number of records to skip",
    ),
    tenant_id: UUID = Depends(get_current_tenant),
    repository: ExecutionLogRepository = Depends(get_log_repository),
) -> HistoryListResponse:
    if limit > settings.max_page_limit:
        raise ValidationError(
            error_code="INVALID_PAGINATION",
            message="Pagination parameters are invalid",
            details={
                "limit": {
                    "provided": limit,
                    "max_allowed": settings.max_page_limit,
                }
            },
        )

    logs, total = await repository.list_paginated(tenant_id, limit, offset)

    items = []
    for log in logs:
        agent_name = log.agent.name if log.agent else "Unknown Agent"
        items.append(
            HistoryItem(
                id=log.id,
                agent_id=log.agent_id,
                agent_name=agent_name,
                prompt=log.prompt,
                model=log.model,
                response=log.response,
                created_at=log.created_at,
            )
        )

    return HistoryListResponse(
        items=items,
        total=total,
        limit=limit,
        offset=offset,
        has_more=(offset + len(items)) < total,
    )
