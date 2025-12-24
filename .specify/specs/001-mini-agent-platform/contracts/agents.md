# API Contract: Agents

## Base URL

`/api/v1/agents`

## Authentication

All endpoints require `X-API-KEY` header.

---

## POST /api/v1/agents

Create a new agent with associated tools.

### Request

```http
POST /api/v1/agents HTTP/1.1
X-API-KEY: tenant-a-api-key
Content-Type: application/json

{
  "name": "Research Assistant",
  "role": "researcher",
  "description": "An agent specialized in finding and summarizing information",
  "tool_ids": [
    "550e8400-e29b-41d4-a716-446655440000",
    "550e8400-e29b-41d4-a716-446655440001"
  ]
}
```

### Request Schema

| Field | Type | Required | Constraints |
|-------|------|----------|-------------|
| name | string | Yes | 1-100 characters |
| role | string | Yes | 1-100 characters |
| description | string | Yes | 1-1000 characters |
| tool_ids | array[UUID] | No | List of tool UUIDs (must belong to same tenant) |

### Response: 201 Created

```json
{
  "id": "660e8400-e29b-41d4-a716-446655440000",
  "name": "Research Assistant",
  "role": "researcher",
  "description": "An agent specialized in finding and summarizing information",
  "tools": [
    {
      "id": "550e8400-e29b-41d4-a716-446655440000",
      "name": "web_search",
      "description": "Search the web for information"
    },
    {
      "id": "550e8400-e29b-41d4-a716-446655440001",
      "name": "calculator",
      "description": "Perform mathematical calculations"
    }
  ],
  "created_at": "2025-12-24T10:30:00Z",
  "updated_at": "2025-12-24T10:30:00Z"
}
```

### Response: 400 Bad Request (Duplicate Name)

```json
{
  "error_code": "DUPLICATE_AGENT_NAME",
  "message": "An agent with this name already exists for your tenant",
  "details": {
    "name": "Research Assistant"
  }
}
```

### Response: 403 Forbidden (Cross-Tenant Tool)

```json
{
  "error_code": "CROSS_TENANT_TOOL",
  "message": "Tool not found or belongs to another tenant",
  "details": {
    "tool_id": "550e8400-e29b-41d4-a716-446655440099"
  }
}
```

---

## GET /api/v1/agents

List all agents for the authenticated tenant.

### Request

```http
GET /api/v1/agents HTTP/1.1
X-API-KEY: tenant-a-api-key
```

### Query Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| tool_name | string | No | Filter agents by associated tool name |

### Response: 200 OK

```json
{
  "items": [
    {
      "id": "660e8400-e29b-41d4-a716-446655440000",
      "name": "Research Assistant",
      "role": "researcher",
      "description": "An agent specialized in finding and summarizing information",
      "tools": [
        {
          "id": "550e8400-e29b-41d4-a716-446655440000",
          "name": "web_search",
          "description": "Search the web for information"
        }
      ],
      "created_at": "2025-12-24T10:30:00Z",
      "updated_at": "2025-12-24T10:30:00Z"
    }
  ],
  "total": 1
}
```

### Example: Filter by Tool Name

```http
GET /api/v1/agents?tool_name=web_search HTTP/1.1
X-API-KEY: tenant-a-api-key
```

Returns only agents that have a tool named "web_search" associated.

---

## GET /api/v1/agents/{id}

Get a specific agent by ID with all associated tools.

### Request

```http
GET /api/v1/agents/660e8400-e29b-41d4-a716-446655440000 HTTP/1.1
X-API-KEY: tenant-a-api-key
```

### Response: 200 OK

