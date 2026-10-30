"""Global settings endpoint."""
import pytest

from backend.core.security.jwt import create_access_token


def _headers(roles: list[str]) -> dict[str, str]:
    token = create_access_token(
        "settings-user", extra_claims={"tenant_id": "tenant-settings", "roles": roles, "scopes": []}
    )
    return {"Authorization": f"Bearer {token}"}


@pytest.mark.asyncio
async def test_global_settings_lists_supported_languages(client) -> None:
    response = await client.get("/api/v1/settings/global", headers=_headers(["user"]))

    assert response.status_code == 200
    assert response.json()["languages"] == ["en", "am", "om"]
    assert response.json()["tracer_enabled"] is False


@pytest.mark.asyncio
async def test_admins_get_the_tracer(client) -> None:
    response = await client.get("/api/v1/settings/global", headers=_headers(["admin"]))

    assert response.status_code == 200
    assert response.json()["tracer_enabled"] is True
