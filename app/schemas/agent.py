"""Agent schemas for request/response validation."""

from datetime import datetime
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel, Field

from app.config import get_settings
from app.schemas.tool import ToolResponse

settings = get_settings()


class AgentCreate(BaseModel):
    """Schema for creating a new agent."""

    name: str = Field(
        ...,
        min_length=1,
        max_length=settings.max_name_length,
        description="Agent name (unique per tenant)",
    )
    role: str = Field(
        ...,
        min_length=1,
        max_length=settings.max_role_length,
        description="Agent role",
    )
    description: str = Field(
        ...,
        min_length=1,
        max_length=settings.max_description_length,
        description="Agent description",
    )
    tool_ids: List[UUID] = Field(
        default_factory=list,
        description="List of tool IDs to associate with the agent",
    )


class AgentUpdate(BaseModel):
    """Schema for updating an existing agent."""

    name: Optional[str] = Field(
        None,
        min_length=1,
        max_length=settings.max_name_length,
        description="Agent name (unique per tenant)",
    )
    role: Optional[str] = Field(
        None,
        min_length=1,
        max_length=settings.max_role_length,
        description="Agent role",
    )
    description: Optional[str] = Field(
        None,
        min_length=1,
        max_length=settings.max_description_length,
        description="Agent description",
    )
    tool_ids: Optional[List[UUID]] = Field(
        None,
        description="List of tool IDs to associate with the agent",
    )


class AgentResponse(BaseModel):
    """Schema for agent response."""

    id: UUID
    name: str
    role: str
    description: str
    tools: List[ToolResponse]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class AgentListResponse(BaseModel):
    """Schema for list of agents response."""

    items: List[AgentResponse]
    total: int
