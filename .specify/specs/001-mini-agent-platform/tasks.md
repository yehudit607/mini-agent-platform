# Tasks: Mini Agent Platform (MAP)

**Input**: Design documents from `.specify/specs/001-mini-agent-platform/`
**Prerequisites**: plan.md ✅, spec.md ✅, research.md ✅, data-model.md ✅, contracts/ ✅

**Tests**: Tests are MANDATORY per constitution (Test-First Development). Write tests first, ensure they fail, then implement.

**Organization**: Tasks are grouped by phase and user story for independent implementation and testing.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[US#]**: User story association (US1-US5)
- Exact file paths included

---

## Phase 1: Setup (Infrastructure)

**Purpose**: Docker Compose with PostgreSQL, Redis, and API skeleton running

**Goal**: `docker-compose up` starts all services with health checks passing

- [ ] T001 Create `docker-compose.yml` with postgres, redis, api services
- [ ] T002 Create `Dockerfile` for Python 3.10+ FastAPI application
- [ ] T003 Create `requirements.txt` with dependencies:
  ```
  fastapi>=0.104.0
  uvicorn[standard]>=0.24.0
  sqlmodel>=0.0.14
  asyncpg>=0.29.0
  redis>=5.0.0
  alembic>=1.12.0
  pydantic>=2.5.0
  pydantic-settings>=2.1.0
  pytest>=7.4.0
  pytest-asyncio>=0.21.0
  pytest-mock>=3.12.0
  httpx>=0.25.0
  ```
- [ ] T004 [P] Create `app/__init__.py` (empty)
- [ ] T005 [P] Create `app/config.py` with Settings class (DATABASE_URL, REDIS_URL, etc.)
- [ ] T006 Create `app/main.py` with FastAPI app and `/health` endpoint
- [ ] T007 Initialize Alembic with `alembic init alembic`
- [ ] T008 Configure `alembic/env.py` for async SQLModel
- [ ] T009 Verify: `docker-compose up` runs all services successfully

**Checkpoint**: Infrastructure ready - all services healthy

---

## Phase 2: Foundational (Auth & Error Handling)

**Purpose**: Authentication middleware and structured error responses

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

### Tests for Phase 2

- [ ] T010 [P] Create `tests/__init__.py`
- [ ] T011 [P] Create `tests/conftest.py` with fixtures:
  - Test database setup/teardown
  - Async test client (httpx)
  - Tenant API keys (tenant-a-key, tenant-b-key)
- [ ] T012 [P] Create `tests/contract/test_auth.py`:
  - Test 401 for missing X-API-KEY
  - Test 401 for invalid X-API-KEY
  - Test 200 for valid X-API-KEY

### Implementation for Phase 2

- [ ] T013 Create `app/schemas/__init__.py`
- [ ] T014 Create `app/schemas/common.py` with:
  - `ErrorResponse(error_code, message, details)`
  - `PaginatedResponse(items, total, limit, offset, has_more)`
- [ ] T015 Create `app/middleware/__init__.py`
- [ ] T016 Create `app/middleware/error_handler.py` with global exception handler
- [ ] T017 Create `app/middleware/auth.py` with:
  - `TENANT_REGISTRY` mapping API keys to tenant UUIDs
  - X-API-KEY header validation
- [ ] T018 Create `app/dependencies.py` with `get_current_tenant()` dependency
- [ ] T019 Register middleware in `app/main.py`
- [ ] T020 Run tests: `pytest tests/contract/test_auth.py` - all pass

**Checkpoint**: Auth works, structured errors return, tenant context available

---

## Phase 3: User Story 1 - Tool Management (Priority: P1) 🎯 MVP

**Goal**: Complete CRUD for Tools with tenant isolation

**Independent Test**: Create tools via API, verify isolation between tenants

### Tests for User Story 1

> **Write tests FIRST, ensure they FAIL before implementation**

- [ ] T021 [P] [US1] Create `tests/contract/test_tools_api.py`:
  - POST /api/v1/tools → 201
  - GET /api/v1/tools → 200 with list
  - GET /api/v1/tools/{id} → 200
  - PUT /api/v1/tools/{id} → 200
  - DELETE /api/v1/tools/{id} → 204
  - POST duplicate name → 400
- [ ] T022 [P] [US1] Create `tests/integration/test_tenant_isolation.py`:
  - Tenant A creates tool
  - Tenant B GET tool → 403
  - Tenant B PUT tool → 403
  - Tenant B DELETE tool → 403
  - Tenant B list tools → empty (not Tenant A's)
- [ ] T023 [P] [US1] Create `tests/unit/test_tool_service.py`:
  - Test create_tool
  - Test get_tool_by_id
  - Test update_tool
  - Test delete_tool
  - Test list_tools

### Implementation for User Story 1

- [ ] T024 Create `app/models/__init__.py`
- [ ] T025 Create `app/models/base.py` with TenantMixin (tenant_id field)
- [ ] T026 [US1] Create `app/models/tool.py` with Tool entity:
  - id, tenant_id, name, description, created_at, updated_at
  - UniqueConstraint("tenant_id", "name")
- [ ] T027 [US1] Create `alembic/versions/001_create_tools_table.py` migration
- [ ] T028 [US1] Create `app/schemas/tool.py`:
  - ToolCreate, ToolUpdate, ToolResponse, ToolListResponse
- [ ] T029 Create `app/repositories/__init__.py`
- [ ] T030 Create `app/repositories/base.py` with BaseRepository pattern
- [ ] T031 [US1] Create `app/repositories/tool_repository.py`:
  - create(), get_by_id(), update(), delete(), list_all()
  - ALL methods filter by tenant_id
- [ ] T032 Create `app/services/__init__.py`
- [ ] T033 [US1] Create `app/services/tool_service.py`:
  - create_tool(), get_tool(), update_tool(), delete_tool(), list_tools()
  - Handle duplicate name error
  - Handle tool-in-use deletion error
- [ ] T034 Create `app/routes/__init__.py`
- [ ] T035 [US1] Create `app/routes/tools.py`:
  - POST /api/v1/tools
  - GET /api/v1/tools (with ?agent_name filter)
  - GET /api/v1/tools/{id}
  - PUT /api/v1/tools/{id}
  - DELETE /api/v1/tools/{id}
- [ ] T036 [US1] Register tool routes in `app/main.py`
- [ ] T037 [US1] Run all tests: `pytest tests/ -k tool` - all pass

**Checkpoint**: Tool CRUD works with tenant isolation verified

---

## Phase 4: User Story 5 - Rate Limiting (Priority: P1)

**Goal**: Redis-based sliding window rate limiter

**Independent Test**: Rapid requests trigger 429 at exactly quota boundary

### Tests for User Story 5

- [ ] T038 [P] [US5] Create `tests/unit/test_rate_limiter.py`:
  - Test allow under limit
  - Test deny at exact limit
  - Test remaining count accuracy
  - Test retry_after calculation
- [ ] T039 [P] [US5] Create `tests/integration/test_rate_limiting.py`:
  - Test 100 requests succeed
  - Test 101st request → 429
  - Test retry-after header present
  - Test window expiration allows new requests

### Implementation for User Story 5

- [ ] T040 [US5] Create `scripts/rate_limiter.lua` with sliding window algorithm
- [ ] T041 [US5] Create `app/services/rate_limiter.py`:
  - RateLimitResult(allowed, remaining, retry_after)
  - RateLimiter.check_and_consume(tenant_id)
  - ServiceUnavailableError on Redis failure (fail closed)
- [ ] T042 [US5] Run tests: `pytest tests/ -k rate_limit` - all pass

**Checkpoint**: Rate limiter works with ±0 tolerance at boundary

---

## Phase 5: User Story 2 - Agent Management (Priority: P2)

**Goal**: Agent CRUD with tool associations and cross-tenant validation

**Independent Test**: Create agents with tools, verify cross-tenant tool rejection

### Tests for User Story 2

- [ ] T043 [P] [US2] Create `tests/contract/test_agents_api.py`:
  - POST /api/v1/agents → 201
  - GET /api/v1/agents → 200
  - GET /api/v1/agents/{id} → 200 with tools
  - PUT /api/v1/agents/{id} → 200
  - DELETE /api/v1/agents/{id} → 204
  - POST duplicate name → 400
  - POST with cross-tenant tool_id → 403
- [ ] T044 [P] [US2] Add to `tests/integration/test_tenant_isolation.py`:
  - Agent isolation tests (same pattern as tools)
  - Cross-tenant tool association blocked
- [ ] T045 [P] [US2] Create `tests/unit/test_agent_service.py`:
  - Test create with tools
  - Test tool ownership validation
  - Test filter by tool_name

### Implementation for User Story 2

- [ ] T046 [US2] Create `app/models/agent.py`:
  - Agent entity (id, tenant_id, name, role, description, timestamps)
  - AgentToolAssociation (agent_id, tool_id)
  - UniqueConstraint("tenant_id", "name")
  - Relationship to tools
- [ ] T047 [US2] Create `alembic/versions/002_create_agents_table.py` migration
- [ ] T048 [US2] Create `app/schemas/agent.py`:
  - AgentCreate (with tool_ids), AgentUpdate, AgentResponse, AgentListResponse
- [ ] T049 [US2] Create `app/repositories/agent_repository.py`:
  - CRUD with tenant filtering
  - Eager loading for tools (selectinload)
  - Filter by tool_name
- [ ] T050 [US2] Create `app/services/agent_service.py`:
  - create_agent() with tool ownership validation
  - update_agent() with tool validation
  - delete_agent()
  - list_agents() with filter
- [ ] T051 [US2] Create `app/routes/agents.py`:
  - All CRUD endpoints
  - ?tool_name query parameter
- [ ] T052 [US2] Update `app/routes/tools.py` for ?agent_name filter
- [ ] T053 [US2] Register agent routes in `app/main.py`
- [ ] T054 [US2] Run tests: `pytest tests/ -k agent` - all pass

**Checkpoint**: Agent CRUD works with tool associations, cross-tenant blocked

---

## Phase 6: User Story 3 - Agent Execution (Priority: P3)

**Goal**: Run agent with mock LLM, rate-limited

**Independent Test**: Run agent, verify deterministic response and rate limiting

### Tests for User Story 3

- [ ] T055 [P] [US3] Create `tests/contract/test_execution_api.py`:
  - POST /api/v1/agents/{id}/run → 200
  - Invalid model → 400
  - Prompt too long → 400
  - Cross-tenant agent → 403
  - Rate exceeded → 429
- [ ] T056 [P] [US3] Create `tests/unit/test_mock_llm.py`:
  - Test deterministic output
  - Same input = same output
- [ ] T057 [P] [US3] Create `tests/integration/test_execution_flow.py`:
  - End-to-end execution with rate limit check
  - Execution logged to history

### Implementation for User Story 3

- [ ] T058 [US3] Create `app/adapters/__init__.py`
- [ ] T059 [US3] Create `app/adapters/mock_llm.py`:
  - MockLLMAdapter.generate(agent, prompt, model)
  - Deterministic response format
- [ ] T060 [US3] Create `app/schemas/execution.py`:
  - ExecutionRequest(prompt, model)
  - ExecutionResponse(execution_id, agent_id, response, etc.)
- [ ] T061 [US3] Create `app/models/execution_log.py`:
  - ExecutionLog entity
  - INDEX(tenant_id, created_at DESC)
- [ ] T062 [US3] Create `alembic/versions/003_create_execution_logs_table.py`
- [ ] T063 [US3] Create `app/repositories/execution_log_repository.py`:
  - create(), list_paginated() with tenant filter
- [ ] T064 [US3] Create `app/services/execution_service.py`:
  - execute_agent(): rate check → load agent → mock LLM → log → return
  - Model validation against ALLOWED_MODELS
- [ ] T065 [US3] Create `app/routes/execution.py`:
  - POST /api/v1/agents/{id}/run
  - Rate limit headers (X-RateLimit-*)
- [ ] T066 [US3] Register execution routes in `app/main.py`
- [ ] T067 [US3] Run tests: `pytest tests/ -k execution` - all pass

**Checkpoint**: Agent execution works with rate limiting and logging

---

## Phase 7: User Story 4 - Execution History (Priority: P4)

**Goal**: Paginated audit trail

**Independent Test**: Query history with pagination, verify tenant isolation

### Tests for User Story 4

- [ ] T068 [P] [US4] Create `tests/contract/test_history_api.py`:
  - GET /api/v1/history → 200
  - Pagination: limit, offset, has_more
  - Ordered by created_at DESC
- [ ] T069 [P] [US4] Add to `tests/integration/test_tenant_isolation.py`:
  - History isolation between tenants

### Implementation for User Story 4

- [ ] T070 [US4] Create `app/routes/history.py`:
  - GET /api/v1/history with limit/offset
- [ ] T071 [US4] Update `app/repositories/execution_log_repository.py`:
  - list_paginated(tenant_id, limit, offset)
  - count_total(tenant_id)
- [ ] T072 [US4] Register history routes in `app/main.py`
- [ ] T073 [US4] Run tests: `pytest tests/ -k history` - all pass

**Checkpoint**: History pagination works with tenant isolation

---

## Phase 8: Polish & Documentation

**Purpose**: Production-ready deliverable

- [ ] T074 [P] Create `README.md` with:
  - Quick start: `docker-compose up`
  - API authentication instructions
  - Tenant API keys (hardcoded for demo)
  - Rate limit documentation (100 req/min)
  - curl examples for all endpoints
- [ ] T075 [P] Verify OpenAPI docs at `/docs` (auto-generated)
- [ ] T076 Run full test suite: `pytest tests/ -v` - all pass
- [ ] T077 Run `docker-compose up` and validate all endpoints with curl
- [ ] T078 [P] Update `app/main.py` with proper metadata (title, description, version)

**Checkpoint**: README complete, all tests pass, system validated end-to-end

---

## Dependencies & Execution Order

### Phase Dependencies

```
Phase 1 (Setup) ──────────────────────────────────────────►
         │
         ▼
Phase 2 (Foundational) ───────────────────────────────────►
         │
         ├───────────────────┬───────────────────┐
         ▼                   ▼                   ▼
Phase 3 (US1: Tools)   Phase 4 (US5: Rate)   (can parallel)
         │                   │
         └─────────┬─────────┘
                   ▼
         Phase 5 (US2: Agents) ───────────────────────────►
                   │
                   ▼
         Phase 6 (US3: Execution) ────────────────────────►
                   │
                   ▼
         Phase 7 (US4: History) ──────────────────────────►
                   │
                   ▼
         Phase 8 (Polish) ────────────────────────────────►
```

### Parallel Opportunities

- **Phase 1**: T004, T005 can run in parallel
- **Phase 2**: T010, T011, T012 can run in parallel
- **Phase 3**: T021, T022, T023 (tests) can run in parallel
- **Phase 4**: T038, T039 (tests) can run in parallel
- **Phase 5**: T043, T044, T045 (tests) can run in parallel
- **Phase 6**: T055, T056, T057 (tests) can run in parallel
- **Phase 7**: T068, T069 (tests) can run in parallel
- **Phase 8**: T074, T075, T078 can run in parallel

### Critical Path

Setup → Foundational → Tools (US1) → Agents (US2) → Execution (US3) → History (US4) → Polish

---

## Task Summary

| Phase | Tasks | User Stories | Critical |
|-------|-------|--------------|----------|
| 1. Setup | T001-T009 | - | Yes |
| 2. Foundational | T010-T020 | US5 (partial) | Yes |
| 3. Tools | T021-T037 | US1 | MVP |
| 4. Rate Limiting | T038-T042 | US5 | MVP |
| 5. Agents | T043-T054 | US2 | - |
| 6. Execution | T055-T067 | US3 | - |
| 7. History | T068-T073 | US4 | - |
| 8. Polish | T074-T078 | - | - |

**Total Tasks**: 78
**Test Tasks**: ~20 (TDD required)
**MVP Tasks**: T001-T042 (Phases 1-4)

---

## MVP Delivery Strategy

1. Complete Phases 1-2 (Infrastructure + Auth)
2. Complete Phase 3 (Tool CRUD) → **Testable MVP slice**
3. Complete Phase 4 (Rate Limiting) → **Full P1 features**
4. Stop and demo Tool Management with rate limiting
5. Continue to Phases 5-8 for full feature set

---

## Notes

- All repository methods MUST filter by tenant_id
- Tests MUST fail before implementation (TDD)
- Commit after each task or logical group
- Run `pytest` after each phase to verify no regressions
- Docker must be used for all development and testing
