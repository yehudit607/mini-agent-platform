# Implementation Plan: Mini Agent Platform (MAP)

**Branch**: `001-mini-agent-platform` | **Date**: 2025-12-24 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `.specify/specs/001-mini-agent-platform/spec.md`

---

## Summary

Build a production-ready multi-tenant backend platform for managing and executing AI Agents. The system prioritizes:
- **Strict tenant isolation** via `tenant_id` filtering on all queries
- **Scalable rate limiting** using Redis Lua scripts for atomic operations
- **Containerized deployment** via Docker Compose for PostgreSQL, Redis, and API
- **Deterministic mock LLM** for testable agent execution

---

## Technical Context

**Language/Version**: Python 3.10+ (Strongly Typed with Type Hints)
**Primary Dependencies**: FastAPI (async), SQLModel (ORM), Redis (aioredis), Pydantic v2
**Storage**: PostgreSQL (primary), Redis (rate limiting/cache)
**Migrations**: Alembic
**Testing**: pytest, pytest-asyncio, pytest-mock, httpx (async test client)
**Target Platform**: Linux server (Docker containers)
**Project Type**: Single backend API service
**Orchestration**: Docker & Docker Compose (mandatory)

**Performance Goals**:
- CRUD operations: < 100ms p95
- Agent execution: < 500ms p95
- Rate limit checks: < 10ms p95
- History pagination: < 200ms p95 (10,000+ records)

**Constraints**:
- 100 concurrent requests without blocking
- Atomic rate limiting (±0 tolerance at quota boundary)
- Zero cross-tenant data leakage

---

## Constitution Check

*GATE: Must pass before implementation begins.*

| Principle | Status | Implementation Approach |
|-----------|--------|------------------------|
| I. Code Quality & Architecture | ✅ PASS | Layered: `routes/` → `services/` → `repositories/` → `models/` |
| II. Multi-Tenancy & Security | ✅ PASS | `tenant_id` on all tables, all repo methods filter by tenant |
| III. Test-First Development | ✅ PASS | Tests written per phase, isolation tests mandatory |
| IV. User Experience Consistency | ✅ PASS | Structured errors: `{error_code, message, details}` |
| V. Performance & Reliability | ✅ PASS | Async SQLModel, Redis Lua scripts, composite indexes |

---

## Project Structure

### Documentation (this feature)

```text
.specify/specs/001-mini-agent-platform/
├── spec.md              # Feature specification (complete)
├── plan.md              # This file
├── research.md          # Technical research notes
├── data-model.md        # Entity relationships and schema
├── contracts/           # API endpoint contracts
│   ├── tools.md
│   ├── agents.md
│   ├── execution.md
│   └── history.md
└── tasks.md             # Implementation tasks (/speckit.tasks output)
```

### Source Code (repository root)

