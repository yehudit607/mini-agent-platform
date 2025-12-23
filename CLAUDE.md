# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Build and Development Commands

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

