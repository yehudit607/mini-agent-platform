# Mini Agent Platform (MAP)

A multi-tenant backend platform for managing and executing AI Agents.

## Quick Start

```bash
docker compose up --build
```

API available at `http://localhost:8000` | Docs at `http://localhost:8000/docs`

## Authentication

All endpoints (except `/health`) require `X-API-KEY` header.

| Tenant | API Key |
|--------|---------|
| A | `tenant-a-key` |
| B | `tenant-b-key` |

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/health` | Health check |
| POST | `/api/v1/tools` | Create tool |
| GET | `/api/v1/tools` | List tools (`?agent_name=`) |
| GET | `/api/v1/tools/{id}` | Get tool |
| PUT | `/api/v1/tools/{id}` | Update tool |
| DELETE | `/api/v1/tools/{id}` | Delete tool |
| POST | `/api/v1/agents` | Create agent |
| GET | `/api/v1/agents` | List agents (`?tool_name=`) |
| GET | `/api/v1/agents/{id}` | Get agent |
| PUT | `/api/v1/agents/{id}` | Update agent |
| DELETE | `/api/v1/agents/{id}` | Delete agent |
| POST | `/api/v1/agents/{id}/run` | Execute agent |
| GET | `/api/v1/history` | Execution history (`?limit=&offset=`) |

## Examples

```bash
# Create tool
curl -X POST http://localhost:8000/api/v1/tools \
  -H "X-API-KEY: tenant-a-key" \
  -H "Content-Type: application/json" \
  -d '{"name": "web_search", "description": "Search the web"}'

# Create agent
curl -X POST http://localhost:8000/api/v1/agents \
  -H "X-API-KEY: tenant-a-key" \
  -H "Content-Type: application/json" \
  -d '{"name": "Assistant", "role": "helper", "description": "General assistant", "tool_ids": []}'

# Execute agent
curl -X POST http://localhost:8000/api/v1/agents/{id}/run \
  -H "X-API-KEY: tenant-a-key" \
  -H "Content-Type: application/json" \
  -d '{"prompt": "Hello", "model": "gpt-4o"}'
```

## Rate Limiting

100 requests/minute per tenant using Redis sliding window. Returns `429` with `Retry-After` header when exceeded.

## Supported Models

`gpt-4o` | `gpt-4` | `gpt-3.5-turbo` | `claude-3-opus` | `claude-3-sonnet`

## Development

```bash
# Run tests
docker compose run api pytest tests/ -v

# Database migrations
alembic revision --autogenerate -m "description"
alembic upgrade head
```

## Architecture

```
app/
├── main.py           # FastAPI entry point
├── config.py         # Settings
├── database.py       # Database connection
├── dependencies.py   # DI providers
├── exceptions.py     # Error types
├── models/           # SQLModel entities
├── schemas/          # Pydantic schemas
├── repositories/     # Data access layer
├── services/         # Business logic
├── routes/           # API handlers
├── middleware/       # Auth, error handling
└── adapters/         # Mock LLM
```

## Multi-Tenancy

All database queries filter by `tenant_id`. Cross-tenant access returns `403 Forbidden`.

## Error Response Format

```json
{
  "error_code": "TENANT_ISOLATION_VIOLATION",
  "message": "Access denied to resource owned by another tenant",
  "details": {"resource_type": "tool", "resource_id": "uuid"}
}
```
