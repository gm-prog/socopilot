#!/usr/bin/env bash
set -e

echo "PHASE 2 HARDENING CHECK"

echo "checking legacy pipeline"
grep -R --include="*.py" "dispatch_ingest_pipeline" app && exit 1

echo "checking direct persistence bypass"
BAD=$(grep -R --include="*.py" "repo\.persist_alert" app | grep -v "gateway.py" || true)

if [ -n "$BAD" ]; then
  echo "$BAD"
  exit 1
fi

echo "OK"
