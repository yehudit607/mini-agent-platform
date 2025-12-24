# API Contract: Tools

## Base URL

`/api/v1/tools`

## Authentication

All endpoints require `X-API-KEY` header.

---

## POST /api/v1/tools

Create a new tool for the authenticated tenant.

### Request

```http
POST /api/v1/tools HTTP/1.1
X-API-KEY: tenant-a-api-key
Content-Type: application/json

{
  "name": "web_search",
  "description": "Search the web for information"
}
```

### Request Schema

| Field | Type | Required | Constraints |
|-------|------|----------|-------------|
| name | string | Yes | 1-100 characters |
| description | string | Yes | 1-1000 characters |

### Response: 201 Created

```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "name": "web_search",
  "description": "Search the web for information",
  "created_at": "2025-12-24T10:30:00Z",
  "updated_at": "2025-12-24T10:30:00Z"
}
```

### Response: 400 Bad Request (Duplicate Name)

```json
{
  "error_code": "DUPLICATE_TOOL_NAME",
  "message": "A tool with this name already exists for your tenant",
  "details": {
    "name": "web_search"
  }
}
```

### Response: 401 Unauthorized

```json
{
  "error_code": "INVALID_API_KEY",
  "message": "Missing or invalid X-API-KEY header",
  "details": {}
}
```

---

## GET /api/v1/tools

List all tools for the authenticated tenant.

### Request

```http
GET /api/v1/tools HTTP/1.1
X-API-KEY: tenant-a-api-key
```

### Query Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| agent_name | string | No | Filter tools by associated agent name |

### Response: 200 OK

```json
{
  "items": [
    {
      "id": "550e8400-e29b-41d4-a716-446655440000",
      "name": "web_search",
      "description": "Search the web for information",
      "created_at": "2025-12-24T10:30:00Z",
      "updated_at": "2025-12-24T10:30:00Z"
    },
    {
      "id": "550e8400-e29b-41d4-a716-446655440001",
      "name": "calculator",
      "description": "Perform mathematical calculations",
      "created_at": "2025-12-24T10:31:00Z",
      "updated_at": "2025-12-24T10:31:00Z"
    }
  ],
  "total": 2
}
```

---

## GET /api/v1/tools/{id}

Get a specific tool by ID.

### Request

```http
GET /api/v1/tools/550e8400-e29b-41d4-a716-446655440000 HTTP/1.1
X-API-KEY: tenant-a-api-key
```

### Response: 200 OK

```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "name": "web_search",
  "description": "Search the web for information",
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
    "resource_type": "tool",
    "resource_id": "550e8400-e29b-41d4-a716-446655440000"
  }
}
```

### Response: 404 Not Found

```json
{
  "error_code": "TOOL_NOT_FOUND",
  "message": "Tool with the specified ID does not exist",
  "details": {
    "tool_id": "550e8400-e29b-41d4-a716-446655440000"
  }
}
```

---

## PUT /api/v1/tools/{id}

Update an existing tool.

### Request

```http
PUT /api/v1/tools/550e8400-e29b-41d4-a716-446655440000 HTTP/1.1
X-API-KEY: tenant-a-api-key
Content-Type: application/json

{
  "name": "advanced_web_search",
  "description": "Search the web with advanced filtering options"
}
```

### Response: 200 OK

```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "name": "advanced_web_search",
  "description": "Search the web with advanced filtering options",
  "created_at": "2025-12-24T10:30:00Z",
  "updated_at": "2025-12-24T11:00:00Z"
}
```

---

## DELETE /api/v1/tools/{id}

Delete a tool.

### Request

```http
DELETE /api/v1/tools/550e8400-e29b-41d4-a716-446655440000 HTTP/1.1
X-API-KEY: tenant-a-api-key
```

### Response: 204 No Content

(Empty body)

### Response: 400 Bad Request (Tool in Use)

```json
{
  "error_code": "TOOL_IN_USE",
  "message": "Cannot delete tool that is associated with agents",
  "details": {
    "dependent_agents": [
      {"id": "agent-uuid-1", "name": "Research Assistant"},
      {"id": "agent-uuid-2", "name": "Code Reviewer"}
    ]
  }
}
```

---

## curl Examples

```bash
# Create tool
curl -X POST http://localhost:8000/api/v1/tools \
  -H "X-API-KEY: tenant-a-key" \
  -H "Content-Type: application/json" \
  -d '{"name": "web_search", "description": "Search the web"}'

# List tools
curl http://localhost:8000/api/v1/tools \
  -H "X-API-KEY: tenant-a-key"

# List tools filtered by agent
curl "http://localhost:8000/api/v1/tools?agent_name=Research%20Assistant" \
  -H "X-API-KEY: tenant-a-key"

# Get tool by ID
curl http://localhost:8000/api/v1/tools/550e8400-e29b-41d4-a716-446655440000 \
  -H "X-API-KEY: tenant-a-key"

# Update tool
curl -X PUT http://localhost:8000/api/v1/tools/550e8400-e29b-41d4-a716-446655440000 \
  -H "X-API-KEY: tenant-a-key" \
  -H "Content-Type: application/json" \
  -d '{"name": "advanced_search", "description": "Advanced web search"}'

# Delete tool
curl -X DELETE http://localhost:8000/api/v1/tools/550e8400-e29b-41d4-a716-446655440000 \
  -H "X-API-KEY: tenant-a-key"
```
