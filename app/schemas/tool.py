"""Tool schemas for request/response validation."""

from datetime import datetime
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel, Field

from app.config import get_settings

settings = get_settings()


class ToolCreate(BaseModel):
    """Schema for creating a new tool."""

    name: str = Field(
        ...,
        min_length=1,
        max_length=settings.max_name_length,
        description="Tool name (unique per tenant)",
    )
    description: str = Field(
        ...,
        min_length=1,
        max_length=settings.max_description_length,
        description="Tool description",
    )


class ToolUpdate(BaseModel):
    """Schema for updating an existing tool."""

    name: Optional[str] = Field(
        None,
        min_length=1,
        max_length=settings.max_name_length,
        description="Tool name (unique per tenant)",
    )
    description: Optional[str] = Field(
        None,
        min_length=1,
        max_length=settings.max_description_length,
        description="Tool description",
    )


class ToolResponse(BaseModel):
    """Schema for tool response."""

    id: UUID
    name: str
    description: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ToolListResponse(BaseModel):
    """Schema for list of tools response."""

    items: List[ToolResponse]
    total: int
