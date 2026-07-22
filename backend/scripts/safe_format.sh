#!/bin/bash

set -e

FILE="app/workers/tasks/ingest.py"

echo "→ Formatting with black (safe AST rebuild)..."
black $FILE

echo "→ Compiling check..."
python3 -m py_compile $FILE

echo "✔ FILE IS SAFE"
