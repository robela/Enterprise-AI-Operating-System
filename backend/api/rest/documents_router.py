"""Documents REST endpoints."""
from typing import Annotated
import structlog

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, Query, Response
from pydantic import BaseModel, Field
from sqlalchemy import text
from sqlalchemy.exc import OperationalError
from sqlalchemy.ext.asyncio import AsyncSession

from backend.ai.rag.pipeline import RAGPipeline
from backend.ai.rag.text_extraction import extract_pdf_pages, extract_text, get_pdf_page_count
from backend.ai.graph.completeness import extract_requirement_candidates
from backend.ai.graph.workflow_extraction import extract_workflow_drafts
from backend.core.database.session import get_db
from backend.core.exceptions.base import ServiceUnavailableException, ValidationException
from backend.core.security.oauth2 import get_current_user, CurrentUser
from backend.domains.documents.application.services.document_service import DocumentService
from backend.domains.documents.application.services.extracted_workflow_service import ExtractedWorkflowService
from backend.domains.documents.domain.entities.document import DocumentLifecycleStatus, DocumentType
from backend.domains.documents.infrastructure.persistence.document_repository_impl import (
    SQLAlchemyDocumentRepository,
)
from backend.infrastructure.storage.factory import get_storage

router = APIRouter(prefix="/documents", tags=["documents"])
logger = structlog.get_logger(__name__)


def get_document_service(db: Annotated[AsyncSession, Depends(get_db)]) -> DocumentService:
    return DocumentService(SQLAlchemyDocumentRepository(db))


class WorkflowUpdateRequest(BaseModel):
    name: str | None = Field(None, min_length=1, max_length=255)
    steps: list[str] | None = Field(None, max_length=50)
    required_fields: list[str] | None = Field(None, max_length=30)


class CompletenessCheckRequest(BaseModel):
    facts: dict[str, str | int | float | bool | None] = Field(default_factory=dict)


def _serialize_workflow(workflow) -> dict:
    return {
        "workflow_id": workflow.workflow_id,
        "document_id": workflow.document_id,
        "name": workflow.name,
        "workflow_type": workflow.workflow_type,
        "steps": workflow.steps or [],
        "required_fields": workflow.required_fields or [],
        "source_pages": workflow.source_pages or [],
        "source_excerpt": workflow.source_excerpt,
        "confidence": workflow.confidence,
        "status": workflow.status,
    }


def _require_tenant_admin(current_user: CurrentUser) -> None:
    if not ({"admin", "tenant_admin"} & set(current_user.roles or [])):
        raise HTTPException(status_code=403, detail="Tenant administrator access is required")


async def _create_workflow_drafts(
    db: AsyncSession, tenant_id: str, document_id: str, content: bytes, filename: str
) -> None:
    """Best-effort draft extraction; it must never fail document indexing."""
    if not filename.lower().endswith(".pdf"):
        return
    try:
        drafts = extract_workflow_drafts(extract_pdf_pages(content))
        await ExtractedWorkflowService(db).replace_drafts(tenant_id, document_id, drafts)
    except Exception as exc:
        logger.warning(
            "document_workflow_extraction_failed",
            tenant_id=tenant_id,
            document_id=document_id,
            error=str(exc),
        )


def _parse_document_type(value: str | None) -> DocumentType:
    if not value:
        return DocumentType.OTHER

    normalized = value.strip().lower()
    aliases = {
        "basic": "primary",
        "reference": "secondary",
    }
    normalized = aliases.get(normalized, normalized)

    try:
        return DocumentType(normalized)
    except ValueError as exc:
        valid_values = ", ".join(sorted(member.value for member in DocumentType))
        raise ValidationException(f"Invalid document_type {value!r}. Expected one of: {valid_values}") from exc


