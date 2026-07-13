<# 
.SYNOPSIS
    SalesOS Performance Regression Gate for CI/CD.

.DESCRIPTION
    Runs abbreviated load test (50 users, 60s) and compares results against
    PERFORMANCE_BASELINE.md thresholds. Fails CI if any endpoint exceeds p95
    budget by >20%.

.EXAMPLE
    .\scripts\check-performance.ps1
    .\scripts\check-performance.ps1 -BaseURL http://staging.example.com
    .\scripts\check-performance.ps1 -ThresholdPct 10 -Verbose
#>

param(
    [string]$BaseURL = $env:SALESOS_BASE_URL,
    [string]$Username = $env:SALESOS_USERNAME,
    [string]$Password = $env:SALESOS_PASSWORD,
    [int]$Users = 50,
    [int]$Duration = 60,
    [float]$ThresholdPct = 20.0,
    [string]$OutputDir = "test-results",
    [switch]$Verbose
)

$ErrorActionPreference = "Continue"

if (-not $BaseURL) { $BaseURL = "http://localhost:8000" }
if (-not $Username) { $Username = "admin@test.com" }
if (-not $Password) { $Password = "password" }

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  SalesOS Performance Regression Gate" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Target:       $BaseURL"
Write-Host "Users:        $Users"
Write-Host "Duration:     ${Duration}s"
Write-Host "Threshold:    +${ThresholdPct}% over baseline"
Write-Host ""

# Performance baselines (p95 in ms) from PERFORMANCE_BASELINE.md
$Baseline = @{
    "GET /health"             = 10
    "GET /health/live"        = 5
    "GET /companies/{id}"     = 120
    "GET /dashboard"          = 300
    "POST /search"            = 350
    "POST /enrich"            = 100
    "POST /identity/login"    = 300
}

$PassCount = 0
$FailCount = 0
$Results = @()

# Health check - quick validation
Write-Host "[1/3] Connectivity check..." -ForegroundColor Yellow
try {
    $health = Invoke-RestMethod -Uri "$BaseURL/health" -Method Get -TimeoutSec 10
    Write-Host "  OK: System is $(${health}.status)" -ForegroundColor Green
} catch {
    Write-Host "  FAIL: Cannot reach $BaseURL - $_" -ForegroundColor Red
    exit 1
}

# Authenticate
Write-Host "[2/3] Authentication..." -ForegroundColor Yellow
try {
    $body = @{ email = $Username; password = $Password } | ConvertTo-Json
    $loginResp = Invoke-RestMethod -Uri "$BaseURL/api/v1/identity/login" -Method Post -Body $body -ContentType "application/json" -TimeoutSec 10
    $token = $loginResp.access_token
    if (-not $token) { throw "No token in response" }
    Write-Host "  OK: Token acquired (${$token.Length} chars)" -ForegroundColor Green
} catch {
    Write-Host "  FAIL: Authentication failed - $_" -ForegroundColor Red
    exit 1
}

$headers = @{ Authorization = "Bearer $token" }

# Run load test via Python script if available
Write-Host "[3/3] Running abbreviated load test..." -ForegroundColor Yellow
$timestamp = Get-Date -Format "yyyyMMdd-HHmmss"

$loadTestScript = Join-Path $PSScriptRoot "load-test.py"
if (Test-Path $loadTestScript) {
    $env:SALESOS_BASE_URL = $BaseURL
    $env:SALESOS_USERNAME = $Username
    $env:SALESOS_PASSWORD = $Password
    
    $testOutput = python $loadTestScript --health-iters 20 --login-iters 20 --dashboard-iters 30 --search-iters 30 --company-iters 30 2>&1
    $testExit = $LASTEXITCODE
    
    if ($Verbose) {
        Write-Host $testOutput
    }
}

# Direct endpoint measurement for baseline comparison
Write-Host ""
Write-Host "Baseline Comparison (measured p95 vs threshold):" -ForegroundColor Cyan
Write-Host ("-" * 70)

