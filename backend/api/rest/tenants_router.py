"""Tenant onboarding and registry endpoints (admin-only)."""
from datetime import datetime, timezone
import re
from typing import Annotated
from uuid import uuid4

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel, EmailStr, Field, field_validator, model_validator
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm.attributes import flag_modified

from backend.core.database.session import get_db
from backend.core.exceptions.base import (
    ConflictException,
    ForbiddenException,
    TenantNotFoundException,
    ValidationException,
)
from backend.core.security.jwt import hash_password
from backend.core.security.oauth2 import CurrentUser, get_current_user, require_roles
from backend.domains.organizations.domain.entities.organization import PlanType
from backend.domains.users.domain.entities.user import User
from backend.domains.users.infrastructure.persistence.user_repository_impl import (
    SQLAlchemyUserRepository,
)
from backend.infrastructure.persistence.models import (
    OrganizationModel,
    SectorCatalogModel,
    TenantSectorModel,
)

router = APIRouter(prefix="/tenants", tags=["tenants"])

_TENANT_ID_PATTERN = re.compile(r"^[a-z0-9][a-z0-9-]{1,62}[a-z0-9]$")
_SECTOR_CODE_PATTERN = re.compile(r"^[a-z0-9][a-z0-9-]{1,62}[a-z0-9]$")


class BootstrapAdminRequest(BaseModel):
    email: EmailStr
    full_name: str = Field(min_length=1, max_length=255)
    password: str = Field(min_length=8, max_length=128)


class TenantCreateRequest(BaseModel):
    tenant_id: str = Field(min_length=3, max_length=64)
    name: str = Field(min_length=2, max_length=255)
    plan: PlanType = PlanType.FREE
    max_users: int = Field(default=10, ge=1, le=100000)
    settings: dict = Field(default_factory=dict)
    bootstrap_admin: BootstrapAdminRequest | None = None

    @field_validator("tenant_id")
    @classmethod
    def normalize_tenant_id(cls, value: str) -> str:
        normalized = value.strip().lower()
        if not _TENANT_ID_PATTERN.fullmatch(normalized):
            raise ValueError(
                "tenant_id must use lowercase letters, numbers, and hyphens (3-64 chars)"
            )
        return normalized


class TenantResponse(BaseModel):
    tenant_id: str
    name: str
    plan: str
    max_users: int
    is_active: bool
    created_at: datetime
    settings: dict


class TenantCreateResponse(TenantResponse):
    bootstrap_admin_user_id: str | None = None
    bootstrap_admin_email: str | None = None


class TenantPromptsUpdateRequest(BaseModel):
    rag_system_v1: str = Field(min_length=20)


class TenantPromptsResponse(BaseModel):
    tenant_id: str
    prompts: dict


class TenantUpdateRequest(BaseModel):
    name: str | None = Field(default=None, min_length=2, max_length=255)
    plan: PlanType | None = None
    max_users: int | None = Field(default=None, ge=1, le=100000)
    is_active: bool | None = None

    @model_validator(mode="after")
    def validate_update_fields(self) -> "TenantUpdateRequest":
        if (
            self.name is None
            and self.plan is None
            and self.max_users is None
            and self.is_active is None
        ):
            raise ValueError(
                "At least one field must be provided (name, plan, max_users, is_active)"
            )
        return self


class SectorLookupResponse(BaseModel):
    code: str
    name: str


class TenantSectorResponse(BaseModel):
    tenant_id: str
    sector: SectorLookupResponse | None


class TenantSectorUpdateRequest(BaseModel):
    sector_code: str | None = None

    @field_validator("sector_code")
    @classmethod
    def normalize_sector_code(cls, value: str | None) -> str | None:
        if value is None:
            return None

        code = value.strip().lower().replace(" ", "-")
        if not _SECTOR_CODE_PATTERN.fullmatch(code):
            raise ValueError(
                "sector code must use lowercase letters, numbers, and hyphens (3-64 chars)"
            )
        return code


def _to_tenant_response(model: OrganizationModel) -> TenantResponse:
    return TenantResponse(
        tenant_id=model.slug,
        name=model.name,
        plan=model.plan,
        max_users=model.max_users,
        is_active=model.is_active,
        created_at=model.created_at,
        settings=model.settings or {},
    )