def _parse_lifecycle_status(value: str | None) -> DocumentLifecycleStatus:
    if not value:
        return DocumentLifecycleStatus.ACTIVE

    normalized = value.strip().lower()
    aliases = {
        "archived": "inactive",
    }
    normalized = aliases.get(normalized, normalized)

    try:
        return DocumentLifecycleStatus(normalized)
    except ValueError as exc:
        valid_values = ", ".join(sorted(member.value for member in DocumentLifecycleStatus))
        raise ValidationException(f"Invalid lifecycle_status {value!r}. Expected one of: {valid_values}") from exc


async def _upload_to_storage(storage, key: str, content: bytes, content_type: str) -> str:
    try:
        return await storage.upload(key, content, content_type)
    except Exception as exc:
        logger.exception("document_storage_upload_failed", key=key, error=str(exc))
        raise ServiceUnavailableException(
            "Document storage is temporarily unavailable. Please try again later."
        ) from exc


@router.post("", status_code=201)
async def upload_document(
    file: UploadFile = File(...),
    document_type: str | None = Form(None),
    lifecycle_status: str | None = Form(None),
    current_user: CurrentUser = Depends(get_current_user),
    service: DocumentService = Depends(get_document_service),
    db: Annotated[AsyncSession, Depends(get_db)] = None,
):
    parsed_document_type = _parse_document_type(document_type)
    parsed_lifecycle_status = _parse_lifecycle_status(lifecycle_status)

    storage = get_storage()
    content = await file.read()
    key = f"{current_user.tenant_id}/documents/{file.filename}"

    storage_path = await _upload_to_storage(
        storage,
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
        doc_type=parsed_document_type,
        lifecycle_status=parsed_lifecycle_status,
    )
    await db.commit()

    try:
        # Skip intermediate status write to reduce SQLite lock pressure.
        pipeline = RAGPipeline(tenant_id=current_user.tenant_id)
        chunk_count = await pipeline.ingest(
            document_id=doc.document_id,
            text=extract_text(content, doc.filename, doc.content_type),
            metadata={
                "tenant_id": current_user.tenant_id,
                "filename": file.filename or "upload",
                "content_type": file.content_type or "application/octet-stream",
                "document_type": doc.doc_type.value,
                "lifecycle_status": doc.lifecycle_status.value,
            },
        )
        doc = await service.mark_indexed(doc.document_id, current_user.tenant_id, chunk_count)
        await db.commit()
        await _create_workflow_drafts(
            db, current_user.tenant_id, doc.document_id, content, doc.filename
        )
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
        "doc_type": doc.doc_type.value,
        "lifecycle_status": doc.lifecycle_status.value,
    }


