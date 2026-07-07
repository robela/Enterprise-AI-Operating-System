"""FastAPI OAuth2 password bearer dependency + RBAC helpers."""
from typing import Annotated

from fastapi import Depends, Security
from fastapi.security import OAuth2PasswordBearer, SecurityScopes

from backend.core.security.jwt import decode_token
from backend.core.exceptions.base import UnauthorizedException, ForbiddenException

oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl="/api/v1/auth/token",
    scopes={
        "users:read": "Read user information",
        "users:write": "Create and update users",
        "admin": "Full administrative access",
    },
)


class CurrentUser:
    def __init__(self, user_id: str, tenant_id: str, roles: list[str], scopes: list[str]):
        self.user_id = user_id
        self.tenant_id = tenant_id
        self.roles = roles
        self.scopes = scopes

    def has_role(self, *roles: str) -> bool:
        return any(r in self.roles for r in roles)

    def has_scope(self, scope: str) -> bool:
        return scope in self.scopes


async def get_current_user(
    security_scopes: SecurityScopes,
    token: Annotated[str, Depends(oauth2_scheme)],
) -> CurrentUser:
    if security_scopes.scopes:
        authenticate_value = f'Bearer scope="{security_scopes.scope_str}"'
    else:
        authenticate_value = "Bearer"

    payload = decode_token(token)

    user_id: str | None = payload.get("sub")
    if not user_id:
        raise UnauthorizedException("Token missing subject", headers={"WWW-Authenticate": authenticate_value})

    token_scopes: list[str] = payload.get("scopes", [])
    for scope in security_scopes.scopes:
        if scope not in token_scopes:
            raise ForbiddenException(
                f"Not enough permissions. Required scope: {scope}",
                headers={"WWW-Authenticate": authenticate_value},
            )

    return CurrentUser(
        user_id=user_id,
        tenant_id=payload.get("tenant_id", "default"),
        roles=payload.get("roles", []),
        scopes=token_scopes,
    )


def require_roles(*roles: str):
    """Dependency factory — requires at least one of the given roles."""
    async def _check(current_user: Annotated[CurrentUser, Depends(get_current_user)]) -> CurrentUser:
        if not current_user.has_role(*roles):
            raise ForbiddenException(f"Required roles: {roles}")
        return current_user
    return _check
