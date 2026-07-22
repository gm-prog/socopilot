ALTER TABLE normalized_alert ADD CONSTRAINT uq_raw_event UNIQUE (raw_event_id);
