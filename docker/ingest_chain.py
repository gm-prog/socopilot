"""Celery ingest chain: v2 pipeline entry."""

from celery import chain
from celery.result import AsyncResult

from app.workers.tasks.ingest import process_ingest_event


def dispatch_ingest_pipeline(raw_event_id: str, correlation_id: str) -> AsyncResult:
    """
    Single-step ingest pipeline (v2):
    all logic handled inside process_ingest_event.
    """
    workflow = chain(
        process_ingest_event.s(raw_event_id, correlation_id),
    )

    return workflow.apply_async(queue="ingest")


def get_chain_task_ids(result: AsyncResult) -> list[str]:
    ids = []
    node = result

    while node:
        if node.id:
            ids.append(node.id)
        node = node.parent if hasattr(node, "parent") else None

    return ids