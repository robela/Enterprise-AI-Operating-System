"""SQLAlchemy implementation of DocumentRepository."""
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.domains.documents.domain.entities.document import Document, DocumentStatus, DocumentType
from backend.domains.documents.domain.repositories.document_repository import DocumentRepository
from backend.infrastructure.persistence.models import DocumentModel


class SQLAlchemyDocumentRepository(DocumentRepository):
    def __init__(self, session: AsyncSession):
        self._session = session

    async def get_by_id(self, document_id: str, tenant_id: str) -> Document | None:
        result = await self._session.execute(
            select(DocumentModel).where(
                DocumentModel.document_id == document_id,
                DocumentModel.tenant_id == tenant_id,
            )
        )
        model = result.scalar_one_or_none()
        return self._to_domain(model) if model else None

    async def save(self, document: Document) -> None:
        result = await self._session.execute(
            select(DocumentModel).where(DocumentModel.document_id == document.document_id)
        )
        model = result.scalar_one_or_none()
        if model:
            model.status = document.status.value
            model.chunk_count = document.chunk_count
            model.updated_at = document.updated_at
        else:
            self._session.add(
                DocumentModel(
                    document_id=document.document_id,
                    tenant_id=document.tenant_id,
                    uploaded_by=document.uploaded_by,
                    filename=document.filename,
                    storage_path=document.storage_path,
                    content_type=document.content_type,
                    size_bytes=document.size_bytes,
                    doc_type=document.doc_type.value,
                    status=document.status.value,
                    chunk_count=document.chunk_count,
                    metadata_=document.metadata,
                    tags=",".join(document.tags),
                    created_at=document.created_at,
                    updated_at=document.updated_at,
                )
            )
        await self._session.flush()

    async def delete(self, document_id: str, tenant_id: str) -> None:
        result = await self._session.execute(
            select(DocumentModel).where(
                DocumentModel.document_id == document_id,
                DocumentModel.tenant_id == tenant_id,
            )
        )
        model = result.scalar_one_or_none()
        if model:
            await self._session.delete(model)
            await self._session.flush()

    async def list_by_tenant(self, tenant_id: str, skip: int = 0, limit: int = 50) -> list[Document]:
        result = await self._session.execute(
            select(DocumentModel)
            .where(DocumentModel.tenant_id == tenant_id)
            .offset(skip)
            .limit(limit)
        )
        return [self._to_domain(m) for m in result.scalars().all()]

    @staticmethod
    def _to_domain(model: DocumentModel) -> Document:
        return Document(
            document_id=model.document_id,
            tenant_id=model.tenant_id,
            uploaded_by=model.uploaded_by,
            filename=model.filename,
            storage_path=model.storage_path,
            content_type=model.content_type,
            size_bytes=model.size_bytes,
            doc_type=DocumentType(model.doc_type),
            status=DocumentStatus(model.status),
            chunk_count=model.chunk_count,
            metadata=model.metadata_ or {},
            tags=model.tags.split(",") if model.tags else [],
            created_at=model.created_at,
            updated_at=model.updated_at,
        )
