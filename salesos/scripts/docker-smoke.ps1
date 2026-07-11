<#
.SYNOPSIS
  SalesOS Docker E2E Smoke Test
.DESCRIPTION
  Builds, starts, and tests all SalesOS Docker services end-to-end.
  Usage: .\docker-smoke.ps1
#>

param(
    [string]$BackendUrl = "http://localhost:8000",
    [string]$FrontendUrl = "http://localhost:3000",
    [int]$BuildTimeoutSec = 300,
    [int]$HealthMaxRetries = 30,
    [int]$HealthRetryInterval = 10,
    [string]$ApiUrl = "http://localhost:8000"
)

$ErrorActionPreference = "Stop"
$script:passed = 0
$script:failed = 0
$script:results = @()

function Write-Step {
    param([string]$Message)
    Write-Host "`n─── $Message ───" -ForegroundColor Yellow
}

function Write-Result {
    param([string]$Name, [string]$Status, [string]$Detail = "")
    $color = if ($Status -eq "PASS") { "Green" } else { "Red" }
    $detailStr = if ($Detail) { " — $Detail" } else { "" }
    Write-Host "  [$Status] $Name$detailStr" -ForegroundColor $color
}

function Check-Docker {
    Write-Step "Checking Docker"
    try {
        $info = docker info --format "{{.ServerVersion}}" 2>$null
        if (-not $info) { throw "no output" }
        Write-Result "Docker Engine" "PASS" "v$info"
        $composeVer = docker compose version 2>$null
        if (-not $composeVer) { throw "no compose output" }
        Write-Result "Docker Compose" "PASS" "$composeVer"
    } catch {
        Write-Result "Docker" "FAIL" "Docker not running or not installed"
        throw "Docker is required. Install Docker Desktop and try again."
    }
}

function Invoke-DockerComposeBuild {
    Write-Step "Building services"
    Write-Host "  Build timeout: ${BuildTimeoutSec}s"
    $sw = [System.Diagnostics.Stopwatch]::StartNew()
    try {
        $output = docker compose build 2>&1
        $sw.Stop()
        $lastLine = $output | Select-Object -Last 1
        if ($LASTEXITCODE -ne 0) {
            throw "Build failed (exit $LASTEXITCODE): $lastLine"
        }
        Write-Result "Docker Compose Build" "PASS" "$($sw.Elapsed.TotalSeconds.ToString('F1'))s"
    } catch {
        Write-Result "Docker Compose Build" "FAIL"
        Write-Host "  Build output:" -ForegroundColor DarkRed
        $output | ForEach-Object { Write-Host "    $_" -ForegroundColor DarkRed }
        throw $_.Exception.Message
    }
}

function Invoke-DockerComposeUp {
    Write-Step "Starting services"
    try {
        $output = docker compose up -d 2>&1
        if ($LASTEXITCODE -ne 0) {
            throw "docker compose up failed (exit $LASTEXITCODE)"
        }
        Write-Result "Services Started" "PASS"
    } catch {
        Write-Result "Services Start" "FAIL"
        throw $_.Exception.Message
    }
}

function Wait-ForServiceHealthy {
    param(
        [string]$ServiceName,
        [string]$DisplayName,
        [int]$MaxRetries = $HealthMaxRetries,
        [int]$Interval = $HealthRetryInterval
    )
    Write-Host "  Waiting for $DisplayName to be healthy..." -NoNewline
    for ($i = 1; $i -le $MaxRetries; $i++) {
        $status = docker compose ps --format "{{.Status}}" $ServiceName 2>$null
        if ($status -and $status -match "healthy") {
            Write-Host " healthy (attempt $i)" -ForegroundColor Green
            return $true
        }
        if ($status -and $status -match "unhealthy") {
            Write-Host " unhealthy (attempt $i)" -ForegroundColor Red
            return $false
        }
        if ($i % 5 -eq 0) { Write-Host "." -NoNewline }
        Start-Sleep -Seconds $Interval
    }
    Write-Host " timeout" -ForegroundColor Red
    return $false
}

