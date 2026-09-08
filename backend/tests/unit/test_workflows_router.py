from datetime import datetime, timezone

import pytest
from sqlalchemy import select

from backend.core.security.jwt import create_access_token
from backend.infrastructure.persistence.models import (
    OrganizationModel,
    SectorCatalogModel,
    TenantSectorModel,
    WorkflowModel,
    WorkflowTemplateModel,
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
async def test_admin_can_create_and_assign_workflow_template(client, db_session) -> None:
    now = datetime.now(timezone.utc)
    db_session.add_all(
        [
            OrganizationModel(
                org_id="org-workflow-a",
                name="Workflow Org A",
                slug="workflow-org-a",
                plan="starter",
                max_users=10,
                is_active=True,
                created_at=now,
                settings={},
            ),
            SectorCatalogModel(
                code="banking-test-a",
                name="Banking",
                is_active=True,
                sort_order=1,
                created_at=now,
            ),
            TenantSectorModel(
                tenant_id="workflow-org-a",
                sector_code="banking-test-a",
                created_at=now,
            ),
        ]
    )
    await db_session.commit()

    admin_token = _token(user_id="platform-admin", tenant_id="default", roles=["admin"], scopes=["admin"])

    create_response = await client.post(
        "/api/v1/workflows/templates",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={
            "name": "Banking Intake",
            "description": "Default banking intake workflow",
            "definition_id": "loan_approval_v1",
            "sector_code": "banking-test-a",
            "is_default_for_sector": False,
            "config": {
                "tasks": [
                    {"name": "Collect Application", "task_type": "human_approval"},
                    {"name": "Run Scoring", "task_type": "ai_decision"},
                ]
            },
        },
    )

    assert create_response.status_code == 201
    template_id = create_response.json()["template_id"]

    assign_response = await client.put(
        "/api/v1/workflows/tenants/workflow-org-a/template",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={"template_id": template_id},
    )

    assert assign_response.status_code == 200
    payload = assign_response.json()
    assert payload["tenant_id"] == "workflow-org-a"
    assert payload["template"]["template_id"] == template_id


@pytest.mark.asyncio
async def test_assign_template_rejects_sector_mismatch(client, db_session) -> None:
    now = datetime.now(timezone.utc)
    db_session.add_all(
        [
            OrganizationModel(
                org_id="org-workflow-b",
                name="Workflow Org B",
                slug="workflow-org-b",
                plan="starter",
                max_users=10,
                is_active=True,
                created_at=now,
                settings={},
            ),
            SectorCatalogModel(
                code="banking-test-b",
                name="Banking",
                is_active=True,
                sort_order=1,
                created_at=now,
            ),
            SectorCatalogModel(
                code="healthcare-test-b",
                name="Healthcare",
                is_active=True,
                sort_order=2,
                created_at=now,
            ),
            TenantSectorModel(
                tenant_id="workflow-org-b",
                sector_code="banking-test-b",
                created_at=now,
            ),
            WorkflowTemplateModel(
                template_id="health-template-1",
                name="Health Referral",
                description="Healthcare template",
                definition_id="medical_referral_v1",
                sector_code="healthcare-test-b",
                owner_tenant_id=None,
                version=1,
                is_default_for_sector=True,
                is_active=True,
                config={},
                created_by=None,
                created_at=now,
                updated_at=now,
            ),
        ]
    )
    await db_session.commit()

    admin_token = _token(user_id="platform-admin", tenant_id="default", roles=["admin"], scopes=["admin"])

    assign_response = await client.put(
        "/api/v1/workflows/tenants/workflow-org-b/template",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={"template_id": "health-template-1"},
    )

    assert assign_response.status_code == 422
    assert "does not match tenant sector" in assign_response.json()["message"]


@pytest.mark.asyncio
async def test_start_workflow_uses_tenant_template_and_snapshots_tasks(client, db_session) -> None:
    now = datetime.now(timezone.utc)
    db_session.add_all(
        [
            OrganizationModel(
                org_id="org-workflow-c",
                name="Workflow Org C",
                slug="workflow-org-c",
                plan="starter",
                max_users=10,
                is_active=True,
                created_at=now,
                settings={},
            ),
            SectorCatalogModel(
                code="banking-test-c",
                name="Banking",
                is_active=True,
                sort_order=1,
                created_at=now,
            ),
            TenantSectorModel(
                tenant_id="workflow-org-c",
                sector_code="banking-test-c",
                created_at=now,
            ),
            WorkflowTemplateModel(
                template_id="bank-template-1",
                name="Banking Loan Template",
                description="Loan decisions",
                definition_id="loan_approval_v1",
                sector_code="banking-test-c",
                owner_tenant_id=None,
                version=1,
                is_default_for_sector=True,
                is_active=True,
                config={
                    "tasks": [
                        {
                            "name": "AI Risk Assessment",
                            "task_type": "ai_decision",
                            "input_keys": ["loan_amount", "applicant_name"],
                        },
                        {"name": "Manager Approval", "task_type": "human_approval"},
                        {
                            "name": "Compliance Review",
                            "task_type": "human_approval",
                            "condition": "loan_amount_gt_50000",
                        },
                        {"name": "Final Decision", "task_type": "automated"},
                    ]
                },
                created_by=None,
                created_at=now,
                updated_at=now,
            ),
        ]
    )
    await db_session.commit()

    tenant_token = _token(
        user_id="tenant-user-c",
        tenant_id="workflow-org-c",
        roles=["tenant_admin"],
        scopes=["users:read"],
    )

    start_response = await client.post(
        "/api/v1/workflows",
        headers={"Authorization": f"Bearer {tenant_token}"},
        json={
            "context": {
                "loan_amount": 65000,
                "applicant_name": "Casey Applicant",
            }
        },
    )

    assert start_response.status_code == 201
    workflow_id = start_response.json()["workflow_id"]

    get_response = await client.get(
        f"/api/v1/workflows/{workflow_id}",
        headers={"Authorization": f"Bearer {tenant_token}"},
    )

    assert get_response.status_code == 200
    details = get_response.json()
    assert len(details["tasks"]) == 4
    assert [task["name"] for task in details["tasks"]] == [
        "AI Risk Assessment",
        "Manager Approval",
        "Compliance Review",
        "Final Decision",
    ]

    workflow_model = await db_session.scalar(
        select(WorkflowModel).where(WorkflowModel.workflow_id == workflow_id)
    )
    assert workflow_model is not None
    assert workflow_model.definition_id == "loan_approval_v1"
    assert workflow_model.context.get("_workflow_template", {}).get("template_id") == "bank-template-1"
