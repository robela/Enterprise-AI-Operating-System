"""SQLAlchemy implementation of UserRepository."""
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.domains.users.domain.entities.user import User, UserStatus
from backend.domains.users.domain.repositories.user_repository import UserRepository
from backend.domains.users.domain.value_objects.email import Email
from backend.infrastructure.persistence.models import UserModel


class SQLAlchemyUserRepository(UserRepository):
    def __init__(self, session: AsyncSession):
        self._session = session

    async def get_by_id(self, user_id: str, tenant_id: str) -> User | None:
        result = await self._session.execute(
            select(UserModel).where(
                UserModel.user_id == user_id, UserModel.tenant_id == tenant_id
            )
        )
        model = result.scalar_one_or_none()
        return self._to_domain(model) if model else None

    async def get_by_email(self, email: str, tenant_id: str) -> User | None:
        result = await self._session.execute(
            select(UserModel).where(
                UserModel.email == email.lower(), UserModel.tenant_id == tenant_id
            )
        )
        model = result.scalar_one_or_none()
        return self._to_domain(model) if model else None

    async def save(self, user: User) -> None:
        result = await self._session.execute(
            select(UserModel).where(UserModel.user_id == user.user_id)
        )
        model = result.scalar_one_or_none()
        if model:
            model.full_name = user.full_name
            model.hashed_password = user.hashed_password
            model.status = user.status.value
            model.roles = ",".join(user.roles)
            model.updated_at = user.updated_at
            model.last_login_at = user.last_login_at
            model.mfa_enabled = user.mfa_enabled
        else:
            self._session.add(
                UserModel(
                    user_id=user.user_id,
                    tenant_id=user.tenant_id,
                    email=str(user.email),
                    full_name=user.full_name,
                    hashed_password=user.hashed_password,
                    status=user.status.value,
                    roles=",".join(user.roles),
                    created_at=user.created_at,
                    updated_at=user.updated_at,
                    mfa_enabled=user.mfa_enabled,
                )
            )
        await self._session.flush()

    async def delete(self, user_id: str, tenant_id: str) -> None:
        result = await self._session.execute(
            select(UserModel).where(
                UserModel.user_id == user_id, UserModel.tenant_id == tenant_id
            )
        )
        model = result.scalar_one_or_none()
        if model:
            await self._session.delete(model)
            await self._session.flush()

    async def list_by_tenant(self, tenant_id: str, skip: int = 0, limit: int = 50) -> list[User]:
        result = await self._session.execute(
            select(UserModel)
            .where(UserModel.tenant_id == tenant_id)
            .offset(skip)
            .limit(limit)
        )
        return [self._to_domain(m) for m in result.scalars().all()]

    @staticmethod
    def _to_domain(model: UserModel) -> User:
        return User(
            user_id=model.user_id,
            tenant_id=model.tenant_id,
            email=Email(model.email),
            full_name=model.full_name,
            hashed_password=model.hashed_password,
            status=UserStatus(model.status),
            roles=model.roles.split(",") if model.roles else [],
            created_at=model.created_at,
            updated_at=model.updated_at,
            last_login_at=model.last_login_at,
            mfa_enabled=model.mfa_enabled,
        )