async def _get_tenant_or_404(db: AsyncSession, tenant_id: str) -> OrganizationModel:
    tenant = await db.scalar(
        select(OrganizationModel).where(OrganizationModel.slug == tenant_id)
    )
    if not tenant:
        raise TenantNotFoundException(f"Tenant {tenant_id!r} does not exist")
    return tenant


def _assert_tenant_scope(current_user: CurrentUser, tenant_id: str) -> None:
    if current_user.has_role("admin"):
        return
    if current_user.tenant_id != tenant_id:
        raise ForbiddenException("You can only access sectors for your own tenant")


async def _build_tenant_sectors_response(
    db: AsyncSession,
    tenant_id: str,
) -> TenantSectorResponse:
    result = await db.execute(
        select(SectorCatalogModel)
        .join(TenantSectorModel, TenantSectorModel.sector_code == SectorCatalogModel.code)
        .where(TenantSectorModel.tenant_id == tenant_id)
        .order_by(SectorCatalogModel.sort_order.asc(), SectorCatalogModel.name.asc())
    )
    sector = result.scalars().first()

    return TenantSectorResponse(
        tenant_id=tenant_id,
        sector=(
            SectorLookupResponse(code=sector.code, name=sector.name)
            if sector is not None
            else None
        ),
    )


@router.post("", response_model=TenantCreateResponse, status_code=201)
async def create_tenant(
    body: TenantCreateRequest,
    current_user: CurrentUser = Depends(require_roles("admin")),
    db: Annotated[AsyncSession, Depends(get_db)] = None,
):
    existing = await db.scalar(
        select(OrganizationModel).where(OrganizationModel.slug == body.tenant_id)
    )
    if existing:
        raise ConflictException(f"Tenant {body.tenant_id!r} already exists")

    now = datetime.now(timezone.utc)
    tenant = OrganizationModel(
        org_id=str(uuid4()),
        name=body.name.strip(),
        slug=body.tenant_id,
        plan=body.plan.value,
        max_users=body.max_users,
        is_active=True,
        created_at=now,
        settings=body.settings,
    )
    db.add(tenant)

    bootstrap_admin_user_id: str | None = None
    bootstrap_admin_email: str | None = None

    if body.bootstrap_admin:
        user_repo = SQLAlchemyUserRepository(db)
        existing_admin = await user_repo.get_by_email(
            str(body.bootstrap_admin.email), body.tenant_id
        )
        if existing_admin:
            raise ConflictException(
                f"User with email {str(body.bootstrap_admin.email)!r} already exists for tenant {body.tenant_id!r}"
            )

        admin_user = User.create(
            tenant_id=body.tenant_id,
            email=str(body.bootstrap_admin.email),
            full_name=body.bootstrap_admin.full_name,
            hashed_password=hash_password(body.bootstrap_admin.password),
            roles=["admin"],
        )
        admin_user.activate()
        await user_repo.save(admin_user)

        bootstrap_admin_user_id = admin_user.user_id
        bootstrap_admin_email = str(admin_user.email)

    await db.flush()

    return TenantCreateResponse(
        tenant_id=tenant.slug,
        name=tenant.name,
        plan=tenant.plan,
        max_users=tenant.max_users,
        is_active=tenant.is_active,
        created_at=tenant.created_at,
        settings=tenant.settings or {},
        bootstrap_admin_user_id=bootstrap_admin_user_id,
        bootstrap_admin_email=bootstrap_admin_email,
    )


@router.get("", response_model=list[TenantResponse])
async def list_tenants(
    current_user: CurrentUser = Depends(require_roles("admin")),
    db: Annotated[AsyncSession, Depends(get_db)] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    include_inactive: bool = False,
):
    query = select(OrganizationModel)

    if not include_inactive:
        query = query.where(OrganizationModel.is_active.is_(True))

    query = query.order_by(OrganizationModel.created_at.desc()).offset(skip).limit(limit)

    result = await db.execute(query)
    tenants = result.scalars().all()
    return [_to_tenant_response(tenant) for tenant in tenants]


@router.get("/sectors", response_model=list[SectorLookupResponse])
async def list_sector_catalog(
    current_user: CurrentUser = Depends(get_current_user),
    db: Annotated[AsyncSession, Depends(get_db)] = None,
):
    del current_user

    result = await db.execute(
        select(SectorCatalogModel)
        .where(SectorCatalogModel.is_active.is_(True))
        .order_by(SectorCatalogModel.sort_order.asc(), SectorCatalogModel.name.asc())
    )
    sectors = result.scalars().all()

    return [SectorLookupResponse(code=sector.code, name=sector.name) for sector in sectors]


