"""Workflows REST endpoints."""
from datetime import datetime, timezone
from typing import Annotated
from uuid import uuid4

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.core.database.session import get_db
from backend.core.exceptions.base import ForbiddenException, NotFoundException, ValidationException
from backend.core.security.oauth2 import get_current_user, require_roles, CurrentUser
from backend.domains.workflow.application.services.workflow_service import WorkflowService
from backend.domains.workflow.domain.entities.workflow import WorkflowTask
from backend.domains.workflow.infrastructure.persistence.workflow_repository_impl import (
    SQLAlchemyWorkflowRepository,
)
from backend.infrastructure.persistence.models import (
    OrganizationModel,
    SectorCatalogModel,
    TenantSectorModel,
    TenantWorkflowSelectionModel,
    WorkflowTemplateModel,
)

router = APIRouter(prefix="/workflows", tags=["workflows"])


def get_workflow_service(db: Annotated[AsyncSession, Depends(get_db)]) -> WorkflowService:
    return WorkflowService(SQLAlchemyWorkflowRepository(db))


class StartWorkflowRequest(BaseModel):
    template_id: str | None = None
    definition_id: str | None = None
    name: str | None = None
    context: dict = Field(default_factory=dict)


class TaskActionRequest(BaseModel):
    output_data: dict = Field(default_factory=dict)
    comments: str = ""


class WorkflowTemplateResponse(BaseModel):
    template_id: str
    name: str
    description: str | None = None
    definition_id: str
    sector_code: str | None = None
    owner_tenant_id: str | None = None
    version: int
    is_default_for_sector: bool
    is_active: bool
    config: dict
    created_at: datetime
    updated_at: datetime


class AssignTenantWorkflowTemplateRequest(BaseModel):
    template_id: str


class CreateWorkflowTemplateRequest(BaseModel):
    name: str
    definition_id: str
    description: str | None = None
    sector_code: str | None = None
    owner_tenant_id: str | None = None
    is_default_for_sector: bool = False
    config: dict = Field(default_factory=dict)


class CloneWorkflowTemplateRequest(BaseModel):
    tenant_id: str | None = None
    name: str | None = None
    assign_to_tenant: bool = True


class TenantWorkflowSelectionResponse(BaseModel):
    tenant_id: str
    template: WorkflowTemplateResponse | None = None


def _to_template_response(model: WorkflowTemplateModel) -> WorkflowTemplateResponse:
    return WorkflowTemplateResponse(
        template_id=model.template_id,
        name=model.name,
        description=model.description,
        definition_id=model.definition_id,
        sector_code=model.sector_code,
        owner_tenant_id=model.owner_tenant_id,
        version=model.version,
        is_default_for_sector=model.is_default_for_sector,
        is_active=model.is_active,
        config=model.config or {},
        created_at=model.created_at,
        updated_at=model.updated_at,
    )


def _assert_tenant_scope(current_user: CurrentUser, tenant_id: str) -> None:
    if current_user.has_role("admin"):
        return
    if current_user.tenant_id != tenant_id:
        raise ForbiddenException("You can only manage workflow selection for your own tenant")


def _normalize_sector_code(sector_code: str | None) -> str | None:
    if not sector_code:
        return None
    return sector_code.strip().lower().replace(" ", "-")


async def _get_tenant_or_404(db: AsyncSession, tenant_id: str) -> OrganizationModel:
    tenant = await db.scalar(select(OrganizationModel).where(OrganizationModel.slug == tenant_id))
    if tenant is None:
        raise NotFoundException(f"Tenant {tenant_id!r} not found")
    return tenant


async def _get_template_or_404(db: AsyncSession, template_id: str) -> WorkflowTemplateModel:
    template = await db.scalar(
        select(WorkflowTemplateModel).where(WorkflowTemplateModel.template_id == template_id)
    )
    if template is None:
        raise NotFoundException(f"Workflow template {template_id!r} not found")
    return template


async def _get_tenant_sector_code(db: AsyncSession, tenant_id: str) -> str | None:
    return await db.scalar(
        select(TenantSectorModel.sector_code).where(TenantSectorModel.tenant_id == tenant_id)
    )


async def _validate_sector_exists(db: AsyncSession, sector_code: str | None) -> None:
    if not sector_code:
        return
    known_sector = await db.scalar(
        select(SectorCatalogModel.code).where(SectorCatalogModel.code == sector_code)
    )
    if known_sector is None:
        raise ValidationException(f"Unknown sector: {sector_code}")


