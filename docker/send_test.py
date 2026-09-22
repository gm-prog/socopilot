import json
from redis import Redis

# 1. Connect directly to your Redis broker
try:
    redis_client = Redis(host='127.0.0.1', port=6379, db=0)
    print("Successfully connected to Redis broker.")
except Exception as e:
    print(f"Failed to connect to Redis: {e}")
    exit(1)

# 2. Load the mock JSON alert data
try:
    with open('test_event.json', 'r') as f:
        event_data = json.load(f)
except FileNotFoundError:
    print("Error: test_event.json file not found. Ensure you created it!")
    exit(1)

# 3. Format the signature payload exactly how Celery expects it
# This bypasses loading full application dependencies into memory
celery_task_payload = {
    "body": [ [event_data], {}, {"callbacks": None, "errbacks": None, "chain": None, "chord": None} ],
    "headers": {
        "lang": "py",
        "task": "app.workers.tasks.ingest.process_ingest_event",
        "id": "test-task-uuid-12345"
    },
    "properties": {
        "body_encoding": "base64",
        "delivery_mode": 2,
        "delivery_info": {"exchange": "ingest", "routing_key": "ingest"},
        "priority": 0
    }
}

# 4. Serialize and push the message straight into the processing queue
import base64
serialized_body = base64.b64encode(json.dumps(celery_task_payload["body"]).encode('utf-8')).decode('utf-8')
message = {
    "body": serialized_body,
    "headers": celery_task_payload["headers"],
    "properties": celery_task_payload["properties"],
    "content-type": "application/json",
    "content-encoding": "utf-8"
}

redis_client.lpush('ingest', json.dumps(message))
print("Task successfully injected into the 'processing' queue!")
