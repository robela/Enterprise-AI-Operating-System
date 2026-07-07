"""SQLAlchemy implementation of AuditRepository."""
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.domains.audit.domain.entities.audit_log import AuditLog
from backend.domains.audit.domain.repositories.audit_repository import AuditRepository
from backend.infrastructure.persistence.models import AuditLogModel


class SQLAlchemyAuditRepository(AuditRepository):
    def __init__(self, session: AsyncSession):
        self._session = session

    async def append(self, log: AuditLog) -> None:
        self._session.add(
            AuditLogModel(
                log_id=log.log_id,
                tenant_id=log.tenant_id,
                user_id=log.user_id,
                action=log.action,
                resource_type=log.resource_type,
                resource_id=log.resource_id,
                ip_address=log.ip_address,
                user_agent=log.user_agent,
                result=log.result,
                details=log.details,
                occurred_at=log.occurred_at,
            )
        )
        await self._session.flush()

    async def list_by_tenant(self, tenant_id: str, skip: int = 0, limit: int = 100) -> list[AuditLog]:
        result = await self._session.execute(
            select(AuditLogModel)
            .where(AuditLogModel.tenant_id == tenant_id)
            .order_by(AuditLogModel.occurred_at.desc())
            .offset(skip)
            .limit(limit)
        )
        return [
            AuditLog(
                log_id=m.log_id,
                tenant_id=m.tenant_id,
                user_id=m.user_id,
                action=m.action,
                resource_type=m.resource_type,
                resource_id=m.resource_id,
                ip_address=m.ip_address,
                user_agent=m.user_agent,
                result=m.result,
                details=m.details or {},
                occurred_at=m.occurred_at,
            )
            for m in result.scalars().all()
        ]
