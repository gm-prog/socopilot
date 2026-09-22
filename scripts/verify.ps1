# SOCoPilot Phase 0 verification script
$ErrorActionPreference = "Stop"

Write-Host "=== SOCoPilot Verification ===" -ForegroundColor Cyan

$checks = @(
    @{ Name = "API Health"; Url = "http://localhost:8000/api/v1/health" },
    @{ Name = "API Readiness"; Url = "http://localhost:8000/api/v1/ready" },
    @{ Name = "System Info"; Url = "http://localhost:8000/api/v1/system/info" },
    @{ Name = "Ollama Status"; Url = "http://localhost:8000/api/v1/system/ollama/status" },
    @{ Name = "Frontend"; Url = "http://localhost:3000" },
    @{ Name = "Prometheus"; Url = "http://localhost:9090/-/healthy" },
    @{ Name = "Grafana"; Url = "http://localhost:3001/api/health" },
    @{ Name = "Flower"; Url = "http://localhost:5555" }
)

$failed = 0
foreach ($check in $checks) {
    try {
        $resp = Invoke-WebRequest -Uri $check.Url -UseBasicParsing -TimeoutSec 15
        if ($resp.StatusCode -ge 200 -and $resp.StatusCode -lt 400) {
            Write-Host "[OK] $($check.Name)" -ForegroundColor Green
        } else {
            Write-Host "[FAIL] $($check.Name) - HTTP $($resp.StatusCode)" -ForegroundColor Red
            $failed++
        }
    } catch {
        Write-Host "[FAIL] $($check.Name) - $($_.Exception.Message)" -ForegroundColor Red
        $failed++
    }
}

# Celery ping via docker exec
Write-Host ""
Write-Host "Celery worker ping..." -ForegroundColor Cyan
try {
    $celeryOut = docker compose -f docker/docker-compose.yml exec -T worker celery -A app.workers.celery_app:celery_app inspect ping 2>&1
    if ($celeryOut -match "pong") {
        Write-Host "[OK] Celery worker responding" -ForegroundColor Green
    } else {
        Write-Host "[FAIL] Celery ping - $celeryOut" -ForegroundColor Red
        $failed++
    }
} catch {
    Write-Host "[FAIL] Celery - $($_.Exception.Message)" -ForegroundColor Red
    $failed++
}

Write-Host ""
if ($failed -eq 0) {
    Write-Host "All checks passed." -ForegroundColor Green
    exit 0
} else {
    Write-Host "$failed check(s) failed." -ForegroundColor Red
    exit 1
}
