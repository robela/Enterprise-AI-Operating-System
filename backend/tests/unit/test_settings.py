from backend.core.config.settings import Settings


def test_normalize_postgres_database_url() -> None:
    settings = Settings(
        APP_SECRET_KEY="test-secret",
        JWT_SECRET_KEY="test-jwt-secret",
        DATABASE_URL="postgresql://user:pass@db.example.com:5432/enterprise_ai",
    )

    assert settings.database_url == "postgresql+asyncpg://user:pass@db.example.com:5432/enterprise_ai"


def test_normalize_legacy_postgres_database_url() -> None:
    settings = Settings(
        APP_SECRET_KEY="test-secret",
        JWT_SECRET_KEY="test-jwt-secret",
        DATABASE_URL="postgres://user:pass@db.example.com:5432/enterprise_ai",
    )

    assert settings.database_url == "postgresql+asyncpg://user:pass@db.example.com:5432/enterprise_ai"