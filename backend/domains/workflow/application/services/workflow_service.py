"""Workflow application service."""
from backend.core.exceptions.base import NotFoundException, BadRequestException
from backend.domains.workflow.domain.entities.workflow import Workflow, WorkflowTask, TaskStatus
from backend.domains.workflow.domain.repositories.workflow_repository import WorkflowRepository


class WorkflowService:
    def __init__(self, repository: WorkflowRepository):
        self._repo = repository

    async def start_workflow(
        self,
        tenant_id: str,
        definition_id: str,
        name: str,
        initiator_id: str,
        context: dict | None = None,
    ) -> Workflow:
        wf = Workflow.create(
            tenant_id=tenant_id,
            definition_id=definition_id,
            name=name,
            initiator_id=initiator_id,
            context=context,
        )
        await self._repo.save(wf)
        return wf

    async def get_workflow(self, workflow_id: str, tenant_id: str) -> Workflow:
        wf = await self._repo.get_by_id(workflow_id, tenant_id)
        if not wf:
            raise NotFoundException(f"Workflow {workflow_id!r} not found")
        return wf

    async def complete_task(
        self,
        workflow_id: str,
        task_id: str,
        tenant_id: str,
        output_data: dict | None = None,
    ) -> Workflow:
        wf = await self.get_workflow(workflow_id, tenant_id)
        task = next((t for t in wf.tasks if t.task_id == task_id), None)
        if not task:
            raise NotFoundException(f"Task {task_id!r} not found in workflow")
        task.complete(output_data=output_data)

        # Check if all tasks completed
        if all(t.status == TaskStatus.COMPLETED for t in wf.tasks):
            wf.complete()

        await self._repo.save(wf)
        return wf

    async def reject_task(
        self, workflow_id: str, task_id: str, tenant_id: str, comments: str = ""
    ) -> Workflow:
        wf = await self.get_workflow(workflow_id, tenant_id)
        task = next((t for t in wf.tasks if t.task_id == task_id), None)
        if not task:
            raise NotFoundException(f"Task {task_id!r} not found")
        task.reject(comments=comments)
        await self._repo.save(wf)
        return wf

    async def list_workflows(self, tenant_id: str, skip: int = 0, limit: int = 50) -> list[Workflow]:
        return await self._repo.list_by_tenant(tenant_id, skip=skip, limit=limit)
