# Feature Specification: Mini Agent Platform (MAP)

**Feature Branch**: `001-mini-agent-platform`
**Created**: 2025-12-24
**Status**: Ready for Implementation
**Constitution Version**: 1.0.0

## Overview

The Mini Agent Platform is a multi-tenant backend system designed to manage AI agents and their tools. It provides a controlled environment to execute tasks through a simulated AI pipeline while ensuring strict data isolation between tenants and system stability through rate limiting.

---

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Tool Management (Priority: P1)

As a tenant, I need to create and manage tools that my agents can use, so that I can define the capabilities available to my AI agents.

**Why this priority**: Tools are the foundational building blocks. Agents depend on tools, so tools must exist first. This establishes the base entity model and validates the multi-tenant isolation pattern.

**Independent Test**: Can be fully tested by creating tools via API and verifying CRUD operations work correctly with tenant isolation enforced.

**Acceptance Scenarios**:

1. **Given** a valid API key for Tenant A, **When** I create a tool with name "web_search" and description "Search the web", **Then** the tool is created and returned with a unique ID, and is only visible to Tenant A.

2. **Given** a tool exists for Tenant A, **When** Tenant B attempts to read/update/delete that tool, **Then** the system returns 403 Forbidden.

3. **Given** a valid API key, **When** I create a tool with the same name as an existing tool for my tenant, **Then** the system returns 400 Bad Request with a duplicate name error.

4. **Given** multiple tools exist for my tenant, **When** I list all tools, **Then** only my tenant's tools are returned.

---

### User Story 2 - Agent Management (Priority: P2)

As a tenant, I need to create and manage agents with associated tools, so that I can configure AI entities to perform specific tasks.

**Why this priority**: Agents are the core entity that ties tools together and enables execution. Depends on tools existing but is required before the execution flow can work.

**Independent Test**: Can be fully tested by creating agents, associating tools, and verifying CRUD operations with tenant isolation.

**Acceptance Scenarios**:

1. **Given** valid tools exist for my tenant, **When** I create an agent with name "Research Assistant", role "researcher", description, and tool associations, **Then** the agent is created with the specified tools attached.

2. **Given** an agent exists for Tenant A, **When** Tenant B attempts to access it, **Then** the system returns 403 Forbidden.

3. **Given** multiple agents exist, **When** I filter agents by a specific tool name, **Then** only agents with that tool are returned.

4. **Given** multiple tools exist, **When** I filter tools by a specific agent name, **Then** only tools associated with that agent are returned.

5. **Given** I try to associate a tool belonging to another tenant with my agent, **Then** the system returns 403 Forbidden.

---

### User Story 3 - Agent Execution (Priority: P3)

As a tenant, I need to run an agent with a task prompt, so that I can get AI-generated responses based on the agent's configuration.

**Why this priority**: This is the core value proposition but depends on both tools and agents being fully functional. The mock LLM adapter ensures deterministic testing.

**Independent Test**: Can be tested by running an agent with a prompt and verifying the response structure and deterministic behavior.

**Acceptance Scenarios**:

1. **Given** an agent with tools exists for my tenant, **When** I run the agent with a task "Find information about Python" and model "gpt-4o", **Then** a simulated response is returned reflecting the agent's identity and tools.

2. **Given** the same agent and task, **When** I run the agent multiple times, **Then** the response is deterministic and consistent.

3. **Given** I specify an invalid model identifier, **When** I run the agent, **Then** the system returns 400 Bad Request with valid model options.

4. **Given** I have exceeded my rate limit quota, **When** I attempt to run an agent, **Then** the system returns 429 Too Many Requests with retry information.

---

### User Story 4 - Execution History & Auditing (Priority: P4)

As a tenant, I need to view the history of all agent executions, so that I can audit past runs and debug issues.

**Why this priority**: Auditing is essential for production use but can be deferred until the core execution flow works. Adds compliance and debugging capabilities.