```text
app/
├── __init__.py
├── main.py                    # FastAPI application entry point
├── config.py                  # Settings and configuration (injected)
├── dependencies.py            # FastAPI Depends() providers
│
├── models/                    # SQLModel entities
│   ├── __init__.py
│   ├── base.py               # Base model with tenant_id
│   ├── tool.py               # Tool entity
│   ├── agent.py              # Agent entity + AgentToolAssociation
│   └── execution_log.py      # ExecutionLog entity
│
├── schemas/                   # Pydantic request/response schemas
│   ├── __init__.py
│   ├── tool.py
│   ├── agent.py
│   ├── execution.py
│   └── common.py             # ErrorResponse, PaginatedResponse
│
├── repositories/              # Database access layer
│   ├── __init__.py
│   ├── base.py               # Base repository with tenant filtering
│   ├── tool_repository.py
│   ├── agent_repository.py
│   └── execution_log_repository.py
│
├── services/                  # Business logic layer
│   ├── __init__.py
│   ├── tool_service.py
│   ├── agent_service.py
│   ├── execution_service.py
│   └── rate_limiter.py       # Redis Lua-based rate limiter
│
├── routes/                    # API route handlers (thin)
│   ├── __init__.py
│   ├── tools.py              # /api/v1/tools
│   ├── agents.py             # /api/v1/agents
│   ├── execution.py          # /api/v1/agents/{id}/run
│   └── history.py            # /api/v1/history
│
├── middleware/                # Request processing
│   ├── __init__.py
│   ├── auth.py               # X-API-KEY authentication
│   └── error_handler.py      # Global exception handler
│
└── adapters/                  # External integrations
    ├── __init__.py
    └── mock_llm.py           # Deterministic mock LLM adapter

tests/
├── __init__.py
├── conftest.py               # Fixtures: test DB, test client, tenant keys
├── unit/
│   ├── __init__.py
│   ├── test_tool_service.py
│   ├── test_agent_service.py
│   ├── test_execution_service.py
│   └── test_rate_limiter.py
├── integration/
│   ├── __init__.py
│   ├── test_tenant_isolation.py    # Critical: cross-tenant tests
│   ├── test_rate_limiting.py       # Quota boundary tests
│   └── test_execution_flow.py
└── contract/
    ├── __init__.py
    ├── test_tools_api.py
    ├── test_agents_api.py
    ├── test_execution_api.py
    └── test_history_api.py

alembic/
├── env.py
├── versions/
│   └── 001_initial_schema.py

scripts/
└── rate_limiter.lua          # Atomic sliding window Lua script

docker-compose.yml            # PostgreSQL, Redis, API orchestration
Dockerfile                    # API container
requirements.txt              # Python dependencies
README.md                     # Quick start, API examples, curl commands
```

**Structure Decision**: Single backend API project. No frontend. Layered architecture per constitution with clear separation: routes (thin HTTP handlers) → services (business logic) → repositories (data access) → models (entities).

---

## Data Model

### Entity Relationship Diagram

```
┌─────────────────┐       ┌─────────────────────────┐       ┌─────────────────┐
│      Tool       │       │  AgentToolAssociation   │       │      Agent      │
├─────────────────┤       ├─────────────────────────┤       ├─────────────────┤
│ id (UUID, PK)   │◄──────│ tool_id (FK)            │──────►│ id (UUID, PK)   │
│ tenant_id (UUID)│       │ agent_id (FK)           │       │ tenant_id (UUID)│
│ name (VARCHAR)  │       │ PK(tool_id, agent_id)   │       │ name (VARCHAR)  │
│ description     │       └─────────────────────────┘       │ role (VARCHAR)  │
│ created_at      │                                         │ description     │
│ updated_at      │                                         │ created_at      │
└─────────────────┘                                         │ updated_at      │
        │                                                   └─────────────────┘
        │                                                           │
        │              ┌─────────────────────┐                      │
        │              │   ExecutionLog      │                      │
        │              ├─────────────────────┤                      │
        └──────────────│ tenant_id (UUID)    │◄─────────────────────┘
                       │ agent_id (FK)       │
                       │ id (UUID, PK)       │
                       │ prompt (TEXT)       │
                       │ model (VARCHAR)     │
                       │ response (TEXT)     │
                       │ created_at          │
                       └─────────────────────┘
```

### Database Constraints

| Table | Constraint | Purpose |
|-------|-----------|---------|
| Tool | `UNIQUE(tenant_id, name)` | Prevent duplicate tool names per tenant |
| Agent | `UNIQUE(tenant_id, name)` | Prevent duplicate agent names per tenant |
| ExecutionLog | `INDEX(tenant_id, created_at DESC)` | Fast paginated history queries |
| AgentToolAssociation | `PK(agent_id, tool_id)` | Prevent duplicate associations |

---

## API Contracts

### Authentication

All endpoints require `X-API-KEY` header. Keys map to tenant IDs via predefined registry.

| Header | Required | Description |
|--------|----------|-------------|
| `X-API-KEY` | Yes | Tenant API key (hashed in registry) |

### Error Response Format

```json
{
  "error_code": "TENANT_ISOLATION_VIOLATION",
  "message": "Access denied to resource owned by another tenant",
  "details": {
    "resource_type": "tool",
    "resource_id": "uuid-here"
  }
}
```

### Endpoints Summary