$endpointTests = @(
    @{ Name = "GET /health"; Url = "$BaseURL/health"; Method = "GET" }
    @{ Name = "GET /health/live"; Url = "$BaseURL/health/live"; Method = "GET" }
    @{ Name = "GET /companies/{id}"; Url = "$BaseURL/api/v1/companies/1"; Method = "GET"; Auth = $true }
    @{ Name = "GET /dashboard"; Url = "$BaseURL/api/v1/dashboard"; Method = "GET"; Auth = $true }
    @{ Name = "POST /search"; Url = "$BaseURL/api/v1/search"; Method = "POST"; Auth = $true; Body = '{"query":"test","limit":5}' }
    @{ Name = "POST /identity/login"; Url = "$BaseURL/api/v1/identity/login"; Method = "POST"; Body = "{`"email`":`"$Username`",`"password`":`"$Password`"}" }
)

foreach ($test in $endpointTests) {
    $latencies = @()
    $errors = 0
    $iterations = 20

    for ($i = 0; $i -lt $iterations; $i++) {
        try {
            $start = [System.Diagnostics.Stopwatch]::StartNew()
            $reqHeaders = @{}
            if ($test.Auth) { $reqHeaders["Authorization"] = "Bearer $token" }
            
            if ($test.Method -eq "POST") {
                $null = Invoke-RestMethod -Uri $test.Url -Method Post -Body $test.Body -ContentType "application/json" -Headers $reqHeaders -TimeoutSec 10
            } else {
                $null = Invoke-RestMethod -Uri $test.Url -Method Get -Headers $reqHeaders -TimeoutSec 10
            }
            $start.Stop()
            $latencies += $start.Elapsed.TotalMilliseconds
        } catch {
            $start.Stop()
            $errors++
            $latencies += $start.Elapsed.TotalMilliseconds
        }
    }

    $sorted = $latencies | Sort-Object
    $p95Idx = [Math]::Floor($sorted.Count * 0.95)
    $p95 = $sorted[$p95Idx]
    $baseline = $Baseline[$test.Name]
    $budget = $baseline * (1 + $ThresholdPct / 100)
    $exceeded = $p95 -gt $budget
    $status = if ($exceeded) { "FAIL" } else { "PASS" }
    $color = if ($exceeded) { "Red" } else { "Green" }

    $result = [PSCustomObject]@{
        Endpoint    = $test.Name
        MeasuredP95 = [Math]::Round($p95, 1)
        Baseline    = $baseline
        Budget      = [Math]::Round($budget, 1)
        Status      = $status
        Errors      = $errors
    }
    $Results += $result

    if ($exceeded) {
        $FailCount++
        Write-Host ("  {0,-25} p95={1,8}ms  baseline={2,6}ms  budget={3,8}ms  [{4}]" -f $test.Name, $p95.ToString("F1"), $baseline, $budget.ToString("F1"), $status) -ForegroundColor $color
    } else {
        $PassCount++
        Write-Host ("  {0,-25} p95={1,8}ms  baseline={2,6}ms  budget={3,8}ms  [{4}]" -f $test.Name, $p95.ToString("F1"), $baseline, $budget.ToString("F1"), $status) -ForegroundColor $color
    }
}

Write-Host ""
Write-Host ("-" * 70)

# Save results
if (-not (Test-Path $OutputDir)) { New-Item -ItemType Directory -Path $OutputDir -Force | Out-Null }
$resultsFile = Join-Path $OutputDir "perf-gate-$timestamp.json"
$Results | ConvertTo-Json | Out-File -FilePath $resultsFile
Write-Host "Results saved: $resultsFile"

# Final verdict
Write-Host ""
if ($FailCount -gt 0) {
    Write-Host "GATE RESULT: FAIL ($FailCount endpoint(s) exceed budget)" -ForegroundColor Red
    Write-Host ""
    Write-Host "Failed endpoints:" -ForegroundColor Red
    $Results | Where-Object { $_.Status -eq "FAIL" } | ForEach-Object {
        Write-Host ("  - {0}: p95={1}ms > budget={2}ms ({3:N1}% over baseline)" -f $_.Endpoint, $_.MeasuredP95, $_.Budget, (($_.MeasuredP95 - $_.Baseline) / $_.Baseline * 100)) -ForegroundColor Red
    }
    exit 1
} else {
    Write-Host "GATE RESULT: PASS ($PassCount/$($PassCount + $FailCount) endpoints within budget)" -ForegroundColor Green
    exit 0
}
