"""Celery ingest chain: normalize -> dedup -> persist."""

from celery import chain
from celery.result import AsyncResult

from app.workers.celery_app import celery_app
from app.workers.tasks.ingest import dedup_alert, normalize_raw_event, persist_alert


def dispatch_ingest_pipeline(raw_event_id: str, correlation_id: str) -> AsyncResult:
  """Enqueue ingest -> normalize -> dedup -> persist chain on ingest queue."""
  workflow = chain(
    normalize_raw_event.s(raw_event_id, correlation_id),
    dedup_alert.s(),
    persist_alert.s(),
  )
  return workflow.apply_async(queue="ingest")


def get_chain_task_ids(result: AsyncResult) -> list[str]:
  ids: list[str] = []
  node = result
  while node is not None:
    if node.id:
      ids.append(node.id)
    node = node.parent if hasattr(node, "parent") else None
  return ids
