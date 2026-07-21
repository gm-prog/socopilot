#!/bin/bash

set -e

echo "🔧 Fixing docker-compose.yml postgres init volume..."

# Backup
cp docker-compose.yml docker-compose.yml.bak

# Replace wrong volume with correct one
sed -i 's|./docker/init:/docker-entrypoint-initdb.d:ro|./init-db.sql:/docker-entrypoint-initdb.d/init-db.sql:ro|g' docker-compose.yml

echo "🧹 Restarting containers (resetting DB)..."

docker-compose down -v
docker-compose up -d

echo "⏳ Waiting for Postgres to initialize..."
sleep 10

echo "📊 Checking tables..."
docker-compose exec postgres psql -U socopilot -d socopilot -c "\dt"

echo "✅ DONE"
