"""Main REST API router — aggregates all domain routers.

The app should continue to start even when one optional router is broken or still
under development. This keeps the platform usable while the failing module is fixed.
"""
import structlog
from fastapi import APIRouter

logger = structlog.get_logger(__name__)

api_router = APIRouter()


def _include_router(module_name: str, router_name: str = "router") -> None:
    try:
        module = __import__(module_name, fromlist=[router_name])
        router = getattr(module, router_name)
    except Exception as exc:  # pragma: no cover - defensive start-up guard
        logger.warning("skipping_router_import", module=module_name, error=str(exc))
        return
    api_router.include_router(router)


_include_router("backend.domains.identity.api.router")
_include_router("backend.domains.users.api.router")
_include_router("backend.api.rest.ai_router")
_include_router("backend.api.rest.feedback_router")
_include_router("backend.api.rest.settings_router")
_include_router("backend.api.rest.analytics_router")
_include_router("backend.api.rest.documents_router")
_include_router("backend.api.rest.workflows_router")
_include_router("backend.api.rest.audit_router")
_include_router("backend.api.rest.tenants_router")