@router.put("/{document_id}")
async def replace_document(
    document_id: str,
    file: UploadFile = File(...),
    document_type: str | None = Form(None),
    lifecycle_status: str | None = Form(None),
    current_user: CurrentUser = Depends(get_current_user),
    service: DocumentService = Depends(get_document_service),
    db: Annotated[AsyncSession, Depends(get_db)] = None,
):
    parsed_document_type = _parse_document_type(document_type) if document_type is not None else None
    parsed_lifecycle_status = _parse_lifecycle_status(lifecycle_status) if lifecycle_status is not None else None

    storage = get_storage()
    content = await file.read()

    existing = await service.get(document_id, current_user.tenant_id)
    old_storage_path = existing.storage_path
    key = f"{current_user.tenant_id}/documents/{document_id}/{file.filename}"

    new_storage_path = await _upload_to_storage(
        storage,
        key,
        content,
        file.content_type or "application/octet-stream",
    )

    doc = await service.replace_file(
        document_id=document_id,
        tenant_id=current_user.tenant_id,
        filename=file.filename or existing.filename,
        storage_path=new_storage_path,
        content_type=file.content_type or "application/octet-stream",
        size_bytes=len(content),
        doc_type=parsed_document_type,
        lifecycle_status=parsed_lifecycle_status,
    )
    await db.commit()

    try:
        pipeline = RAGPipeline(tenant_id=current_user.tenant_id)
        await pipeline.delete_document(document_id=doc.document_id)
        chunk_count = await pipeline.ingest(
            document_id=doc.document_id,
            text=extract_text(content, doc.filename, doc.content_type),
            metadata={
                "tenant_id": current_user.tenant_id,
                "filename": file.filename or existing.filename,
                "content_type": file.content_type or "application/octet-stream",
                "document_type": doc.doc_type.value,
                "lifecycle_status": doc.lifecycle_status.value,
            },
        )
        doc = await service.mark_indexed(doc.document_id, current_user.tenant_id, chunk_count)
        await db.commit()
        await _create_workflow_drafts(
            db, current_user.tenant_id, doc.document_id, content, doc.filename
        )
        await db.commit()
    except Exception as exc:
        logger.warning(
            "document_reindexing_failed",
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
                "document_replace_mark_failed_persist_failed",
                document_id=doc.document_id,
                tenant_id=current_user.tenant_id,
                error=str(mark_failed_exc),
            )
            doc.mark_failed()

    if old_storage_path and old_storage_path != new_storage_path:
        try:
            await storage.delete(old_storage_path)
        except Exception as cleanup_exc:
            logger.warning(
                "document_old_file_cleanup_failed",
                document_id=doc.document_id,
                tenant_id=current_user.tenant_id,
                old_storage_path=old_storage_path,
                error=str(cleanup_exc),
            )

    return {
        "document_id": doc.document_id,
        "status": doc.status.value,
        "chunk_count": doc.chunk_count,
        "doc_type": doc.doc_type.value,
        "lifecycle_status": doc.lifecycle_status.value,
    }


@router.patch("/{document_id}/lifecycle")
async def update_document_lifecycle(
    document_id: str,
    lifecycle_status: str = Form(...),
    current_user: CurrentUser = Depends(get_current_user),
    service: DocumentService = Depends(get_document_service),
    db: Annotated[AsyncSession, Depends(get_db)] = None,
):
    parsed_lifecycle_status = _parse_lifecycle_status(lifecycle_status)
    doc = await service.update_metadata(
        document_id=document_id,
        tenant_id=current_user.tenant_id,
        lifecycle_status=parsed_lifecycle_status,
    )
    await db.commit()

    return {
        "document_id": doc.document_id,
        "status": doc.status.value,
        "chunk_count": doc.chunk_count,
        "doc_type": doc.doc_type.value,
        "lifecycle_status": doc.lifecycle_status.value,
    }


@router.get("")
async def list_documents(
    current_user: CurrentUser = Depends(get_current_user),
    service: DocumentService = Depends(get_document_service),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
):
    docs = await service.list_documents(current_user.tenant_id, skip=skip, limit=limit)
    return {
        "items": [
            {
                "document_id": d.document_id,
                "filename": d.filename,
                "status": d.status.value,
                "doc_type": d.doc_type.value,
                "lifecycle_status": d.lifecycle_status.value,
            }
            for d in docs
        ]
    }


@router.post("/{document_id}/extract-workflows")
async def extract_document_workflows(
    document_id: str,
    current_user: CurrentUser = Depends(get_current_user),
    service: DocumentService = Depends(get_document_service),
    db: Annotated[AsyncSession, Depends(get_db)] = None,
):
    """Create reviewable workflow drafts from explicit PDF instruction blocks."""
    _require_tenant_admin(current_user)
    doc = await service.get(document_id, current_user.tenant_id)
    if not doc.filename.lower().endswith(".pdf"):
        raise ValidationException("Workflow extraction is currently available for PDF documents only")

    content = await get_storage().download(doc.storage_path)
    drafts = extract_workflow_drafts(extract_pdf_pages(content))
    workflows = await ExtractedWorkflowService(db).replace_drafts(
        current_user.tenant_id, doc.document_id, drafts
    )
    return {"items": [_serialize_workflow(workflow) for workflow in workflows]}


