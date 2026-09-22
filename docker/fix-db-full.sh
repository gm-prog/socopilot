#!/bin/bash

set -e

echo "🧠 Step 1: Fixing postgres volume mount properly..."

# Force correct mount (overwrite postgres section safely)
awk '
BEGIN {in_pg=0}

/postgres:/ {in_pg=1}

/^[a-zA-Z]/ && !/postgres:/ {in_pg=0}

{
    if(in_pg==1 && $0 ~ /volumes:/) {
        print $0
        print "      - ./init-db.sql:/docker-entrypoint-initdb.d/init-db.sql:ro"
        next
    }
    print $0
}
' docker-compose.yml > docker-compose.fixed.yml

mv docker-compose.fixed.yml docker-compose.yml

echo "🧹 Rebuilding everything clean..."

docker-compose down -v

docker-compose up -d

echo "⏳ Waiting for Postgres..."
sleep 15

echo "📊 Checking if users table exists..."
docker-compose exec postgres psql -U socopilot -d socopilot -c "\dt"

echo "📂 Checking init scripts inside container..."
docker-compose exec postgres ls /docker-entrypoint-initdb.d || true

echo "✅ DONE"
