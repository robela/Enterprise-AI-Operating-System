"""Audit log REST endpoints."""
from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from backend.core.database.session import get_db
from backend.core.security.oauth2 import get_current_user, CurrentUser, require_roles
from backend.domains.audit.application.services.audit_service import AuditService
from backend.domains.audit.infrastructure.persistence.audit_repository_impl import (
    SQLAlchemyAuditRepository,
)

router = APIRouter(prefix="/audit", tags=["audit"])


def get_audit_service(db: Annotated[AsyncSession, Depends(get_db)]) -> AuditService:
    return AuditService(SQLAlchemyAuditRepository(db))


@router.get("")
async def list_audit_logs(
    current_user: CurrentUser = Depends(require_roles("admin")),
    service: AuditService = Depends(get_audit_service),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
):
    logs = await service.get_logs(current_user.tenant_id, skip=skip, limit=limit)
    return {
        "items": [
            {
                "log_id": l.log_id,
                "action": l.action,
                "resource_type": l.resource_type,
                "user_id": l.user_id,
                "result": l.result,
                "occurred_at": l.occurred_at.isoformat(),
            }
            for l in logs
        ]
    }
