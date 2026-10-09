"""Document entity and value objects."""
from __future__ import annotations
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum


class DocumentStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    INDEXED = "indexed"
    FAILED = "failed"


class DocumentType(str, Enum):
    PRIMARY = "primary"
    SECONDARY = "secondary"
    PDF = "pdf"
    WORD = "word"
    EXCEL = "excel"
    TEXT = "text"
    MARKDOWN = "markdown"
    HTML = "html"
    OTHER = "other"


class DocumentLifecycleStatus(str, Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"


@dataclass
class Document:
    document_id: str
    tenant_id: str
    uploaded_by: str
    filename: str
    storage_path: str
    content_type: str
    size_bytes: int
    doc_type: DocumentType = DocumentType.OTHER
    lifecycle_status: DocumentLifecycleStatus = DocumentLifecycleStatus.ACTIVE
    status: DocumentStatus = DocumentStatus.PENDING
    chunk_count: int = 0
    metadata: dict = field(default_factory=dict)
    tags: list[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    @classmethod
    def create(
        cls,
        tenant_id: str,
        uploaded_by: str,
        filename: str,
        storage_path: str,
        content_type: str,
        size_bytes: int,
        doc_type: DocumentType = DocumentType.OTHER,
        lifecycle_status: DocumentLifecycleStatus = DocumentLifecycleStatus.ACTIVE,
    ) -> Document:
        return cls(
            document_id=str(uuid.uuid4()),
            tenant_id=tenant_id,
            uploaded_by=uploaded_by,
            filename=filename,
            storage_path=storage_path,
            content_type=content_type,
            size_bytes=size_bytes,
            doc_type=doc_type,
            lifecycle_status=lifecycle_status,
        )

    def mark_processing(self) -> None:
        self.status = DocumentStatus.PROCESSING
        self.updated_at = datetime.now(timezone.utc)

    def mark_indexed(self, chunk_count: int) -> None:
        self.status = DocumentStatus.INDEXED
        self.chunk_count = chunk_count
        self.updated_at = datetime.now(timezone.utc)

    def mark_failed(self) -> None:
        self.status = DocumentStatus.FAILED
        self.updated_at = datetime.now(timezone.utc)

    def replace_file(
        self,
        *,
        filename: str,
        storage_path: str,
        content_type: str,
        size_bytes: int,
        doc_type: DocumentType | None = None,
        lifecycle_status: DocumentLifecycleStatus | None = None,
    ) -> None:
        self.filename = filename
        self.storage_path = storage_path
        self.content_type = content_type
        self.size_bytes = size_bytes
        if doc_type is not None:
            self.doc_type = doc_type
        if lifecycle_status is not None:
            self.lifecycle_status = lifecycle_status
        self.status = DocumentStatus.PENDING
        self.chunk_count = 0
        self.updated_at = datetime.now(timezone.utc)

    def update_metadata(
        self,
        *,
        doc_type: DocumentType | None = None,
        lifecycle_status: DocumentLifecycleStatus | None = None,
    ) -> None:
        if doc_type is not None:
            self.doc_type = doc_type
        if lifecycle_status is not None:
            self.lifecycle_status = lifecycle_status
        self.updated_at = datetime.now(timezone.utc)
