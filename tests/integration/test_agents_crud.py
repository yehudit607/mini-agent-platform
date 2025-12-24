"""Integration tests for Agents CRUD operations and tool assignment."""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_create_agent_minimal(
    client: AsyncClient, tenant_a_headers: dict, seed_auth_data
):
    """Should create agent with minimal required fields."""
    payload = {
        "name": "Simple Agent",
        "role": "assistant",
        "description": "A basic agent",
    }

    response = await client.post(
        "/api/v1/agents", json=payload, headers=tenant_a_headers
    )

    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Simple Agent"
    assert data["role"] == "assistant"
    assert data["description"] == "A basic agent"
    assert data["tools"] == []
    assert "id" in data
    assert "created_at" in data


@pytest.mark.asyncio
async def test_create_agent_with_tools(
    client: AsyncClient, tenant_a_headers: dict, seed_auth_data
):
    """Should create agent with assigned tools."""
    # Create tools first
    tool1_response = await client.post(
        "/api/v1/tools",
        json={"name": "search", "description": "Web search"},
        headers=tenant_a_headers,
    )
    tool2_response = await client.post(
        "/api/v1/tools",
        json={"name": "calculator", "description": "Math operations"},
        headers=tenant_a_headers,
    )
    tool1_id = tool1_response.json()["id"]
    tool2_id = tool2_response.json()["id"]

    # Create agent with tools
    response = await client.post(
        "/api/v1/agents",
        json={
            "name": "Research Agent",
            "role": "researcher",
            "description": "Agent with tools",
            "tool_ids": [tool1_id, tool2_id],
        },
        headers=tenant_a_headers,
    )

    assert response.status_code == 201
    data = response.json()
    assert len(data["tools"]) == 2
    tool_names = [t["name"] for t in data["tools"]]
    assert "search" in tool_names
    assert "calculator" in tool_names


@pytest.mark.asyncio
async def test_create_agent_duplicate_name_fails(
    client: AsyncClient, tenant_a_headers: dict, seed_auth_data
):
    """Should reject duplicate agent name for same tenant."""
    payload = {
        "name": "Unique Agent",
        "role": "helper",
        "description": "First one",
    }

    # Create first agent
    response1 = await client.post(
        "/api/v1/agents", json=payload, headers=tenant_a_headers
    )
    assert response1.status_code == 201

    # Attempt duplicate
    response2 = await client.post(
        "/api/v1/agents", json=payload, headers=tenant_a_headers
    )

    assert response2.status_code == 400
    assert response2.json()["error_code"] == "DUPLICATE_RESOURCE"


@pytest.mark.asyncio
async def test_create_agent_with_invalid_tool_id_fails(
    client: AsyncClient, tenant_a_headers: dict, seed_auth_data
):
    """Should fail when assigning non-existent tool."""
    fake_tool_id = "00000000-0000-0000-0000-000000000000"

    response = await client.post(
        "/api/v1/agents",
        json={
            "name": "Bad Agent",
            "role": "tester",
            "description": "Has invalid tool",
            "tool_ids": [fake_tool_id],
        },
        headers=tenant_a_headers,
    )

    assert response.status_code == 404


@pytest.mark.asyncio
async def test_list_agents_empty(
    client: AsyncClient, tenant_a_headers: dict, seed_auth_data
):
    """Should return empty list when no agents exist."""
    response = await client.get("/api/v1/agents", headers=tenant_a_headers)

    assert response.status_code == 200
    data = response.json()
    assert data["items"] == []
    assert data["total"] == 0


@pytest.mark.asyncio
async def test_list_agents_returns_created_agents(
    client: AsyncClient, tenant_a_headers: dict, seed_auth_data
):
    """Should return all agents for tenant."""
    # Create agents
    await client.post(
        "/api/v1/agents",
        json={"name": "Agent One", "role": "worker", "description": "First"},
        headers=tenant_a_headers,
    )
    await client.post(
        "/api/v1/agents",
        json={"name": "Agent Two", "role": "manager", "description": "Second"},
        headers=tenant_a_headers,
    )

    response = await client.get("/api/v1/agents", headers=tenant_a_headers)

    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 2
    names = [a["name"] for a in data["items"]]
    assert "Agent One" in names
    assert "Agent Two" in names


