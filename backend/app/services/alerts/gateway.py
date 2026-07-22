from app.db.models.normalized_alert import NormalizedAlert
from app.db.repositories.ingest import IngestRepository

class AlertGateway:
    def __init__(self, session):
        self.session = session
        self.repo = IngestRepository(session)

    def create_alert(self, *, tenant_id, raw_event_id, canonical, dedup):
        existing = (
            self.session.query(NormalizedAlert)
            .filter_by(raw_event_id=raw_event_id)
            .first()
        )

        if existing:
            return existing

        alert = self.repo.persist_alert(
            tenant_id=tenant_id,
            raw_event_id=raw_event_id,
            canonical=canonical,
            dedup=dedup,
        )

        try:
            self.session.flush()
        except Exception:
            self.session.rollback()
            return (
                self.session.query(NormalizedAlert)
                .filter_by(raw_event_id=raw_event_id)
                .first()
            )

        return alert