function Invoke-ApiTest {
    param(
        [string]$Name,
        [string]$Method = "GET",
        [string]$Url,
        [string]$Body = "",
        [string]$AuthToken = "",
        [string]$TenantId = "",
        [int]$ExpectedStatus = 200,
        [string]$ExpectedContent = ""
    )
    try {
        $params = @{
            Uri = $Url
            Method = $Method
            UseBasicParsing = $true
            TimeoutSec = 15
            SkipCertificateCheck = $true
            ContentType = "application/json"
        }
        $headers = @{}
        if ($AuthToken) { $headers["Authorization"] = "Bearer $AuthToken" }
        if ($TenantId) { $headers["X-Tenant-Id"] = $TenantId }
        if ($headers.Count -gt 0) { $params["Headers"] = $headers }
        if ($Body -and ($Method -eq "POST" -or $Method -eq "PUT" -or $Method -eq "PATCH")) {
            $params["Body"] = $Body
        }
        $response = Invoke-WebRequest @params
        $status = $response.StatusCode
        $content = $response.Content
        if ($status -ne $ExpectedStatus) {
            throw "Expected status $ExpectedStatus, got $status"
        }
        if ($ExpectedContent -and $content -notmatch $ExpectedContent) {
            throw "Expected content to match '$ExpectedContent'"
        }
        $script:passed++
        Write-Result "API $Name" "PASS" "$status"
        return $content
    } catch {
        $script:failed++
        $errMsg = $_.Exception.Message
        Write-Result "API $Name" "FAIL" $errMsg
        return $null
    }
}

function Test-Frontend {
    Write-Step "Testing Frontend"
    try {
        $response = Invoke-WebRequest -Uri $FrontendUrl -UseBasicParsing -TimeoutSec 15 -SkipCertificateCheck
        if ($response.StatusCode -eq 200) {
            $script:passed++
            Write-Result "Frontend" "PASS" "200"
        } else {
            throw "Status $($response.StatusCode)"
        }
    } catch {
        $script:failed++
        Write-Result "Frontend" "FAIL" $_.Exception.Message
    }
}

function Show-FailingLogs {
    Write-Step "Failing service logs"
    $services = docker compose ps --format "{{.Name}}" 2>$null
    foreach ($svc in $services) {
        $status = docker compose ps --format "{{.Status}}" $svc 2>$null
        if ($status -and ($status -match "unhealthy" -or $status -match "exited")) {
            Write-Host "`n── Logs for $svc (status: $status) ──" -ForegroundColor DarkRed
            $logs = docker compose logs --tail=30 $svc 2>&1
            $logs | ForEach-Object { Write-Host "  $_" -ForegroundColor DarkRed }
        }
    }
}

function New-DockerSmokeTestReport {
    $total = $script:passed + $script:failed
    Write-Host "`n"
    Write-Host "╔════════════════════════════════════════════════════╗" -ForegroundColor Cyan
    Write-Host "║          SalesOS Docker E2E Smoke Results          ║" -ForegroundColor Cyan
    Write-Host "╚════════════════════════════════════════════════════╝" -ForegroundColor Cyan
    Write-Host "  Total: $total"
    Write-Host "  Passed: $($script:passed)" -ForegroundColor Green
    Write-Host "  Failed: $($script:failed)" -ForegroundColor $(if ($script:failed -eq 0) { "Green" } else { "Red" })

    $reportPath = Join-Path $PSScriptRoot "..\docs\DOCKER_SMOKE_RESULTS.json"
    $report = @{
        timestamp = (Get-Date -Format "yyyy-MM-ddTHH:mm:ssZ")
        total = $total
        passed = $script:passed
        failed = $script:failed
    }
    $report | ConvertTo-Json | Set-Content -Path $reportPath -Encoding UTF8
    Write-Host "  Report saved to: $reportPath" -ForegroundColor Gray
}

# ─────────────────────────────────────────────────────────────────
# Main
# ─────────────────────────────────────────────────────────────────
Write-Host "╔════════════════════════════════════════════════════╗" -ForegroundColor Cyan
Write-Host "║     SalesOS Docker E2E Smoke Test v1.0            ║" -ForegroundColor Cyan
Write-Host "╚════════════════════════════════════════════════════╝" -ForegroundColor Cyan
Write-Host ""

