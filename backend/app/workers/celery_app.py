"""Celery application configuration."""

from celery import Celery
from app.core.config import get_settings

# get_settings() function call karke settings load karo
settings = get_settings()

celery_app = Celery(
    "socopilot",
    broker=settings.broker_url,
    backend=settings.result_backend_url,
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,

    task_track_started=True,
    task_acks_late=True,
    worker_prefetch_multiplier=1,

    task_default_queue="default",

    include=["app.workers.tasks"],

    task_routes={
        "app.workers.tasks.health.*": {"queue": "processing"},
        "app.workers.tasks.ingest.*": {"queue": "ingest"},
        
        # Explicit high-priority override for indexing task to target worker-enrichment
        "app.workers.tasks.phase2.index_alert_opensearch": {"queue": "enrichment"},
        
        "app.workers.tasks.phase2.*": {"queue": "processing"},
        "app.workers.tasks.enrichment.*": {"queue": "enrichment"},
    },
)

celery_app.autodiscover_tasks(["app.workers"], related_name="tasks", force=True)
