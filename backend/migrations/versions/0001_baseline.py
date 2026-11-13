"""Baseline: the schema that create_all built before migrations existed.

Tables that already exist are skipped, so a database created by the old startup
create_all adopts migrations without a manual ``alembic stamp``. Columns of existing
tables are not changed here.

Revision ID: 0001_baseline
Revises:
Create Date: 2026-11-13
"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from pgvector.sqlalchemy import Vector

from backend.core.config.settings import settings

revision: str = "0001_baseline"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

_TZ = sa.DateTime(timezone=True)


def _id(name: str, length: int = 36, **kwargs) -> sa.Column:
    return sa.Column(name, sa.String(length), primary_key=True, **kwargs)


def _str(name: str, length: int, nullable: bool = False, *args) -> sa.Column:
    return sa.Column(name, sa.String(length), *args, nullable=nullable)


def _create(name: str, *columns, indexes: Sequence[str] = (), unique: Sequence[str] = ()) -> None:
    if sa.inspect(op.get_bind()).has_table(name):
        return
    op.create_table(name, *columns)
    for column in indexes:
        op.create_index(f"ix_{name}_{column}", name, [column], unique=column in unique)


def upgrade() -> None:
    bind = op.get_bind()
    if bind.dialect.name == "postgresql":
        op.execute("CREATE EXTENSION IF NOT EXISTS vector")

    _create(
        "users",
        _id("user_id"),
        _str("tenant_id", 36),
        _str("email", 255),
        _str("full_name", 255),
        _str("hashed_password", 255),
        _str("status", 50),
        sa.Column("roles", sa.Text(), nullable=False),
        sa.Column("mfa_enabled", sa.Boolean(), nullable=False),
        sa.Column("created_at", _TZ, nullable=False),
        sa.Column("updated_at", _TZ, nullable=False),
        sa.Column("last_login_at", _TZ, nullable=True),
        indexes=["tenant_id"],
    )
    _create(
        "organizations",
        _id("org_id"),
        _str("name", 255),
        _str("slug", 100),
        _str("plan", 50),
        sa.Column("max_users", sa.Integer(), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("created_at", _TZ, nullable=False),
        sa.Column("settings", sa.JSON(), nullable=False),
        indexes=["slug"],
        unique=["slug"],
    )
    _create(
        "sector_catalog",
        _id("code", 64),
        _str("name", 255),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("sort_order", sa.Integer(), nullable=False),
        sa.Column("created_at", _TZ, nullable=False),
    )
    _create(
        "tenant_sectors",
        sa.Column(
            "tenant_id", sa.String(100), sa.ForeignKey("organizations.slug"), primary_key=True
        ),
        _str("sector_code", 64, False, sa.ForeignKey("sector_catalog.code")),
        sa.Column("created_at", _TZ, nullable=False),
    )
    _create(
        "workflow_templates",
        _id("template_id", 64),
        _str("name", 255),
        _str("description", 500, True),
        _str("definition_id", 100),
        _str("sector_code", 64, True, sa.ForeignKey("sector_catalog.code")),
        _str("owner_tenant_id", 100, True, sa.ForeignKey("organizations.slug")),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column("is_default_for_sector", sa.Boolean(), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("config", sa.JSON(), nullable=False),
        _str("created_by", 36, True),
        sa.Column("created_at", _TZ, nullable=False),
        sa.Column("updated_at", _TZ, nullable=False),
        indexes=["sector_code", "owner_tenant_id"],
    )
    _create(
        "tenant_workflow_selection",
        sa.Column(
            "tenant_id", sa.String(100), sa.ForeignKey("organizations.slug"), primary_key=True
        ),
        _str("template_id", 64, False, sa.ForeignKey("workflow_templates.template_id")),
        _str("assigned_by", 36, True),
        sa.Column("assigned_at", _TZ, nullable=False),
    )
    _create(
        "documents",
        _id("document_id"),
        _str("tenant_id", 36),
        _str("uploaded_by", 36),
        _str("filename", 500),
        _str("storage_path", 1000),
        _str("content_type", 100),
        sa.Column("size_bytes", sa.Integer(), nullable=False),
        _str("doc_type", 50),
        _str("status", 50),
        sa.Column("chunk_count", sa.Integer(), nullable=False),
        sa.Column("metadata", sa.JSON(), nullable=False),
        sa.Column("tags", sa.Text(), nullable=False),
        sa.Column("created_at", _TZ, nullable=False),
        sa.Column("updated_at", _TZ, nullable=False),
        indexes=["tenant_id"],
    )
    _create(
        "document_chunks",
        _id("tenant_id"),
        _id("document_id"),
        sa.Column("chunk_index", sa.Integer(), primary_key=True),
        sa.Column("chunk_text", sa.Text(), nullable=False),
        sa.Column(
            "embedding",
            Vector(settings.embedding_dimension).with_variant(sa.Text(), "sqlite"),
            nullable=False,
        ),
        sa.Column("metadata", sa.Text(), nullable=True),
    )
    _create(
        "extracted_workflows",
        _id("workflow_id"),
        _str("tenant_id", 36),
        _str("document_id", 36),
        _str("name", 255),
        _str("workflow_type", 50),
        sa.Column("steps", sa.JSON(), nullable=False),
        sa.Column("required_fields", sa.JSON(), nullable=False),
        sa.Column("source_pages", sa.JSON(), nullable=False),
        sa.Column("source_excerpt", sa.Text(), nullable=False),
        _str("confidence", 20),
        _str("status", 20),
        _str("reviewed_by", 36, True),
        sa.Column("reviewed_at", _TZ, nullable=True),
        sa.Column("created_at", _TZ, nullable=False),
        sa.Column("updated_at", _TZ, nullable=False),
        indexes=["tenant_id", "document_id", "status"],
    )
    _create(
        "workflows",
        _id("workflow_id"),
        _str("tenant_id", 36),
        _str("definition_id", 100),
        _str("name", 255),
        _str("initiator_id", 36),
        _str("status", 50),
        sa.Column("context", sa.JSON(), nullable=False),
        sa.Column("created_at", _TZ, nullable=False),
        sa.Column("updated_at", _TZ, nullable=False),
        sa.Column("completed_at", _TZ, nullable=True),
        indexes=["tenant_id"],
    )
    _create(
        "workflow_tasks",
        _id("task_id"),
        _str("workflow_id", 36, False, sa.ForeignKey("workflows.workflow_id")),
        _str("name", 255),
        _str("task_type", 100),
        _str("status", 50),
        _str("assignee_id", 36, True),
        sa.Column("input_data", sa.JSON(), nullable=False),
        sa.Column("output_data", sa.JSON(), nullable=False),
        sa.Column("started_at", _TZ, nullable=True),
        sa.Column("completed_at", _TZ, nullable=True),
        sa.Column("comments", sa.Text(), nullable=False),
    )
    _create(
        "audit_logs",
        _id("log_id"),
        _str("tenant_id", 36),
        _str("user_id", 36, True),
        _str("action", 255),
        _str("resource_type", 100),
        _str("resource_id", 255, True),
        _str("ip_address", 45, True),
        _str("user_agent", 500, True),
        _str("result", 50),
        sa.Column("details", sa.JSON(), nullable=False),
        sa.Column("occurred_at", _TZ, nullable=False),
        indexes=["tenant_id", "occurred_at"],
    )
    _create(
        "conversations",
        _id("conversation_id"),
        _str("user_id", 36),
        _str("tenant_id", 36),
        _str("title", 255, True),
        sa.Column("created_at", _TZ, nullable=False),
        sa.Column("updated_at", _TZ, nullable=False),
        sa.Column("message_count", sa.Integer(), nullable=False),
        indexes=["user_id", "tenant_id", "created_at"],
    )
    _create(
        "messages",
        _id("message_id"),
        _str("conversation_id", 36, False, sa.ForeignKey("conversations.conversation_id")),
        _str("role", 50),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("citations", sa.JSON(), nullable=False),
        sa.Column("images", sa.JSON(), nullable=False),
        sa.Column("videos", sa.JSON(), nullable=False),
        _str("audio_url", 1000, True),
        sa.Column("created_at", _TZ, nullable=False),
        indexes=["conversation_id", "created_at"],
    )
    _create(
        "dislike_reasons",
        _id("dislike_reason_id"),
        _str("tenant_id", 36),
        _str("name", 255),
        _str("category", 100),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("created_at", _TZ, nullable=False),
        sa.Column("updated_at", _TZ, nullable=False),
        indexes=["tenant_id"],
    )
    _create(
        "feedback",
        _id("feedback_id"),
        _str("conversation_id", 36, False, sa.ForeignKey("conversations.conversation_id")),
        _str("message_id", 36, False, sa.ForeignKey("messages.message_id")),
        _str("user_id", 36),
        sa.Column("liked", sa.Boolean(), nullable=True),
        sa.Column("categorical_tags", sa.JSON(), nullable=False),
        sa.Column("created_at", _TZ, nullable=False),
        sa.Column("updated_at", _TZ, nullable=False),
        indexes=["conversation_id", "message_id", "user_id", "created_at"],
    )
    _create(
        "surveys",
        _id("survey_id"),
        _str("conversation_id", 36, False, sa.ForeignKey("conversations.conversation_id")),
        _str("user_id", 36),
        sa.Column("action_taken", sa.JSON(), nullable=False),
        sa.Column("intent_changed", sa.Boolean(), nullable=False),
        sa.Column("additional_feedback", sa.Text(), nullable=True),
        sa.Column("created_at", _TZ, nullable=False),
        sa.Column("updated_at", _TZ, nullable=False),
        sa.UniqueConstraint("conversation_id"),
        indexes=["user_id", "created_at"],
    )


def downgrade() -> None:
    for name in (
        "surveys",
        "feedback",
        "dislike_reasons",
        "messages",
        "conversations",
        "audit_logs",
        "workflow_tasks",
        "workflows",
        "extracted_workflows",
        "document_chunks",
        "documents",
        "tenant_workflow_selection",
        "workflow_templates",
        "tenant_sectors",
        "sector_catalog",
        "organizations",
        "users",
    ):
        op.drop_table(name)
