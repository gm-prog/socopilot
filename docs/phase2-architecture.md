# Phase 2 Architecture

## Pipeline (decoupled)

```
INGEST (Phase 1)                    POST-INGEST (Phase 2, async)
─────────────────                   ─────────────────────────────
Webhook → RawEvent                  extract_iocs → alert_iocs
  → normalize                         ↓
  → dedup → NormalizedAlert         dispatch_enrichment_jobs
                                      ↓ (per provider, enrichment queue)
                                    AbuseIPDB / stubs → enrichment_results

Parallel (non-blocking):
  • index_alert_opensearch
  • generate_alert_embedding → alert_embeddings
```

## Storage

| Layer | Role |
|-------|------|
| PostgreSQL | System of record (alerts, IOCs, enrichment, DLQ) |
| OpenSearch | Optional search index (graceful fallback) |
| alert_embeddings | Semantic foundation (PG JSONB vectors) |

## Replay

`POST /api/v1/replay/{raw_event_id}` re-runs ingest chain from immutable `raw_events.payload`.
