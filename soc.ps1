param(
    [string]$Command
)

$BASE_URL = "http://localhost:8000"

function Login {

    Write-Host "Logging in..."

    $body = @{
        email = "admin@test.com"
        password = "admin123"
    } | ConvertTo-Json

    try {

        $response = Invoke-RestMethod `
            -Uri "$BASE_URL/api/v1/auth/login" `
            -Method POST `
            -ContentType "application/json" `
            -Body $body

        $token = $response.access_token

        if (-not $token) {
            Write-Host "Login failed"
            return
        }

        Set-Content -Path ".soc_token" -Value $token
# === AUTO FIX FRONTEND LOGIN ===
$frontendTokenPath = "frontend\public\token.txt"

if (!(Test-Path "frontend\public")) {
    New-Item -ItemType Directory -Path "frontend\public" | Out-Null
}

Set-Content -Path $frontendTokenPath -Value $token
Write-Host "Frontend token synced"

        Write-Host ""
        Write-Host "Token saved"
        Write-Host ""
        Write-Host $token

    } catch {

        Write-Host ""
        Write-Host "Request failed"
        Write-Host $_
    }
}

function Me {

    if (!(Test-Path ".soc_token")) {
        Write-Host "No token found. Run login first."
        return
    }

    $token = Get-Content ".soc_token"

    try {

        Invoke-RestMethod `
            -Uri "$BASE_URL/api/v1/auth/me" `
            -Method GET `
            -Headers @{
                Authorization = "Bearer $token"
            }

    } catch {

        Write-Host ""
        Write-Host "Request failed"
        Write-Host $_
    }
}

function Test-Ingest {

    if (!(Test-Path ".soc_token")) {
        Write-Host "No token found. Run login first."
        return
    }

    $token = Get-Content ".soc_token"

    $body = @{
        title = "Suspicious PowerShell Activity"
        severity = "high"
        source = "soc-cli"
        description = "Encoded PowerShell command detected"
    } | ConvertTo-Json

    try {

        $response = Invoke-RestMethod `
            -Uri "$BASE_URL/api/v1/ingest/alerts" `
            -Method POST `
            -ContentType "application/json" `
            -Headers @{
                Authorization = "Bearer $token"
            } `
            -Body $body

        Write-Host ""
        Write-Host "Alert ingested successfully"
        Write-Host ""

        $response | ConvertTo-Json -Depth 10

    } catch {

        Write-Host ""
        Write-Host "Ingest failed"
        Write-Host $_
    }
}

switch ($Command) {

    "login" {
        Login
    }

    "me" {
        Me
    }

    "test-ingest" {
        Test-Ingest
    }

    default {

        Write-Host ""
        Write-Host "Available commands:"
        Write-Host ""

        Write-Host ".\soc.ps1 login"
        Write-Host ".\soc.ps1 me"
        Write-Host ".\soc.ps1 test-ingest"
    }
}