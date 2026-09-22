# Start SOCoPilot development stack
param(
    [switch]$Build,
    [switch]$PullModels
)

$Root = Split-Path -Parent $PSScriptRoot
Set-Location $Root

if (-not (Test-Path ".env")) {
    Copy-Item ".env.example" ".env"
    # Generate a strong SECRET_KEY so local/dev never runs on a placeholder.
    # The value is written directly into .env and never displayed.
    $bytes = New-Object byte[] 32
    [System.Security.Cryptography.RandomNumberGenerator]::Create().GetBytes($bytes)
    $generatedKey = ($bytes | ForEach-Object { $_.ToString("x2") }) -join ""
    (Get-Content ".env") -replace '^SECRET_KEY=.*$', "SECRET_KEY=$generatedKey" | Set-Content ".env"
    Write-Host "Created .env from .env.example with a freshly generated SECRET_KEY"
    Write-Host "Seed admin passwords (backend/scripts/seed_admin.py) still come from"
    Write-Host "SEED_ADMIN_PASSWORD / SEED_ADMIN2_PASSWORD or are randomized - see docs/SECURITY_RUNBOOK.md"
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
