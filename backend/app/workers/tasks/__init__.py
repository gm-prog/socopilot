"""Celery task modules — import submodules for autodiscovery."""

from app.workers.tasks import enrichment, health, ingest, phase2  # noqa: F401

__all__ = ["enrichment", "health", "ingest", "phase2"]