def _build_tasks_from_template_config(template: WorkflowTemplateModel, context: dict) -> list[WorkflowTask]:
    raw_tasks = (template.config or {}).get("tasks")
    if not isinstance(raw_tasks, list):
        return []

    tasks: list[WorkflowTask] = []
    for raw_task in raw_tasks:
        if not isinstance(raw_task, dict):
            continue

        name = str(raw_task.get("name", "")).strip()
        task_type = str(raw_task.get("task_type", "")).strip()
        if not name or not task_type:
            continue

        condition = raw_task.get("condition")
        if condition == "loan_amount_gt_50000":
            try:
                if float(context.get("loan_amount", 0)) <= 50000:
                    continue
            except (TypeError, ValueError):
                continue

        input_data: dict = {}
        input_keys = raw_task.get("input_keys")
        if isinstance(input_keys, list):
            for key in input_keys:
                if isinstance(key, str) and key in context:
                    input_data[key] = context[key]

        tasks.append(
            WorkflowTask(
                task_id=str(uuid4()),
                name=name,
                task_type=task_type,
                input_data=input_data,
            )
        )

    return tasks


async def _resolve_template_for_start(
    db: AsyncSession,
    tenant_id: str,
    requested_template_id: str | None,
) -> WorkflowTemplateModel | None:
    if requested_template_id:
        return await _get_template_or_404(db, requested_template_id)

    selection = await db.scalar(
        select(TenantWorkflowSelectionModel).where(TenantWorkflowSelectionModel.tenant_id == tenant_id)
    )
    if selection is not None:
        return await _get_template_or_404(db, selection.template_id)

    tenant_sector = await _get_tenant_sector_code(db, tenant_id)
    if not tenant_sector:
        return None

    return await db.scalar(
        select(WorkflowTemplateModel)
        .where(
            WorkflowTemplateModel.owner_tenant_id.is_(None),
            WorkflowTemplateModel.sector_code == tenant_sector,
            WorkflowTemplateModel.is_default_for_sector.is_(True),
            WorkflowTemplateModel.is_active.is_(True),
        )
        .order_by(WorkflowTemplateModel.version.desc())
        .limit(1)
    )


async def _upsert_tenant_workflow_selection(
    db: AsyncSession,
    tenant_id: str,
    template_id: str,
    assigned_by: str,
) -> TenantWorkflowSelectionModel:
    selection = await db.scalar(
        select(TenantWorkflowSelectionModel).where(TenantWorkflowSelectionModel.tenant_id == tenant_id)
    )
    now = datetime.now(timezone.utc)

    if selection is None:
        selection = TenantWorkflowSelectionModel(
            tenant_id=tenant_id,
            template_id=template_id,
            assigned_by=assigned_by,
            assigned_at=now,
        )
        db.add(selection)
    else:
        selection.template_id = template_id
        selection.assigned_by = assigned_by
        selection.assigned_at = now

    await db.flush()
    return selection


async def _get_tenant_selection_response(
    db: AsyncSession,
    tenant_id: str,
) -> TenantWorkflowSelectionResponse:
    selection = await db.scalar(
        select(TenantWorkflowSelectionModel).where(TenantWorkflowSelectionModel.tenant_id == tenant_id)
    )
    if selection is None:
        return TenantWorkflowSelectionResponse(tenant_id=tenant_id, template=None)

    template = await _get_template_or_404(db, selection.template_id)
    return TenantWorkflowSelectionResponse(
        tenant_id=tenant_id,
        template=_to_template_response(template),
    )


