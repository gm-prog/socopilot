"""Post-ingest pipeline — decoupled from core ingest chain."""

from celery import chain, group

from app.workers.celery_app import celery_app
from app.workers.tasks.phase2 import (
    dispatch_enrichment_jobs,
    extract_iocs_task,
    generate_alert_embedding,
    index_alert_opensearch,
)


def dispatch_post_ingest_pipeline(
    alert_id: str,
    tenant_id: str,
    correlation_id: str,
    raw_event_id: str | None = None,
) -> None:
    """
    After persist: extract IOCs -> dispatch enrichment.
    Parallel: OpenSearch index + embedding (non-blocking).
    """
    header = {
        "alert_id": alert_id,
        "tenant_id": tenant_id,
        "correlation_id": correlation_id,
        "raw_event_id": raw_event_id,
    }
    main_chain = chain(
        extract_iocs_task.s(header),
        dispatch_enrichment_jobs.s(),
    )
    parallel = group(
        index_alert_opensearch.s(header),
        generate_alert_embedding.s(header),
    )
    main_chain.apply_async(queue="processing")
    parallel.apply_async(queue="processing")