| Method | Endpoint | Description | User Story |
|--------|----------|-------------|------------|
| POST | `/api/v1/tools` | Create tool | US1 |
| GET | `/api/v1/tools` | List tools (optional: `?agent_name=`) | US1 |
| GET | `/api/v1/tools/{id}` | Get tool by ID | US1 |
| PUT | `/api/v1/tools/{id}` | Update tool | US1 |
| DELETE | `/api/v1/tools/{id}` | Delete tool | US1 |
| POST | `/api/v1/agents` | Create agent with tools | US2 |
| GET | `/api/v1/agents` | List agents (optional: `?tool_name=`) | US2 |
| GET | `/api/v1/agents/{id}` | Get agent by ID | US2 |
| PUT | `/api/v1/agents/{id}` | Update agent | US2 |
| DELETE | `/api/v1/agents/{id}` | Delete agent | US2 |
| POST | `/api/v1/agents/{id}/run` | Execute agent | US3 |
| GET | `/api/v1/history` | Paginated execution history | US4 |

---

## Redis Rate Limiter Design

### Sliding Window Algorithm (Lua Script)

```lua
-- scripts/rate_limiter.lua
-- Atomic sliding window rate limiter
-- KEYS[1]: rate limit key (e.g., "ratelimit:{tenant_id}")
-- ARGV[1]: window size in seconds
-- ARGV[2]: max requests allowed
-- ARGV[3]: current timestamp (milliseconds)

local key = KEYS[1]
local window = tonumber(ARGV[1]) * 1000  -- convert to ms
local limit = tonumber(ARGV[2])
local now = tonumber(ARGV[3])
local window_start = now - window

-- Remove expired entries
redis.call('ZREMRANGEBYSCORE', key, '-inf', window_start)

-- Count current requests in window
local count = redis.call('ZCARD', key)

if count < limit then
    -- Allow request, add timestamp
    redis.call('ZADD', key, now, now .. ':' .. math.random())
    redis.call('EXPIRE', key, ARGV[1] * 2)  -- TTL = 2x window
    return {1, limit - count - 1, 0}  -- allowed, remaining, retry_after
else
    -- Get oldest entry to calculate retry_after
    local oldest = redis.call('ZRANGE', key, 0, 0, 'WITHSCORES')
    local retry_after = oldest[2] and (oldest[2] + window - now) / 1000 or ARGV[1]
    return {0, 0, math.ceil(retry_after)}  -- denied, remaining, retry_after
end
```

### Rate Limiter Service Interface

```python
class RateLimiter:
    async def check_and_consume(self, tenant_id: str) -> RateLimitResult:
        """
        Returns: RateLimitResult(allowed: bool, remaining: int, retry_after: int)
        Raises: ServiceUnavailableError if Redis is down (fail closed)
        """
```

---

## Phase-by-Phase Implementation Roadmap

### Phase 1: Infrastructure Setup

**Goal**: Docker Compose with PostgreSQL, Redis, and API skeleton running

**Deliverables**:
- `docker-compose.yml` with postgres, redis, api services
- `Dockerfile` for API container
- `requirements.txt` with all dependencies
- `app/main.py` with health check endpoint
- `app/config.py` with environment-based settings
- Alembic initialized with empty migration

**Constitution Gates**:
- ✅ Async database connection configured
- ✅ Environment-based configuration (not globals)

---

### Phase 2: Authentication & Tenant Context

**Goal**: X-API-KEY middleware injecting tenant context into all requests

**Deliverables**:
- `app/middleware/auth.py` - API key validation and tenant lookup
- `app/dependencies.py` - `get_current_tenant()` dependency
- `app/middleware/error_handler.py` - Global structured error responses
- Predefined tenant registry (hardcoded for MVP)
- Tests: 401 for missing/invalid keys

**Constitution Gates**:
- ✅ All requests authenticated
- ✅ Tenant context available via dependency injection
- ✅ Structured error responses

---

### Phase 3: Tool CRUD (User Story 1)

**Goal**: Complete Tool management with tenant isolation

