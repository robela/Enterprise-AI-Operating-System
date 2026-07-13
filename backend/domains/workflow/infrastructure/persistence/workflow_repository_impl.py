"""SQLAlchemy implementation of WorkflowRepository."""
import json
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.domains.workflow.domain.entities.workflow import (
    Workflow, WorkflowStatus, WorkflowTask, TaskStatus,
)
from backend.domains.workflow.domain.repositories.workflow_repository import WorkflowRepository
from backend.infrastructure.persistence.models import WorkflowModel, WorkflowTaskModel


class SQLAlchemyWorkflowRepository(WorkflowRepository):
    def __init__(self, session: AsyncSession):
        self._session = session

    async def get_by_id(self, workflow_id: str, tenant_id: str) -> Workflow | None:
        result = await self._session.execute(
            select(WorkflowModel).where(
                WorkflowModel.workflow_id == workflow_id,
                WorkflowModel.tenant_id == tenant_id,
            )
        )
        model = result.scalar_one_or_none()
        return self._to_domain(model) if model else None

    async def save(self, workflow: Workflow) -> None:
        result = await self._session.execute(
            select(WorkflowModel).where(WorkflowModel.workflow_id == workflow.workflow_id)
        )
        model = result.scalar_one_or_none()
        if model:
            model.status = workflow.status.value
            model.context = workflow.context
            model.updated_at = workflow.updated_at
            model.completed_at = workflow.completed_at
        else:
            model = WorkflowModel(
                workflow_id=workflow.workflow_id,
                tenant_id=workflow.tenant_id,
                definition_id=workflow.definition_id,
                name=workflow.name,
                initiator_id=workflow.initiator_id,
                status=workflow.status.value,
                context=workflow.context,
                created_at=workflow.created_at,
                updated_at=workflow.updated_at,
            )
            self._session.add(model)
        await self._session.flush()

    async def list_by_tenant(self, tenant_id: str, skip: int = 0, limit: int = 50) -> list[Workflow]:
        result = await self._session.execute(
            select(WorkflowModel)
            .where(WorkflowModel.tenant_id == tenant_id)
            .offset(skip)
            .limit(limit)
        )
        return [self._to_domain(m) for m in result.scalars().all()]

    @staticmethod
    def _to_domain(model: WorkflowModel) -> Workflow:
        tasks = [
            WorkflowTask(
                task_id=t.task_id,
                name=t.name,
                task_type=t.task_type,
                status=TaskStatus(t.status),
                assignee_id=t.assignee_id,
                input_data=t.input_data or {},
                output_data=t.output_data or {},
                started_at=t.started_at,
                completed_at=t.completed_at,
                comments=t.comments or "",
            )
            for t in (model.tasks or [])
        ]
        return Workflow(
            workflow_id=model.workflow_id,
            tenant_id=model.tenant_id,
            definition_id=model.definition_id,
            name=model.name,
            initiator_id=model.initiator_id,
            status=WorkflowStatus(model.status),
            tasks=tasks,
            context=model.context or {},
            created_at=model.created_at,
            updated_at=model.updated_at,
            completed_at=model.completed_at,
        )
