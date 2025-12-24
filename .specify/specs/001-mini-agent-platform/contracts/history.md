# API Contract: Execution History

## Base URL

`/api/v1/history`

## Authentication

All endpoints require `X-API-KEY` header.

---

## GET /api/v1/history

Retrieve paginated execution history for the authenticated tenant.

### Request

```http
GET /api/v1/history?limit=10&offset=0 HTTP/1.1
X-API-KEY: tenant-a-api-key
```

### Query Parameters

| Parameter | Type | Required | Default | Constraints |
|-----------|------|----------|---------|-------------|
| limit | integer | No | 20 | 1-100 |
| offset | integer | No | 0 | >= 0 |

### Response: 200 OK

```json
{
  "items": [
    {
      "id": "770e8400-e29b-41d4-a716-446655440002",
      "agent_id": "660e8400-e29b-41d4-a716-446655440000",
      "agent_name": "Research Assistant",
      "prompt": "Find information about machine learning",
      "model": "gpt-4o",
      "response": "[Mock Response] Agent 'Research Assistant' (role: researcher) processed your request...",
      "created_at": "2025-12-24T11:00:00Z"
    },
    {
      "id": "770e8400-e29b-41d4-a716-446655440001",
      "agent_id": "660e8400-e29b-41d4-a716-446655440000",
      "agent_name": "Research Assistant",
      "prompt": "Summarize Python best practices",
      "model": "gpt-4o",
      "response": "[Mock Response] Agent 'Research Assistant' (role: researcher) processed your request...",
      "created_at": "2025-12-24T10:45:00Z"
    },
    {
      "id": "770e8400-e29b-41d4-a716-446655440000",
      "agent_id": "660e8400-e29b-41d4-a716-446655440000",
      "agent_name": "Research Assistant",
      "prompt": "Find information about Python best practices",
      "model": "gpt-4o",
      "response": "[Mock Response] Agent 'Research Assistant' (role: researcher) processed your request...",
      "created_at": "2025-12-24T10:30:00Z"
    }
  ],
  "total": 150,
  "limit": 10,
  "offset": 0,
  "has_more": true
}
```

### Response Schema

| Field | Type | Description |
|-------|------|-------------|
| items | array | List of execution log entries |
| total | integer | Total count of records for this tenant |
| limit | integer | Number of records requested |
| offset | integer | Number of records skipped |
| has_more | boolean | Whether more records exist beyond current page |

### Execution Log Entry Schema

| Field | Type | Description |
|-------|------|-------------|
| id | UUID | Unique execution log ID |
| agent_id | UUID | ID of the executed agent |
| agent_name | string | Name of the agent (for display) |
| prompt | string | The original user prompt |
| model | string | Model used for execution |
| response | string | The generated response |
| created_at | datetime | When the execution occurred (ISO 8601) |

### Ordering

Results are always ordered by `created_at DESC` (newest first).

---

## Pagination Examples

### First Page (Default)

```http
GET /api/v1/history HTTP/1.1
```

Returns records 1-20 (default limit).

### Second Page

```http
GET /api/v1/history?limit=20&offset=20 HTTP/1.1
```

Returns records 21-40.

### Custom Page Size

```http
GET /api/v1/history?limit=50 HTTP/1.1
```

Returns records 1-50.

### Maximum Page Size

```http
GET /api/v1/history?limit=100 HTTP/1.1
```

Returns records 1-100 (maximum allowed).

### Response: 400 Bad Request (Invalid Pagination)

```json
{
  "error_code": "INVALID_PAGINATION",
  "message": "Pagination parameters are invalid",
  "details": {
    "limit": {
      "provided": 500,
      "max_allowed": 100
    }
  }
}
```

---

## Tenant Isolation

History is strictly tenant-isolated. Tenants can only see their own execution logs.

**Test Case**: Tenant B should never see Tenant A's execution history, even with:
- Valid Tenant B API key
- Knowledge of Tenant A's execution log IDs (brute force protection)

The endpoint returns only records where `execution_logs.tenant_id` matches the authenticated tenant.

---

## Performance Considerations

### Index Usage

The query uses the composite index `(tenant_id, created_at DESC)` for optimal performance:

```sql
SELECT * FROM execution_logs
WHERE tenant_id = :tenant_id
ORDER BY created_at DESC
LIMIT :limit OFFSET :offset;
```

### SLA Target

- < 200ms p95 for queries with 10,000+ total records

### Large Offset Warning

For very large offsets (> 10,000), consider using cursor-based pagination in future versions. The current limit/offset approach is acceptable for the MVP scope.

---

## curl Examples

```bash
# Get first page (default)
curl http://localhost:8000/api/v1/history \
  -H "X-API-KEY: tenant-a-key"

# Get second page
curl "http://localhost:8000/api/v1/history?limit=20&offset=20" \
  -H "X-API-KEY: tenant-a-key"

# Get specific page size
curl "http://localhost:8000/api/v1/history?limit=50" \
  -H "X-API-KEY: tenant-a-key"

# Maximum page size
curl "http://localhost:8000/api/v1/history?limit=100" \
  -H "X-API-KEY: tenant-a-key"

# Pagination for UI (page 3, 10 items per page)
curl "http://localhost:8000/api/v1/history?limit=10&offset=20" \
  -H "X-API-KEY: tenant-a-key"
```

---

## Integration with Agent Execution

Every successful agent execution (POST `/api/v1/agents/{id}/run`) creates a corresponding entry in the execution history.

**Relationship**:
- `execution_logs.agent_id` → `agents.id`
- Agent deletion cascades to delete related execution logs
- Execution logs are immutable (no update/delete endpoints)