**Independent Test**: Can be tested by running agents, then querying history and verifying pagination works correctly.

**Acceptance Scenarios**:

1. **Given** I have run agents multiple times, **When** I request execution history, **Then** I receive a paginated list of all my tenant's executions with prompt, model, timestamp, and response.

2. **Given** 100 execution records exist, **When** I request with limit=10 and offset=20, **Then** I receive exactly 10 records starting from the 21st record, ordered by timestamp descending.

3. **Given** Tenant B has execution records, **When** Tenant A requests history, **Then** Tenant A sees only their own records (never Tenant B's).

---

### User Story 5 - API Authentication & Rate Limiting (Priority: P1)

As a platform operator, I need all API requests to be authenticated and rate-limited, so that the system remains secure and stable under load.

**Why this priority**: Security and stability are foundational. Without authentication, nothing else works securely. Rate limiting prevents abuse and ensures fair resource allocation.

**Independent Test**: Can be tested by sending requests with valid/invalid API keys and by simulating rapid requests to verify throttling.

**Acceptance Scenarios**:

1. **Given** a request without X-API-KEY header, **When** any endpoint is called, **Then** the system returns 401 Unauthorized.

2. **Given** a request with an invalid API key, **When** any endpoint is called, **Then** the system returns 401 Unauthorized.

3. **Given** a valid API key, **When** requests exceed the tenant's rate limit, **Then** the system returns 429 Too Many Requests at exactly the quota boundary.

4. **Given** the rate limit window expires, **When** I make a new request, **Then** the request succeeds.

---

### Edge Cases

- What happens when a tenant tries to delete a tool that is associated with agents? → Return 400 with list of dependent agents.
- What happens when an agent has no tools? → Allow execution but include warning in response that no tools are available.
- What happens when database is unavailable? → Return 503 Service Unavailable with structured error.
- What happens when Redis is unavailable? → Fail closed (deny requests) with 503 Service Unavailable for security.
- How does the system handle very long prompts? → Enforce max length of 10,000 characters via Pydantic validation.

---

## Requirements *(mandatory)*

### Functional Requirements

**Authentication & Authorization:**
- **FR-001**: System MUST authenticate all requests via X-API-KEY header
- **FR-002**: System MUST map API keys to tenant IDs using a predefined registry
- **FR-003**: System MUST reject requests with invalid/missing API keys with 401 Unauthorized
- **FR-004**: System MUST enforce tenant isolation - no cross-tenant data access

**Tool Management:**
- **FR-005**: System MUST support CRUD operations for Tools (name, description)
- **FR-006**: System MUST enforce unique tool names per tenant via database constraint
- **FR-007**: System MUST filter tools by agent name when requested

**Agent Management:**
- **FR-008**: System MUST support CRUD operations for Agents (name, role, description, tools)
- **FR-009**: System MUST enforce unique agent names per tenant via database constraint
- **FR-010**: System MUST filter agents by tool name when requested
- **FR-011**: System MUST prevent associating tools from other tenants

**Agent Execution:**
- **FR-012**: System MUST validate tenant quota before execution (throttling)
- **FR-013**: System MUST load agent metadata and authorized tools for execution
- **FR-014**: System MUST generate system prompt combining agent role, tools, and user task
- **FR-015**: System MUST invoke mock LLM adapter for deterministic responses
- **FR-016**: System MUST validate model identifier against allowed list
- **FR-017**: System MUST log all executions with prompt, model, timestamp, response

**History & Auditing:**
- **FR-018**: System MUST provide paginated execution history per tenant
- **FR-019**: System MUST support limit/offset pagination for history queries
- **FR-020**: System MUST order history by timestamp descending (newest first)

**Rate Limiting:**
- **FR-021**: System MUST implement rate limiting per tenant using Redis
- **FR-022**: System MUST use atomic Lua scripts for rate limit operations
- **FR-023**: System MUST return 429 with retry-after information when limit exceeded

### Key Entities

- **Tool**: Represents a capability that agents can use. Attributes: id, tenant_id, name, description, created_at, updated_at. Unique constraint on (tenant_id, name).

- **Agent**: Represents an AI entity with a specific role. Attributes: id, tenant_id, name, role, description, created_at, updated_at. Unique constraint on (tenant_id, name). Has many-to-many relationship with Tools.

- **AgentToolAssociation**: Join table linking Agents to Tools. Attributes: agent_id, tool_id. Both must belong to same tenant.

- **ExecutionLog**: Records each agent run. Attributes: id, tenant_id, agent_id, prompt, model, response, created_at. Indexed on (tenant_id, created_at) for efficient pagination.

- **Tenant**: Logical grouping for isolation. Identified by tenant_id derived from API key. Not stored as entity - derived from authentication.

---

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: All CRUD operations complete in < 100ms p95 latency
- **SC-002**: Agent execution completes in < 500ms p95 latency (mock LLM)
- **SC-003**: Rate limit checks complete in < 10ms p95 latency
- **SC-004**: Paginated history queries with 10,000+ records complete in < 200ms p95
- **SC-005**: 100% of cross-tenant access attempts are blocked (verified by isolation tests)
- **SC-006**: Rate limiter activates at exactly the configured quota (±0 tolerance)
- **SC-007**: All API errors return structured JSON with error_code, message, details
- **SC-008**: System handles 100 concurrent requests without errors or blocking

### Test Coverage Requirements

- **TC-001**: Unit tests for all service layer business logic
- **TC-002**: Integration tests for tenant isolation (Tenant A cannot access Tenant B)
- **TC-003**: Integration tests for rate limiting at exact quota boundaries
- **TC-004**: Contract tests for all API endpoints
- **TC-005**: Mock LLM adapter tests for deterministic output

---

## Constitution Compliance Checklist

| Principle | Compliance |
|-----------|------------|
| I. Code Quality & Architecture | ✅ Layered architecture (routes/services/repositories/models) specified |
| II. Multi-Tenancy & Security | ✅ Tenant isolation in all queries, unique constraints, 403 on violations |
| III. Test-First Development | ✅ Test coverage requirements defined, isolation tests mandatory |
| IV. User Experience Consistency | ✅ Structured error responses, RESTful conventions specified |
| V. Performance & Reliability | ✅ Async operations, Redis Lua scripts, SLA targets defined |

---

## Clarified Decisions

The following open questions have been resolved with recommended values:

| Decision | Value | Rationale |
|----------|-------|-----------|
| **Rate Limit** | 100 requests/minute per tenant | Reasonable default for API usage; prevents abuse while allowing normal operations |
| **Max Prompt Length** | 10,000 characters | Sufficient for most use cases; prevents memory exhaustion attacks |
| **Supported Models** | `gpt-4o`, `gpt-4`, `gpt-3.5-turbo`, `claude-3-opus`, `claude-3-sonnet` | Common model identifiers covering major providers |
| **Redis Failure Mode** | Fail closed (deny requests) | Security-first approach; prevents bypass of rate limiting during outages |
| **Tool Deletion with Dependencies** | Block with error listing dependent agents | Data integrity; prevents orphaned references and accidental data loss |

### Additional Configuration Constants

```python
# Rate Limiting
RATE_LIMIT_REQUESTS = 100
RATE_LIMIT_WINDOW_SECONDS = 60

# Input Validation
MAX_PROMPT_LENGTH = 10_000
MAX_NAME_LENGTH = 100
MAX_DESCRIPTION_LENGTH = 1_000
MAX_ROLE_LENGTH = 100

# Pagination Defaults
DEFAULT_PAGE_LIMIT = 20
MAX_PAGE_LIMIT = 100

# Supported Models
ALLOWED_MODELS = [
    "gpt-4o",
    "gpt-4",
    "gpt-3.5-turbo",
    "claude-3-opus",
    "claude-3-sonnet",
]
```
