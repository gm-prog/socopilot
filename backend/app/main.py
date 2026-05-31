"""SOCoPilot FastAPI application entrypoint."""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from prometheus_fastapi_instrumentator import Instrumentator

from app import __version__
from app.api.v1.router import api_router
from app.api.ws.alerts import router as alerts_ws_router
from app.core.config import get_settings
from app.core.logging import get_logger, setup_logging
from app.middleware.correlation import CorrelationIdMiddleware
from app.middleware.pii_redaction import PIIRedactionMiddleware
from app.realtime.alerts import AlertsEventBroker, AlertsWebSocketManager


def _assert_routes(app: FastAPI) -> None:
    required = {
        "/api/v1/ingest/alerts",
        "/api/v1/alerts",
        "/api/v1/replay/{raw_event_id}",
        "/api/v1/iocs",
        "/api/v1/search/semantic",
    }
    paths = {getattr(r, "path", "") for r in app.routes}
    missing = [p for p in required if p not in paths]
    if missing:
        from app.core.logging import get_logger

        get_logger(__name__).warning("startup_missing_routes", routes=missing)


@asynccontextmanager
async def lifespan(app: FastAPI):
    setup_logging()
    settings = get_settings()
    get_logger(__name__).info(
        "settings_loaded",
        secret_key_source=settings.secret_key_source,
        jwt_algorithm=settings.algorithm,
    )
    app.state.alerts_ws_manager = AlertsWebSocketManager()
    app.state.alerts_event_broker = AlertsEventBroker()
    await app.state.alerts_event_broker.start(app.state.alerts_ws_manager)
    _assert_routes(app)
    yield
    await app.state.alerts_event_broker.stop()


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(
        title=settings.app_name,
        version=__version__,
        description="AI SIEM Alert Triage & False Positive Reducer",
        lifespan=lifespan,
    )

    cors_origins = [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://frontend:3000",
    ]
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

    app.include_router(api_router, prefix="/api/v1")
    app.include_router(alerts_ws_router)

    Instrumentator().instrument(app).expose(app, endpoint="/metrics")

    return app


app = create_app()
