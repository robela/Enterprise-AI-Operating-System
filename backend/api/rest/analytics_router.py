"""Analytics REST endpoints."""
from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.core.database.session import get_db
from backend.core.security.oauth2 import CurrentUser, require_roles
from backend.infrastructure.persistence.models import (
    AuditLogModel,
    DocumentModel,
    UserModel,
    WorkflowModel,
)

router = APIRouter(prefix="/analytics", tags=["analytics"])


async def _count_for_tenant(
    db: AsyncSession,
    model: type[UserModel] | type[DocumentModel] | type[WorkflowModel] | type[AuditLogModel],
    tenant_id: str,
) -> int:
    result = await db.execute(
        select(func.count()).select_from(model).where(model.tenant_id == tenant_id)
    )
    return int(result.scalar_one())


@router.get("/metrics")
async def get_metrics(
    current_user: CurrentUser = Depends(require_roles("admin")),
    db: Annotated[AsyncSession, Depends(get_db)] = None,
):
    tenant_id = current_user.tenant_id

    users_count = await _count_for_tenant(db, UserModel, tenant_id)
    documents_count = await _count_for_tenant(db, DocumentModel, tenant_id)
    workflows_count = await _count_for_tenant(db, WorkflowModel, tenant_id)
    audit_logs_count = await _count_for_tenant(db, AuditLogModel, tenant_id)

    return [
        {"label": "Users", "value": users_count},
        {"label": "Documents", "value": documents_count},
        {"label": "Workflows", "value": workflows_count},
        {"label": "Audit Logs", "value": audit_logs_count},
    ]