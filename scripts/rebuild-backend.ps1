# Rebuild API + workers after backend code changes (fixes stale-route 404s)
$Root = Split-Path -Parent $PSScriptRoot
Set-Location $Root

$env:CACHEBUST = [DateTimeOffset]::UtcNow.ToUnixTimeSeconds().ToString()
Write-Host "Rebuilding backend images (CACHEBUST=$($env:CACHEBUST))..." -ForegroundColor Cyan

docker compose -f docker/docker-compose.yml build --no-cache api worker celery-beat
docker compose -f docker/docker-compose.yml up -d --force-recreate api worker celery-beat

Write-Host "Verifying ingest route in container..." -ForegroundColor Cyan
docker compose -f docker/docker-compose.yml exec api python -c "from app.main import app; assert any(r.path=='/api/v1/ingest/alerts' for r in app.routes), 'ingest route missing'; print('OK: /api/v1/ingest/alerts registered')"
