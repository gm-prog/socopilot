import os
from socopilot.tasks import process_ingest_event

# Explicitly tell the task client where to find the broker
process_ingest_event.app.conf.broker_url = 'redis://redis:6379/0'

def execute_load_test():
    print("\n" + "="*56)
    print("🚀 DISPATCHING 200 PAYLOADS TO CELERY WORKERS")
    print("="*56 + "\n")
    
    unique_events = [f"event_{i}" for i in range(50)]
    
    for event_id in unique_events:
        for attempt in range(4):
            payload = {"data": f"content_{event_id}_{attempt}"}
            process_ingest_event.delay(event_id, payload)
            
    print("[*] 200 tasks dispatched. Check your worker terminal!")

if __name__ == "__main__":
    execute_load_test()
