"""Authentication service — login, token refresh, logout."""
from backend.core.security.jwt import verify_password, create_access_token, create_refresh_token, decode_token
from backend.core.exceptions.base import UnauthorizedException
from backend.domains.users.domain.repositories.user_repository import UserRepository
from backend.domains.users.domain.entities.user import UserStatus


class AuthService:
    def __init__(self, user_repository: UserRepository):
        self._users = user_repository

    async def login(self, email: str, password: str, tenant_id: str) -> dict:
        user = await self._users.get_by_email(email, tenant_id)
        if not user:
            raise UnauthorizedException("Invalid credentials")

        if not verify_password(password, user.hashed_password):
            raise UnauthorizedException("Invalid credentials")

        if user.status not in (UserStatus.ACTIVE,):
            raise UnauthorizedException("Account is not active")

        user.record_login()
        await self._users.save(user)

        extra_claims = {
            "tenant_id": tenant_id,
            "roles": user.roles,
            "scopes": self._roles_to_scopes(user.roles),
        }
        access_token = create_access_token(subject=user.user_id, extra_claims=extra_claims)
        refresh_token = create_refresh_token(subject=user.user_id)

        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
        }

    async def refresh(self, refresh_token: str) -> dict:
        payload = decode_token(refresh_token)
        if payload.get("type") != "refresh":
            raise UnauthorizedException("Not a refresh token")

        user_id = payload["sub"]
        # Re-issue access token (look up user for fresh claims)
        access_token = create_access_token(subject=user_id)
        return {"access_token": access_token, "token_type": "bearer"}

    @staticmethod
    def _roles_to_scopes(roles: list[str]) -> list[str]:
        scopes = ["users:read"]
        if "admin" in roles:
            scopes += ["users:write", "admin"]
        elif "manager" in roles:
            scopes += ["users:write"]
        return scopes
