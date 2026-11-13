"""Per-request trace records for tenant admins.

Revision ID: 0002_request_traces
Revises: 0001_baseline
Create Date: 2026-11-13
"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0002_request_traces"
down_revision: str | None = "0001_baseline"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "request_traces",
        sa.Column("trace_id", sa.String(36), primary_key=True),
        sa.Column("tenant_id", sa.String(100), nullable=False),
        sa.Column("user_id", sa.String(36), nullable=True),
        sa.Column("conversation_id", sa.String(36), nullable=True),
        sa.Column("message_id", sa.String(36), nullable=True),
        sa.Column("endpoint", sa.String(50), nullable=False),
        sa.Column("agent", sa.String(50), nullable=True),
        sa.Column("status", sa.String(20), nullable=False),
        sa.Column("language", sa.String(16), nullable=True),
        sa.Column("reranker", sa.String(20), nullable=True),
        sa.Column("query_rewritten", sa.Boolean(), nullable=False),
        sa.Column("chunks_used", sa.Integer(), nullable=False),
        sa.Column("sources", sa.JSON(), nullable=False),
        sa.Column("requires_human_review", sa.Boolean(), nullable=False),
        sa.Column("latency_ms", sa.Integer(), nullable=False),
        sa.Column("error_type", sa.String(100), nullable=True),
        sa.Column("details", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    for column in ("tenant_id", "conversation_id", "created_at"):
        op.create_index(f"ix_request_traces_{column}", "request_traces", [column])


def downgrade() -> None:
    op.drop_table("request_traces")
