<!--
Sync Impact Report:
- Version: Initial → 1.0.0
- Rationale: First constitution establishing foundational principles
- Modified principles: N/A (initial creation)
- Added sections: Core Principles (5), Architecture Standards, Performance Standards, Governance
- Removed sections: N/A
- Templates requiring updates: ✅ All templates aligned with initial constitution
- Follow-up TODOs: None
-->

# Agent Platform Constitution

## Core Principles

### I. Code Quality & Architecture (NON-NEGOTIABLE)

**Layered Architecture MUST be enforced:**
- Separate concerns into `routes`, `services`, `repositories`, and `models` layers
- Route handlers MUST NOT contain business logic - delegate to services
- Services MUST NOT directly access database - use repository pattern
- All code MUST follow SOLID principles with single-responsibility classes
- Type safety is mandatory: Python Type Hints required everywhere
- Pydantic models MUST be used for all request/response schemas
- Naming MUST be descriptive and intention-revealing (e.g., `get_agent_execution_history_by_tenant` not `get_history`)

**Rationale:** Clean architecture enables maintainability, testability, and allows multiple engineers to work in parallel without conflicts. Type safety catches errors at development time rather than production.

### II. Multi-Tenancy & Security (NON-NEGOTIABLE)

**Isolation by design:**
- Every repository method MUST accept and filter by `tenant_id`
- No query may execute without a `WHERE tenant_id = ...` clause
- Cross-tenant access attempts MUST return `403 Forbidden` immediately
- Input validation MUST be enforced via Pydantic constraints (min/max length, regex patterns)
- Database constraints MUST include `UniqueConstraint("tenant_id", "name")` for entities like Agent and Tool
- Composite indexes MUST be created on `(tenant_id, created_at)` for history queries

**Rationale:** Multi-tenant data isolation is a security requirement. A single cross-tenant data leak destroys trust and violates compliance requirements. Prevention must be systematic and enforced at the architecture level.

### III. Test-First Development (NON-NEGOTIABLE)

**Testing workflow:**
- Tests MUST be written before implementation (TDD)
- Tests MUST fail initially, then pass after implementation (Red-Green-Refactor)
- Unit tests MUST cover all service layer business logic
- Integration tests MUST validate multi-tenant isolation
- Integration tests MUST validate rate limiting behavior
- `pytest-mock` MUST be used to simulate external dependencies (LLM adapters, external APIs)

**Required test coverage areas:**
- Tenant isolation: Test that Tenant A cannot access Tenant B's data
- Rate limiting: Verify throttling activates at exact quota limits
- Input validation: Test boundary conditions and invalid inputs
- Error handling: Verify structured error responses with `error_code`, `message`, `details`

**Rationale:** Test-first development catches bugs early, documents intended behavior, and enables confident refactoring. Multi-tenancy bugs in production are unacceptable.

### IV. User Experience Consistency

**API response standards:**
- All errors MUST return structured JSON: `{"error_code": "...", "message": "...", "details": {}}`
- HTTP status codes MUST be semantically correct (200, 201, 400, 403, 404, 500)
- Error messages MUST be actionable and user-friendly
- API endpoints MUST follow RESTful conventions
- Response times MUST be predictable and within performance SLAs

**Rationale:** Consistent error handling and API design reduces integration friction, improves debugging, and creates predictable developer experience for API consumers.

### V. Performance & Reliability

**Asynchronous operations:**
- Database calls MUST use SQLAlchemy async engine with `async/await`
- Redis interactions MUST be async
- Rate limiting MUST be implemented with atomic Lua scripts in Redis
- Long-running operations MUST not block the event loop

**Database optimization:**
- Queries MUST use composite indexes on `(tenant_id, created_at)` for pagination
- N+1 query problems MUST be avoided via eager loading or batch queries
- Database migrations MUST be version controlled via Alembic

**Rationale:** Async operations ensure high concurrency under load. Atomic rate limiting prevents race conditions. Proper indexing ensures sub-100ms query times even with millions of records.

## Architecture Standards

**Technology Stack:**
- FastAPI for async HTTP API with automatic OpenAPI documentation
- SQLAlchemy (async) for database ORM with Alembic migrations
- Pydantic for schema validation and serialization
- Redis for rate limiting and caching (with Lua scripts for atomicity)
- pytest with pytest-mock for testing

**Dependency Injection:**
- Database sessions MUST be injected via FastAPI `Depends()`
- Configuration MUST be injected, never imported as globals
- Services MUST receive dependencies through constructors

## Performance Standards

**Response Time SLAs:**
- Simple CRUD operations: < 100ms p95
- Complex queries with joins: < 500ms p95
- Rate limit checks: < 10ms p95

**Scalability Requirements:**
- API MUST handle concurrent requests without blocking
- Database connection pooling MUST be configured appropriately
- Redis rate limiter MUST scale linearly with tenant count

## Governance

**Constitution Authority:**
- This constitution supersedes all informal practices and guidelines
- All code reviews MUST verify compliance with constitutional principles
- Deviations require documented justification and architect approval

**Amendment Process:**
- Amendments require documented rationale and impact analysis
- Version increments follow semantic versioning (MAJOR.MINOR.PATCH)
- Breaking changes require migration plans and backward compatibility strategy

**Compliance Review:**
- Pre-merge: Automated tests MUST pass including tenant isolation tests
- Code review: Reviewer MUST verify layered architecture and type safety
- Post-deployment: Monitor performance metrics against SLA targets

**Runtime Guidance:**
- See `CLAUDE.md` for detailed development guidance and command reference

**Version**: 1.0.0 | **Ratified**: 2025-12-24 | **Last Amended**: 2025-12-24
