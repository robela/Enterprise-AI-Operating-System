"""User repository port (interface)."""
from abc import ABC, abstractmethod

from backend.domains.users.domain.entities.user import User


class UserRepository(ABC):
    @abstractmethod
    async def get_by_id(self, user_id: str, tenant_id: str) -> User | None: ...

    @abstractmethod
    async def get_by_email(self, email: str, tenant_id: str) -> User | None: ...

    @abstractmethod
    async def save(self, user: User) -> None: ...

    @abstractmethod
    async def delete(self, user_id: str, tenant_id: str) -> None: ...

    @abstractmethod
    async def list_by_tenant(self, tenant_id: str, skip: int = 0, limit: int = 50) -> list[User]: ...
