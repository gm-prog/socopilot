-- Replay Safety Lock
-- ensures idempotent alert creation

CREATE UNIQUE INDEX IF NOT EXISTS uq_normalized_alert_raw_event
ON normalized_alert (raw_event_id);
