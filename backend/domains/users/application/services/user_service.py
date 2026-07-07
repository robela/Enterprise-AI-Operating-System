"""User application service — orchestrates use cases."""
from backend.core.security.jwt import hash_password
from backend.core.events.bus import event_bus
from backend.core.exceptions.base import NotFoundException, ConflictException
from backend.domains.users.domain.entities.user import User
from backend.domains.users.domain.repositories.user_repository import UserRepository


class UserService:
    def __init__(self, repository: UserRepository):
        self._repo = repository

    async def create_user(
        self,
        tenant_id: str,
        email: str,
        full_name: str,
        password: str,
        roles: list[str] | None = None,
    ) -> User:
        existing = await self._repo.get_by_email(email, tenant_id)
        if existing:
            raise ConflictException(f"User with email {email!r} already exists")

        user = User.create(
            tenant_id=tenant_id,
            email=email,
            full_name=full_name,
            hashed_password=hash_password(password),
            roles=roles,
        )
        await self._repo.save(user)

        for event in user.pop_events():
            await event_bus.publish(event)

        return user

    async def get_user(self, user_id: str, tenant_id: str) -> User:
        user = await self._repo.get_by_id(user_id, tenant_id)
        if not user:
            raise NotFoundException(f"User {user_id!r} not found")
        return user

    async def update_user(
        self,
        user_id: str,
        tenant_id: str,
        full_name: str | None = None,
        roles: list[str] | None = None,
    ) -> User:
        user = await self.get_user(user_id, tenant_id)
        user.update(full_name=full_name, roles=roles)
        await self._repo.save(user)

        for event in user.pop_events():
            await event_bus.publish(event)

        return user

    async def deactivate_user(self, user_id: str, tenant_id: str) -> None:
        user = await self.get_user(user_id, tenant_id)
        user.deactivate()
        await self._repo.save(user)

        for event in user.pop_events():
            await event_bus.publish(event)

    async def list_users(self, tenant_id: str, skip: int = 0, limit: int = 50) -> list[User]:
        return await self._repo.list_by_tenant(tenant_id, skip=skip, limit=limit)
