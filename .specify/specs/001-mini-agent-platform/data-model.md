# Data Model: Mini Agent Platform

## Entity Definitions

### Tool

Represents a capability that agents can use (e.g., web_search, calculator).

```python
class Tool(SQLModel, table=True):
    __tablename__ = "tools"
    __table_args__ = (
        UniqueConstraint("tenant_id", "name", name="uq_tool_tenant_name"),
    )

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    tenant_id: UUID = Field(index=True, nullable=False)
    name: str = Field(max_length=100, nullable=False)
    description: str = Field(max_length=1000, nullable=False)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    # Relationships
    agents: List["Agent"] = Relationship(
        back_populates="tools",
        link_model=AgentToolAssociation
    )
```

### Agent

Represents an AI entity with a specific role and set of tools.

```python
class Agent(SQLModel, table=True):
    __tablename__ = "agents"
    __table_args__ = (
        UniqueConstraint("tenant_id", "name", name="uq_agent_tenant_name"),
    )

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    tenant_id: UUID = Field(index=True, nullable=False)
    name: str = Field(max_length=100, nullable=False)
    role: str = Field(max_length=100, nullable=False)
    description: str = Field(max_length=1000, nullable=False)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    # Relationships
    tools: List["Tool"] = Relationship(
        back_populates="agents",
        link_model=AgentToolAssociation
    )
    execution_logs: List["ExecutionLog"] = Relationship(back_populates="agent")
```

### AgentToolAssociation

Join table for many-to-many relationship between Agents and Tools.

```python
class AgentToolAssociation(SQLModel, table=True):
    __tablename__ = "agent_tool_associations"

    agent_id: UUID = Field(foreign_key="agents.id", primary_key=True)
    tool_id: UUID = Field(foreign_key="tools.id", primary_key=True)
```

### ExecutionLog

Records each agent execution for auditing.

```python
class ExecutionLog(SQLModel, table=True):
    __tablename__ = "execution_logs"
    __table_args__ = (
        Index("ix_execution_log_tenant_created", "tenant_id", "created_at"),
    )

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    tenant_id: UUID = Field(index=True, nullable=False)
    agent_id: UUID = Field(foreign_key="agents.id", nullable=False)
    prompt: str = Field(max_length=10000, nullable=False)
    model: str = Field(max_length=50, nullable=False)
    response: str = Field(nullable=False)  # TEXT, no max
    created_at: datetime = Field(default_factory=datetime.utcnow)

    # Relationships
    agent: "Agent" = Relationship(back_populates="execution_logs")
```

---

## Database Schema (SQL)

```sql
-- Alembic migration: 001_initial_schema.py

CREATE TABLE tools (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL,
    name VARCHAR(100) NOT NULL,
    description VARCHAR(1000) NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW(),
    CONSTRAINT uq_tool_tenant_name UNIQUE (tenant_id, name)
);

CREATE INDEX ix_tools_tenant_id ON tools(tenant_id);

CREATE TABLE agents (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL,
    name VARCHAR(100) NOT NULL,
    role VARCHAR(100) NOT NULL,
    description VARCHAR(1000) NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW(),
    CONSTRAINT uq_agent_tenant_name UNIQUE (tenant_id, name)
);

CREATE INDEX ix_agents_tenant_id ON agents(tenant_id);

CREATE TABLE agent_tool_associations (
    agent_id UUID NOT NULL REFERENCES agents(id) ON DELETE CASCADE,
    tool_id UUID NOT NULL REFERENCES tools(id) ON DELETE RESTRICT,
    PRIMARY KEY (agent_id, tool_id)
);

CREATE TABLE execution_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL,
    agent_id UUID NOT NULL REFERENCES agents(id) ON DELETE CASCADE,
    prompt TEXT NOT NULL,
    model VARCHAR(50) NOT NULL,
    response TEXT NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE INDEX ix_execution_logs_tenant_id ON execution_logs(tenant_id);
CREATE INDEX ix_execution_log_tenant_created ON execution_logs(tenant_id, created_at DESC);
```

---

## Constraints & Indexes Summary

| Table | Constraint/Index | Type | Purpose |
|-------|-----------------|------|---------|
| tools | `uq_tool_tenant_name` | UNIQUE | Prevent duplicate tool names per tenant |
| tools | `ix_tools_tenant_id` | INDEX | Fast tenant-filtered queries |
| agents | `uq_agent_tenant_name` | UNIQUE | Prevent duplicate agent names per tenant |
| agents | `ix_agents_tenant_id` | INDEX | Fast tenant-filtered queries |
| agent_tool_associations | PRIMARY KEY | PK | Prevent duplicate associations |
| agent_tool_associations | `tool_id` FK | RESTRICT | Block tool deletion if associated |
| execution_logs | `ix_execution_log_tenant_created` | INDEX | Fast paginated history (tenant + timestamp) |

---

## Tenant Isolation Enforcement

**Repository Layer Pattern**:

All repository methods MUST filter by `tenant_id`. No exceptions.

```python
class ToolRepository:
    async def get_by_id(self, tenant_id: UUID, tool_id: UUID) -> Tool | None:
        """Get tool only if it belongs to the tenant."""
        statement = select(Tool).where(
            Tool.tenant_id == tenant_id,
            Tool.id == tool_id
        )
        return await self.session.exec(statement).first()

    async def list_all(self, tenant_id: UUID) -> List[Tool]:
        """List all tools for a specific tenant."""
        statement = select(Tool).where(Tool.tenant_id == tenant_id)
        return await self.session.exec(statement).all()
```

**Service Layer Validation**:

Cross-tenant tool association is blocked at service level:

```python
class AgentService:
    async def create_agent(
        self, tenant_id: UUID, data: AgentCreate
    ) -> Agent:
        # Validate all tool_ids belong to this tenant
        for tool_id in data.tool_ids:
            tool = await self.tool_repo.get_by_id(tenant_id, tool_id)
            if tool is None:
                raise ForbiddenError(
                    error_code="CROSS_TENANT_TOOL",
                    message="Tool not found or belongs to another tenant",
                    details={"tool_id": str(tool_id)}
                )
        # ... create agent
```

---

## Cascade Behavior

| Relationship | Delete Behavior | Rationale |
|--------------|----------------|-----------|
| Agent → ExecutionLog | CASCADE | Logs are meaningless without agent |
| Agent → AgentToolAssociation | CASCADE | Clean up associations |
| Tool → AgentToolAssociation | RESTRICT | Prevent orphaned agents; require explicit unlink |
