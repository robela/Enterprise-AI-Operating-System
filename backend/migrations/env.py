"""Alembic environment: the app's models and DATABASE_URL from settings.

Tests pass an open connection through ``config.attributes["connection"]``; otherwise
this connects with the async engine for DATABASE_URL."""
import asyncio
from logging.config import fileConfig

from alembic import context
from sqlalchemy import pool, text
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import create_async_engine

import backend.infrastructure.persistence.models  # noqa: F401  (registers every table)
from backend.core.config.settings import settings
from backend.core.database.session import Base

config = context.config
if config.config_file_name and not config.attributes.get("connection"):
    fileConfig(config.config_file_name, disable_existing_loggers=False)

target_metadata = Base.metadata

# Any fixed number: lets only one instance run migrations at a time on PostgreSQL.
_MIGRATION_LOCK_ID = 73162041


def _run(connection: Connection) -> None:
    context.configure(
        connection=connection,
        target_metadata=target_metadata,
        render_as_batch=connection.dialect.name == "sqlite",
    )
    with context.begin_transaction():
        if connection.dialect.name == "postgresql":
            # Released at commit. Another instance starting at the same time waits here,
            # then finds the migrations already applied.
            connection.execute(text("SELECT pg_advisory_xact_lock(:id)"), {"id": _MIGRATION_LOCK_ID})
        context.run_migrations()


async def _run_async() -> None:
    engine = create_async_engine(settings.database_url, poolclass=pool.NullPool)
    try:
        async with engine.connect() as connection:
            await connection.run_sync(_run)
            await connection.commit()
    finally:
        await engine.dispose()


def run_migrations_offline() -> None:
    context.configure(
        url=settings.database_url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
elif (connection := config.attributes.get("connection")) is not None:
    _run(connection)
else:
    asyncio.run(_run_async())
