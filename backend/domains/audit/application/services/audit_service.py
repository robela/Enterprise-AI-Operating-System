"""Audit service."""
from backend.domains.audit.domain.entities.audit_log import AuditLog
from backend.domains.audit.domain.repositories.audit_repository import AuditRepository


class AuditService:
    def __init__(self, repository: AuditRepository):
        self._repo = repository

    async def log(
        self,
        tenant_id: str,
        action: str,
        resource_type: str,
        result: str = "success",
        **kwargs,
    ) -> AuditLog:
        entry = AuditLog.create(
            tenant_id=tenant_id,
            action=action,
            resource_type=resource_type,
            result=result,
            **kwargs,
        )
        await self._repo.append(entry)
        return entry

    async def get_logs(
        self, tenant_id: str, skip: int = 0, limit: int = 100
    ) -> list[AuditLog]:
        return await self._repo.list_by_tenant(tenant_id, skip=skip, limit=limit)
