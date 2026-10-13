"""Unit tests for the User domain."""
import pytest

from backend.domains.users.application.services.user_service import UserService
from backend.domains.users.domain.entities.user import User, UserStatus
from backend.domains.identity.application.services.auth_service import AuthService
from backend.domains.users.domain.value_objects.email import Email
from backend.domains.users.domain.events.user_events import UserCreated, UserDeactivated


def test_email_valid():
    email = Email("alice@example.com")
    assert str(email) == "alice@example.com"
    assert email.domain == "example.com"


def test_email_invalid():
    with pytest.raises(ValueError):
        Email("not-an-email")


def test_user_create_emits_created_event():
    user = User.create(
        tenant_id="tenant-1",
        email="bob@example.com",
        full_name="Bob Smith",
        hashed_password="hashed",
    )
    assert user.status == UserStatus.PENDING_VERIFICATION
    assert user.roles == ["user"]

    events = user.pop_events()
    assert len(events) == 1
    assert isinstance(events[0], UserCreated)
    assert events[0].email == "bob@example.com"


def test_user_deactivate_emits_event():
    user = User.create("t1", "c@x.com", "Charlie", "hash")
    user.activate()
    user.pop_events()  # clear creation event

    user.deactivate()
    assert user.status == UserStatus.INACTIVE
    events = user.pop_events()
    assert any(isinstance(e, UserDeactivated) for e in events)


def test_user_update():
    user = User.create("t1", "d@x.com", "Dave", "hash")
    user.update(full_name="David Updated", roles=["admin"])
    assert user.full_name == "David Updated"
    assert "admin" in user.roles


@pytest.mark.asyncio
async def test_administrator_created_user_is_active(db_session):
    from backend.domains.users.infrastructure.persistence.user_repository_impl import (
        SQLAlchemyUserRepository,
    )

    service = UserService(SQLAlchemyUserRepository(db_session))
    user = await service.create_user(
        tenant_id="tenant-1",
        email="new-user@example.com",
        full_name="New User",
        password="strong-password",
        roles=["tenant_user"],
    )

    assert user.status == UserStatus.ACTIVE


@pytest.mark.asyncio
async def test_administrator_created_user_can_log_in_immediately(db_session):
    from backend.domains.users.infrastructure.persistence.user_repository_impl import (
        SQLAlchemyUserRepository,
    )

    repository = SQLAlchemyUserRepository(db_session)
    await UserService(repository).create_user(
        tenant_id="tenant-1",
        email="new-user@example.com",
        full_name="New User",
        password="strong-password",
        roles=["tenant_user"],
    )

    tokens = await AuthService(repository).login(
        email="new-user@example.com",
        password="strong-password",
        tenant_id="tenant-1",
    )

    assert tokens["access_token"]


@pytest.mark.asyncio
async def test_administrator_can_activate_existing_pending_user(db_session):
    from backend.domains.users.infrastructure.persistence.user_repository_impl import (
        SQLAlchemyUserRepository,
    )

    repository = SQLAlchemyUserRepository(db_session)
    pending_user = User.create(
        tenant_id="tenant-1",
        email="pending-user@example.com",
        full_name="Pending User",
        hashed_password="hashed",
        roles=["tenant_user"],
    )
    await repository.save(pending_user)

    activated_user = await UserService(repository).activate_user(
        pending_user.user_id,
        "tenant-1",
    )

    assert activated_user.status == UserStatus.ACTIVE


@pytest.mark.asyncio
async def test_email_must_be_unique_across_tenants(db_session):
    from backend.domains.users.infrastructure.persistence.user_repository_impl import (
        SQLAlchemyUserRepository,
    )

    service = UserService(SQLAlchemyUserRepository(db_session))
    await service.create_user(
        tenant_id="tenant-1",
        email="admin@moh.gov",
        full_name="First Admin",
        password="strong-password",
        roles=["tenant_admin"],
    )

    with pytest.raises(ConflictException):
        await service.create_user(
            tenant_id="tenant-2",
            email="admin@moh.gov",
            full_name="Second Admin",
            password="strong-password",
            roles=["tenant_admin"],
        )


@pytest.mark.asyncio
async def test_administrator_can_deactivate_user_in_another_tenant(db_session):
    from backend.domains.users.infrastructure.persistence.user_repository_impl import (
        SQLAlchemyUserRepository,
    )

    repository = SQLAlchemyUserRepository(db_session)
    user = await UserService(repository).create_user(
        tenant_id="tenant-2",
        email="other-tenant@example.com",
        full_name="Other Tenant User",
        password="strong-password",
        roles=["tenant_user"],
    )

    await UserService(repository).deactivate_user_as_admin(user.user_id)

    assert (await repository.get_by_id_any_tenant(user.user_id)).status == UserStatus.INACTIVE


@pytest.mark.asyncio
async def test_administrator_can_delete_user_in_another_tenant(db_session):
    from backend.domains.users.infrastructure.persistence.user_repository_impl import (
        SQLAlchemyUserRepository,
    )

    repository = SQLAlchemyUserRepository(db_session)
    user = await UserService(repository).create_user(
        tenant_id="tenant-2",
        email="delete-me@example.com",
        full_name="Delete Me",
        password="strong-password",
        roles=["tenant_user"],
    )

    await UserService(repository).delete_user_as_admin(user.user_id)

    assert await repository.get_by_id_any_tenant(user.user_id) is None
