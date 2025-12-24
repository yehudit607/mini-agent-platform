# Technical Research: Mini Agent Platform

## Technology Decisions

### 1. ORM: SQLModel vs SQLAlchemy

**Decision**: SQLModel

**Rationale**:
- Built on top of SQLAlchemy, provides async support
- Native Pydantic integration (models are both ORM and validation schemas)
- Cleaner syntax for FastAPI projects
- Maintained by the FastAPI creator (tiangolo)

**Trade-offs**:
- Less mature than pure SQLAlchemy
- Some advanced SQLAlchemy patterns require dropping to raw SA

**Example**:
```python
from sqlmodel import SQLModel, Field
from uuid import UUID, uuid4

class Tool(SQLModel, table=True):
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    name: str = Field(max_length=100)
```

### 2. Redis Client: redis-py vs aioredis

**Decision**: redis-py with async support (redis>=4.2.0)

**Rationale**:
- aioredis has been merged into redis-py as of v4.2.0
- Single dependency for sync and async operations
- Native Lua script support via `register_script()`

**Example**:
```python
import redis.asyncio as redis

client = redis.from_url("redis://localhost")
await client.eval(lua_script, keys=[key], args=[window, limit, now])
```

### 3. Rate Limiting Algorithm: Fixed Window vs Sliding Window

**Decision**: Sliding Window Counter (Redis Sorted Set)

**Rationale**:
- More accurate than fixed window (no burst at window boundary)
- Atomicity via Lua script prevents race conditions
- Sorted Set allows efficient cleanup of expired entries

**Comparison**:
| Algorithm | Accuracy | Complexity | Redis Operations |
|-----------|----------|------------|------------------|
| Fixed Window | Low (boundary burst) | Simple | GET/INCR |
| Sliding Window Log | High | Higher | ZADD/ZCOUNT |
| Sliding Window Counter | High | Medium | Hybrid |

**Implementation**: Use Sorted Set with timestamp scores, ZREMRANGEBYSCORE for cleanup.

### 4. API Key Storage: Hashed vs Plain

**Decision**: Plain text (hardcoded for MVP)

**Rationale**:
- MVP scope: predefined tenant registry
- Production enhancement: bcrypt/argon2 hashed keys in database
- Current implementation is demonstration-only

**MVP Registry**:
```python
TENANT_REGISTRY = {
    "tenant-a-api-key": UUID("11111111-1111-1111-1111-111111111111"),
    "tenant-b-api-key": UUID("22222222-2222-2222-2222-222222222222"),
}
```

**Future**: Database table with hashed keys, key rotation support.

### 5. Database Connection Pooling

**Decision**: SQLAlchemy async pool with sensible defaults

**Configuration**:
```python
from sqlalchemy.ext.asyncio import create_async_engine

engine = create_async_engine(
    DATABASE_URL,
    pool_size=5,
    max_overflow=10,
    pool_pre_ping=True,  # Health check on checkout
    pool_recycle=3600,   # Recycle connections after 1 hour
)
```

**Rationale**:
- `pool_pre_ping` prevents stale connection errors
- `pool_recycle` handles long-running containers
- Async engine for FastAPI compatibility

### 6. Pagination: Offset vs Cursor

**Decision**: Offset-based pagination (MVP)

**Rationale**:
- Simpler implementation
- Good enough for < 100,000 records per tenant
- Cursor-based is future enhancement for scale

**Trade-offs**:
| Approach | Pros | Cons |
|----------|------|------|
| Offset | Simple, random access | Slow at high offsets |
| Cursor | Fast, consistent | No random access |

**Future**: Add cursor-based option when offset > 10,000.

---

## Architecture Patterns

### Layered Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                      Routes (Thin)                          │
│  - HTTP handling, validation, response formatting           │
│  - NO business logic                                        │
└────────────────────────────┬────────────────────────────────┘
                             │
┌────────────────────────────▼────────────────────────────────┐
│                     Services (Business Logic)               │
│  - Orchestration, validation, cross-cutting concerns        │
│  - Rate limiting checks                                     │
└────────────────────────────┬────────────────────────────────┘
                             │
