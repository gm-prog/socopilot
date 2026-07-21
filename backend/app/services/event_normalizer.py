"""Pure event normalization for the SOC v2 ingestion pipeline."""

from __future__ import annotations

import copy
from datetime import UTC, datetime
from typing import Any


def normalize_event(event: dict[str, Any]) -> dict[str, Any]:
    """
    Standardize inbound ingest events without mutating the input.

    Output:
        {
          "source": str,
          "event_type": str,
          "payload": dict,
          "timestamp": str | None
        }
    """
    if not isinstance(event, dict):
        raise ValueError("event must be a dict")

    source = str(event.get("source") or "unknown").strip() or "unknown"
    event_type = str(
        event.get("event_type") or event.get("type") or "unknown"
    ).strip() or "unknown"

    raw_payload = event.get("payload")
    if raw_payload is None:
        raw_payload = {
            key: value
            for key, value in event.items()
            if key not in {"source", "event_type", "type", "timestamp"}
        }
    if not isinstance(raw_payload, dict):
        raw_payload = {"value": raw_payload}

    timestamp = event.get("timestamp")
    if timestamp is not None:
        timestamp = str(timestamp)
    else:
        timestamp = datetime.now(UTC).isoformat()

    return {
        "source": source,
        "event_type": event_type,
        "payload": copy.deepcopy(raw_payload),
        "timestamp": timestamp,
    }
