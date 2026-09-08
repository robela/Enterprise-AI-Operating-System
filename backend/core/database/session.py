"""Async SQLAlchemy session factory."""
from collections.abc import AsyncGenerator
from datetime import datetime, timezone

from sqlalchemy import event, select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from backend.core.config.settings import settings

_is_sqlite = settings.database_url.startswith("sqlite")
_engine_kwargs: dict = {"echo": settings.app_debug, "future": True}
if not _is_sqlite:
    _engine_kwargs["pool_size"] = settings.database_pool_size
    _engine_kwargs["max_overflow"] = settings.database_max_overflow
else:
    _engine_kwargs["connect_args"] = {"timeout": 30}

engine = create_async_engine(settings.database_url, **_engine_kwargs)

if _is_sqlite:
    @event.listens_for(engine.sync_engine, "connect")
    def _set_sqlite_pragmas(dbapi_connection, connection_record):  # pragma: no cover - runtime DB hook
        del connection_record
        cursor = dbapi_connection.cursor()
        try:
            cursor.execute("PRAGMA journal_mode=WAL")
            cursor.execute("PRAGMA synchronous=NORMAL")
            cursor.execute("PRAGMA busy_timeout=30000")
        finally:
            cursor.close()

AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


class Base(DeclarativeBase):
    """Shared declarative base for all SQLAlchemy models."""
    pass


DEFAULT_SECTOR_CATALOG: list[tuple[str, str]] = [
    ("financial-services", "Financial Services"),
    ("banking", "Banking"),
    ("insurance", "Insurance"),
    ("healthcare", "Healthcare"),
    ("pharmaceuticals", "Pharmaceuticals"),
    ("legal", "Legal"),
    ("telecommunications", "Telecommunications"),
    ("education", "Education"),
    ("agriculture", "Agriculture"),
    ("real-estate", "Real Estate"),
]

DEFAULT_WORKFLOW_TEMPLATES: list[dict[str, object]] = [
    {
        "template_id": "banking-loan-approval-v1",
        "name": "Banking Loan Approval",
        "description": "Default banking workflow for loan approval decisions.",
        "definition_id": "loan_approval_v1",
        "sector_code": "banking",
        "config": {
            "tasks": [
                {
                    "name": "AI Risk Assessment",
                    "task_type": "ai_decision",
                    "input_keys": ["loan_amount", "applicant_name"],
                },
                {
                    "name": "Manager Approval",
                    "task_type": "human_approval",
                },
                {
                    "name": "Compliance Review",
                    "task_type": "human_approval",
                    "condition": "loan_amount_gt_50000",
                },
                {
                    "name": "Final Decision",
                    "task_type": "automated",
                },
            ]
        },
    },
    {
        "template_id": "healthcare-medical-referral-v1",
        "name": "Healthcare Medical Referral",
        "description": "Default healthcare workflow for specialist referral handling.",
        "definition_id": "medical_referral_v1",
        "sector_code": "healthcare",
        "config": {
            "tasks": [
                {
                    "name": "AI Pre-screening",
                    "task_type": "ai_decision",
                    "input_keys": ["patient_id", "specialist_type"],
                },
                {
                    "name": "Primary Doctor Review",
                    "task_type": "human_approval",
                },
                {
                    "name": "Insurance Authorization",
                    "task_type": "human_approval",
                },
                {
                    "name": "Specialist Booking Confirmation",
                    "task_type": "automated",
                },
            ]
        },
    },
]


async def init_db() -> None:
    """Create all tables (dev/test only — production uses Alembic)."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    # Seed default sectors and workflow templates in dev/test environments.
    from backend.infrastructure.persistence.models import (
        SectorCatalogModel,
        WorkflowTemplateModel,
    )

    async with AsyncSessionLocal() as session:
        existing_codes = set(
            (await session.execute(select(SectorCatalogModel.code))).scalars().all()
        )
        changed = False
        if len(existing_codes) < len(DEFAULT_SECTOR_CATALOG):
            now = datetime.now(timezone.utc)
            for sort_order, (code, name) in enumerate(DEFAULT_SECTOR_CATALOG, start=1):
                if code in existing_codes:
                    continue
                session.add(
                    SectorCatalogModel(
                        code=code,
                        name=name,
                        is_active=True,
                        sort_order=sort_order,
                        created_at=now,
                    )
                )
                changed = True

        existing_templates = {
            model.template_id: model
            for model in (await session.execute(select(WorkflowTemplateModel))).scalars().all()
        }
        now = datetime.now(timezone.utc)
        for template in DEFAULT_WORKFLOW_TEMPLATES:
            template_id = str(template["template_id"])
            existing = existing_templates.get(template_id)
            if existing is None:
                session.add(
                    WorkflowTemplateModel(
                        template_id=template_id,
                        name=str(template["name"]),
                        description=str(template["description"]),
                        definition_id=str(template["definition_id"]),
                        sector_code=str(template["sector_code"]),
                        owner_tenant_id=None,
                        version=1,
                        is_default_for_sector=True,
                        is_active=True,
                        config=dict(template.get("config", {})),
                        created_by=None,
                        created_at=now,
                        updated_at=now,
                    )
                )
                changed = True
                continue

            expected_config = dict(template.get("config", {}))
            if existing.owner_tenant_id is None and (existing.config or {}) != expected_config:
                existing.config = expected_config
                existing.updated_at = now
                changed = True

        if changed:
            await session.commit()


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI dependency — yields an async DB session."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
