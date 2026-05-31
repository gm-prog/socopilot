"""Create enrichment jobs and queue provider tasks — decoupled from ingest."""

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models.alert_ioc import AlertIOC
from app.db.models.enrichment import EnrichmentJob
from app.enrichment.providers import PROVIDER_REGISTRY


class EnrichmentDispatcher:
    """Dispatch enrichment jobs for extracted IOCs."""

    DEFAULT_PROVIDERS = ("abuseipdb", "virustotal", "greynoise", "shodan")

    def create_jobs(
        self,
        session: Session,
        tenant_id: UUID,
        alert_id: UUID,
        providers: tuple[str, ...] | None = None,
    ) -> list[EnrichmentJob]:
        provider_names = providers or self.DEFAULT_PROVIDERS
        iocs = list(
            session.execute(
                select(AlertIOC).where(
                    AlertIOC.alert_id == alert_id,
                    AlertIOC.tenant_id == tenant_id,
                )
            ).scalars()
        )
        jobs: list[EnrichmentJob] = []

        for provider_name in provider_names:
            if provider_name not in PROVIDER_REGISTRY:
                continue
            provider = PROVIDER_REGISTRY[provider_name]()
            matched = [ioc for ioc in iocs if provider.supports(ioc.ioc_type)]
            if not matched:
                job = EnrichmentJob(
                    tenant_id=tenant_id,
                    alert_id=alert_id,
                    provider=provider_name,
                    status="skipped",
                    ioc_type=None,
                    ioc_value=None,
                )
                session.add(job)
                jobs.append(job)
                continue
            for ioc in matched[:5]:
                job = EnrichmentJob(
                    tenant_id=tenant_id,
                    alert_id=alert_id,
                    provider=provider_name,
                    status="pending",
                    ioc_type=ioc.ioc_type,
                    ioc_value=ioc.ioc_value,
                )
                session.add(job)
                jobs.append(job)
        session.flush()
        return jobs
