# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Spec-Driven Development Workflow

This project uses **Specify** (GitHub Spec Kit) for spec-driven development. Follow this workflow for new features:

### Core Workflow Commands

1. `/speckit.constitution` - Establish/update project principles and governance rules
2. `/speckit.specify` - Create detailed feature specification (requires constitution first)
3. `/speckit.plan` - Generate implementation plan from specification
4. `/speckit.tasks` - Break plan into actionable tasks
5. `/speckit.implement` - Execute implementation following tasks

### Optional Enhancement Commands

- `/speckit.clarify` - Ask structured questions to de-risk ambiguous areas (run before planning)
- `/speckit.checklist` - Generate quality checklists for requirements validation (after planning)
- `/speckit.analyze` - Cross-artifact consistency & alignment report (before implementation)

### Project Structure

- `.specify/memory/constitution.md` - Project constitution defining core principles
- `.specify/templates/` - Templates for specs, plans, tasks, and checklists
- `.specify/scripts/` - Automation scripts for common workflows
- `.claude/commands/` - Custom slash commands for spec-driven workflow

### Recommended Feature Development Flow

1. Review constitution for project principles
2. Create specification using `/speckit.specify`
3. Generate implementation plan with `/speckit.plan`
4. Break into tasks with `/speckit.tasks`
5. Implement following tasks systematically

## Build and Development Commands

[To be added as Backend/FastAPI implementation progresses]

# Instructions for LLM: Senior Coding Standards

You are a Senior Backend Engineer building a high-security Agent Platform. Follow these rules strictly:

## 1. Clean Code & Architecture
* **Layered Architecture:** Separate code into `routes`, `services`, `repositories`, and `models`. Never put business logic in the route handlers.
* **SOLID Principles:** Ensure classes are small and focused. Use Dependency Injection (via FastAPI `Depends`) for database sessions and configuration.
* **Naming:** Use clear, descriptive names. (e.g., `get_agent_execution_history_by_tenant` instead of `get_history`).
* **Type Safety:** Use Python Type Hints everywhere. Pydantic models must be used for all request/response schemas.

## 2. Multi-Tenancy & Security
* **Isolation by Design:** Every repository method MUST accept a `tenant_id`. [cite_start]No query should ever run without a `WHERE tenant_id = ...` filter[cite: 14].
* **Fail Fast:** Throw a `403 Forbidden` if a tenant tries to access an ID belonging to another tenant (even if the record exists).
* **Input Validation:** Sanitize all inputs. Use Pydantic to enforce field constraints (e.g., min/max length for names).

## 3. Database & Persistence
* **Unique Constraints:** Add a `UniqueConstraint("tenant_id", "name")` to Agent and Tool tables to prevent duplicates within a tenant.
* [cite_start]**Indexing:** Create composite indexes on `(tenant_id, created_at)` for the history table to ensure fast paginated queries[cite: 34].
* [cite_start]**Migrations:** Every change must be reflected in an Alembic migration script[cite: 41].

## 4. Reliability & Performance
* **Redis Lua Limiter:** Implement the rate limiter using a Lua script to ensure atomicity. Do not use plain Python counters in Redis.
* **Async Everything:** Use `async/await` for database calls (SQLAlchemy async engine) and Redis interactions to ensure the API handles high concurrency.
* **Error Handling:** Use a global exception handler to return structured JSON errors: `{"error_code": "...", "message": "...", "details": {}}`.


## [cite_start]5. Testing Requirements [cite: 42]
* **Isolation Test:** Write a test that creates data for Tenant A and attempts to fetch it using Tenant B's API key. This MUST fail.
* **Rate Limit Test:** Simulate rapid requests to verify the Redis-based throttling kicks in exactly at the quota limit.
* **Mocking:** Use `pytest-mock` to simulate the LLM adapter without real overhead.

