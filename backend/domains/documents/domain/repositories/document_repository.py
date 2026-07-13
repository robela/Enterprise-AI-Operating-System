"""Document repository port."""
from abc import ABC, abstractmethod
from backend.domains.documents.domain.entities.document import Document


class DocumentRepository(ABC):
    @abstractmethod
    async def get_by_id(self, document_id: str, tenant_id: str) -> Document | None: ...

    @abstractmethod
    async def save(self, document: Document) -> None: ...

    @abstractmethod
    async def delete(self, document_id: str, tenant_id: str) -> None: ...

    @abstractmethod
    async def list_by_tenant(self, tenant_id: str, skip: int = 0, limit: int = 50) -> list[Document]: ...
