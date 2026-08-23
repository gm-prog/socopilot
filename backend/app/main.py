import os
from contextlib import asynccontextmanager
import asyncio
from typing import Set

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from app.db.seed import seed_default_tenant
from app.db.session import AsyncSessionLocal, engine
from app.db.sync_session import sync_engine
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text

from app import __version__
from app.api.v1.router import api_router
from app.core.config import get_settings
from app.core.logging import get_logger, setup_logging
from app.core.redis import close_redis_client
from app.middleware.correlation import CorrelationIdMiddleware
from app.middleware.pii_redaction import PIIRedactionMiddleware
from fastapi.staticfiles import StaticFiles
from prometheus_fastapi_instrumentator import Instrumentator
from app.realtime.alerts import AlertsEventBroker, AlertsWebSocketManager


def _extract_paths(app: FastAPI) -> Set[str]:
    paths: Set[str] = set()

    for route in app.routes:
        path = getattr(route, "path", None)
        if isinstance(path, str):
            paths.add(path)

    return paths


def _assert_routes(app: FastAPI) -> None:
    required = {
        "/api/v1/ingest/alerts",
        "/api/v1/ingest/event",
        "/api/v1/alerts",
        "/api/v1/replay/{raw_event_id}",
        "/api/v1/iocs",
        "/api/v1/search/semantic",
    }

    paths = _extract_paths(app)
    missing = sorted(required - paths)

    if missing:
        get_logger(__name__).warning(
            "startup_missing_routes",
            routes=missing,
        )


def _test_sync_database_connection() -> None:
    with sync_engine.connect() as connection:
        connection.execute(text("SELECT 1"))


async def _test_database_connections() -> None:
    settings = get_settings()
    logger = get_logger(__name__)

    try:
        async with engine.connect() as connection:
            await connection.execute(text("SELECT 1"))

        await asyncio.to_thread(_test_sync_database_connection)

        logger.info("Database connection established")

    except Exception as exc:
        logger.error(
            "database_connection_failed",
            database_url=settings.redacted_database_url,
            database_url_sync=settings.redacted_database_url_sync,
            error=str(exc),
        )
        raise RuntimeError("Database connection failed") from exc


async def wait_for_db(engine, retries=15, delay=2):
    logger = get_logger(__name__)

    for i in range(retries):
        try:
            async with engine.connect() as conn:
                await conn.execute(text("SELECT 1"))
            logger.info("Database connection established")
            return
        except Exception as e:
            logger.warning(f"DB not ready ({i+1}/{retries}): {e}")
            await asyncio.sleep(delay)

    raise RuntimeError("Database failed after retries")


@asynccontextmanager
async def lifespan(app: FastAPI):
    setup_logging()
    settings = get_settings()
    logger = get_logger(__name__)

    logger.info(
        "settings_loaded",
        secret_key_source=settings.secret_key_source,
        jwt_algorithm=settings.algorithm,
    )

    # 1. WAIT FOR DATABASE
    await wait_for_db(engine)

    # 2. SAFE SEEDING (NON-FATAL)
    try:
        async with AsyncSessionLocal() as session:
            await seed_default_tenant(session)
    except Exception as e:
        logger.warning("seed_failed_non_fatal", error=str(e))

    # Initialize OpenSearch indices once at startup
    try:
        from app.integrations.opensearch.client import OpenSearchClient
        os_client = OpenSearchClient()
        if os_client.enabled and not os.getenv("TESTING") and "pytest" not in os.environ.get("PYTEST_CURRENT_TEST", ""):
            os_client.ensure_indices()
            logger.info("opensearch_indices_ensured")
    except Exception as e:
        logger.warning("opensearch_indices_init_failed", error=str(e))

    # 3. INIT REALTIME SYSTEMS
    app.state.alerts_ws_manager = AlertsWebSocketManager()
    app.state.alerts_event_broker = AlertsEventBroker()

    await app.state.alerts_event_broker.start(
        app.state.alerts_ws_manager
    )

    # 4. ROUTE VALIDATION
    _assert_routes(app)

    yield

    await app.state.alerts_event_broker.stop()
    await engine.dispose()
    sync_engine.dispose()
    logger.info("database_engines_disposed")
    await close_redis_client()
    logger.info("redis_connections_closed")


def create_app() -> FastAPI:
    settings = get_settings()

    app = FastAPI(
        title=settings.app_name,
        version=__version__,
        description="AI SIEM Alert Triage & False Positive Reducer",
        lifespan=lifespan,
    )

    cors_origins = getattr(settings, "cors_origins", [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://frontend:3000",
    ])

    app.add_middleware(
        CORSMiddleware,
        allow_origins=cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
        expose_headers=["X-Correlation-ID"],
    )

    app.add_middleware(CorrelationIdMiddleware)
    app.add_middleware(PIIRedactionMiddleware)

    # ------------------------------------------------------------------
    # FastAPI compatibility patch (safe)
    # ------------------------------------------------------------------
    try:
        from fastapi.routing import _IncludedRouter

        if not hasattr(_IncludedRouter, "path"):
            _IncludedRouter.path = property(
                lambda self: getattr(self.include_context, "prefix", "")
            )
    except (ImportError, AttributeError):
        pass

    # PROMETHEUS METRICS
    Instrumentator().instrument(app).expose(
        app,
        endpoint="/metrics",
        include_in_schema=False,
    )

    # ROUTES
    app.include_router(api_router, prefix="/api/v1")

    @app.get("/api/v1/health")
    def health():
        return {"status": "ok"}

    @app.get("/api/v1/ready")
    def ready():
        return {"status": "ready"}

    # STATIC FILES (frontend)
    app.mount("/", StaticFiles(directory="app/static", html=True), name="static")

    @app.exception_handler(Exception)
    async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
        correlation_id = request.headers.get("X-Correlation-ID", "unknown")
        logger = get_logger(__name__)
        logger.exception("unhandled_internal_error", correlation_id=correlation_id, error=str(exc))
        return JSONResponse(
            status_code=500,
            content={
                "error": {
                    "code": "INTERNAL_SERVER_ERROR",
                    "message": "An unexpected error occurred.",
                    "correlation_id": correlation_id,
                }
            },
        )

    return app


app = create_app()
