"""Per-provider enrichment worker tasks."""

from datetime import UTC, datetime
from uuid import UUID

from app.core.logging import bind_context, get_logger
from app.core.metrics import ENRICHMENT_LATENCY, PROVIDER_FAILURES
from app.db.models.enrichment import EnrichmentJob, EnrichmentResult
from app.db.models.normalized_alert import NormalizedAlert
from app.db.sync_session import get_sync_db
from app.enrichment.providers import get_provider
from app.workers.celery_app import celery_app

logger = get_logger(__name__)

LIFECYCLE_STATES = frozenset(
    {"new", "triaged", "investigating", "contained", "resolved", "false_positive"}
)


@celery_app.task(
    name="app.workers.tasks.enrichment.run_enrichment_job",
    bind=True,
    autoretry_for=(ValueError,),
    retry_kwargs={"max_retries": 5, "countdown": 2},
    exponential_backoff=True,
)
def run_enrichment_job(self, job_id: str) -> dict:
    bind_context(enrichment_job_id=job_id, stage="enrichment_provider")
    jid = UUID(job_id)

    with get_sync_db() as session:
        if session.get(EnrichmentJob, jid) is None:
            raise ValueError(f"Enrichment job {job_id} not found")

    with get_sync_db() as session:
        job = session.get(EnrichmentJob, jid)
        if job is None:
            raise ValueError(f"Enrichment job {job_id} not found")
        if job.status in ("success", "skipped"):
            return {"status": job.status}

        job.status = "running"
        job.started_at = datetime.now(UTC)
        session.flush()

        if not job.ioc_type or not job.ioc_value:
            job.status = "skipped"
            job.completed_at = datetime.now(UTC)
            return {"status": "skipped"}

        try:
            provider = get_provider(job.provider)
            result = provider.enrich(job.ioc_type, job.ioc_value)
            ENRICHMENT_LATENCY.labels(provider=job.provider).observe(result.latency_ms / 1000.0)

            er = EnrichmentResult(
                job_id=job.id,
                tenant_id=job.tenant_id,
                alert_id=job.alert_id,
                provider=job.provider,
                status=result.status,
                latency_ms=result.latency_ms,
                raw_response=result.raw_response,
                error_message=result.error_message,
                summary=result.summary,
            )
            session.add(er)
            job.status = result.status
            job.completed_at = datetime.now(UTC)

            if result.status == "error":
                PROVIDER_FAILURES.labels(provider=job.provider).inc()
                if job.retry_count < 3:
                    job.retry_count += 1
                    raise self.retry(exc=Exception(result.error_message or "provider error"))

            _merge_enrichment_summary(session, job.alert_id, job.provider, result.summary)
            session.flush()
            logger.info("enrichment_complete", provider=job.provider, status=result.status)
            return {"status": result.status, "provider": job.provider}
        except Exception as exc:
            job.status = "error"
            job.completed_at = datetime.now(UTC)
            PROVIDER_FAILURES.labels(provider=job.provider).inc()
            session.add(
                EnrichmentResult(
                    job_id=job.id,
                    tenant_id=job.tenant_id,
                    alert_id=job.alert_id,
                    provider=job.provider,
                    status="error",
                    error_message=str(exc),
                )
            )
            raise


def _merge_enrichment_summary(session, alert_id: UUID, provider: str, summary: dict | None):
    if not summary:
        return
    alert = session.get(NormalizedAlert, alert_id)
    if alert is None:
        return
    base = alert.enrichment_summary or {}
    providers = base.get("providers", {})
    providers[provider] = summary
    base["providers"] = providers
    alert.enrichment_summary = base
    if alert.lifecycle_state == "new":
        alert.lifecycle_state = "triaged"
