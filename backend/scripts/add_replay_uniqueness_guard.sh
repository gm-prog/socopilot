#!/usr/bin/env bash
set -e

echo "Adding DB-level replay safety constraint..."

grep -R "raw_event_id" app/db/models/normalized_alert.py || true
