"""Documents REST endpoints."""
from typing import Annotated

from fastapi import APIRouter, Depends, UploadFile, File, Query
from sqlalchemy.ext.asyncio import AsyncSession

from backend.core.database.session import get_db
from backend.core.security.oauth2 import get_current_user, CurrentUser
from backend.domains.documents.application.services.document_service import DocumentService
from backend.domains.documents.infrastructure.persistence.document_repository_impl import (
    SQLAlchemyDocumentRepository,
)
from backend.infrastructure.storage.factory import get_storage

router = APIRouter(prefix="/documents", tags=["documents"])


def get_document_service(db: Annotated[AsyncSession, Depends(get_db)]) -> DocumentService:
    return DocumentService(SQLAlchemyDocumentRepository(db))


@router.post("", status_code=201)
async def upload_document(
    file: UploadFile = File(...),
    current_user: CurrentUser = Depends(get_current_user),
    service: DocumentService = Depends(get_document_service),
):
    storage = get_storage()
    content = await file.read()
    key = f"{current_user.tenant_id}/documents/{file.filename}"
    storage_path = await storage.upload(key, content, file.content_type or "application/octet-stream")

    doc = await service.upload(
        tenant_id=current_user.tenant_id,
        uploaded_by=current_user.user_id,
        filename=file.filename or "upload",
        storage_path=storage_path,
        content_type=file.content_type or "application/octet-stream",
        size_bytes=len(content),
    )
    return {"document_id": doc.document_id, "status": doc.status.value}


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