┌────────────────────────────▼────────────────────────────────┐
│                  Repositories (Data Access)                 │
│  - Database queries with mandatory tenant filtering         │
│  - No business logic                                        │
└────────────────────────────┬────────────────────────────────┘
                             │
┌────────────────────────────▼────────────────────────────────┐
│                      Models (Entities)                      │
│  - SQLModel definitions                                     │
│  - Relationships, constraints                               │
└─────────────────────────────────────────────────────────────┘
```

### Tenant Context Injection

```python
# dependencies.py
async def get_current_tenant(
    api_key: str = Header(..., alias="X-API-KEY"),
) -> UUID:
    tenant_id = TENANT_REGISTRY.get(api_key)
    if tenant_id is None:
        raise HTTPException(status_code=401, detail="Invalid API key")
    return tenant_id

# routes/tools.py
@router.get("/tools")
async def list_tools(
    tenant_id: UUID = Depends(get_current_tenant),
    service: ToolService = Depends(get_tool_service),
) -> ToolListResponse:
    return await service.list_tools(tenant_id)
```

---

## Testing Strategy

### Test Database

Use separate PostgreSQL database for tests:
```python
# conftest.py
TEST_DATABASE_URL = "postgresql+asyncpg://test:test@localhost/map_test"

@pytest.fixture
async def db_session():
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)
    async with AsyncSession(engine) as session:
        yield session
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.drop_all)
```

### Mock Redis for Unit Tests

```python
@pytest.fixture
def mock_redis():
    with patch("app.services.rate_limiter.redis_client") as mock:
        yield mock
```

### Tenant Isolation Test Pattern

```python
async def test_tenant_isolation(client, tenant_a_key, tenant_b_key):
    # Create tool as Tenant A
    response = await client.post(
        "/api/v1/tools",
        headers={"X-API-KEY": tenant_a_key},
        json={"name": "test", "description": "test"}
    )
    tool_id = response.json()["id"]

    # Attempt access as Tenant B
    response = await client.get(
        f"/api/v1/tools/{tool_id}",
        headers={"X-API-KEY": tenant_b_key}
    )
    assert response.status_code == 403
```

---

## Performance Benchmarks (Targets)

| Operation | Target p95 | Index Required |
|-----------|------------|----------------|
| Create Tool | < 50ms | - |
| List Tools (100) | < 100ms | tenant_id |
| Get Agent with Tools | < 100ms | eager load |
| Run Agent | < 500ms | - |
| History (10k records) | < 200ms | (tenant_id, created_at) |
| Rate Limit Check | < 10ms | Redis in-memory |

---

## Security Considerations

### Input Validation

All inputs validated via Pydantic with explicit constraints:
```python
class ToolCreate(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    description: str = Field(min_length=1, max_length=1000)
```

### SQL Injection Prevention

SQLModel/SQLAlchemy parameterized queries prevent injection:
```python
# Safe: parameterized
statement = select(Tool).where(Tool.tenant_id == tenant_id)

# Never do this (unsafe):
# f"SELECT * FROM tools WHERE tenant_id = '{tenant_id}'"
```

### Rate Limit Bypass Prevention

- Fail closed on Redis failure
- Atomic Lua script (no TOCTOU race)
- Per-tenant limiting (not per-IP)

---

## Docker Compose Architecture

```yaml
services:
  api:
    build: .
    ports: ["8000:8000"]
    depends_on: [postgres, redis]
    environment:
      DATABASE_URL: postgresql+asyncpg://map:map@postgres/map
      REDIS_URL: redis://redis:6379

  postgres:
    image: postgres:15
    environment:
      POSTGRES_DB: map
      POSTGRES_USER: map
      POSTGRES_PASSWORD: map
    volumes: [postgres_data:/var/lib/postgresql/data]

  redis:
    image: redis:7-alpine
    volumes: [redis_data:/data]

volumes:
  postgres_data:
  redis_data:
```
