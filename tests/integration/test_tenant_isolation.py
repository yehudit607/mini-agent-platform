"""Integration tests for tenant isolation.

These tests verify that tenants cannot access each other's resources.
Critical for multi-tenant security.
"""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_tenant_cannot_see_other_tenant_tools(
    client: AsyncClient,
    tenant_a_headers: dict,
    tenant_b_headers: dict,
    seed_auth_data,
):
    """Tenant A's tools should not appear in Tenant B's list."""
    # Tenant A creates a tool
    await client.post(
        "/api/v1/tools",
        json={"name": "tenant_a_tool", "description": "Belongs to A"},
        headers=tenant_a_headers,
    )

    # Tenant B lists tools
    response = await client.get("/api/v1/tools", headers=tenant_b_headers)

    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 0
    assert data["items"] == []


@pytest.mark.asyncio
async def test_tenant_cannot_get_other_tenant_tool_by_id(
    client: AsyncClient,
    tenant_a_headers: dict,
    tenant_b_headers: dict,
    seed_auth_data,
):
    """Tenant B should get 404 when accessing Tenant A's tool."""
    # Tenant A creates a tool
    create_response = await client.post(
        "/api/v1/tools",
        json={"name": "private_tool", "description": "Private to A"},
        headers=tenant_a_headers,
    )
    tool_id = create_response.json()["id"]

    # Tenant B tries to access it
    response = await client.get(f"/api/v1/tools/{tool_id}", headers=tenant_b_headers)

    assert response.status_code == 404
    assert response.json()["error_code"] == "NOT_FOUND"


@pytest.mark.asyncio
async def test_tenant_cannot_update_other_tenant_tool(
    client: AsyncClient,
    tenant_a_headers: dict,
    tenant_b_headers: dict,
    seed_auth_data,
):
    """Tenant B should not be able to update Tenant A's tool."""
    # Tenant A creates a tool
    create_response = await client.post(
        "/api/v1/tools",
        json={"name": "secure_tool", "description": "Original"},
        headers=tenant_a_headers,
    )
    tool_id = create_response.json()["id"]

    # Tenant B tries to update it
    response = await client.put(
        f"/api/v1/tools/{tool_id}",
        json={"description": "Hacked by B"},
        headers=tenant_b_headers,
    )

    assert response.status_code == 404

    # Verify original is unchanged
    get_response = await client.get(
        f"/api/v1/tools/{tool_id}", headers=tenant_a_headers
    )
    assert get_response.json()["description"] == "Original"


@pytest.mark.asyncio
async def test_tenant_cannot_delete_other_tenant_tool(
    client: AsyncClient,
    tenant_a_headers: dict,
    tenant_b_headers: dict,
    seed_auth_data,
):
    """Tenant B should not be able to delete Tenant A's tool."""
    # Tenant A creates a tool
    create_response = await client.post(
        "/api/v1/tools",
        json={"name": "protected_tool", "description": "Cannot delete"},
        headers=tenant_a_headers,
    )
    tool_id = create_response.json()["id"]

    # Tenant B tries to delete it
    response = await client.delete(
        f"/api/v1/tools/{tool_id}", headers=tenant_b_headers
    )

    assert response.status_code == 404

    # Verify still exists for Tenant A
    get_response = await client.get(
        f"/api/v1/tools/{tool_id}", headers=tenant_a_headers
    )
    assert get_response.status_code == 200


@pytest.mark.asyncio
async def test_tenant_cannot_see_other_tenant_agents(
    client: AsyncClient,
    tenant_a_headers: dict,
    tenant_b_headers: dict,
    seed_auth_data,
):
    """Tenant A's agents should not appear in Tenant B's list."""
    # Tenant A creates an agent
    await client.post(
        "/api/v1/agents",
        json={
            "name": "Agent A",
            "role": "assistant",
            "description": "Belongs to A",
        },
        headers=tenant_a_headers,
    )

    # Tenant B lists agents
    response = await client.get("/api/v1/agents", headers=tenant_b_headers)

    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 0


@pytest.mark.asyncio
async def test_tenant_cannot_run_other_tenant_agent(
    client: AsyncClient,
    tenant_a_headers: dict,
    tenant_b_headers: dict,
    seed_auth_data,
):
    """Tenant B should not be able to execute Tenant A's agent."""
    # Tenant A creates an agent
    create_response = await client.post(
        "/api/v1/agents",
        json={
            "name": "Secret Agent",
            "role": "spy",
            "description": "Top secret",
        },
        headers=tenant_a_headers,
    )
    agent_id = create_response.json()["id"]

    # Tenant B tries to run it
    response = await client.post(
        f"/api/v1/agents/{agent_id}/run",
        json={"prompt": "Steal secrets", "model": "gpt-4o-mini"},
        headers=tenant_b_headers,
    )

    assert response.status_code == 404


@pytest.mark.asyncio
async def test_tenant_cannot_assign_other_tenant_tool_to_agent(
    client: AsyncClient,
    tenant_a_headers: dict,
    tenant_b_headers: dict,
    seed_auth_data,
):
    """Tenant B should not be able to use Tenant A's tool in their agent."""
    # Tenant A creates a tool
    tool_response = await client.post(
        "/api/v1/tools",
        json={"name": "a_tool", "description": "A's tool"},
        headers=tenant_a_headers,
    )
    tool_id = tool_response.json()["id"]

    # Tenant B tries to create agent with A's tool
    response = await client.post(
        "/api/v1/agents",
        json={
            "name": "Sneaky Agent",
            "role": "thief",
            "description": "Tries to steal tools",
            "tool_ids": [tool_id],
        },
        headers=tenant_b_headers,
    )

    # Should fail - tool doesn't belong to B
    assert response.status_code in [400, 404]


@pytest.mark.asyncio
async def test_each_tenant_has_independent_tool_namespace(
    client: AsyncClient,
    tenant_a_headers: dict,
    tenant_b_headers: dict,
    seed_auth_data,
):
    """Both tenants can create tools with same name independently."""
    tool_data = {"name": "common_tool", "description": "Same name, different tenant"}

    # Both tenants create tool with same name
    response_a = await client.post(
        "/api/v1/tools", json=tool_data, headers=tenant_a_headers
    )
    response_b = await client.post(
        "/api/v1/tools", json=tool_data, headers=tenant_b_headers
    )

    assert response_a.status_code == 201
    assert response_b.status_code == 201

    # Different IDs
    assert response_a.json()["id"] != response_b.json()["id"]

    # Each tenant sees only their own
    list_a = await client.get("/api/v1/tools", headers=tenant_a_headers)
    list_b = await client.get("/api/v1/tools", headers=tenant_b_headers)

    assert list_a.json()["total"] == 1
    assert list_b.json()["total"] == 1