@router.post("", status_code=201)
async def start_workflow(
    body: StartWorkflowRequest,
    current_user: CurrentUser = Depends(get_current_user),
    service: WorkflowService = Depends(get_workflow_service),
    db: Annotated[AsyncSession, Depends(get_db)] = None,
):
    template = await _resolve_template_for_start(db, current_user.tenant_id, body.template_id)

    if template is not None:
        if not template.is_active:
            raise ValidationException("Cannot start workflow from an inactive template")
        if template.owner_tenant_id and template.owner_tenant_id != current_user.tenant_id:
            raise ForbiddenException("Cannot use a template owned by another tenant")

        tenant_sector = await _get_tenant_sector_code(db, current_user.tenant_id)
        if template.sector_code and tenant_sector and template.sector_code != tenant_sector:
            raise ValidationException(
                f"Template sector {template.sector_code!r} does not match tenant sector {tenant_sector!r}"
            )

    definition_id = template.definition_id if template else body.definition_id
    if not definition_id:
        raise ValidationException(
            "No workflow template resolved for tenant. Provide template_id or definition_id."
        )

    name = body.name or (template.name if template else f"Workflow {definition_id}")
    context = dict(body.context)
    initial_tasks: list[WorkflowTask] | None = None

    if template is not None:
        context.setdefault("_workflow_template", {})
        context["_workflow_template"] = {
            "template_id": template.template_id,
            "name": template.name,
            "sector_code": template.sector_code,
            "version": template.version,
        }
        generated_tasks = _build_tasks_from_template_config(template, context)
        if generated_tasks:
            initial_tasks = generated_tasks

    wf = await service.start_workflow(
        tenant_id=current_user.tenant_id,
        definition_id=definition_id,
        name=name,
        initiator_id=current_user.user_id,
        context=context,
        initial_tasks=initial_tasks,
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


@router.get("/templates", response_model=list[WorkflowTemplateResponse])
async def list_workflow_templates(
    current_user: CurrentUser = Depends(get_current_user),
    db: Annotated[AsyncSession, Depends(get_db)] = None,
    sector_code: str | None = Query(default=None),
    tenant_id: str | None = Query(default=None),
    include_inactive: bool = Query(default=False),
):
    target_tenant_id = tenant_id or current_user.tenant_id
    if tenant_id is not None and not current_user.has_role("admin") and tenant_id != current_user.tenant_id:
        raise ForbiddenException("Only admin can list templates for another tenant")

    normalized_sector = _normalize_sector_code(sector_code)
    await _validate_sector_exists(db, normalized_sector)

    query = select(WorkflowTemplateModel).where(
        (WorkflowTemplateModel.owner_tenant_id.is_(None))
        | (WorkflowTemplateModel.owner_tenant_id == target_tenant_id)
    )
    if normalized_sector:
        query = query.where(WorkflowTemplateModel.sector_code == normalized_sector)
    if not include_inactive:
        query = query.where(WorkflowTemplateModel.is_active.is_(True))

    query = query.order_by(
        WorkflowTemplateModel.is_default_for_sector.desc(),
        WorkflowTemplateModel.version.desc(),
        WorkflowTemplateModel.name.asc(),
    )
    templates = (await db.execute(query)).scalars().all()
    return [_to_template_response(item) for item in templates]


@router.post("/templates", response_model=WorkflowTemplateResponse, status_code=201)
async def create_workflow_template(
    body: CreateWorkflowTemplateRequest,
    current_user: CurrentUser = Depends(require_roles("admin", "tenant_admin")),
    db: Annotated[AsyncSession, Depends(get_db)] = None,
):
    name = body.name.strip()
    definition_id = body.definition_id.strip()
    if not name:
        raise ValidationException("Template name cannot be empty")
    if not definition_id:
        raise ValidationException("definition_id cannot be empty")

    normalized_sector = _normalize_sector_code(body.sector_code)
    await _validate_sector_exists(db, normalized_sector)

    owner_tenant_id = body.owner_tenant_id
    if current_user.has_role("tenant_admin"):
        owner_tenant_id = current_user.tenant_id
    elif owner_tenant_id:
        await _get_tenant_or_404(db, owner_tenant_id)

    if body.is_default_for_sector:
        if owner_tenant_id is not None:
            raise ValidationException("Only global templates can be marked as default for a sector")
        if not normalized_sector:
            raise ValidationException("sector_code is required for default sector templates")

        defaults = (await db.execute(
            select(WorkflowTemplateModel).where(
                WorkflowTemplateModel.owner_tenant_id.is_(None),
                WorkflowTemplateModel.sector_code == normalized_sector,
                WorkflowTemplateModel.is_default_for_sector.is_(True),
            )
        )).scalars().all()
        for default_template in defaults:
            default_template.is_default_for_sector = False
            default_template.updated_at = datetime.now(timezone.utc)

    now = datetime.now(timezone.utc)
    template = WorkflowTemplateModel(
        template_id=str(uuid4()),
        name=name,
        description=body.description.strip() if body.description else None,
        definition_id=definition_id,
        sector_code=normalized_sector,
        owner_tenant_id=owner_tenant_id,
        version=1,
        is_default_for_sector=body.is_default_for_sector,
        is_active=True,
        config=body.config,
        created_by=current_user.user_id,
        created_at=now,
        updated_at=now,
    )
    db.add(template)
    await db.flush()
    return _to_template_response(template)


@router.get("/tenants/{tenant_id}/template", response_model=TenantWorkflowSelectionResponse)
async def get_tenant_workflow_template(
    tenant_id: str,
    current_user: CurrentUser = Depends(get_current_user),
    db: Annotated[AsyncSession, Depends(get_db)] = None,
):
    _assert_tenant_scope(current_user, tenant_id)
    await _get_tenant_or_404(db, tenant_id)
    return await _get_tenant_selection_response(db, tenant_id)


@router.put("/tenants/{tenant_id}/template", response_model=TenantWorkflowSelectionResponse)
async def assign_tenant_workflow_template(
    tenant_id: str,
    body: AssignTenantWorkflowTemplateRequest,
    current_user: CurrentUser = Depends(require_roles("admin", "tenant_admin")),
    db: Annotated[AsyncSession, Depends(get_db)] = None,
):
    _assert_tenant_scope(current_user, tenant_id)
    await _get_tenant_or_404(db, tenant_id)
    template = await _get_template_or_404(db, body.template_id)

    if not template.is_active:
        raise ValidationException("Cannot assign an inactive workflow template")
    if template.owner_tenant_id and template.owner_tenant_id != tenant_id:
        raise ForbiddenException("Cannot assign a template owned by another tenant")

    tenant_sector = await _get_tenant_sector_code(db, tenant_id)
    if template.sector_code and tenant_sector and template.sector_code != tenant_sector:
        raise ValidationException(
            f"Template sector {template.sector_code!r} does not match tenant sector {tenant_sector!r}"
        )

    await _upsert_tenant_workflow_selection(
        db=db,
        tenant_id=tenant_id,
        template_id=template.template_id,
        assigned_by=current_user.user_id,
    )
    return await _get_tenant_selection_response(db, tenant_id)


@router.post("/templates/{template_id}/clone", response_model=WorkflowTemplateResponse, status_code=201)
async def clone_workflow_template(
    template_id: str,
    body: CloneWorkflowTemplateRequest,
    current_user: CurrentUser = Depends(require_roles("admin", "tenant_admin")),
    db: Annotated[AsyncSession, Depends(get_db)] = None,
):
    source = await _get_template_or_404(db, template_id)
    if not source.is_active:
        raise ValidationException("Cannot clone an inactive workflow template")

    target_tenant_id = body.tenant_id or current_user.tenant_id
    _assert_tenant_scope(current_user, target_tenant_id)
    await _get_tenant_or_404(db, target_tenant_id)

    tenant_sector = await _get_tenant_sector_code(db, target_tenant_id)
    if source.sector_code and tenant_sector and source.sector_code != tenant_sector:
        raise ValidationException(
            f"Template sector {source.sector_code!r} does not match tenant sector {tenant_sector!r}"
        )

    if source.owner_tenant_id and source.owner_tenant_id != target_tenant_id:
        raise ForbiddenException("Cannot clone a tenant-owned template from another tenant")

    now = datetime.now(timezone.utc)
    clone_name = body.name.strip() if body.name else f"{source.name} (Custom)"
    if not clone_name:
        raise ValidationException("Template name cannot be empty")

    new_template = WorkflowTemplateModel(
        template_id=str(uuid4()),
        name=clone_name,
        description=source.description,
        definition_id=source.definition_id,
        sector_code=source.sector_code,
        owner_tenant_id=target_tenant_id,
        version=source.version + 1,
        is_default_for_sector=False,
        is_active=True,
        config=dict(source.config or {}),
        created_by=current_user.user_id,
        created_at=now,
        updated_at=now,
    )
    db.add(new_template)
    await db.flush()

    if body.assign_to_tenant:
        await _upsert_tenant_workflow_selection(
            db=db,
            tenant_id=target_tenant_id,
            template_id=new_template.template_id,
            assigned_by=current_user.user_id,
        )

    return _to_template_response(new_template)


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