**Deliverables**:
- `app/models/tool.py` - Tool entity with tenant_id
- `app/schemas/tool.py` - Request/response schemas
- `app/repositories/tool_repository.py` - CRUD with tenant filtering
- `app/services/tool_service.py` - Business logic
- `app/routes/tools.py` - API endpoints
- Alembic migration for tools table
- Tests: CRUD, tenant isolation, duplicate name rejection

**Constitution Gates**:
- ✅ Layered architecture (route → service → repository)
- ✅ All queries filter by tenant_id
- ✅ UniqueConstraint(tenant_id, name)
- ✅ Tenant isolation tests

---

### Phase 4: Agent CRUD (User Story 2)

**Goal**: Agent management with tool associations

**Deliverables**:
- `app/models/agent.py` - Agent entity + AgentToolAssociation
- `app/schemas/agent.py` - Schemas with tool IDs
- `app/repositories/agent_repository.py` - CRUD with eager loading
- `app/services/agent_service.py` - Tool validation (same tenant only)
- `app/routes/agents.py` - API endpoints with filtering
- Alembic migration for agents and association tables
- Tests: CRUD, filtering, cross-tenant tool rejection

**Constitution Gates**:
- ✅ Cross-tenant tool association blocked (403)
- ✅ Eager loading prevents N+1 queries
- ✅ Filter by tool_name query parameter

---

### Phase 5: Rate Limiting (User Story 5)

**Goal**: Redis-based sliding window rate limiter

**Deliverables**:
- `scripts/rate_limiter.lua` - Atomic Lua script
- `app/services/rate_limiter.py` - RateLimiter service
- Integration in middleware (applied to `/run` endpoint)
- Tests: Exact quota boundary, window expiration, Redis failure (503)

**Constitution Gates**:
- ✅ Atomic Lua script (not Python counters)
- ✅ Fail closed on Redis unavailability
- ✅ ±0 tolerance at quota boundary

---

### Phase 6: Agent Execution (User Story 3)

**Goal**: Run agent with mock LLM, rate-limited

**Deliverables**:
- `app/adapters/mock_llm.py` - Deterministic mock adapter
- `app/services/execution_service.py` - Orchestrates run flow
- `app/schemas/execution.py` - Run request/response
- `app/routes/execution.py` - POST /agents/{id}/run
- Tests: Deterministic output, model validation, rate limit integration

**Constitution Gates**:
- ✅ Rate limit checked before execution
- ✅ System prompt combines role + tools + task
- ✅ Deterministic mock response

---

### Phase 7: Execution History (User Story 4)

**Goal**: Paginated audit trail

**Deliverables**:
- `app/models/execution_log.py` - ExecutionLog entity
- `app/repositories/execution_log_repository.py` - Paginated queries
- `app/routes/history.py` - GET /history with limit/offset
- Alembic migration with composite index
- Tests: Pagination accuracy, tenant isolation, descending order

**Constitution Gates**:
- ✅ INDEX(tenant_id, created_at DESC)
- ✅ Limit/offset pagination
- ✅ < 200ms p95 for 10,000+ records

---

### Phase 8: Documentation & Polish

**Goal**: Production-ready deliverable

**Deliverables**:
- `README.md` with:
  - Quick start: `docker-compose up`
  - API authentication instructions
  - Rate limit documentation
  - Tenant isolation explanation
  - curl examples for every endpoint
- OpenAPI documentation (auto-generated by FastAPI)
- Final test coverage report

---

## Complexity Tracking

> No constitution violations - plan follows all principles.

| Decision | Rationale |
|----------|-----------|
| SQLModel instead of raw SQLAlchemy | Simplifies Pydantic integration while maintaining async support |
| Hardcoded tenant registry | MVP scope - database-backed registry is future enhancement |
| Mock LLM only | Specification requirement - real LLM adapter out of scope |

---

## Risk Mitigation

| Risk | Mitigation |
|------|------------|
| Redis unavailability | Fail closed with 503, circuit breaker pattern for future |
| N+1 queries on agents | Eager loading via `selectinload` in repository |
| Slow history pagination | Composite index + limit/offset with cursor option for future |
| Cross-tenant data leak | Mandatory isolation tests, repository-level enforcement |
