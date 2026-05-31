"""API v1 router aggregation."""

from fastapi import APIRouter

from app.api.v1 import alerts, auth, cases, enrichment, health, ingest, iocs, replay, search, system

api_router = APIRouter()
api_router.include_router(health.router)
api_router.include_router(auth.router)
api_router.include_router(system.router)
api_router.include_router(ingest.router)
api_router.include_router(alerts.router)
api_router.include_router(cases.router)
api_router.include_router(iocs.router)
api_router.include_router(enrichment.router)
api_router.include_router(replay.router)
api_router.include_router(search.router)
