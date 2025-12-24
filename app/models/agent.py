"""Agent entity model with tool associations."""

from datetime import datetime
from typing import TYPE_CHECKING, List, Optional
from uuid import UUID, uuid4

from sqlalchemy import UniqueConstraint
from sqlmodel import Field, Relationship, SQLModel

if TYPE_CHECKING:
    from app.models.tool import Tool
    from app.models.execution_log import ExecutionLog


class AgentToolLink(SQLModel, table=True):
    """Association table linking Agents to Tools (many-to-many)."""

    __tablename__ = "agent_tool_links"

    agent_id: UUID = Field(foreign_key="agents.id", primary_key=True, ondelete="CASCADE")
    tool_id: UUID = Field(foreign_key="tools.id", primary_key=True, ondelete="RESTRICT")

    agent: "Agent" = Relationship(back_populates="tool_links")
    tool: "Tool" = Relationship(back_populates="agent_links")


class Agent(SQLModel, table=True):
    """Agent entity representing an AI entity with a specific role."""

    __tablename__ = "agents"
    __table_args__ = (
        UniqueConstraint("tenant_id", "name", name="uq_agent_tenant_name"),
    )

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    tenant_id: UUID = Field(index=True, nullable=False)
    name: str = Field(max_length=100, nullable=False)
    role: str = Field(max_length=100, nullable=False)
    description: str = Field(max_length=1000, nullable=False)
    created_at: datetime = Field(default_factory=datetime.utcnow, nullable=False)
    updated_at: datetime = Field(default_factory=datetime.utcnow, nullable=False)

    tool_links: List[AgentToolLink] = Relationship(
        back_populates="agent",
        sa_relationship_kwargs={"cascade": "all, delete-orphan"},
    )
    execution_logs: List["ExecutionLog"] = Relationship(back_populates="agent")

    @property
    def tools(self) -> List["Tool"]:
        """Get all tools associated with this agent."""
        return [link.tool for link in self.tool_links]
