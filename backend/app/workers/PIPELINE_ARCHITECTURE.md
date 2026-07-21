"""
Async Multi-Stage Ingestion Pipeline — Architecture & Usage Guide

This module implements a 3-stage async ingestion pipeline for SOCoPilot,
orchestrated via Celery workers and integrated with Ollama for embeddings/LLM
and Redis for real-time Pub/Sub updates.

ARCHITECTURE OVERVIEW
=====================

┌──────────────────────────────────────────────────────────────────────┐
│                     INGEST PIPELINE (3 STAGES)                       │
└──────────────────────────────────────────────────────────────────────┘

STAGE 1: INGEST (worker-ingest)
────────────────────────────────────
  Task: ingest.capture_raw_event()
  
  Purpose:
    - Capture incoming telemetry from webhooks, Syslog, APIs, etc.
    - Validate tenant_id (strict data isolation)
    - Store raw payload to RawEvent table
    - Update status: received → queued
  
  Input:
    {
      "tenant_id": "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx",
      "correlation_id": "unique-trace-id",
      "source_label": "webhook|syslog|api",
      "payload": {...raw alert data...},
      "client_ip": "192.168.1.1"
    }
  
  Output:
    {
      "raw_event_id": "uuid",
      "status": "captured",
      "next_task": "processing_task_id"
    }
  
  Error Handling:
    - Max 3 retries with exponential backoff (2^retries seconds)
    - Validation errors → IngestFailure DLQ
    - Failed events logged with correlation_id for audit trail

  Dependencies:
    - RawEvent model (no schema changes)
    - IngestRepository.get_db_session()

──────────────────────────────────────────────────────────────────────

STAGE 2: PROCESSING (worker-processing)
────────────────────────────────────────
  Task: ingest.process_alert()
  
  Purpose:
    - Normalize raw alert into CanonicalAlertSchema
    - Generate embeddings via Ollama nomic-embed-text model
    - Deduplicate similar alerts (fingerprinting + time bucketing)
    - Persist to NormalizedAlert table
    - Update status: queued → processing → normalized
  
  Input:
    {
      "tenant_id": "uuid",
      "raw_event_id": "uuid",
      "correlation_id": "trace-id",
      "payload": {...raw data...}
    }
  
  Output:
    {
      "alert_id": "uuid",
      "status": "normalized",
      "next_task": "enrichment_task_id"
    }
  
  Ollama Integration:
    - Model: nomic-embed-text (768-dimensional embeddings)
    - Endpoint: http://ollama:11434/api/embeddings
    - Timeout: 120s per request
    - Uses async httpx.AsyncClient (non-blocking)
    - Fallback: empty embedding on Ollama failure (non-fatal)
  
  Error Handling:
    - Max 3 retries with exponential backoff (2^retries seconds)
    - Validation errors (bad tenant_id, missing RawEvent) → DLQ
    - Ollama failures → logged warning, task continues
  
  Dependencies:
    - NormalizedAlert model (no schema changes)
    - IngestRepository.persist_alert()
    - CanonicalAlertSchema
    - OllamaClient (async HTTP)

──────────────────────────────────────────────────────────────────────

STAGE 3: ENRICHMENT (worker-enrichment)
────────────────────────────────────────
  Task: ingest.enrich_alert()
  
  Purpose:
    - Generate structured AI insights via Mistral 7B Instruct
    - Extract threat patterns, severity assessments, recommended actions
    - Store enrichment_data on alert
    - Publish real-time update to Redis Pub/Sub (socopilot:alerts channel)
    - Update status: enriched
  
  Input:
    {
      "tenant_id": "uuid",
      "alert_id": "uuid",
      "raw_event_id": "uuid",
      "correlation_id": "trace-id",
      "title": "Alert Title",
      "description": "Alert Description"
    }
  
  Output:
    {
      "alert_id": "uuid",
      "status": "enriched",
      "insights": {
        "severity_assessment": "high",
        "threat_actor": "APT28",
        "recommended_action": "Isolate host and investigate...",
        "false_positive_likelihood": 0.1,
        "additional_iocs": ["192.168.1.100", "malware.exe"]
      }
    }
  
  Ollama Integration:
    - Model: mistral:7b-instruct
    - Endpoint: http://ollama:11434/api/generate
    - Temperature: 0.3 (deterministic)
    - Timeout: 120s per request
    - Uses async httpx.AsyncClient
    - Output: JSON-formatted insights (with fallback to raw text)
  
  Redis Pub/Sub:
    - Channel: "socopilot:alerts"
    - Event type: "alert_enriched"
    - Payload: alert_id, tenant_id, insights dict
    - Purpose: Real-time UI updates + external integrations
  
  Error Handling:
    - Max 2 retries with exponential backoff
    - Validation errors → DLQ
    - LLM/Redis failures → logged warning, task continues (non-fatal)
  
  Dependencies:
    - NormalizedAlert model (no schema changes)
    - OllamaClient (async HTTP)
    - RedisPublisher (sync wrapper around redis-py)

──────────────────────────────────────────────────────────────────────

TASK CHAINING (Celery Signatures)
──────────────────────────────────
  
  The pipeline uses Celery's signature() to chain tasks:
  
    capture_raw_event()
        ↓ (creates signature)
    process_alert()
        ↓ (creates signature)
    enrich_alert()
        ↓ (publishes to Redis)
    [Complete]
  
  Each task returns the next stage's task ID, allowing:
  - Loose coupling: stages can fail independently
  - Observability: track pipeline progress via task IDs
  - Flexibility: skip stages or route to different workers


TENANT ISOLATION & SECURITY
════════════════════════════

All stages validate tenant_id:
  1. Parse tenant_id as UUID (ValueError if invalid)
  2. Retrieve records and verify tenant_id matches
  3. Reject cross-tenant access with ValueError
  4. Log all auth failures with correlation_id

Example:
  ✓ Task 1 creates RawEvent with tenant_id="ABC..."
  ✓ Task 2 retrieves RawEvent and validates tenant_id="ABC..."
  ✗ If Task 2 gets mismatched tenant_id → ValueError → DLQ


DATABASE SESSION MANAGEMENT
════════════════════════════

Workers use synchronous sessions to avoid event loop conflicts:

  def get_db_session() -> Session:
      return SessionLocal()  # sync sessionmaker
  
  @celery_app.task
  def my_task():
      db = get_db_session()
      try:
          repo = IngestRepository(db)  # sync repository
          ...
      finally:
          db.close()
  
Benefits:
  - No async/await in worker task body (Celery limitation)
  - Explicit session lifecycle (no implicit scoping issues)
  - Async HTTP calls isolated to OllamaClient context manager
  - Compatible with existing IngestRepository (no refactoring)


FAILURE HANDLING & DLQ
══════════════════════

Failed events are routed to IngestFailure table:

  Fields:
    - tenant_id: Tenant UUID (nullable for pre-capture failures)
    - correlation_id: Trace ID for investigation
    - raw_event_id: RawEvent UUID (nullable)
    - stage: Pipeline stage name ("ingest.capture", "ingest.process", etc.)
    - error_message: Human-readable error
    - payload: Original payload (for replay/debugging)
    - error_detail: Structured error info (e.g., {"exception": "ValueError"})

  Retry Strategy:
    - Stage 1 (capture): 3 retries, backoff = 2^retry seconds
    - Stage 2 (process): 3 retries, backoff = 2^retry seconds
    - Stage 3 (enrich): 2 retries, backoff = 2^retry seconds
    
    - Max backoff: 2^3 = 8 seconds (stage 1-2), 2^2 = 4 seconds (stage 3)
    - After max retries exhausted: record to DLQ, raise exception

  Replay:
    SELECT * FROM ingest_failure WHERE stage = 'ingest.process'
    AND created_at > NOW() - INTERVAL '1 hour';
    
    # Manually replay via task ID:
    from app.workers.tasks.ingest_pipeline import process_alert
    process_alert.delay(
      tenant_id=row.tenant_id,
      raw_event_id=row.raw_event_id,
      correlation_id=row.correlation_id,
      payload=row.payload
    )


EXTERNAL INTEGRATIONS
══════════════════════

1. OLLAMA (nomic-embed-text + mistral:7b-instruct)
   ────────────────────────────────────────────────
   
   Configuration:
     - Endpoint: http://ollama:11434
     - Models: nomic-embed-text, mistral:7b-instruct
     - Timeout: 120s per request
   
   Health Check:
     curl http://localhost:11434/api/tags
     # Should list available models
   
   Usage in Code:
     async with OllamaClient() as client:
         embedding = await client.get_embedding(text)
         insights = await client.generate_insights(prompt)
   
   Fallback:
     - Embedding failure → empty vector, logged warning
     - LLM failure → {"error": "..."}, non-fatal
   
   Performance:
     - nomic-embed-text: ~50ms per request (CPU)
     - mistral:7b-instruct: ~5-10s per request (GPU-accelerated if available)

2. REDIS (Pub/Sub)
   ───────────────
   
   Configuration:
     - Host: redis
     - Port: 6379
     - DB: 0
     - Channel: socopilot:alerts
   
   Events Published:
     - alert_created: When alert is first ingested
     - alert_enriched: When enrichment completes
     - alert_status_updated: When status changes
   
   Payload Example:
     {
       "event": "alert_enriched",
       "alert_id": "uuid",
       "tenant_id": "uuid",
       "insights": {
         "severity_assessment": "high",
         "threat_actor": "APT28",
         ...
       }
     }
   
   Subscribers:
     - Frontend WebSocket connections (real-time alerts)
     - External SIEM integrations
     - Alerting services (Slack, PagerDuty, etc.)
   
   Connection Handling:
     publisher = RedisPublisher()
     publisher.connect()  # Validates connectivity
     publisher.publish_alert_enriched(...)
     publisher.disconnect()


USAGE EXAMPLES
══════════════

1. Manual Pipeline Trigger
   ────────────────────────
   
   from app.workers.tasks.ingest_pipeline import capture_raw_event
   
   result = capture_raw_event.delay(
       tenant_id="50c02278-977e-4139-bc9e-9c38b905a12f",
       correlation_id="trace-12345",
       source_label="webhook",
       payload={
           "source": "CrowdStrike",
           "title": "Suspicious Process Execution",
           "description": "mimikatz.exe detected",
           "severity": "critical"
       },
       client_ip="192.168.1.100"
   )
   
   print(f"Task ID: {result.id}")
   print(f"Status: {result.status}")

2. Monitor Pipeline Progress
   ──────────────────────────
   
   from celery.result import AsyncResult
   
   task = AsyncResult(task_id)
   print(f"State: {task.state}")  # PENDING, STARTED, SUCCESS, FAILURE
   print(f"Result: {task.result}")  # Return dict or exception

3. Replay Failed Event
   ────────────────────
   
   from app.db.models.ingest_failure import IngestFailure
   from app.workers.tasks.ingest_pipeline import process_alert
   
   failure = db.query(IngestFailure).filter(...).first()
   
   # Re-enqueue for processing
   task = process_alert.delay(
       tenant_id=str(failure.tenant_id),
       raw_event_id=str(failure.raw_event_id),
       correlation_id=failure.correlation_id,
       payload=failure.payload
   )

4. Custom Task Chain (e.g., skip enrichment)
   ─────────────────────────────────────────
   
   from celery import signature, chain
   
   # Skip enrichment, go straight to alert creation
   pipeline = chain(
       signature("ingest.capture_raw_event", {...}),
       signature("ingest.process_alert", {...})
   )
   result = pipeline.apply_async()


OBSERVABILITY & LOGGING
════════════════════════

All tasks log structured events (JSON) with:
  - event: Event type (e.g., "raw_event_captured")
  - level: Log level (info, warning, error)
  - timestamp: ISO 8601 timestamp
  - correlation_id: Trace ID for correlation
  - tenant_id: Tenant UUID (if applicable)
  - Other context (alert_id, error, etc.)

Example Log Output:
  {"event": "raw_event_captured", "raw_event_id": "...", "tenant_id": "...", ...}
  {"event": "alert_normalized", "title": "...", "tenant_id": "...", ...}
  {"event": "alert_enriched", "alert_id": "...", "insights_keys": [...], ...}
  {"event": "failure_recorded", "stage": "ingest.process", "correlation_id": "...", ...}

Query Logs (ELK / CloudWatch):
  # Find all events for a tenant
  correlation_id="trace-12345"
  
  # Find all failures in a stage
  event="failure_recorded" AND stage="ingest.process"
  
  # Timeline of alert lifecycle
  alert_id="uuid" | sort timestamp


DEPLOYMENT & CONFIGURATION
════════════════════════════

1. Environment Variables (.env)
   ────────────────────────────
   DATABASE_URL=postgresql+asyncpg://...
   REDIS_HOST=redis
   REDIS_PORT=6379
   CELERY_BROKER_URL=redis://redis:6379/0
   # (Ollama endpoint is hardcoded to http://ollama:11434)

2. Docker Compose Services
   ───────────────────────
   services:
     postgres: (stores RawEvent, NormalizedAlert, IngestFailure)
     redis: (message broker + Pub/Sub)
     ollama: (embeddings + LLM inference)
     celery-worker-ingest: (stage 1)
     celery-worker-processing: (stage 2)
     celery-worker-enrichment: (stage 3)
     api: (FastAPI serving endpoints)
     frontend: (UI consuming Redis events)

3. Worker Configuration
   ────────────────────
   # Start dedicated workers per stage (optional, can share one worker)
   
   # Worker 1: Capture + Processing
   celery -A app.workers.celery_app worker \
     -l info \
     -Q ingest,processing \
     -c 4 \
     --max-tasks-per-child=1000
   
   # Worker 2: Enrichment (GPU-bound, fewer concurrency)
   celery -A app.workers.celery_app worker \
     -l info \
     -Q enrichment \
     -c 2 \
     --max-tasks-per-child=100


TESTING
════════

1. Unit Tests for Pipeline
   ───────────────────────
   
   # Mock OllamaClient
   from unittest.mock import AsyncMock, patch
   
   @patch('app.workers.tasks.ingest_pipeline.OllamaClient')
   async def test_process_alert_with_embedding(mock_ollama):
       mock_ollama.return_value.__aenter__.return_value.get_embedding.return_value = [0.1] * 768
       
       result = process_alert(...)
       assert result['status'] == 'normalized'
   
   # Mock RedisPublisher
   @patch('app.workers.tasks.ingest_pipeline.RedisPublisher')
   def test_enrich_alert_publishes(mock_redis):
       mock_redis.return_value.publish_alert_enriched.return_value = 1
       
       result = enrich_alert(...)
       mock_redis.return_value.connect.assert_called_once()

2. Integration Tests
   ─────────────────
   # Start actual Celery worker + Redis + Ollama
   # Trigger pipeline and verify:
   # - RawEvent created
   # - NormalizedAlert created with embedding
   # - Redis message published
   # - IngestFailure empty (no errors)


TROUBLESHOOTING
════════════════

Issue: Ollama connection refused
───────────────────────────────
  Fix:
    1. Verify Ollama running: curl http://ollama:11434/api/tags
    2. Check network: docker network ls, docker network inspect <network>
    3. Restart Ollama: docker restart ollama
  
  Fallback: Tasks continue with empty embeddings/insights (non-fatal)

Issue: Redis Pub/Sub not delivering messages
──────────────────────────────────────────
  Fix:
    1. Check Redis running: redis-cli ping
    2. Verify channel: redis-cli SUBSCRIBE socopilot:alerts
    3. Check network connectivity between worker and Redis
  
  Fallback: Task completes without pub/sub (non-fatal)

Issue: Tasks stuck in PENDING state
──────────────────────────────────
  Fix:
    1. Check Celery worker running: celery -A app.workers.celery_app inspect active
    2. Check message broker (Redis): redis-cli INFO
    3. Check logs for worker errors
    4. Verify DATABASE_URL in worker environment

Issue: IngestFailure table growing rapidly
─────────────────────────────────────────
  Fix:
    1. Query: SELECT stage, COUNT(*) FROM ingest_failure GROUP BY stage
    2. Check logs for common error patterns
    3. Replay failed batches after fixing root cause
    4. Consider increasing retry delays or max_retries


REFERENCES
═══════════

- Celery Task Guide: https://docs.celeryproject.org/en/stable/userguide/tasks.html
- Ollama API: https://github.com/ollama/ollama/blob/main/docs/api.md
- Redis Pub/Sub: https://redis.io/docs/latest/develop/interact/pubsub/
- SQLAlchemy Sessions: https://docs.sqlalchemy.org/en/20/orm/session.html
"""
