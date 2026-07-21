import asyncio
from uuid import uuid4
import datetime
from app.db.sync_session import SyncSessionLocal
from app.db.models.normalized_alert import NormalizedAlert
from app.workers.tasks.phase2 import generate_copilot_summary_task

async def main():
    db = SyncSessionLocal()
    tenant_id = None
    alert_id = uuid4()
    now = datetime.datetime.now(datetime.UTC)
    
    try:
        from sqlalchemy import text
        tenant_row = db.execute(text("SELECT id FROM tenants LIMIT 1")).fetchone()
        if tenant_row:
            tenant_id = tenant_row[0]
        else:
            tenant_id = uuid4()
            db.execute(text("INSERT INTO tenants (id, name, created_at, updated_at) VALUES (:id, 'Test', :now, :now)"),
                       {"id": tenant_id, "now": now})

        print(f"[*] Inserting NormalizedAlert record...")
        
        # Satisfying all required fields
        mock_alert = NormalizedAlert(
            id=alert_id,
            tenant_id=tenant_id,
            fingerprint=f"fp-{alert_id}",
            time_bucket="2026-06-25",
            title="Brute Force Detection Test",
            severity="high",
            status="NEW",
            detected_at=now,
            normalized_payload={"raw": "test data"},
            duplicate_count=1,
            lifecycle_state="new",
            tags=[]
        )
        
        db.add(mock_alert)
        db.commit()
        print(f"[+] Successfully inserted NormalizedAlert: {alert_id}")
            
    except Exception as e:
        db.rollback()
        print(f"[-] Insertion failed: {e}")
        return
    finally:
        db.close()

    print(f"[*] Triggering task...")
    task = generate_copilot_summary_task.delay({"alert_id": str(alert_id), "tenant_id": str(tenant_id)})
    print(f"[+] Task dispatched: {task.id}")

if __name__ == "__main__":
    asyncio.run(main())
