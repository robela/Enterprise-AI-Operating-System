"""Main REST API router — aggregates all domain routers."""
from fastapi import APIRouter

from backend.domains.users.api.router import router as users_router
from backend.domains.identity.api.router import router as auth_router
from backend.api.rest.ai_router import router as ai_router
from backend.api.rest.analytics_router import router as analytics_router
from backend.api.rest.documents_router import router as documents_router
from backend.api.rest.workflows_router import router as workflows_router
from backend.api.rest.audit_router import router as audit_router

api_router = APIRouter()

api_router.include_router(auth_router)
api_router.include_router(users_router)
api_router.include_router(ai_router)
api_router.include_router(analytics_router)
api_router.include_router(documents_router)
api_router.include_router(workflows_router)
api_router.include_router(audit_router)
