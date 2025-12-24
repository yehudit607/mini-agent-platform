"""Integration tests for Tools CRUD operations."""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_create_tool(client: AsyncClient, tenant_a_headers: dict, seed_auth_data):
    """Should create a new tool and return 201."""
    payload = {
        "name": "web_search",
        "description": "Search the web for information",
    }

    response = await client.post(
        "/api/v1/tools", json=payload, headers=tenant_a_headers
    )

    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "web_search"
    assert data["description"] == "Search the web for information"
    assert "id" in data
    assert "created_at" in data


@pytest.mark.asyncio
async def test_create_tool_duplicate_name_fails(
    client: AsyncClient, tenant_a_headers: dict, seed_auth_data
):
    """Should reject duplicate tool name for same tenant."""
    payload = {"name": "calculator", "description": "Math operations"}

    # Create first tool
    response1 = await client.post(
        "/api/v1/tools", json=payload, headers=tenant_a_headers
    )
    assert response1.status_code == 201

    # Attempt duplicate
    response2 = await client.post(
        "/api/v1/tools", json=payload, headers=tenant_a_headers
    )

    assert response2.status_code == 400
    assert response2.json()["error_code"] == "DUPLICATE_TOOL_NAME"


@pytest.mark.asyncio
async def test_list_tools_empty(
    client: AsyncClient, tenant_a_headers: dict, seed_auth_data
):
    """Should return empty list when no tools exist."""
    response = await client.get("/api/v1/tools", headers=tenant_a_headers)

    assert response.status_code == 200
    data = response.json()
    assert data["items"] == []
    assert data["total"] == 0


@pytest.mark.asyncio
async def test_list_tools_returns_created_tools(
    client: AsyncClient, tenant_a_headers: dict, seed_auth_data
):
    """Should return all tools for tenant."""
    # Create two tools
    await client.post(
        "/api/v1/tools",
        json={"name": "tool_one", "description": "First tool"},
        headers=tenant_a_headers,
    )
    await client.post(
        "/api/v1/tools",
        json={"name": "tool_two", "description": "Second tool"},
        headers=tenant_a_headers,
    )

    response = await client.get("/api/v1/tools", headers=tenant_a_headers)

    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 2
    names = [t["name"] for t in data["items"]]
    assert "tool_one" in names
    assert "tool_two" in names


@pytest.mark.asyncio
async def test_get_tool_by_id(
    client: AsyncClient, tenant_a_headers: dict, seed_auth_data
):
    """Should return tool by ID."""
    # Create tool
    create_response = await client.post(
        "/api/v1/tools",
        json={"name": "fetch_tool", "description": "Fetches data"},
        headers=tenant_a_headers,
    )
    tool_id = create_response.json()["id"]

    # Get by ID
    response = await client.get(f"/api/v1/tools/{tool_id}", headers=tenant_a_headers)

    assert response.status_code == 200
    data = response.json()
    assert data["id"] == tool_id
    assert data["name"] == "fetch_tool"


@pytest.mark.asyncio
async def test_get_tool_not_found(
    client: AsyncClient, tenant_a_headers: dict, seed_auth_data
):
    """Should return 404 for non-existent tool."""
    fake_id = "00000000-0000-0000-0000-000000000000"

    response = await client.get(f"/api/v1/tools/{fake_id}", headers=tenant_a_headers)

    assert response.status_code == 404
    assert response.json()["error_code"] == "TOOL_NOT_FOUND"


@pytest.mark.asyncio
async def test_update_tool(client: AsyncClient, tenant_a_headers: dict, seed_auth_data):
    """Should update tool and return updated data."""
    # Create tool
    create_response = await client.post(
        "/api/v1/tools",
        json={"name": "old_name", "description": "Old description"},
        headers=tenant_a_headers,
    )
    tool_id = create_response.json()["id"]

    # Update tool
    response = await client.put(
        f"/api/v1/tools/{tool_id}",
        json={"name": "new_name", "description": "New description"},
        headers=tenant_a_headers,
    )

    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "new_name"
    assert data["description"] == "New description"


@pytest.mark.asyncio
async def test_update_tool_partial(
    client: AsyncClient, tenant_a_headers: dict, seed_auth_data
):
    """Should allow partial updates."""
    # Create tool
    create_response = await client.post(
        "/api/v1/tools",
        json={"name": "partial_tool", "description": "Original"},
        headers=tenant_a_headers,
    )
    tool_id = create_response.json()["id"]

    # Update only description
    response = await client.put(
        f"/api/v1/tools/{tool_id}",
        json={"description": "Updated description"},
        headers=tenant_a_headers,
    )

    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "partial_tool"  # Unchanged
    assert data["description"] == "Updated description"


@pytest.mark.asyncio
async def test_delete_tool(client: AsyncClient, tenant_a_headers: dict, seed_auth_data):
    """Should delete tool and return 204."""
    # Create tool
    create_response = await client.post(
        "/api/v1/tools",
        json={"name": "to_delete", "description": "Will be deleted"},
        headers=tenant_a_headers,
    )
    tool_id = create_response.json()["id"]

    # Delete tool
    response = await client.delete(
        f"/api/v1/tools/{tool_id}", headers=tenant_a_headers
    )

    assert response.status_code == 204

    # Verify deleted
    get_response = await client.get(
        f"/api/v1/tools/{tool_id}", headers=tenant_a_headers
    )
    assert get_response.status_code == 404


@pytest.mark.asyncio
async def test_delete_tool_not_found(
    client: AsyncClient, tenant_a_headers: dict, seed_auth_data
):
    """Should return 404 when deleting non-existent tool."""
    fake_id = "00000000-0000-0000-0000-000000000000"

    response = await client.delete(f"/api/v1/tools/{fake_id}", headers=tenant_a_headers)

    assert response.status_code == 404
