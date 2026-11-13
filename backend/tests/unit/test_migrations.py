"""Migrations build the same schema as the models, so a model change needs a migration."""
from pathlib import Path

import pytest
from alembic import command
from alembic.autogenerate import compare_metadata
from alembic.config import Config
from alembic.migration import MigrationContext
from alembic.script import ScriptDirectory
from sqlalchemy import create_engine, inspect

import backend.infrastructure.persistence.models  # noqa: F401
from backend.core.database.session import Base

ALEMBIC_INI = Path(__file__).resolve().parents[2] / "alembic.ini"


@pytest.fixture
def engine(tmp_path):
    engine = create_engine(f"sqlite:///{tmp_path / 'migrations.db'}")
    yield engine
    engine.dispose()


def _alembic(connection) -> Config:
    config = Config(str(ALEMBIC_INI))
    config.attributes["connection"] = connection
    return config


def _upgrade(engine, revision: str = "head") -> None:
    with engine.begin() as connection:
        command.upgrade(_alembic(connection), revision)


def _schema_diff(engine) -> list:
    with engine.connect() as connection:
        context = MigrationContext.configure(connection, opts={"compare_type": False})
        return compare_metadata(context, Base.metadata)


def test_migrations_match_the_models(engine) -> None:
    _upgrade(engine)

    assert _schema_diff(engine) == []


def test_one_head() -> None:
    assert len(ScriptDirectory.from_config(Config(str(ALEMBIC_INI))).get_heads()) == 1


def test_downgrade_then_upgrade(engine) -> None:
    _upgrade(engine)
    with engine.begin() as connection:
        command.downgrade(_alembic(connection), "base")
    assert inspect(engine).get_table_names() == ["alembic_version"]

    _upgrade(engine)
    assert _schema_diff(engine) == []


def test_database_built_by_create_all_adopts_migrations(engine) -> None:
    """Databases from before migrations: the baseline skips existing tables."""
    tables = [t for name, t in Base.metadata.tables.items() if name != "request_traces"]
    Base.metadata.create_all(engine, tables=tables)

    _upgrade(engine)

    assert _schema_diff(engine) == []
