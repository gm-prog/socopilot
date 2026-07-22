#!/usr/bin/env bash
set -e

echo "CHECKING ARCHITECTURE RULES"

echo "1. legacy pipeline"
grep -R --include="*.py" "dispatch_ingest_pipeline" app && exit 1

echo "2. repo writes outside gateway"
BAD=$(grep -R --include="*.py" "repo\.persist_alert" app | grep -v "gateway.py" || true)

if [ -n "$BAD" ]; then
  echo "$BAD"
  exit 1
fi

echo "OK"
