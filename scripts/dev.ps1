# Start SOCoPilot development stack
param(
    [switch]$Build,
    [switch]$PullModels
)

$Root = Split-Path -Parent $PSScriptRoot
Set-Location $Root

if (-not (Test-Path ".env")) {
    Copy-Item ".env.example" ".env"
    Write-Host "Created .env from .env.example"
}

if ($Build) {
    $env:CACHEBUST = [DateTimeOffset]::UtcNow.ToUnixTimeSeconds().ToString()
    docker compose -f docker/docker-compose.yml build api worker celery-beat
    docker compose -f docker/docker-compose.yml up -d --force-recreate api worker celery-beat
}

docker compose -f docker/docker-compose.yml up -d

Write-Host "Waiting for API..." -ForegroundColor Cyan
$max = 60
for ($i = 0; $i -lt $max; $i++) {
    try {
        $r = Invoke-WebRequest -Uri "http://localhost:8000/api/v1/health" -UseBasicParsing -TimeoutSec 3
        if ($r.StatusCode -eq 200) { break }
    } catch { Start-Sleep -Seconds 2 }
}

if ($PullModels) {
    Write-Host "Pulling Ollama models (this may take a while)..." -ForegroundColor Cyan
    docker compose -f docker/docker-compose.yml run --rm ollama-init
}

Write-Host ""
Write-Host "SOCoPilot is running:" -ForegroundColor Green
Write-Host "  API:        http://localhost:8000/docs"
Write-Host "  Frontend:   http://localhost:3000"
Write-Host "  Grafana:    http://localhost:3001  (admin / socopilot)"
Write-Host "  Flower:     http://localhost:5555"
Write-Host "  Prometheus: http://localhost:9090"
