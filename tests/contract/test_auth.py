"""Contract tests for API authentication."""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_missing_api_key_returns_401(client: AsyncClient):
    """Request without X-API-KEY header should return 401."""
    response = await client.get("/api/v1/tools")

    assert response.status_code == 401
    data = response.json()
    assert data["error_code"] == "MISSING_API_KEY"
    assert "X-API-KEY" in data["message"]


@pytest.mark.asyncio
async def test_invalid_api_key_returns_401(client: AsyncClient, invalid_headers: dict):
    """Request with invalid X-API-KEY should return 401."""
    response = await client.get("/api/v1/tools", headers=invalid_headers)

    assert response.status_code == 401
    data = response.json()
    assert data["error_code"] == "INVALID_API_KEY"


@pytest.mark.asyncio
async def test_valid_api_key_returns_200(
    client: AsyncClient, tenant_a_headers: dict, seed_auth_data
):
    """Request with valid X-API-KEY should succeed."""
    response = await client.get("/api/v1/tools", headers=tenant_a_headers)

    # Should be 200 (empty list, but authorized)
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_health_endpoint_no_auth_required(client: AsyncClient):
    """Health endpoint should not require authentication."""
    response = await client.get("/health")

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
