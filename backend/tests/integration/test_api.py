"""Integration tests for the REST API."""
import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_health_endpoint(client: AsyncClient):
    response = await client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


@pytest.mark.asyncio
async def test_create_user_unauthorized(client: AsyncClient):
    """Creating a user without a token should return 401."""
    response = await client.post(
        "/api/v1/users",
        json={"email": "test@example.com", "full_name": "Test User", "password": "password123"},
    )
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_openapi_schema(client: AsyncClient):
    response = await client.get("/openapi.json")
    assert response.status_code == 200
    schema = response.json()
    assert "paths" in schema
    assert "/api/v1/users" in schema["paths"]
