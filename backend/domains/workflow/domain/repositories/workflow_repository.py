"""Workflow repository port."""
from abc import ABC, abstractmethod
from backend.domains.workflow.domain.entities.workflow import Workflow


class WorkflowRepository(ABC):
    @abstractmethod
    async def get_by_id(self, workflow_id: str, tenant_id: str) -> Workflow | None: ...

    @abstractmethod
    async def save(self, workflow: Workflow) -> None: ...

    @abstractmethod
    async def list_by_tenant(self, tenant_id: str, skip: int = 0, limit: int = 50) -> list[Workflow]: ...
