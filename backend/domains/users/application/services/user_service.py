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
        existing = await self._repo.get_by_email_any_tenant(email)
        if existing:
            raise ConflictException(f"User with email {email!r} already exists")

        user = User.create(
            tenant_id=tenant_id,
            email=email,
            full_name=full_name,
            hashed_password=hash_password(password),
            roles=roles,
        )
        user.activate()
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

    async def deactivate_user_as_admin(self, user_id: str) -> None:
        user = await self._repo.get_by_id_any_tenant(user_id)
        if not user:
            raise NotFoundException(f"User {user_id!r} not found")
        user.deactivate()
        await self._repo.save(user)

        for event in user.pop_events():
            await event_bus.publish(event)

    async def delete_user(self, user_id: str, tenant_id: str) -> None:
        user = await self.get_user(user_id, tenant_id)
        await self._repo.delete(user.user_id, tenant_id)

    async def delete_user_as_admin(self, user_id: str) -> None:
        user = await self._repo.get_by_id_any_tenant(user_id)
        if not user:
            raise NotFoundException(f"User {user_id!r} not found")
        await self._repo.delete_any_tenant(user.user_id)

    async def reset_password_as_admin(self, user_id: str, password: str) -> User:
        user = await self._repo.get_by_id_any_tenant(user_id)
        if not user:
            raise NotFoundException(f"User {user_id!r} not found")
        user.hashed_password = hash_password(password)
        await self._repo.save(user)
        return user

    async def activate_user(self, user_id: str, tenant_id: str) -> User:
        user = await self.get_user(user_id, tenant_id)
        user.activate()
        await self._repo.save(user)

        for event in user.pop_events():
            await event_bus.publish(event)

        return user

    async def activate_user_as_admin(self, user_id: str) -> User:
        user = await self._repo.get_by_id_any_tenant(user_id)
        if not user:
            raise NotFoundException(f"User {user_id!r} not found")
        user.activate()
        await self._repo.save(user)

        for event in user.pop_events():
            await event_bus.publish(event)

        return user

    async def list_users(self, tenant_id: str, skip: int = 0, limit: int = 50) -> list[User]:
        return await self._repo.list_by_tenant(tenant_id, skip=skip, limit=limit)

    async def list_all_users(self, skip: int = 0, limit: int = 50) -> list[User]:
        return await self._repo.list_all(skip=skip, limit=limit)
