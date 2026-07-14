from datetime import datetime, timezone

import pytest

from backend.core.security.jwt import create_access_token
from backend.infrastructure.persistence.models import (
    AuditLogModel,
    DocumentModel,
    UserModel,
    WorkflowModel,
)


@pytest.mark.asyncio
async def test_metrics_returns_tenant_scoped_counts(client, db_session) -> None:
    tenant_id = "default"
    other_tenant_id = "other-tenant"
    now = datetime.now(timezone.utc)

    db_session.add_all(
        [
            UserModel(
                user_id="user-1",
                tenant_id=tenant_id,
                email="admin@enterprise.ai",
                full_name="Admin",
                hashed_password="hash",
                status="active",
                roles="admin",
                created_at=now,
                updated_at=now,
            ),
            UserModel(
                user_id="user-2",
                tenant_id=other_tenant_id,
                email="other@enterprise.ai",
                full_name="Other",
                hashed_password="hash",
                status="active",
                roles="user",
                created_at=now,
                updated_at=now,
            ),
            DocumentModel(
                document_id="doc-1",
                tenant_id=tenant_id,
                uploaded_by="user-1",
                filename="one.pdf",
                storage_path="gs://bucket/one.pdf",
                content_type="application/pdf",
                size_bytes=123,
                created_at=now,
                updated_at=now,
            ),
            WorkflowModel(
                workflow_id="wf-1",
                tenant_id=tenant_id,
                definition_id="definition-1",
                name="Workflow One",
                initiator_id="user-1",
                created_at=now,
                updated_at=now,
            ),
            AuditLogModel(
                log_id="log-1",
                tenant_id=tenant_id,
                user_id="user-1",
                action="login",
                resource_type="auth",
                occurred_at=now,
            ),
        ]
    )
    await db_session.commit()

    token = create_access_token(
        "user-1",
        extra_claims={
            "tenant_id": tenant_id,
            "roles": ["admin"],
            "scopes": ["admin"],
        },
    )

    response = await client.get(
        "/api/v1/analytics/metrics",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200
    assert response.json() == [
        {"label": "Users", "value": 1},
        {"label": "Documents", "value": 1},
        {"label": "Workflows", "value": 1},
        {"label": "Audit Logs", "value": 1},
    ]