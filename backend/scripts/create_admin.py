"""One-time script to create the initial admin user.

Usage:
    python -m backend.scripts.create_admin
    python -m backend.scripts.create_admin --email admin@example.com --password MyP@ss123 --name "Admin User"
"""
import argparse
import asyncio
import os
import sys

# Ensure env is loaded before settings import
os.environ.setdefault("APP_SECRET_KEY", os.environ.get("APP_SECRET_KEY", "dev-secret-key"))
os.environ.setdefault("JWT_SECRET_KEY", os.environ.get("JWT_SECRET_KEY", "dev-jwt-secret"))

from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession

from backend.core.config.settings import settings
from backend.core.database.session import Base
from backend.core.security.jwt import hash_password
from backend.domains.users.infrastructure.persistence.user_repository_impl import (
    SQLAlchemyUserRepository,
)
from backend.domains.users.domain.entities.user import User


async def create_admin(email: str, password: str, full_name: str) -> None:
    engine = create_async_engine(settings.database_url, echo=False)
    session_factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with session_factory() as session:
        repo = SQLAlchemyUserRepository(session)

        existing = await repo.get_by_email(email, tenant_id="default")
        if existing:
            print(f"[!] User '{email}' already exists — skipping.")
            await engine.dispose()
            return

        user = User.create(
            tenant_id="default",
            email=email,
            full_name=full_name,
            hashed_password=hash_password(password),
            roles=["admin"],
        )
        await repo.save(user)
        await session.commit()

    await engine.dispose()
    print(f"[+] Admin user created successfully!")
    print(f"    Email   : {email}")
    print(f"    Password: {password}")
    print(f"    Roles   : admin")


def main() -> None:
    parser = argparse.ArgumentParser(description="Create initial admin user")
    parser.add_argument("--email", default="admin@enterprise.ai")
    parser.add_argument("--password", default="Admin@1234")
    parser.add_argument("--name", default="Admin")
    args = parser.parse_args()

    asyncio.run(create_admin(args.email, args.password, args.name))


if __name__ == "__main__":
    main()
