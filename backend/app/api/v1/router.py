from fastapi import APIRouter

from app.api.v1.health import router as health_router
from app.api.v1.alerts import router as alerts_router
from app.api.v1.ingest import router as ingest_router
from app.api.v1.iocs import router as iocs_router
from app.api.v1.search import router as search_router
from app.api.v1.replay import router as replay_router
from app.api.v1.enrichment import router as enrichment_router
from app.api.v1.auth import router as auth_router
from app.api.v1.cases import router as cases_router
from app.api.v1.websocket import router as ws_router
from app.api.v1.system import router as system_router

api_router = APIRouter()

api_router.include_router(health_router)
api_router.include_router(alerts_router)
api_router.include_router(ingest_router)
api_router.include_router(iocs_router)
api_router.include_router(search_router)
api_router.include_router(replay_router)
api_router.include_router(enrichment_router)
api_router.include_router(auth_router)
api_router.include_router(cases_router)
api_router.include_router(ws_router)
api_router.include_router(system_router)
