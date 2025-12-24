# API Contract: Agent Execution

## Base URL

`/api/v1/agents/{agent_id}/run`

## Authentication

All endpoints require `X-API-KEY` header.

---

## POST /api/v1/agents/{agent_id}/run

Execute an agent with a task prompt. Rate-limited per tenant.

### Request

```http
POST /api/v1/agents/660e8400-e29b-41d4-a716-446655440000/run HTTP/1.1
X-API-KEY: tenant-a-api-key
Content-Type: application/json

{
  "prompt": "Find information about Python programming best practices",
  "model": "gpt-4o"
}
```

### Request Schema

| Field | Type | Required | Constraints |
|-------|------|----------|-------------|
| prompt | string | Yes | 1-10,000 characters |
| model | string | Yes | Must be one of: `gpt-4o`, `gpt-4`, `gpt-3.5-turbo`, `claude-3-opus`, `claude-3-sonnet` |

### Response: 200 OK

```json
{
  "execution_id": "770e8400-e29b-41d4-a716-446655440000",
  "agent_id": "660e8400-e29b-41d4-a716-446655440000",
  "agent_name": "Research Assistant",
  "model": "gpt-4o",
  "prompt": "Find information about Python programming best practices",
  "response": "[Mock Response] Agent 'Research Assistant' (role: researcher) processed your request using tools: [web_search, calculator]. Based on the task 'Find information about Python programming best practices', here is a simulated response demonstrating the agent's capabilities.",
  "tools_available": ["web_search", "calculator"],
  "executed_at": "2025-12-24T10:30:00Z"
}
```

### Mock LLM Response Format

The mock adapter generates deterministic responses following this pattern:

```
[Mock Response] Agent '{agent_name}' (role: {role}) processed your request
using tools: [{tool_names}]. Based on the task '{prompt_preview}', here is
a simulated response demonstrating the agent's capabilities.
```

**Determinism**: Same agent + same prompt + same model = identical response.

### Response: 400 Bad Request (Invalid Model)

```json
{
  "error_code": "INVALID_MODEL",
  "message": "The specified model is not supported",
  "details": {
    "provided_model": "gpt-5-turbo",
    "allowed_models": ["gpt-4o", "gpt-4", "gpt-3.5-turbo", "claude-3-opus", "claude-3-sonnet"]
  }
}
```

### Response: 400 Bad Request (Prompt Too Long)

```json
{
  "error_code": "PROMPT_TOO_LONG",
  "message": "Prompt exceeds maximum length of 10,000 characters",
  "details": {
    "provided_length": 12500,
    "max_length": 10000
  }
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

### Response: 429 Too Many Requests

```json
{
  "error_code": "RATE_LIMIT_EXCEEDED",
  "message": "Rate limit exceeded. Please try again later.",
  "details": {
    "limit": 100,
    "window_seconds": 60,
    "retry_after_seconds": 45
  }
}
```

**Headers included**:
```http
Retry-After: 45
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 0
X-RateLimit-Reset: 1703416245
```

### Response: 503 Service Unavailable (Redis Down)

```json
{
  "error_code": "SERVICE_UNAVAILABLE",
  "message": "Rate limiting service temporarily unavailable",
  "details": {
    "reason": "redis_connection_failed"
  }
}
```

**Note**: System fails closed when Redis is unavailable (security-first approach).

---

## Execution Flow

1. **Authentication**: Validate `X-API-KEY` and extract `tenant_id`
2. **Rate Limit Check**: Query Redis sliding window counter
   - If exceeded: Return 429 immediately
   - If Redis down: Return 503 (fail closed)
3. **Agent Lookup**: Fetch agent with tools (tenant-filtered)
   - If not found or wrong tenant: Return 403/404
4. **Input Validation**: Validate prompt length and model
5. **Generate System Prompt**: Combine agent role + tools + user prompt
6. **Mock LLM Invocation**: Generate deterministic response
7. **Log Execution**: Persist to execution_logs table
8. **Return Response**: Include execution_id for audit trail

---

## Agent Execution with No Tools (Warning)

If an agent has no tools associated, execution proceeds but includes a warning:

```json
{
  "execution_id": "770e8400-e29b-41d4-a716-446655440001",
  "agent_id": "660e8400-e29b-41d4-a716-446655440001",
  "agent_name": "Basic Agent",
  "model": "gpt-4o",
  "prompt": "Hello",
  "response": "[Mock Response] Agent 'Basic Agent' (role: assistant) processed your request with no tools available. Based on the task 'Hello', here is a simulated response.",
  "tools_available": [],
  "warning": "This agent has no tools configured. Consider adding tools for enhanced capabilities.",
  "executed_at": "2025-12-24T10:30:00Z"
}
```

---

## curl Examples

```bash
# Run agent with valid model
curl -X POST http://localhost:8000/api/v1/agents/660e8400-e29b-41d4-a716-446655440000/run \
  -H "X-API-KEY: tenant-a-key" \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "Find information about Python best practices",
    "model": "gpt-4o"
  }'

# Run agent with different model
curl -X POST http://localhost:8000/api/v1/agents/660e8400-e29b-41d4-a716-446655440000/run \
  -H "X-API-KEY: tenant-a-key" \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "Summarize this document",
    "model": "claude-3-sonnet"
  }'

# Trigger rate limit (run in loop)
for i in {1..101}; do
  curl -s -o /dev/null -w "%{http_code}\n" \
    -X POST http://localhost:8000/api/v1/agents/660e8400-e29b-41d4-a716-446655440000/run \
    -H "X-API-KEY: tenant-a-key" \
    -H "Content-Type: application/json" \
    -d '{"prompt": "test", "model": "gpt-4o"}'
done
# Last request should return 429
```
