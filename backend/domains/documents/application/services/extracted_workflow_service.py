"""Persistence and evaluation of approved document-extracted workflows."""
from __future__ import annotations

from datetime import datetime, timezone
from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.ai.graph.workflow_extraction import WorkflowDraft
from backend.core.exceptions.base import NotFoundException
from backend.infrastructure.persistence.models import ExtractedWorkflowModel


class ExtractedWorkflowService:
    def __init__(self, db: AsyncSession):
        self._db = db

    async def replace_drafts(
        self, tenant_id: str, document_id: str, drafts: list[WorkflowDraft]
    ) -> list[ExtractedWorkflowModel]:
        existing = await self.list(tenant_id, document_id)
        for workflow in existing:
            if workflow.status == "draft":
                await self._db.delete(workflow)

        now = datetime.now(timezone.utc)
        records = [
            ExtractedWorkflowModel(
                workflow_id=str(uuid4()), tenant_id=tenant_id, document_id=document_id,
                name=draft.name, workflow_type=draft.workflow_type, steps=draft.steps,
                required_fields=draft.required_fields, source_pages=draft.source_pages,
                source_excerpt=draft.source_excerpt, confidence=draft.confidence,
                status="draft", created_at=now, updated_at=now,
            )
            for draft in drafts
        ]
        self._db.add_all(records)
        await self._db.flush()
        return records

    async def list(self, tenant_id: str, document_id: str) -> list[ExtractedWorkflowModel]:
        result = await self._db.execute(
            select(ExtractedWorkflowModel).where(
                ExtractedWorkflowModel.tenant_id == tenant_id,
                ExtractedWorkflowModel.document_id == document_id,
            ).order_by(ExtractedWorkflowModel.created_at)
        )
        return list(result.scalars().all())

    async def get(self, tenant_id: str, workflow_id: str) -> ExtractedWorkflowModel:
        workflow = await self._db.scalar(
            select(ExtractedWorkflowModel).where(
                ExtractedWorkflowModel.tenant_id == tenant_id,
                ExtractedWorkflowModel.workflow_id == workflow_id,
            )
        )
        if not workflow:
            raise NotFoundException(f"Extracted workflow {workflow_id!r} not found")
        return workflow

    async def update(
        self, tenant_id: str, workflow_id: str, *, name: str | None = None,
        steps: list[str] | None = None, required_fields: list[str] | None = None,
    ) -> ExtractedWorkflowModel:
        workflow = await self.get(tenant_id, workflow_id)
        if name is not None:
            workflow.name = name.strip()
        if steps is not None:
            workflow.steps = [step.strip() for step in steps if step.strip()]
        if required_fields is not None:
            workflow.required_fields = [field.strip() for field in required_fields if field.strip()]
        workflow.updated_at = datetime.now(timezone.utc)
        await self._db.flush()
        return workflow

    async def set_status(
        self, tenant_id: str, workflow_id: str, status: str, reviewer_id: str
    ) -> ExtractedWorkflowModel:
        workflow = await self.get(tenant_id, workflow_id)
        workflow.status = status
        workflow.reviewed_by = reviewer_id
        workflow.reviewed_at = datetime.now(timezone.utc)
        workflow.updated_at = workflow.reviewed_at
        await self._db.flush()
        return workflow