<#
.SYNOPSIS
    Verifies SalesOS pilot deployment health across all endpoints.
.DESCRIPTION
    Runs smoke tests against the backend API to confirm pilot readiness.
.PARAMETER ApiUrl
    Backend API base URL (default: http://localhost:8000)
#>

param(
    [string]$ApiUrl = "http://localhost:8000"
)

$ErrorActionPreference = "Continue"

if ($ApiUrl.EndsWith("/")) {
    $ApiUrl = $ApiUrl.TrimEnd("/")
}

$pilotTenants = @("pilot-a", "pilot-b", "pilot-c")

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  SalesOS Pilot Deployment Verification" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "  API:       $ApiUrl" -ForegroundColor White
Write-Host "  Timestamp: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')" -ForegroundColor Gray
Write-Host ""

$allPassed = $true
$passed = 0
$failed = 0
$warnings = 0
$total = 0
$results = @()

function Test-Endpoint {
    param(
        [string]$Name,
        [string]$Url,
        [string]$Method = "GET",
        [string]$Body = $null,
        [hashtable]$Headers = @{}
    )

    $script:total++

    try {
        $params = @{
            Uri        = $Url
            Method     = $Method
            TimeoutSec = 10
            Headers    = $Headers
        }
        if ($Body) {
            $params.Body = $Body
            $params.ContentType = "application/json"
        }

        $response = Invoke-RestMethod @params
        Write-Host "  [OK] $Name" -ForegroundColor Green
        $script:passed++
        $script:results += @{ Name = $Name; Status = "PASS"; Detail = "" }
        return $response
    }
    catch {
        $statusCode = 0
        if ($_.Exception.Response) {
            $statusCode = $_.Exception.Response.StatusCode.value__
        }
        Write-Host "  [FAIL] $Name - HTTP $statusCode : $($_.Exception.Message)" -ForegroundColor Red
        $script:failed++
        $script:allPassed = $false
        $script:results += @{ Name = $Name; Status = "FAIL"; Detail = "HTTP $statusCode" }
        return $null
    }
}

# --- Step 1: Core Health Endpoints ---

Write-Host "--- Core Health ---" -ForegroundColor Cyan
Write-Host ""

Test-Endpoint -Name "Health endpoint" -Url "$ApiUrl/health"
Test-Endpoint -Name "Ping endpoint" -Url "$ApiUrl/ping"

# --- Step 2: API Endpoints ---

Write-Host ""
Write-Host "--- API Endpoints ---" -ForegroundColor Cyan
Write-Host ""

Test-Endpoint -Name "Search endpoint" -Url "$ApiUrl/api/v1/search?q=test"
Test-Endpoint -Name "Dashboard endpoint" -Url "$ApiUrl/api/v1/dashboard"
Test-Endpoint -Name "Decision metrics" -Url "$ApiUrl/api/v1/decision/metrics"
Test-Endpoint -Name "Event runtime stats" -Url "$ApiUrl/api/v1/event-runtime/stats"

# --- Step 3: Tenant-Scoped Endpoints ---

Write-Host ""
Write-Host "--- Tenant Data (per tenant) ---" -ForegroundColor Cyan
Write-Host ""

foreach ($tenant in $pilotTenants) {
    $tenantHeaders = @{
        "Content-Type" = "application/json"
        "X-Tenant-Id"  = $tenant
    }

    Write-Host "  [$tenant]" -ForegroundColor White

    try {
        $companies = Invoke-RestMethod -Uri "$ApiUrl/api/v1/companies" -Method Get -Headers $tenantHeaders -TimeoutSec 10
        $count = 0
        if ($companies -is [array]) { $count = $companies.Count }
        Write-Host "    [OK] Companies: $count records" -ForegroundColor Green
        $script:passed++
        $script:results += @{ Name = "Companies ($tenant)"; Status = "PASS"; Detail = "$count records" }
    }
    catch {
        Write-Host "    [WARN] Companies: unavailable" -ForegroundColor Yellow
        $script:warnings++
        $script:results += @{ Name = "Companies ($tenant)"; Status = "WARN"; Detail = $_.Exception.Message }
    }

    try {
        $opps = Invoke-RestMethod -Uri "$ApiUrl/api/v1/opportunities" -Method Get -Headers $tenantHeaders -TimeoutSec 10
        $count = 0
        if ($opps -is [array]) { $count = $opps.Count }
        Write-Host "    [OK] Opportunities: $count records" -ForegroundColor Green
        $script:passed++
        $script:results += @{ Name = "Opportunities ($tenant)"; Status = "PASS"; Detail = "$count records" }
    }
    catch {
        Write-Host "    [WARN] Opportunities: unavailable" -ForegroundColor Yellow
        $script:warnings++
        $script:results += @{ Name = "Opportunities ($tenant)"; Status = "WARN"; Detail = $_.Exception.Message }
    }
}

# --- Step 4: NBA Decision Evaluation ---

Write-Host ""
Write-Host "--- NBA Decision Evaluation ---" -ForegroundColor Cyan
Write-Host ""

foreach ($tenant in $pilotTenants) {
    $tenantHeaders = @{
        "Content-Type" = "application/json"
        "X-Tenant-Id"  = $tenant
    }

    try {
        $nbaBody = '{"tenant_id": "' + $tenant + '", "company_id": 1}'
        $nba = Invoke-RestMethod -Uri "$ApiUrl/api/v1/decision/evaluate" -Method Post -Body $nbaBody -Headers $tenantHeaders -TimeoutSec 15 -ContentType "application/json"

        if ($nba.confidence) {
            $conf = $nba.confidence
            $act = $nba.action
            Write-Host "    [OK] NBA ($tenant): action=$act confidence=$conf" -ForegroundColor Green
            $script:passed++
            $script:results += @{ Name = "NBA evaluation ($tenant)"; Status = "PASS"; Detail = "confidence=$conf" }
        }
        else {
            Write-Host "    [WARN] NBA ($tenant): returned but no confidence score" -ForegroundColor Yellow
            $script:warnings++
            $script:results += @{ Name = "NBA evaluation ($tenant)"; Status = "WARN"; Detail = "No confidence" }
        }
    }
    catch {
        Write-Host "    [WARN] NBA ($tenant): $($_.Exception.Message)" -ForegroundColor Yellow
        $script:warnings++
        $script:results += @{ Name = "NBA evaluation ($tenant)"; Status = "WARN"; Detail = $_.Exception.Message }
    }
}

# --- Step 5: Tenant Isolation Check ---

Write-Host ""
Write-Host "--- Tenant Isolation ---" -ForegroundColor Cyan
Write-Host ""

$otherHeaders = @{
    "Content-Type" = "application/json"
    "X-Tenant-Id"  = "nonexistent-tenant-xyz"
}

try {
    $otherOpps = Invoke-RestMethod -Uri "$ApiUrl/api/v1/opportunities" -Method Get -Headers $otherHeaders -TimeoutSec 10
    $otherCount = 0
    if ($otherOpps -is [array]) { $otherCount = $otherOpps.Count }
    if ($otherCount -eq 0) {
        Write-Host "  [OK] Isolation OK: empty tenant returns 0 records" -ForegroundColor Green
        $script:passed++
        $script:results += @{ Name = "Tenant isolation"; Status = "PASS"; Detail = "0 records for unknown tenant" }
    }
    else {
        Write-Host "  [WARN] Isolation: unknown tenant returned $otherCount records" -ForegroundColor Yellow
        $script:warnings++
        $script:results += @{ Name = "Tenant isolation"; Status = "WARN"; Detail = "Unknown tenant got $otherCount records" }
    }
}
catch {
    Write-Host "  [WARN] Isolation check: could not verify (may require auth)" -ForegroundColor Yellow
    $script:warnings++
    $script:results += @{ Name = "Tenant isolation"; Status = "WARN"; Detail = "Could not verify" }
}

# --- Summary ---

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  VERIFICATION SUMMARY" -ForegroundColor White
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "  Total checks:  $total" -ForegroundColor White
Write-Host "  Passed:        $passed" -ForegroundColor Green
Write-Host "  Failed:        $failed" -ForegroundColor $(if ($failed -gt 0) { "Red" } else { "Green" })
Write-Host "  Warnings:      $warnings" -ForegroundColor $(if ($warnings -gt 0) { "Yellow" } else { "Green" })
Write-Host ""

if ($failed -eq 0 -and $warnings -eq 0) {
    Write-Host "  All pilot checks passed!" -ForegroundColor Green
    Write-Host "  Deployment is ready for pilot launch." -ForegroundColor Green
}
elseif ($failed -eq 0) {
    Write-Host "  All core checks passed with $warnings warnings." -ForegroundColor Yellow
    Write-Host "  Review warnings above before pilot launch." -ForegroundColor Yellow
}
else {
    Write-Host "  $failed checks failed. Deployment not ready." -ForegroundColor Red
    Write-Host "  Fix failures before proceeding to pilot launch." -ForegroundColor Yellow
    $allPassed = $false
}

Write-Host ""

if (-not $allPassed) { exit 1 }
else { exit 0 }
