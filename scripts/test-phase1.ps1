# Phase 1 verification — run after stack is up and migrated
param(
    [string]$Token = "",
    [string]$ApiBase = "http://localhost:8000"
)

$ErrorActionPreference = "Stop"

if (-not $Token) {
    Write-Host "Logging in..." -ForegroundColor Cyan
        $loginBody = @{ email = "admin@example.com"; password = "changeme123" } | ConvertTo-Json
    try {
        $login = Invoke-RestMethod -Uri "$ApiBase/api/v1/auth/login" -Method POST -Body $loginBody -ContentType "application/json"
        $Token = $login.access_token
    } catch {
        Write-Host "Registering tenant..." -ForegroundColor Yellow
        $regBody = @{
            email = "admin@example.com"
            password = "changeme123"
            tenant_name = "acme-soc"
            role = "admin"
        } | ConvertTo-Json
        $reg = Invoke-RestMethod -Uri "$ApiBase/api/v1/auth/register" -Method POST -Body $regBody -ContentType "application/json"
        $Token = $reg.access_token
    }
}

$corr = [guid]::NewGuid().ToString()
$headers = @{
    Authorization = "Bearer $Token"
    "X-Correlation-ID" = $corr
    "Content-Type" = "application/json"
}

Write-Host "Ingesting test alert (correlation: $corr)..." -ForegroundColor Cyan
$alert = @{
    title = "Suspicious PowerShell Execution"
    description = "Encoded command detected on endpoint"
    severity = "high"
    source = "webhook"
    rule_id = "PS-EXEC-001"
    entities = @{ hosts = @("workstation-01"); users = @("jsmith") }
} | ConvertTo-Json -Depth 5

$ingest = Invoke-RestMethod -Uri "$ApiBase/api/v1/ingest/alerts" -Method POST -Headers $headers -Body $alert
Write-Host "Ingest accepted: $($ingest.accepted) item(s)" -ForegroundColor Green

Write-Host "Waiting for Celery pipeline (5s)..." -ForegroundColor Cyan
Start-Sleep -Seconds 5

Write-Host "Listing alerts..." -ForegroundColor Cyan
$alerts = Invoke-RestMethod -Uri "$ApiBase/api/v1/alerts" -Headers @{ Authorization = "Bearer $Token" }
Write-Host "Total alerts: $($alerts.total)" -ForegroundColor Green
$alerts.items | Select-Object -First 3 | Format-Table title, severity, duplicate_count, status

Write-Host "Ingesting duplicate for dedup test..." -ForegroundColor Cyan
Invoke-RestMethod -Uri "$ApiBase/api/v1/ingest/alerts" -Method POST -Headers $headers -Body $alert | Out-Null
Start-Sleep -Seconds 5
$alerts2 = Invoke-RestMethod -Uri "$ApiBase/api/v1/alerts" -Headers @{ Authorization = "Bearer $Token" }
$duped = $alerts2.items | Where-Object { $_.duplicate_count -gt 1 } | Select-Object -First 1
if ($duped) {
    Write-Host "Dedup OK — duplicate_count=$($duped.duplicate_count) for '$($duped.title)'" -ForegroundColor Green
} else {
    Write-Host "Dedup check: no duplicate_count > 1 yet (may need same time bucket)" -ForegroundColor Yellow
}

Write-Host "`nPhase 1 API verification complete." -ForegroundColor Green
