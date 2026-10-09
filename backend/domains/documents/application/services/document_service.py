"""Document service — upload, index, search."""
from backend.core.exceptions.base import NotFoundException
from backend.domains.documents.domain.entities.document import (
    Document,
    DocumentLifecycleStatus,
    DocumentType,
)
from backend.domains.documents.domain.repositories.document_repository import DocumentRepository


class DocumentService:
    def __init__(self, repository: DocumentRepository):
        self._repo = repository

    async def upload(
        self,
        tenant_id: str,
        uploaded_by: str,
        filename: str,
        storage_path: str,
        content_type: str,
        size_bytes: int,
        doc_type: DocumentType = DocumentType.OTHER,
        lifecycle_status: DocumentLifecycleStatus = DocumentLifecycleStatus.ACTIVE,
    ) -> Document:
        doc = Document.create(
            tenant_id=tenant_id,
            uploaded_by=uploaded_by,
            filename=filename,
            storage_path=storage_path,
            content_type=content_type,
            size_bytes=size_bytes,
            doc_type=doc_type,
            lifecycle_status=lifecycle_status,
        )
        await self._repo.save(doc)
        return doc

    async def get(self, document_id: str, tenant_id: str) -> Document:
        doc = await self._repo.get_by_id(document_id, tenant_id)
        if not doc:
            raise NotFoundException(f"Document {document_id!r} not found")
        return doc

    async def list_documents(
        self, tenant_id: str, skip: int = 0, limit: int = 50
    ) -> list[Document]:
        return await self._repo.list_by_tenant(tenant_id, skip=skip, limit=limit)

    async def delete(self, document_id: str, tenant_id: str) -> None:
        await self._repo.delete(document_id, tenant_id)

    async def replace_file(
        self,
        document_id: str,
        tenant_id: str,
        filename: str,
        storage_path: str,
        content_type: str,
        size_bytes: int,
        doc_type: DocumentType | None = None,
        lifecycle_status: DocumentLifecycleStatus | None = None,
    ) -> Document:
        doc = await self.get(document_id, tenant_id)
        doc.replace_file(
            filename=filename,
            storage_path=storage_path,
            content_type=content_type,
            size_bytes=size_bytes,
            doc_type=doc_type,
            lifecycle_status=lifecycle_status,
        )
        await self._repo.save(doc)
        return doc

    async def update_metadata(
        self,
        document_id: str,
        tenant_id: str,
        doc_type: DocumentType | None = None,
        lifecycle_status: DocumentLifecycleStatus | None = None,
    ) -> Document:
        doc = await self.get(document_id, tenant_id)
        doc.update_metadata(doc_type=doc_type, lifecycle_status=lifecycle_status)
        await self._repo.save(doc)
        return doc

    async def mark_processing(self, document_id: str, tenant_id: str) -> Document:
        doc = await self.get(document_id, tenant_id)
        doc.mark_processing()
        await self._repo.save(doc)
        return doc

    async def mark_indexed(self, document_id: str, tenant_id: str, chunk_count: int) -> Document:
        doc = await self.get(document_id, tenant_id)
        doc.mark_indexed(chunk_count)
        await self._repo.save(doc)
        return doc

    async def mark_failed(self, document_id: str, tenant_id: str) -> Document:
        doc = await self.get(document_id, tenant_id)
        doc.mark_failed()
        await self._repo.save(doc)
        return doc