@router.get("/{document_id}/extracted-workflows")
async def list_extracted_workflows(
    document_id: str,
    current_user: CurrentUser = Depends(get_current_user),
    service: DocumentService = Depends(get_document_service),
    db: Annotated[AsyncSession, Depends(get_db)] = None,
):
    doc = await service.get(document_id, current_user.tenant_id)
    workflows = await ExtractedWorkflowService(db).list(current_user.tenant_id, doc.document_id)
    return {"items": [_serialize_workflow(workflow) for workflow in workflows]}


@router.patch("/extracted-workflows/{workflow_id}")
async def update_extracted_workflow(
    workflow_id: str,
    body: WorkflowUpdateRequest,
    current_user: CurrentUser = Depends(get_current_user),
    db: Annotated[AsyncSession, Depends(get_db)] = None,
):
    _require_tenant_admin(current_user)
    workflow = await ExtractedWorkflowService(db).update(
        current_user.tenant_id,
        workflow_id,
        name=body.name,
        steps=body.steps,
        required_fields=body.required_fields,
    )
    return _serialize_workflow(workflow)


async def _review_extracted_workflow(
    workflow_id: str,
    status: str,
    current_user: CurrentUser = Depends(get_current_user),
    db: Annotated[AsyncSession, Depends(get_db)] = None,
):
    _require_tenant_admin(current_user)
    workflow = await ExtractedWorkflowService(db).set_status(
        current_user.tenant_id,
        workflow_id,
        "approved" if status == "approve" else "rejected",
        current_user.user_id,
    )
    return _serialize_workflow(workflow)


@router.post("/extracted-workflows/{workflow_id}/approve")
async def approve_extracted_workflow(
    workflow_id: str,
    current_user: CurrentUser = Depends(get_current_user),
    db: Annotated[AsyncSession, Depends(get_db)] = None,
):
    return await _review_extracted_workflow(workflow_id, "approve", current_user, db)


@router.post("/extracted-workflows/{workflow_id}/reject")
async def reject_extracted_workflow(
    workflow_id: str,
    current_user: CurrentUser = Depends(get_current_user),
    db: Annotated[AsyncSession, Depends(get_db)] = None,
):
    return await _review_extracted_workflow(workflow_id, "reject", current_user, db)


@router.post("/extracted-workflows/{workflow_id}/completeness-check")
async def check_workflow_completeness(
    workflow_id: str,
    body: CompletenessCheckRequest,
    current_user: CurrentUser = Depends(get_current_user),
    db: Annotated[AsyncSession, Depends(get_db)] = None,
):
    workflow = await ExtractedWorkflowService(db).get(current_user.tenant_id, workflow_id)
    if workflow.status != "approved":
        raise ValidationException("Only approved workflows can be used for completeness checks")

    present_fields = {
        key for key, value in body.facts.items()
        if value is not None and (not isinstance(value, str) or value.strip())
    }
    missing_fields = [field for field in (workflow.required_fields or []) if field not in present_fields]
    return {
        "workflow_id": workflow.workflow_id,
        "missing_fields": missing_fields,
        "complete": not missing_fields,
        "source_pages": workflow.source_pages or [],
    }


@router.get("/{document_id}")
async def get_document(
    document_id: str,
    current_user: CurrentUser = Depends(get_current_user),
    service: DocumentService = Depends(get_document_service),
):
    doc = await service.get(document_id, current_user.tenant_id)
    return {
        "document_id": doc.document_id,
        "filename": doc.filename,
        "status": doc.status.value,
        "doc_type": doc.doc_type.value,
        "lifecycle_status": doc.lifecycle_status.value,
    }


@router.get("/{document_id}/content")
async def get_document_content(
    document_id: str,
    current_user: CurrentUser = Depends(get_current_user),
    service: DocumentService = Depends(get_document_service),
):
    doc = await service.get(document_id, current_user.tenant_id)
    storage = get_storage()
    content = await storage.download(doc.storage_path)
    media_type = "application/pdf" if doc.filename.lower().endswith(".pdf") else doc.content_type
    return Response(
        content=content,
        media_type=media_type or "application/octet-stream",
        headers={"Content-Disposition": f'inline; filename="{doc.filename}"'},
    )


