"""Audit repository port."""
from abc import ABC, abstractmethod
from backend.domains.audit.domain.entities.audit_log import AuditLog


class AuditRepository(ABC):
    @abstractmethod
    async def append(self, log: AuditLog) -> None: ...

    @abstractmethod
    async def list_by_tenant(self, tenant_id: str, skip: int = 0, limit: int = 100) -> list[AuditLog]: ...
