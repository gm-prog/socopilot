# Rebuild frontend after UI/API connectivity changes
$Root = Split-Path -Parent $PSScriptRoot
Set-Location $Root

$env:CACHEBUST = [DateTimeOffset]::UtcNow.ToUnixTimeSeconds().ToString()
Write-Host "Rebuilding frontend (CACHEBUST=$($env:CACHEBUST))..." -ForegroundColor Cyan

docker compose -f docker/docker-compose.yml build --no-cache frontend
docker compose -f docker/docker-compose.yml up -d --force-recreate frontend api

Write-Host "Testing proxied health via frontend nginx..." -ForegroundColor Cyan
Start-Sleep -Seconds 3
try {
    $h = Invoke-RestMethod -Uri "http://localhost:3000/api/v1/health" -UseBasicParsing
    Write-Host "OK: $($h.status) — $($h.service) v$($h.version)" -ForegroundColor Green
} catch {
    Write-Host "FAIL: $_" -ForegroundColor Red
    Write-Host "Also try: http://127.0.0.1:3000/api/v1/health" -ForegroundColor Yellow
}