@router.get("/{tenant_id}/sector", response_model=TenantSectorResponse)
@router.get("/{tenant_id}/sectors", response_model=TenantSectorResponse)
async def get_tenant_sector(
    tenant_id: str,
    current_user: CurrentUser = Depends(get_current_user),
    db: Annotated[AsyncSession, Depends(get_db)] = None,
):
    _assert_tenant_scope(current_user, tenant_id)
    await _get_tenant_or_404(db, tenant_id)
    return await _build_tenant_sectors_response(db, tenant_id)


@router.put("/{tenant_id}/sector", response_model=TenantSectorResponse)
@router.put("/{tenant_id}/sectors", response_model=TenantSectorResponse)
async def update_tenant_sector(
    tenant_id: str,
    body: TenantSectorUpdateRequest,
    current_user: CurrentUser = Depends(require_roles("admin", "tenant_admin")),
    db: Annotated[AsyncSession, Depends(get_db)] = None,
):
    _assert_tenant_scope(current_user, tenant_id)
    await _get_tenant_or_404(db, tenant_id)

    if body.sector_code is not None:
        is_valid = await db.scalar(
            select(SectorCatalogModel.code).where(
                SectorCatalogModel.is_active.is_(True),
                SectorCatalogModel.code == body.sector_code,
            )
        )
        if is_valid is None:
            raise ValidationException(
                f"Unknown or inactive sector: {body.sector_code}"
            )

    await db.execute(
        delete(TenantSectorModel).where(TenantSectorModel.tenant_id == tenant_id)
    )

    if body.sector_code is not None:
        now = datetime.now(timezone.utc)
        db.add(
            TenantSectorModel(
                tenant_id=tenant_id,
                sector_code=body.sector_code,
                created_at=now,
            )
        )

    await db.flush()
    return await _build_tenant_sectors_response(db, tenant_id)


@router.patch("/{tenant_id}", response_model=TenantResponse)
async def update_tenant(
    tenant_id: str,
    body: TenantUpdateRequest,
    current_user: CurrentUser = Depends(require_roles("admin")),
    db: Annotated[AsyncSession, Depends(get_db)] = None,
):
    tenant = await _get_tenant_or_404(db, tenant_id)

    if body.name is not None:
        tenant.name = body.name.strip()
    if body.plan is not None:
        tenant.plan = body.plan.value
    if body.max_users is not None:
        tenant.max_users = body.max_users
    if body.is_active is not None:
        tenant.is_active = body.is_active

    await db.flush()
    return _to_tenant_response(tenant)


@router.get("/{tenant_id}/prompts", response_model=TenantPromptsResponse)
async def get_tenant_prompts(
    tenant_id: str,
    current_user: CurrentUser = Depends(require_roles("admin")),
    db: Annotated[AsyncSession, Depends(get_db)] = None,
):
    tenant = await _get_tenant_or_404(db, tenant_id)
    settings = tenant.settings if isinstance(tenant.settings, dict) else {}
    prompts = settings.get("prompts", {}) if isinstance(settings.get("prompts", {}), dict) else {}
    return TenantPromptsResponse(tenant_id=tenant.slug, prompts=prompts)


@router.patch("/{tenant_id}/prompts", response_model=TenantPromptsResponse)
async def update_tenant_prompts(
    tenant_id: str,
    body: TenantPromptsUpdateRequest,
    current_user: CurrentUser = Depends(require_roles("admin")),
    db: Annotated[AsyncSession, Depends(get_db)] = None,
):
    tenant = await _get_tenant_or_404(db, tenant_id)
    # Reassign fresh dicts so SQLAlchemy tracks JSON changes reliably.
    settings = dict(tenant.settings) if isinstance(tenant.settings, dict) else {}
    prompts = dict(settings.get("prompts")) if isinstance(settings.get("prompts"), dict) else {}

    prompts["rag_system_v1"] = body.rag_system_v1
    settings["prompts"] = prompts
    tenant.settings = settings
    flag_modified(tenant, "settings")

    await db.flush()
    return TenantPromptsResponse(tenant_id=tenant.slug, prompts=tenant.settings.get("prompts", {}))
