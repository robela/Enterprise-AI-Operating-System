from datetime import datetime, timezone

import pytest
from sqlalchemy import select

from backend.core.security.jwt import create_access_token
from backend.infrastructure.persistence.models import (
    OrganizationModel,
    SectorCatalogModel,
    TenantSectorModel,
    UserModel,
)


def _token(*, user_id: str, tenant_id: str, roles: list[str], scopes: list[str] | None = None) -> str:
    return create_access_token(
        user_id,
        extra_claims={
            "tenant_id": tenant_id,
            "roles": roles,
            "scopes": scopes or ["users:read"],
        },
    )


@pytest.mark.asyncio
async def test_admin_can_create_tenant_with_bootstrap_admin(client, db_session) -> None:
    token = _token(user_id="platform-admin", tenant_id="default", roles=["admin"], scopes=["admin"])

    response = await client.post(
        "/api/v1/tenants",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "tenant_id": "acme-health",
            "name": "Acme Health",
            "plan": "starter",
            "max_users": 25,
            "settings": {"region": "us-central1"},
            "bootstrap_admin": {
                "email": "admin@acme.health",
                "full_name": "Acme Admin",
                "password": "AcmeAdmin@123",
            },
        },
    )

    assert response.status_code == 201
    payload = response.json()
    assert payload["tenant_id"] == "acme-health"
    assert payload["name"] == "Acme Health"
    assert payload["plan"] == "starter"
    assert payload["bootstrap_admin_email"] == "admin@acme.health"
    assert payload["bootstrap_admin_user_id"]

    tenant_model = await db_session.scalar(
        select(OrganizationModel).where(OrganizationModel.slug == "acme-health")
    )
    assert tenant_model is not None
    assert tenant_model.max_users == 25

    admin_model = await db_session.scalar(
        select(UserModel).where(
            UserModel.tenant_id == "acme-health",
            UserModel.email == "admin@acme.health",
        )
    )
    assert admin_model is not None
    assert admin_model.status == "active"
    assert "admin" in (admin_model.roles or "")


