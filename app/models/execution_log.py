"""ExecutionLog entity model for audit trail."""

from datetime import datetime
from typing import TYPE_CHECKING, Optional
from uuid import UUID, uuid4

from sqlalchemy import Index
from sqlmodel import Field, Relationship, SQLModel

if TYPE_CHECKING:
    from app.models.agent import Agent


class ExecutionLog(SQLModel, table=True):
    """ExecutionLog entity recording each agent execution."""

    __tablename__ = "execution_logs"
    __table_args__ = (
        Index("ix_execution_log_tenant_created", "tenant_id", "created_at"),
    )

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    tenant_id: UUID = Field(index=True, nullable=False)
    agent_id: UUID = Field(foreign_key="agents.id", nullable=False, ondelete="CASCADE")
    prompt: str = Field(nullable=False)  # TEXT, no max length
    model: str = Field(max_length=50, nullable=False)
    response: str = Field(nullable=False)  # TEXT, no max length
    created_at: datetime = Field(default_factory=datetime.utcnow, nullable=False)
    agent: Optional["Agent"] = Relationship(back_populates="execution_logs")