try {
    # Step 1: Check Docker
    Check-Docker

    # Step 2: Build
    Invoke-DockerComposeBuild

    # Step 3: Start services
    Invoke-DockerComposeUp

    # Step 4: Wait for core infrastructure
    Write-Step "Waiting for infrastructure"
    $infraServices = @(
        @{Name="postgres"; Display="PostgreSQL"},
        @{Name="redis"; Display="Redis"},
        @{Name="neo4j"; Display="Neo4j"}
    )
    foreach ($svc in $infraServices) {
        $healthy = Wait-ForServiceHealthy -ServiceName $svc.Name -DisplayName $svc.Display
        if (-not $healthy) {
            Write-Result "Infrastructure: $($svc.Display)" "FAIL" "Not healthy"
            Show-FailingLogs
            throw "Infrastructure service $($svc.Name) failed to become healthy"
        }
    }

    # Step 5: Wait for backend
    Write-Step "Waiting for backend"
    $backendHealthy = Wait-ForServiceHealthy -ServiceName "backend" -DisplayName "Backend API"
    if (-not $backendHealthy) {
        Show-FailingLogs
        throw "Backend failed to become healthy"
    }

    # Step 6: Wait for frontend
    Write-Step "Waiting for frontend"
    $frontendHealthy = Wait-ForServiceHealthy -ServiceName "frontend" -DisplayName "Frontend" -MaxRetries 20 -Interval 10
    if (-not $frontendHealthy) {
        Write-Result "Frontend" "WARN" "Not marked healthy, will attempt HTTP test"
    }

    # Step 7: Unauthenticated API tests
    Write-Step "Unauthenticated API tests"
    Invoke-ApiTest -Name "Ping" -Method GET -Url "$BackendUrl/ping" -ExpectedStatus 200 -ExpectedContent "pong"
    Invoke-ApiTest -Name "Health" -Method GET -Url "$BackendUrl/health" -ExpectedStatus 200 -ExpectedContent "status"

    # Step 8: Register test user & get token
    Write-Step "Registering test user"
    $testEmail = "smoke-$(Get-Random -Minimum 10000 -Maximum 99999)@salesos-test.io"
    $testPassword = "TestPass123!"
    $registerBody = @{
        email = $testEmail
        password = $testPassword
        full_name = "Smoke Tester"
    } | ConvertTo-Json

    try {
        $regParams = @{
            Uri = "$BackendUrl/api/v1/identity/register"
            Method = "POST"
            Body = $registerBody
            ContentType = "application/json"
            UseBasicParsing = $true
            TimeoutSec = 15
            SkipCertificateCheck = $true
        }
        $regResponse = Invoke-WebRequest @regParams
        if ($regResponse.StatusCode -eq 201) {
            $regData = $regResponse.Content | ConvertFrom-Json
            $script:authToken = $regData.access_token
            $script:tenantId = $regData.tenant_id
            $script:passed++
            Write-Result "Register Test User" "PASS" "201"
        } else {
            throw "Status $($regResponse.StatusCode)"
        }
    } catch {
        $script:failed++
        $errMsg = $_.Exception.Message
        Write-Result "Register Test User" "FAIL" $errMsg
        Write-Host "  Skipping authenticated tests..." -ForegroundColor DarkYellow
        $script:authToken = $null
    }

    # Step 9: Authenticated API tests
    if ($script:authToken) {
        Write-Step "Authenticated API tests"

        # Decision evaluate
        $evalBody = @{
            tenant_id = $script:tenantId
            actor_id = "smoke-tester"
            entity_id = "test-entity-001"
            entity_type = "opportunity"
            opportunity_id = "opp-smoke-001"
            company_id = "comp-smoke-001"
            signal_id = "signal-manual"
            metadata = @{
                source = "docker-smoke-test"
            }
        } | ConvertTo-Json
        Invoke-ApiTest -Name "Decision Evaluate" -Method POST -Url "$BackendUrl/api/v1/decision/evaluate" -Body $evalBody -AuthToken $script:authToken -TenantId $script:tenantId -ExpectedStatus 200 -ExpectedContent "decisionId"

        # Decision rules
        Invoke-ApiTest -Name "Decision Rules" -Method GET -Url "$BackendUrl/api/v1/decision/rules" -AuthToken $script:authToken -TenantId $script:tenantId -ExpectedStatus 200
    } else {
        Write-Step "Authenticated API tests (skipped)"
    }

    # Step 10: Frontend test
    Test-Frontend

    # Step 11: Per-service status summary
    Write-Step "Service status"
    $allServices = docker compose ps --format "table {{.Name}}\t{{.Status}}\t{{.Ports}}" 2>$null
    if ($allServices) { $allServices | ForEach-Object { Write-Host "  $_" } }

} catch {
    Write-Host "`n[FATAL] $($_.Exception.Message)" -ForegroundColor Red
    Show-FailingLogs
} finally {
    New-DockerSmokeTestReport
}

if ($script:failed -gt 0) {
    exit 1
}
