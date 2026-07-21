#!/bin/bash

set -e

echo "🧨 FULL DATABASE RESET STARTING..."

# Step 1: Stop everything
docker-compose down -v

# Step 2: Safety cleanup (optional but good)
docker volume prune -f

# Step 3: Ensure correct init mount exists
if ! grep -q "docker-entrypoint-initdb.d" docker-compose.yml; then
  echo "❌ init volume missing in docker-compose.yml"
  exit 1
fi

# Step 4: Start fresh stack
docker-compose up -d

echo "⏳ Waiting for Postgres init..."
sleep 12

# Step 5: Verify tables
echo "📊 Checking DB schema..."
docker-compose exec postgres psql -U socopilot -d socopilot -c "\dt"

echo "📊 Checking users table specifically..."
docker-compose exec postgres psql -U socopilot -d socopilot -c "\d users"

echo "✅ RESET COMPLETE"