@pytest.mark.asyncio
async def test_list_agents_filter_by_tool_name(
    client: AsyncClient, tenant_a_headers: dict, seed_auth_data
):
    """Should filter agents by tool name."""
    # Create tool
    tool_response = await client.post(
        "/api/v1/tools",
        json={"name": "special_tool", "description": "Special"},
        headers=tenant_a_headers,
    )
    tool_id = tool_response.json()["id"]

    # Create agent with tool
    await client.post(
        "/api/v1/agents",
        json={
            "name": "Agent With Tool",
            "role": "specialist",
            "description": "Has the tool",
            "tool_ids": [tool_id],
        },
        headers=tenant_a_headers,
    )

    # Create agent without tool
    await client.post(
        "/api/v1/agents",
        json={"name": "Agent Without Tool", "role": "basic", "description": "No tools"},
        headers=tenant_a_headers,
    )

    # Filter by tool name
    response = await client.get(
        "/api/v1/agents?tool_name=special_tool", headers=tenant_a_headers
    )

    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 1
    assert data["items"][0]["name"] == "Agent With Tool"


@pytest.mark.asyncio
async def test_get_agent_by_id(
    client: AsyncClient, tenant_a_headers: dict, seed_auth_data
):
    """Should return agent by ID with tools."""
    # Create tool
    tool_response = await client.post(
        "/api/v1/tools",
        json={"name": "get_tool", "description": "For get test"},
        headers=tenant_a_headers,
    )
    tool_id = tool_response.json()["id"]

    # Create agent
    create_response = await client.post(
        "/api/v1/agents",
        json={
            "name": "Get Agent",
            "role": "getter",
            "description": "Test get",
            "tool_ids": [tool_id],
        },
        headers=tenant_a_headers,
    )
    agent_id = create_response.json()["id"]

    # Get by ID
    response = await client.get(f"/api/v1/agents/{agent_id}", headers=tenant_a_headers)

    assert response.status_code == 200
    data = response.json()
    assert data["id"] == agent_id
    assert data["name"] == "Get Agent"
    assert len(data["tools"]) == 1
    assert data["tools"][0]["name"] == "get_tool"


@pytest.mark.asyncio
async def test_get_agent_not_found(
    client: AsyncClient, tenant_a_headers: dict, seed_auth_data
):
    """Should return 404 for non-existent agent."""
    fake_id = "00000000-0000-0000-0000-000000000000"

    response = await client.get(f"/api/v1/agents/{fake_id}", headers=tenant_a_headers)

    assert response.status_code == 404
    assert response.json()["error_code"] == "NOT_FOUND"


@pytest.mark.asyncio
async def test_update_agent_basic_fields(
    client: AsyncClient, tenant_a_headers: dict, seed_auth_data
):
    """Should update agent name, role, and description."""
    # Create agent
    create_response = await client.post(
        "/api/v1/agents",
        json={"name": "Old Name", "role": "old_role", "description": "Old desc"},
        headers=tenant_a_headers,
    )
    agent_id = create_response.json()["id"]

    # Update agent
    response = await client.put(
        f"/api/v1/agents/{agent_id}",
        json={"name": "New Name", "role": "new_role", "description": "New desc"},
        headers=tenant_a_headers,
    )

    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "New Name"
    assert data["role"] == "new_role"
    assert data["description"] == "New desc"


