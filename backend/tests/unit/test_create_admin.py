from backend.core.security.jwt import verify_password
from backend.domains.users.domain.entities.user import User, UserStatus
from backend.scripts.create_admin import build_or_update_admin_user


def test_build_or_update_admin_user_creates_active_admin() -> None:
    user, created = build_or_update_admin_user(
        existing_user=None,
        email="admin@enterprise.ai",
        password="Admin@1234",
        full_name="Admin",
    )

    assert created is True
    assert user.status == UserStatus.ACTIVE
    assert user.roles == ["admin"]
    assert verify_password("Admin@1234", user.hashed_password)


def test_build_or_update_admin_user_repairs_existing_admin() -> None:
    existing = User.create(
        tenant_id="default",
        email="admin@enterprise.ai",
        full_name="Old Name",
        hashed_password="old-hash",
        roles=["user"],
    )

    user, created = build_or_update_admin_user(
        existing_user=existing,
        email="admin@enterprise.ai",
        password="Admin@1234",
        full_name="Admin",
    )

    assert created is False
    assert user is existing
    assert user.full_name == "Admin"
    assert user.status == UserStatus.ACTIVE
    assert user.roles == ["admin"]
    assert verify_password("Admin@1234", user.hashed_password)