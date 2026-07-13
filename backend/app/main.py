"""Enterprise AI Operating System — FastAPI application factory."""
from contextlib import asynccontextmanager
import structlog

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.core.config.settings import settings
from backend.core.database.session import init_db
from backend.core.cache.redis import init_redis, close_redis
from backend.core.events.bus import event_bus
from backend.core.logging.logger import configure_logging
from backend.core.middleware.tenant import TenantMiddleware
from backend.core.middleware.audit import AuditMiddleware
from backend.core.middleware.logging import RequestLoggingMiddleware
from backend.core.exceptions.base import register_exception_handlers
from backend.infrastructure.monitoring.telemetry import configure_telemetry
from backend.api.rest.router import api_router

logger = structlog.get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage startup and shutdown lifecycle."""
    try:
        configure_logging()
        configure_telemetry(app)
        await init_db()
        try:
            await init_redis()
        except Exception as e:
            logger.warning("Failed to connect to Redis, continuing without caching", error=str(e))
        await event_bus.start()
        yield
        await event_bus.stop()
        await close_redis()
    except Exception as e:
        logger.error("Fatal error during app startup", error=str(e))
        raise


def create_app() -> FastAPI:
    app = FastAPI(
        title=settings.app_name,
        version="1.0.0",
        description="Enterprise AI Operating System — multi-tenant, multi-industry AI platform",
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
        lifespan=lifespan,
    )

    # CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Custom middleware (order matters — outermost first)
    app.add_middleware(RequestLoggingMiddleware)
    app.add_middleware(AuditMiddleware)
    app.add_middleware(TenantMiddleware)

    # Exception handlers
    register_exception_handlers(app)

    # Routers
    app.include_router(api_router, prefix="/api/v1")

    @app.get("/", tags=["info"])
    async def root():
        return {
            "service": settings.app_name,
            "version": "1.0.0",
            "description": "Enterprise AI Operating System — multi-tenant, multi-industry AI platform",
            "docs": "/docs",
            "redoc": "/redoc",
            "openapi": "/openapi.json",
            "health": "/health",
            "api": "/api/v1"
        }

    @app.get("/health", tags=["health"])
    async def health_check():
        return {"status": "ok", "service": settings.app_name}

    return app


app = create_app()
