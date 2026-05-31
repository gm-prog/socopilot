# Full Phase 2 rebuild — backend + frontend + OpenSearch
$Root = Split-Path -Parent $PSScriptRoot
Set-Location $Root

$env:CACHEBUST = [DateTimeOffset]::UtcNow.ToUnixTimeSeconds().ToString()
Write-Host "Rebuilding Phase 2 stack..." -ForegroundColor Cyan

docker compose -f docker/docker-compose.yml build --no-cache api worker celery-beat frontend
docker compose -f docker/docker-compose.yml up -d --force-recreate api worker celery-beat frontend opensearch

Write-Host "Waiting for services..." -ForegroundColor Cyan
Start-Sleep -Seconds 20

docker compose -f docker/docker-compose.yml exec api alembic upgrade head
Write-Host "Migration status:" -ForegroundColor Cyan
docker compose -f docker/docker-compose.yml exec api alembic current

Write-Host "`nRoute check:" -ForegroundColor Cyan
docker compose -f docker/docker-compose.yml exec api python -c "from app.main import app; print([r.path for r in app.routes if 'ingest' in r.path or 'replay' in r.path or 'search' in r.path][:8])"

Invoke-RestMethod http://localhost:3000/api/v1/health | ConvertTo-Json