@pytest.mark.asyncio
async def test_update_agent_add_tools(
    client: AsyncClient, tenant_a_headers: dict, seed_auth_data
):
    """Should add tools to existing agent."""
    # Create tool
    tool_response = await client.post(
        "/api/v1/tools",
        json={"name": "new_tool", "description": "To be added"},
        headers=tenant_a_headers,
    )
    tool_id = tool_response.json()["id"]

    # Create agent without tools
    create_response = await client.post(
        "/api/v1/agents",
        json={"name": "Toolless Agent", "role": "basic", "description": "No tools yet"},
        headers=tenant_a_headers,
    )
    agent_id = create_response.json()["id"]
    assert create_response.json()["tools"] == []

    # Update to add tool
    response = await client.put(
        f"/api/v1/agents/{agent_id}",
        json={"tool_ids": [tool_id]},
        headers=tenant_a_headers,
    )

    assert response.status_code == 200
    data = response.json()
    assert len(data["tools"]) == 1
    assert data["tools"][0]["name"] == "new_tool"


@pytest.mark.asyncio
async def test_update_agent_replace_tools(
    client: AsyncClient, tenant_a_headers: dict, seed_auth_data
):
    """Should replace agent's tools completely."""
    # Create two tools
    tool1_response = await client.post(
        "/api/v1/tools",
        json={"name": "tool_1", "description": "First"},
        headers=tenant_a_headers,
    )
    tool2_response = await client.post(
        "/api/v1/tools",
        json={"name": "tool_2", "description": "Second"},
        headers=tenant_a_headers,
    )
    tool1_id = tool1_response.json()["id"]
    tool2_id = tool2_response.json()["id"]

    # Create agent with tool_1
    create_response = await client.post(
        "/api/v1/agents",
        json={
            "name": "Tool Agent",
            "role": "tester",
            "description": "Has tool 1",
            "tool_ids": [tool1_id],
        },
        headers=tenant_a_headers,
    )
    agent_id = create_response.json()["id"]

    # Update to use tool_2 instead
    response = await client.put(
        f"/api/v1/agents/{agent_id}",
        json={"tool_ids": [tool2_id]},
        headers=tenant_a_headers,
    )

    assert response.status_code == 200
    data = response.json()
    assert len(data["tools"]) == 1
    assert data["tools"][0]["name"] == "tool_2"


@pytest.mark.asyncio
async def test_update_agent_remove_all_tools(
    client: AsyncClient, tenant_a_headers: dict, seed_auth_data
):
    """Should remove all tools when empty array provided."""
    # Create tool
    tool_response = await client.post(
        "/api/v1/tools",
        json={"name": "removable_tool", "description": "Will be removed"},
        headers=tenant_a_headers,
    )
    tool_id = tool_response.json()["id"]

    # Create agent with tool
    create_response = await client.post(
        "/api/v1/agents",
        json={
            "name": "Losing Tools",
            "role": "loser",
            "description": "Will lose tools",
            "tool_ids": [tool_id],
        },
        headers=tenant_a_headers,
    )
    agent_id = create_response.json()["id"]

    # Update to remove tools
    response = await client.put(
        f"/api/v1/agents/{agent_id}",
        json={"tool_ids": []},
        headers=tenant_a_headers,
    )

    assert response.status_code == 200
    data = response.json()
    assert data["tools"] == []


@pytest.mark.asyncio
async def test_delete_agent(client: AsyncClient, tenant_a_headers: dict, seed_auth_data):
    """Should delete agent and return 204."""
    # Create agent
    create_response = await client.post(
        "/api/v1/agents",
        json={"name": "To Delete", "role": "temporary", "description": "Will be gone"},
        headers=tenant_a_headers,
    )
    agent_id = create_response.json()["id"]

    # Delete
    response = await client.delete(
        f"/api/v1/agents/{agent_id}", headers=tenant_a_headers
    )

    assert response.status_code == 204

    # Verify deleted
    get_response = await client.get(
        f"/api/v1/agents/{agent_id}", headers=tenant_a_headers
    )
    assert get_response.status_code == 404


@pytest.mark.asyncio
async def test_delete_agent_not_found(
    client: AsyncClient, tenant_a_headers: dict, seed_auth_data
):
    """Should return 404 when deleting non-existent agent."""
    fake_id = "00000000-0000-0000-0000-000000000000"

    response = await client.delete(f"/api/v1/agents/{fake_id}", headers=tenant_a_headers)

    assert response.status_code == 404
