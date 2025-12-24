# Mini Agent Platform (MAP)

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.104+-00a393.svg)](https://fastapi.tiangolo.com/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-15-336791.svg)](https://www.postgresql.org/)
[![Redis](https://img.shields.io/badge/Redis-7-DC382D.svg)](https://redis.io/)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

A multi-tenant backend platform for managing and executing AI Agents. Built with **FastAPI**, **async PostgreSQL**, and **Redis**, designed for horizontal scalability and strict tenant isolation.

---

## Table of Contents

- [Project Overview](#project-overview)
- [Architecture](#architecture)
- [Key Design Decisions](#key-design-decisions)
- [Quick Start](#quick-start)
- [API Reference](#api-reference)
- [Testing](#testing)
- [Project Structure](#project-structure)

---

## Project Overview

MAP provides a secure, scalable foundation for multi-tenant AI agent orchestration:

| Capability | Implementation |
|------------|----------------|
| **Multi-Tenancy** | Column-based `tenant_id` isolation with repository-level filtering |
| **Async I/O** | Full async/await with SQLAlchemy 2.0 + asyncpg |
| **Rate Limiting** | Redis sliding window (Lua scripts) - 100 req/min per tenant |
| **AI-Ready** | Pluggable LLM adapter pattern (Mock implementation included) |
| **Audit Trail** | Paginated execution history with tenant scoping |

---

## Architecture

### High-Level System Architecture

```mermaid
flowchart TB
    subgraph Client
        A[API Consumer]
    end

    subgraph API Gateway
        B[FastAPI Application]
        C[Auth Middleware]
        D[Rate Limiter]
    end

    subgraph Service Layer
        E[Tool Service]
        F[Agent Service]
        G[Execution Service]
    end

    subgraph Data Layer
        H[Tool Repository]
        I[Agent Repository]
        J[ExecutionLog Repository]
    end

    subgraph Infrastructure
        K[(PostgreSQL)]
        L[(Redis)]
        M[Mock LLM Adapter]
    end

    A -->|HTTP + X-API-KEY| B
    B --> C
    C --> D
    D -->|Tenant Context| E & F & G

    E --> H
    F --> I
    G --> J
    G --> M

    H & I & J -->|Async Queries| K
    D -->|Sliding Window| L
```
---

## Key Design Decisions

### 1. Multi-Tenancy Strategy

**Approach:** Column-based isolation with `tenant_id` on all tenant-scoped tables.

```python
# Every repository method enforces tenant filtering
statement = select(Tool).where(
    Tool.tenant_id == tenant_id,
    Tool.id == tool_id,
)
```

**Why this approach?**
- **Simplicity**: Single database, single schema - reduces operational overhead
- **Performance**: Proper indexing on `tenant_id` ensures O(log n) lookups
- **Security**: Repository layer acts as a mandatory filter - no query can bypass tenant context
- **Cost-effective**: No per-tenant database provisioning required

**Trade-off acknowledged:** For extremely large tenants with strict compliance requirements, schema-per-tenant or database-per-tenant would provide stronger isolation guarantees.

---

### 2. Rate Limiting: Redis + Lua Scripts

**Approach:** Sliding window counter implemented as an atomic Lua script.

```lua
-- Atomic operations prevent race conditions
redis.call('ZREMRANGEBYSCORE', key, '-inf', window_start)
local count = redis.call('ZCARD', key)
if count < limit then
    redis.call('ZADD', key, now, now .. ':' .. math.random(1000000))
    return {1, limit - count - 1, 0}
end
```

**Why Lua scripts?**
- **Atomicity**: All operations execute in a single Redis transaction
- **No race conditions**: Concurrent requests can't read stale counts
- **Network efficiency**: Single round-trip vs. multiple commands

---

### 3. Clean Architecture: Separation of Concerns

```
Routes (HTTP) → Services (Business Logic) → Repositories (Data Access)
```

**Layer Responsibilities:**

| Layer | Responsibility | Example |
|-------|---------------|---------|
| **Routes** | HTTP handling, request/response serialization | Validate input, return proper status codes |
| **Services** | Business rules, orchestration | Check duplicates before create, validate cross-tenant tool access |
| **Repositories** | Data access, query construction | All queries filtered by `tenant_id` |

**Benefits:**
- **Testability**: Services can be unit tested with mocked repositories
- **Flexibility**: Swap PostgreSQL for another DB by changing only repositories
- **Maintainability**: Business logic changes don't touch HTTP layer

---

## Quick Start

### Prerequisites

- [Docker](https://docs.docker.com/get-docker/) (20.10+)
- [Docker Compose](https://docs.docker.com/compose/install/) (v2+)

### One-Command Setup

```bash
docker compose up --build
```

This starts:
- **PostgreSQL 15** on port `5432`
- **Redis 7** on port `6379`
- **FastAPI application** on port `8000`

Migrations run automatically on startup.

### Verify Installation

```bash
# Health check
curl http://localhost:8000/health

# Expected response:
# {"status":"healthy","service":"Mini Agent Platform","version":"1.0.0"}
```

### Interactive API Documentation

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

---

## API Reference

### Authentication

All endpoints (except `/health`) require the `X-API-KEY` header.

| Tenant | API Key | Tenant UUID |
|--------|---------|-------------|
| A | `tenant-a-key` | `11111111-1111-1111-1111-111111111111` |
| B | `tenant-b-key` | `22222222-2222-2222-2222-222222222222` |

### Endpoints Overview

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/health` | Health check (no auth) |
| `POST` | `/api/v1/tools` | Create a tool |
| `GET` | `/api/v1/tools` | List tools |
| `GET` | `/api/v1/tools/{id}` | Get tool by ID |
| `PUT` | `/api/v1/tools/{id}` | Update tool |
| `DELETE` | `/api/v1/tools/{id}` | Delete tool |
| `POST` | `/api/v1/agents` | Create an agent |
| `GET` | `/api/v1/agents` | List agents |
| `GET` | `/api/v1/agents/{id}` | Get agent by ID |
| `PUT` | `/api/v1/agents/{id}` | Update agent |
| `DELETE` | `/api/v1/agents/{id}` | Delete agent |
| `POST` | `/api/v1/agents/{id}/run` | Execute an agent |
| `GET` | `/api/v1/history` | Get execution history |

### Example: Complete Workflow

#### 1. Create a Tool

```bash
curl -X POST http://localhost:8000/api/v1/tools \
  -H "X-API-KEY: tenant-a-key" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "web_search",
    "description": "Search the web for real-time information"
  }'
```

**Response:**
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "name": "web_search",
  "description": "Search the web for real-time information",
  "created_at": "2024-01-15T10:30:00Z",
  "updated_at": "2024-01-15T10:30:00Z"
}
```

#### 2. Create an Agent with Tools

```bash
curl -X POST http://localhost:8000/api/v1/agents \
  -H "X-API-KEY: tenant-a-key" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Research Assistant",
    "role": "researcher",
    "description": "An AI agent specialized in research tasks",
    "tool_ids": ["550e8400-e29b-41d4-a716-446655440000"]
  }'
```

#### 3. Execute the Agent

```bash
curl -X POST http://localhost:8000/api/v1/agents/{agent_id}/run \
  -H "X-API-KEY: tenant-a-key" \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "Find the latest trends in AI agent frameworks",
    "model": "gpt-4o"
  }'
```

**Response Headers:**
```
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 99
X-RateLimit-Window: 60
```

**Response Body:**
```json
{
  "execution_id": "...",
  "agent_id": "...",
  "agent_name": "Research Assistant",
  "model": "gpt-4o",
  "prompt": "Find the latest trends in AI agent frameworks",
  "response": "[Mock Response] Agent 'Research Assistant' (role: researcher)...",
  "tools_available": ["web_search"],
  "executed_at": "2024-01-15T10:35:00Z"
}
```

### Error Response Format

All errors follow a consistent structure:

```json
{
  "error_code": "TENANT_ISOLATION_VIOLATION",
  "message": "Access denied to resource owned by another tenant",
  "details": {
    "resource_type": "agent",
    "resource_id": "550e8400-e29b-41d4-a716-446655440000"
  }
}
```

---

## Testing

### Run Full Test Suite

```bash
# Using Docker
docker compose run api pytest tests/ -v

# Local (requires PostgreSQL and Redis)
pytest tests/ -v --cov=app --cov-report=term-missing
```

### Test Categories

```bash
# Unit tests only
pytest tests/unit/ -v

# Integration tests
pytest tests/integration/ -v

# Contract tests (API behavior)
pytest tests/contract/ -v
```

---

## Project Structure

```
mini-agent-platform/
├── app/
│   ├── main.py              # FastAPI application entry point
│   ├── config.py            # Pydantic settings management
│   ├── database.py          # Async SQLAlchemy engine & session
│   ├── dependencies.py      # FastAPI dependency injection
│   ├── exceptions.py        # Custom exception hierarchy
│   ├── models/              # SQLModel entity definitions
│   │   ├── base.py          # TenantModel base class
│   │   ├── tool.py
│   │   ├── agent.py
│   │   └── execution_log.py
│   ├── schemas/             # Pydantic request/response schemas
│   ├── repositories/        # Data access layer (tenant-filtered)
│   ├── services/            # Business logic layer
│   │   ├── tool_service.py
│   │   ├── agent_service.py
│   │   ├── execution_service.py
│   │   └── rate_limiter.py  # Redis sliding window implementation
│   ├── routes/              # API endpoint handlers
│   ├── middleware/          # Auth & error handling
│   └── adapters/            # External service adapters (Mock LLM)
├── alembic/                 # Database migrations
├── scripts/
│   └── rate_limiter.lua     # Atomic rate limiting script
├── tests/
│   ├── unit/
│   ├── integration/
│   └── contract/
├── docker-compose.yml
├── Dockerfile
├── requirements.txt
└── README.md
```

---

## Supported Models

The following models are accepted by the `/run` endpoint:

- `gpt-4o`
- `gpt-4`
- `gpt-3.5-turbo`
- `claude-3-opus`
- `claude-3-sonnet`

> **Note:** The current implementation uses a Mock LLM adapter for deterministic testing. Replace `MockLLMAdapter` with a real provider integration for production use.

---

## License

MIT License - see [LICENSE](LICENSE) for details.
