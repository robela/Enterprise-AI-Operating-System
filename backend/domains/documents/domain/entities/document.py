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
    PDF = "pdf"
    WORD = "word"
    EXCEL = "excel"
    TEXT = "text"
    MARKDOWN = "markdown"
    HTML = "html"
    OTHER = "other"


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
    ) -> Document:
        return cls(
            document_id=str(uuid.uuid4()),
            tenant_id=tenant_id,
            uploaded_by=uploaded_by,
            filename=filename,
            storage_path=storage_path,
            content_type=content_type,
            size_bytes=size_bytes,
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
