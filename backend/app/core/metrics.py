"""Prometheus metrics for SOCoPilot pipelines."""

from prometheus_client import Counter, Histogram

INGEST_LATENCY = Histogram(
    "socopilot_ingest_latency_seconds",
    "Ingest pipeline end-to-end latency",
    ["stage"],
)

QUEUE_LATENCY = Histogram(
    "socopilot_queue_latency_seconds",
    "Celery queue wait/processing latency",
    ["queue"],
)

DEDUP_HITS = Counter(
    "socopilot_dedup_hits_total",
    "Dedup duplicate detections",
)

DEDUP_CREATES = Counter(
    "socopilot_dedup_creates_total",
    "New unique alerts created",
)

ENRICHMENT_LATENCY = Histogram(
    "socopilot_enrichment_latency_seconds",
    "Enrichment provider latency",
    ["provider"],
)

PROVIDER_FAILURES = Counter(
    "socopilot_provider_failures_total",
    "Threat intel provider failures",
    ["provider"],
)

EXTRACTION_COUNT = Counter(
    "socopilot_extraction_iocs_total",
    "IOCs extracted",
    ["ioc_type"],
)

OPENSEARCH_INDEX_LATENCY = Histogram(
    "socopilot_opensearch_index_latency_seconds",
    "OpenSearch document indexing latency",
)

EMBEDDING_LATENCY = Histogram(
    "socopilot_embedding_latency_seconds",
    "Semantic embedding generation latency",
)

DLQ_ENTRIES = Counter(
    "socopilot_dlq_entries_total",
    "Dead letter queue entries",
    ["stage"],
)
