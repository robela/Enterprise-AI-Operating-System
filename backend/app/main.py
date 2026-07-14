"""Enterprise AI Operating System — FastAPI application factory."""
import asyncio
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

STARTUP_DB_TIMEOUT_SECONDS = 10
STARTUP_REDIS_TIMEOUT_SECONDS = 5


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage startup and shutdown lifecycle."""
    try:
        logger.info("Starting application lifespan initialization...")
        
        try:
            configure_logging()
            logger.info("Logging configured")
        except Exception as e:
            logger.error("Failed to configure logging", error=str(e))
            raise
        
        try:
            configure_telemetry(app)
            logger.info("Telemetry configured")
        except Exception as e:
            logger.error("Failed to configure telemetry", error=str(e))
            raise
        
        try:
            await asyncio.wait_for(init_db(), timeout=STARTUP_DB_TIMEOUT_SECONDS)
            logger.info("Database initialized")
        except asyncio.TimeoutError:
            logger.warning(
                "Database initialization timed out; continuing in degraded mode",
                timeout_seconds=STARTUP_DB_TIMEOUT_SECONDS,
            )
        except Exception as e:
            logger.error("Failed to initialize database", error=str(e), exc_info=True)
            # Don't fail completely - allow app to run in degraded mode
        
        try:
            await asyncio.wait_for(init_redis(), timeout=STARTUP_REDIS_TIMEOUT_SECONDS)
            logger.info("Redis connected")
        except asyncio.TimeoutError:
            logger.warning(
                "Redis initialization timed out; continuing without caching",
                timeout_seconds=STARTUP_REDIS_TIMEOUT_SECONDS,
            )
        except Exception as e:
            logger.warning("Failed to connect to Redis, continuing without caching", error=str(e))
        
        try:
            await event_bus.start()
            logger.info("Event bus started")
        except Exception as e:
            logger.warning("Failed to start event bus", error=str(e))
            # Allow app to run without event bus
        
        logger.info("Application startup complete")
        yield
        logger.info("Starting shutdown sequence...")
        
        try:
            await event_bus.stop()
        except Exception as e:
            logger.warning("Error during event bus shutdown", error=str(e))
        
        try:
            await close_redis()
        except Exception as e:
            logger.warning("Error during Redis shutdown", error=str(e))
        
        logger.info("Application shutdown complete")
        
    except Exception as e:
        logger.error("Fatal error during app startup", error=str(e), exc_info=True)
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

    @app.get("/status", tags=["health"])
    async def status():
        """Detailed status endpoint for debugging."""
        return {
            "status": "running",
            "service": settings.app_name,
            "version": "1.0.0",
            "environment": settings.app_env,
            "debug": settings.app_debug,
        }

    return app


app = create_app()
