"""Multi-tenant middleware — resolves tenant from JWT or X-Tenant-ID header."""
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response
import structlog

from backend.core.config.settings import settings

logger = structlog.get_logger(__name__)

TENANT_CONTEXT_KEY = "tenant_id"


class TenantMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next) -> Response:
        tenant_id = (
            request.headers.get("X-Tenant-ID")
            or self._tenant_from_token(request)
            or settings.default_tenant_id
        )
        request.state.tenant_id = tenant_id
        structlog.contextvars.bind_contextvars(tenant_id=tenant_id)
        response = await call_next(request)
        structlog.contextvars.clear_contextvars()
        return response

    @staticmethod
    def _tenant_from_token(request: Request) -> str | None:
        """Best-effort extract tenant from JWT without full validation (done later in auth)."""
        try:
            auth = request.headers.get("Authorization", "")
            if not auth.startswith("Bearer "):
                return None
            from jose import jwt as _jwt
            payload = _jwt.get_unverified_claims(auth.split(" ", 1)[1])
            return payload.get("tenant_id")
        except Exception:
            return None
