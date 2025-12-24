"""Execution schemas for request/response validation."""

from datetime import datetime
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel, Field, field_validator

from app.config import get_settings

settings = get_settings()


class ExecutionRequest(BaseModel):
    """Schema for agent execution request."""

    prompt: str = Field(
        ...,
        min_length=1,
        max_length=settings.max_prompt_length,
        description="The task prompt for the agent",
    )
    model: str = Field(
        ...,
        description="The model to use for execution",
    )
    temperature: Optional[float] = Field(
        default=0.7,
        ge=0.0,
        le=2.0,
        description="Controls randomness (0.0=deterministic, 2.0=creative)",
    )
    max_tokens: Optional[int] = Field(
        default=None,
        ge=1,
        le=4096,
        description="Maximum tokens in response (None=model default)",
    )

    @field_validator("model")
    @classmethod
    def validate_model(cls, v: str) -> str:
        """Validate that model is in allowed list."""
        if v not in settings.allowed_models:
            raise ValueError(
                f"Invalid model. Allowed models: {settings.allowed_models}"
            )
        return v


class ExecutionResponse(BaseModel):
    """Schema for agent execution response."""

    execution_id: UUID
    agent_id: UUID
    agent_name: str
    model: str
    prompt: str
    response: str
    tools_available: List[str]
    warning: Optional[str] = None
    executed_at: datetime


class HistoryItem(BaseModel):
    """Schema for execution history item."""

    id: UUID
    agent_id: UUID
    agent_name: str
    prompt: str
    model: str
    response: str
    created_at: datetime

    class Config:
        from_attributes = True


class HistoryListResponse(BaseModel):
    """Schema for paginated execution history response."""

    items: List[HistoryItem]
    total: int
    limit: int
    offset: int
    has_more: bool