@router.get("/{document_id}/page-count")
async def get_document_page_count(
    document_id: str,
    current_user: CurrentUser = Depends(get_current_user),
    service: DocumentService = Depends(get_document_service),
):
    doc = await service.get(document_id, current_user.tenant_id)
    if not doc.filename.lower().endswith(".pdf"):
        return {"page_count": None}
    content = await get_storage().download(doc.storage_path)
    return {"page_count": get_pdf_page_count(content)}


@router.get("/{document_id}/chunks")
async def get_document_chunks(
    document_id: str,
    current_user: CurrentUser = Depends(get_current_user),
    service: DocumentService = Depends(get_document_service),
    db: Annotated[AsyncSession, Depends(get_db)] = None,
    limit: int = Query(25, ge=1, le=100),
):
    doc = await service.get(document_id, current_user.tenant_id)
    if doc.filename.lower().endswith(".pdf"):
        content = await get_storage().download(doc.storage_path)
        return {
            "items": [
                {"index": index, "text": page_text[:2000]}
                for index, page_text in enumerate(extract_pdf_pages(content)[:limit])
                if page_text.strip()
            ]
        }

    try:
        result = await db.execute(
            text(
                """
                SELECT chunk_index, chunk_text
                FROM document_chunks
                WHERE tenant_id = :tenant_id AND document_id = :document_id
                ORDER BY chunk_index
                LIMIT :limit
                """
            ),
            {
                "tenant_id": current_user.tenant_id,
                "document_id": document_id,
                "limit": limit,
            },
        )
    except OperationalError:
        return {"items": []}

    return {
        "items": [
            {"index": row.chunk_index, "text": row.chunk_text[:2000]}
            for row in result.fetchall()
        ]
    }


@router.get("/{document_id}/completeness-candidates")
async def get_completeness_candidates(
    document_id: str,
    current_user: CurrentUser = Depends(get_current_user),
    service: DocumentService = Depends(get_document_service),
    limit: int = Query(50, ge=1, le=100),
):
    """Return source-backed candidate assessment requirements for review.

    Results are not clinical rules: a guideline owner must approve and structure
    them before the application can use them to identify missing information.
    """
    doc = await service.get(document_id, current_user.tenant_id)
    if not doc.filename.lower().endswith(".pdf"):
        raise ValidationException("Completeness candidates are currently available for PDF documents only")

    content = await get_storage().download(doc.storage_path)
    candidates = extract_requirement_candidates(extract_pdf_pages(content), limit=limit)
    return {
        "document_id": doc.document_id,
        "items": [
            {"text": candidate.text, "page_number": candidate.page_number}
            for candidate in candidates
        ],
        "review_required": True,
    }


@router.delete("/{document_id}", status_code=204)
async def delete_document(
    document_id: str,
    current_user: CurrentUser = Depends(get_current_user),
    service: DocumentService = Depends(get_document_service),
):
    doc = await service.get(document_id, current_user.tenant_id)
    await service.delete(document_id, current_user.tenant_id)

    storage = get_storage()
    try:
        await storage.delete(doc.storage_path)
    except Exception as storage_exc:
        logger.warning(
            "document_delete_storage_cleanup_failed",
            document_id=document_id,
            tenant_id=current_user.tenant_id,
            error=str(storage_exc),
        )

    try:
        pipeline = RAGPipeline(tenant_id=current_user.tenant_id)
        await pipeline.delete_document(document_id=document_id)
    except Exception as vector_exc:
        logger.warning(
            "document_delete_vector_cleanup_failed",
            document_id=document_id,
            tenant_id=current_user.tenant_id,
            error=str(vector_exc),
        )
