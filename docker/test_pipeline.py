import asyncio
from uuid import uuid4
import datetime
from app.db.sync_session import SyncSessionLocal
from app.db.models.normalized_alert import NormalizedAlert
from app.pipelines.post_ingest import dispatch_post_ingest_pipeline

async def main():
    db = SyncSessionLocal()
    tenant_id = None
    alert_id = uuid4()
    now = datetime.datetime.now(datetime.UTC)
    
    try:
        from sqlalchemy import text
        tenant_row = db.execute(text("SELECT id FROM tenants LIMIT 1")).fetchone()
        tenant_id = tenant_row[0] if tenant_row else uuid4()
        if not tenant_row:
            db.execute(text("INSERT INTO tenants (id, name, created_at, updated_at) VALUES (:id, 'Test', :now, :now)"),
                       {"id": tenant_id, "now": now})

        print(f"[*] Creating full pipeline mock alert with compliant payload...")
        
        # Build a payload that passes CanonicalAlertSchema validation
        compliant_payload = {
            "source": "webhook",
            "title": "Pipeline Chain Test",
            "severity": "high",
            "detected_at": now.isoformat(),
            "raw": "Brute force attack logs matching signatures"
        }

        mock_alert = NormalizedAlert(
            id=alert_id,
            tenant_id=tenant_id,
            fingerprint=f"pipeline-test-{alert_id}",
            time_bucket="2026-06-26",
            title="Pipeline Chain Test",
            severity="high",
            status="NEW",
            detected_at=now,
            normalized_payload=compliant_payload, # Satisfies Pydantic validation
            duplicate_count=1,
            lifecycle_state="new",
            tags=[]
        )
        db.add(mock_alert)
        db.commit()
        print(f"[+] Alert committed: {alert_id}")
            
    except Exception as e:
        db.rollback()
        print(f"[-] Setup failed: {e}")
        return
    finally:
        db.close()

    print(f"[*] Firing entire post-ingest pipeline...")
    dispatch_post_ingest_pipeline(
        alert_id=str(alert_id),
        tenant_id=str(tenant_id),
        correlation_id=str(uuid4())
    )
    print(f"[+] Pipeline triggered! Check worker logs.")

if __name__ == "__main__":
    asyncio.run(main())
