"""Documents REST endpoints."""
from typing import Annotated
import structlog

from fastapi import APIRouter, Depends, UploadFile, File, Query
from sqlalchemy.ext.asyncio import AsyncSession

from backend.ai.rag.pipeline import RAGPipeline
from backend.core.database.session import get_db
from backend.core.security.oauth2 import get_current_user, CurrentUser
from backend.domains.documents.application.services.document_service import DocumentService
from backend.domains.documents.infrastructure.persistence.document_repository_impl import (
    SQLAlchemyDocumentRepository,
)
from backend.infrastructure.storage.factory import get_storage

router = APIRouter(prefix="/documents", tags=["documents"])
logger = structlog.get_logger(__name__)


def get_document_service(db: Annotated[AsyncSession, Depends(get_db)]) -> DocumentService:
    return DocumentService(SQLAlchemyDocumentRepository(db))


@router.post("", status_code=201)
async def upload_document(
    file: UploadFile = File(...),
    current_user: CurrentUser = Depends(get_current_user),
    service: DocumentService = Depends(get_document_service),
    db: Annotated[AsyncSession, Depends(get_db)] = None,
):
    storage = get_storage()
    content = await file.read()
    key = f"{current_user.tenant_id}/documents/{file.filename}"

    storage_path = await storage.upload(
        key,
        content,
        file.content_type or "application/octet-stream",
    )

    doc = await service.upload(
        tenant_id=current_user.tenant_id,
        uploaded_by=current_user.user_id,
        filename=file.filename or "upload",
        storage_path=storage_path,
        content_type=file.content_type or "application/octet-stream",
        size_bytes=len(content),
    )
    await db.commit()

    try:
        # Skip intermediate status write to reduce SQLite lock pressure.
        pipeline = RAGPipeline(tenant_id=current_user.tenant_id)
        chunk_count = await pipeline.ingest(
            document_id=doc.document_id,
            text=content.decode("utf-8", errors="ignore"),
            metadata={
                "tenant_id": current_user.tenant_id,
                "filename": file.filename or "upload",
                "content_type": file.content_type or "application/octet-stream",
            },
        )
        doc = await service.mark_indexed(doc.document_id, current_user.tenant_id, chunk_count)
        await db.commit()
    except Exception as exc:
        logger.warning(
            "document_indexing_failed",
            document_id=doc.document_id,
            tenant_id=current_user.tenant_id,
            error=str(exc),
        )
        try:
            doc = await service.mark_failed(doc.document_id, current_user.tenant_id)
            await db.commit()
        except Exception as mark_failed_exc:
            await db.rollback()
            logger.error(
                "document_mark_failed_persist_failed",
                document_id=doc.document_id,
                tenant_id=current_user.tenant_id,
                error=str(mark_failed_exc),
            )
            # Keep response consistent even if failed-status persistence races on local SQLite.
            doc.mark_failed()

    return {
        "document_id": doc.document_id,
        "status": doc.status.value,
        "chunk_count": doc.chunk_count,
    }


@router.get("")
async def list_documents(
    current_user: CurrentUser = Depends(get_current_user),
    service: DocumentService = Depends(get_document_service),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
):
    docs = await service.list_documents(current_user.tenant_id, skip=skip, limit=limit)
    return {"items": [{"document_id": d.document_id, "filename": d.filename, "status": d.status.value} for d in docs]}


@router.get("/{document_id}")
async def get_document(
    document_id: str,
    current_user: CurrentUser = Depends(get_current_user),
    service: DocumentService = Depends(get_document_service),
):
    doc = await service.get(document_id, current_user.tenant_id)
    return {"document_id": doc.document_id, "filename": doc.filename, "status": doc.status.value}


@router.delete("/{document_id}", status_code=204)
async def delete_document(
    document_id: str,
    current_user: CurrentUser = Depends(get_current_user),
    service: DocumentService = Depends(get_document_service),
):
    await service.delete(document_id, current_user.tenant_id)
