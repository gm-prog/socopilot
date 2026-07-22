#!/usr/bin/env bash
set -e

echo "Checking legacy ingest pipeline usage in Python code only..."

# Only scan Python files
if grep -R --include="*.py" "dispatch_ingest_pipeline" app; then
  echo "❌ Legacy ingest pipeline detected in Python code"
  exit 1
fi

echo "✅ Ingest guardrails OK"