@pytest.mark.asyncio
async def test_list_tenants_is_admin_only_and_honors_include_inactive(client, db_session) -> None:
    now = datetime.now(timezone.utc)
    db_session.add_all(
        [
            OrganizationModel(
                org_id="org-active",
                name="Active Org",
                slug="active-org",
                plan="free",
                max_users=10,
                is_active=True,
                created_at=now,
                settings={},
            ),
            OrganizationModel(
                org_id="org-inactive",
                name="Inactive Org",
                slug="inactive-org",
                plan="starter",
                max_users=10,
                is_active=False,
                created_at=now,
                settings={},
            ),
        ]
    )
    await db_session.commit()

    user_token = _token(user_id="normal-user", tenant_id="default", roles=["user"])
    forbidden = await client.get(
        "/api/v1/tenants",
        headers={"Authorization": f"Bearer {user_token}"},
    )
    assert forbidden.status_code == 403

    admin_token = _token(user_id="admin-user", tenant_id="default", roles=["admin"], scopes=["admin"])

    visible_default = await client.get(
        "/api/v1/tenants",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert visible_default.status_code == 200
    visible_slugs = {item["tenant_id"] for item in visible_default.json()}
    assert "active-org" in visible_slugs
    assert "inactive-org" not in visible_slugs

    visible_all = await client.get(
        "/api/v1/tenants?include_inactive=true",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert visible_all.status_code == 200
    all_slugs = {item["tenant_id"] for item in visible_all.json()}
    assert "active-org" in all_slugs
    assert "inactive-org" in all_slugs


@pytest.mark.asyncio
async def test_admin_can_update_and_get_tenant_prompts(client, db_session) -> None:
    now = datetime.now(timezone.utc)
    db_session.add(
        OrganizationModel(
            org_id="org-prompts",
            name="Prompt Org",
            slug="prompt-org",
            plan="starter",
            max_users=10,
            is_active=True,
            created_at=now,
            settings={},
        )
    )
    await db_session.commit()

    admin_token = _token(user_id="admin-user", tenant_id="default", roles=["admin"], scopes=["admin"])
    custom_prompt = (
        "You are the Prompt Org assistant for tenant {tenant_id}. "
        "Use only this context:\n{context}\n"
        "If unknown, say you do not know."
    )

    patch_response = await client.patch(
        "/api/v1/tenants/prompt-org/prompts",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={"rag_system_v1": custom_prompt},
    )
    assert patch_response.status_code == 200
    assert patch_response.json()["prompts"]["rag_system_v1"] == custom_prompt

    get_response = await client.get(
        "/api/v1/tenants/prompt-org/prompts",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert get_response.status_code == 200
    assert get_response.json() == {
        "tenant_id": "prompt-org",
        "prompts": {"rag_system_v1": custom_prompt},
    }


@pytest.mark.asyncio
async def test_admin_can_update_tenant_metadata(client, db_session) -> None:
    now = datetime.now(timezone.utc)
    db_session.add(
        OrganizationModel(
            org_id="org-edit",
            name="Edit Org",
            slug="edit-org",
            plan="starter",
            max_users=10,
            is_active=True,
            created_at=now,
            settings={},
        )
    )
    await db_session.commit()

    admin_token = _token(user_id="admin-user", tenant_id="default", roles=["admin"], scopes=["admin"])

    response = await client.patch(
        "/api/v1/tenants/edit-org",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={
            "name": "Edited Org",
            "plan": "enterprise",
            "max_users": 77,
            "is_active": False,
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["tenant_id"] == "edit-org"
    assert payload["name"] == "Edited Org"
    assert payload["plan"] == "enterprise"
    assert payload["max_users"] == 77
    assert payload["is_active"] is False

    tenant_model = await db_session.scalar(
        select(OrganizationModel).where(OrganizationModel.slug == "edit-org")
    )
    assert tenant_model is not None
    assert tenant_model.name == "Edited Org"
    assert tenant_model.plan == "enterprise"
    assert tenant_model.max_users == 77
    assert tenant_model.is_active is False


@pytest.mark.asyncio
async def test_non_admin_cannot_update_tenant_metadata(client, db_session) -> None:
    now = datetime.now(timezone.utc)
    db_session.add(
        OrganizationModel(
            org_id="org-edit-denied",
            name="Edit Denied Org",
            slug="edit-denied-org",
            plan="starter",
            max_users=10,
            is_active=True,
            created_at=now,
            settings={},
        )
    )
    await db_session.commit()

    tenant_admin_token = _token(
        user_id="tenant-admin",
        tenant_id="edit-denied-org",
        roles=["tenant_admin"],
        scopes=["users:read"],
    )

    response = await client.patch(
        "/api/v1/tenants/edit-denied-org",
        headers={"Authorization": f"Bearer {tenant_admin_token}"},
        json={"name": "Should Not Apply"},
    )

    assert response.status_code == 403


@pytest.mark.asyncio
async def test_admin_can_list_catalog_and_assign_single_tenant_sector(client, db_session) -> None:
    now = datetime.now(timezone.utc)
    db_session.add(
        OrganizationModel(
            org_id="org-sectors",
            name="Sector Org",
            slug="sector-org",
            plan="starter",
            max_users=10,
            is_active=True,
            created_at=now,
            settings={},
        )
    )
    db_session.add_all(
        [
            SectorCatalogModel(
                code="banking",
                name="Banking",
                is_active=True,
                sort_order=1,
                created_at=now,
            ),
            SectorCatalogModel(
                code="healthcare",
                name="Healthcare",
                is_active=True,
                sort_order=2,
                created_at=now,
            ),
        ]
    )
    await db_session.commit()

    admin_token = _token(user_id="admin-user", tenant_id="default", roles=["admin"], scopes=["admin"])

    catalog_response = await client.get(
        "/api/v1/tenants/sectors",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert catalog_response.status_code == 200
    assert [item["code"] for item in catalog_response.json()] == ["banking", "healthcare"]

    assign_response = await client.put(
        "/api/v1/tenants/sector-org/sectors",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={"sector_code": "banking"},
    )
    assert assign_response.status_code == 200
    assert assign_response.json()["tenant_id"] == "sector-org"
    assert assign_response.json()["sector"]["code"] == "banking"

    replace_response = await client.put(
        "/api/v1/tenants/sector-org/sectors",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={"sector_code": "healthcare"},
    )
    assert replace_response.status_code == 200
    assert replace_response.json()["sector"]["code"] == "healthcare"

    rows = (
        await db_session.execute(
            select(TenantSectorModel).where(TenantSectorModel.tenant_id == "sector-org")
        )
    ).scalars().all()
    assert len(rows) == 1
    assert rows[0].sector_code == "healthcare"


@pytest.mark.asyncio
async def test_tenant_admin_can_only_assign_own_tenant_sectors(client, db_session) -> None:
    now = datetime.now(timezone.utc)
    db_session.add_all(
        [
            OrganizationModel(
                org_id="org-a",
                name="Org A",
                slug="org-a",
                plan="starter",
                max_users=10,
                is_active=True,
                created_at=now,
                settings={},
            ),
            OrganizationModel(
                org_id="org-b",
                name="Org B",
                slug="org-b",
                plan="starter",
                max_users=10,
                is_active=True,
                created_at=now,
                settings={},
            ),
            SectorCatalogModel(
                code="legal",
                name="Legal",
                is_active=True,
                sort_order=1,
                created_at=now,
            ),
        ]
    )
    await db_session.commit()

    tenant_admin_token = _token(
        user_id="tenant-admin-a",
        tenant_id="org-a",
        roles=["tenant_admin"],
        scopes=["users:read"],
    )

    own_response = await client.put(
        "/api/v1/tenants/org-a/sectors",
        headers={"Authorization": f"Bearer {tenant_admin_token}"},
        json={"sector_code": "legal"},
    )
    assert own_response.status_code == 200

    other_response = await client.put(
        "/api/v1/tenants/org-b/sectors",
        headers={"Authorization": f"Bearer {tenant_admin_token}"},
        json={"sector_code": "legal"},
    )
    assert other_response.status_code == 403


@pytest.mark.asyncio
async def test_admin_can_clear_tenant_sector_assignment(client, db_session) -> None:
    now = datetime.now(timezone.utc)
    db_session.add_all(
        [
            OrganizationModel(
                org_id="org-clear",
                name="Org Clear",
                slug="org-clear",
                plan="starter",
                max_users=10,
                is_active=True,
                created_at=now,
                settings={},
            ),
            SectorCatalogModel(
                code="education",
                name="Education",
                is_active=True,
                sort_order=1,
                created_at=now,
            ),
        ]
    )
    await db_session.commit()

    admin_token = _token(user_id="admin-user", tenant_id="default", roles=["admin"], scopes=["admin"])

    set_response = await client.put(
        "/api/v1/tenants/org-clear/sector",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={"sector_code": "education"},
    )
    assert set_response.status_code == 200
    assert set_response.json()["sector"]["code"] == "education"

    clear_response = await client.put(
        "/api/v1/tenants/org-clear/sector",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={"sector_code": None},
    )
    assert clear_response.status_code == 200
    assert clear_response.json()["sector"] is None
