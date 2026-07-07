"""Workflows REST endpoints."""
from typing import Annotated

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from backend.core.database.session import get_db
from backend.core.security.oauth2 import get_current_user, CurrentUser
from backend.domains.workflow.application.services.workflow_service import WorkflowService
from backend.domains.workflow.infrastructure.persistence.workflow_repository_impl import (
    SQLAlchemyWorkflowRepository,
)

router = APIRouter(prefix="/workflows", tags=["workflows"])


def get_workflow_service(db: Annotated[AsyncSession, Depends(get_db)]) -> WorkflowService:
    return WorkflowService(SQLAlchemyWorkflowRepository(db))


class StartWorkflowRequest(BaseModel):
    definition_id: str
    name: str
    context: dict = {}


class TaskActionRequest(BaseModel):
    output_data: dict = {}
    comments: str = ""


@router.post("", status_code=201)
async def start_workflow(
    body: StartWorkflowRequest,
    current_user: CurrentUser = Depends(get_current_user),
    service: WorkflowService = Depends(get_workflow_service),
):
    wf = await service.start_workflow(
        tenant_id=current_user.tenant_id,
        definition_id=body.definition_id,
        name=body.name,
        initiator_id=current_user.user_id,
        context=body.context,
    )
    return {"workflow_id": wf.workflow_id, "status": wf.status.value}


@router.get("")
async def list_workflows(
    current_user: CurrentUser = Depends(get_current_user),
    service: WorkflowService = Depends(get_workflow_service),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
):
    workflows = await service.list_workflows(current_user.tenant_id, skip=skip, limit=limit)
    return {"items": [{"workflow_id": w.workflow_id, "name": w.name, "status": w.status.value} for w in workflows]}


@router.get("/{workflow_id}")
async def get_workflow(
    workflow_id: str,
    current_user: CurrentUser = Depends(get_current_user),
    service: WorkflowService = Depends(get_workflow_service),
):
    wf = await service.get_workflow(workflow_id, current_user.tenant_id)
    return {"workflow_id": wf.workflow_id, "name": wf.name, "status": wf.status.value, "tasks": [
        {"task_id": t.task_id, "name": t.name, "status": t.status.value} for t in wf.tasks
    ]}


@router.post("/{workflow_id}/tasks/{task_id}/complete")
async def complete_task(
    workflow_id: str,
    task_id: str,
    body: TaskActionRequest,
    current_user: CurrentUser = Depends(get_current_user),
    service: WorkflowService = Depends(get_workflow_service),
):
    wf = await service.complete_task(workflow_id, task_id, current_user.tenant_id, body.output_data)
    return {"workflow_id": wf.workflow_id, "status": wf.status.value}


@router.post("/{workflow_id}/tasks/{task_id}/reject")
async def reject_task(
    workflow_id: str,
    task_id: str,
    body: TaskActionRequest,
    current_user: CurrentUser = Depends(get_current_user),
    service: WorkflowService = Depends(get_workflow_service),
):
    wf = await service.reject_task(workflow_id, task_id, current_user.tenant_id, body.comments)
    return {"workflow_id": wf.workflow_id, "status": wf.status.value}
