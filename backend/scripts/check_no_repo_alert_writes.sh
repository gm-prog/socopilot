#!/usr/bin/env bash
set -e

echo "Checking direct alert writes..."

if grep -R --include="*.py" "IngestRepository(.*)\.persist_alert" app; then
  echo "❌ Direct alert repository writes detected"
  exit 1
fi

echo "✅ Single write rule enforced"