```json
{
  "id": "660e8400-e29b-41d4-a716-446655440000",
  "name": "Research Assistant",
  "role": "researcher",
  "description": "An agent specialized in finding and summarizing information",
  "tools": [
    {
      "id": "550e8400-e29b-41d4-a716-446655440000",
      "name": "web_search",
      "description": "Search the web for information"
    },
    {
      "id": "550e8400-e29b-41d4-a716-446655440001",
      "name": "calculator",
      "description": "Perform mathematical calculations"
    }
  ],
  "created_at": "2025-12-24T10:30:00Z",
  "updated_at": "2025-12-24T10:30:00Z"
}
```

### Response: 403 Forbidden (Cross-Tenant Access)

```json
{
  "error_code": "TENANT_ISOLATION_VIOLATION",
  "message": "Access denied to resource owned by another tenant",
  "details": {
    "resource_type": "agent",
    "resource_id": "660e8400-e29b-41d4-a716-446655440000"
  }
}
```

### Response: 404 Not Found

```json
{
  "error_code": "AGENT_NOT_FOUND",
  "message": "Agent with the specified ID does not exist",
  "details": {
    "agent_id": "660e8400-e29b-41d4-a716-446655440000"
  }
}
```

---

## PUT /api/v1/agents/{id}

Update an existing agent.

### Request

```http
PUT /api/v1/agents/660e8400-e29b-41d4-a716-446655440000 HTTP/1.1
X-API-KEY: tenant-a-api-key
Content-Type: application/json

{
  "name": "Senior Research Assistant",
  "role": "senior_researcher",
  "description": "An experienced agent for complex research tasks",
  "tool_ids": [
    "550e8400-e29b-41d4-a716-446655440000",
    "550e8400-e29b-41d4-a716-446655440002"
  ]
}
```

### Response: 200 OK

```json
{
  "id": "660e8400-e29b-41d4-a716-446655440000",
  "name": "Senior Research Assistant",
  "role": "senior_researcher",
  "description": "An experienced agent for complex research tasks",
  "tools": [
    {
      "id": "550e8400-e29b-41d4-a716-446655440000",
      "name": "web_search",
      "description": "Search the web for information"
    },
    {
      "id": "550e8400-e29b-41d4-a716-446655440002",
      "name": "document_analyzer",
      "description": "Analyze documents and extract key information"
    }
  ],
  "created_at": "2025-12-24T10:30:00Z",
  "updated_at": "2025-12-24T12:00:00Z"
}
```

---

## DELETE /api/v1/agents/{id}

Delete an agent and all associated execution logs.

### Request

```http
DELETE /api/v1/agents/660e8400-e29b-41d4-a716-446655440000 HTTP/1.1
X-API-KEY: tenant-a-api-key
```

### Response: 204 No Content

(Empty body)

---

## curl Examples

```bash
# Create agent with tools
curl -X POST http://localhost:8000/api/v1/agents \
  -H "X-API-KEY: tenant-a-key" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Research Assistant",
    "role": "researcher",
    "description": "An agent for research tasks",
    "tool_ids": ["550e8400-e29b-41d4-a716-446655440000"]
  }'

# List all agents
curl http://localhost:8000/api/v1/agents \
  -H "X-API-KEY: tenant-a-key"

# List agents filtered by tool name
curl "http://localhost:8000/api/v1/agents?tool_name=web_search" \
  -H "X-API-KEY: tenant-a-key"

# Get agent by ID
curl http://localhost:8000/api/v1/agents/660e8400-e29b-41d4-a716-446655440000 \
  -H "X-API-KEY: tenant-a-key"

# Update agent
curl -X PUT http://localhost:8000/api/v1/agents/660e8400-e29b-41d4-a716-446655440000 \
  -H "X-API-KEY: tenant-a-key" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Senior Research Assistant",
    "role": "senior_researcher",
    "description": "Experienced research agent",
    "tool_ids": ["550e8400-e29b-41d4-a716-446655440000"]
  }'

# Delete agent
curl -X DELETE http://localhost:8000/api/v1/agents/660e8400-e29b-41d4-a716-446655440000 \
  -H "X-API-KEY: tenant-a-key"
```
