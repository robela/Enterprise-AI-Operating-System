"""Unit tests for the User domain."""
import pytest

from backend.domains.users.domain.entities.user import User, UserStatus
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
