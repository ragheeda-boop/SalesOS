param(
    [string]$BaseUrl = "http://localhost:8000",
    [int]$MaxRetries = 15,
    [int]$RetryInterval = 5
)

$ErrorActionPreference = "Stop"
$passed = 0
$failed = 0
$results = @()

function Test-Endpoint {
    param(
        [string]$Name,
        [string]$Url,
        [int[]]$ValidStatuses = @(200, 401),
        [int]$TimeoutSec = 10
    )

    try {
        $response = Invoke-WebRequest -Uri $Url -UseBasicParsing -TimeoutSec $TimeoutSec -SkipCertificateCheck
        $status = $response.StatusCode
        if ($ValidStatuses -contains $status) {
            Write-Host "  [PASS] $Name — $status" -ForegroundColor Green
            return @{Name=$Name; Status=$status; Result="PASS"; Url=$Url}
        } else {
            Write-Host "  [FAIL] $Name — Expected $($ValidStatuses -join ' or '), got $status" -ForegroundColor Red
            return @{Name=$Name; Status=$status; Result="FAIL"; Url=$Url}
        }
    } catch {
        $status = if ($_.Exception.Response) { $_.Exception.Response.StatusCode.value__ } else { 0 }
        $errorMsg = if ($status -eq 0) { "Connection failed: $($_.Exception.Message)" } else { "Status $status" }
        Write-Host "  [FAIL] $Name — $errorMsg" -ForegroundColor Red
        return @{Name=$Name; Status=$status; Result="FAIL"; Url=$Url; Error=$errorMsg}
    }
}

Write-Host "╔════════════════════════════════════════════════════╗" -ForegroundColor Cyan
Write-Host "║       SalesOS v0.8 — Production Smoke Tests        ║" -ForegroundColor Cyan
Write-Host "╚════════════════════════════════════════════════════╝" -ForegroundColor Cyan
Write-Host "Target: $BaseUrl"
Write-Host ""

# ─── Step 1: Wait for health endpoint ───
Write-Host "─── Step 1: Wait for backend health ───" -ForegroundColor Yellow
$healthy = $false
for ($i = 1; $i -le $MaxRetries; $i++) {
    try {
        $r = Invoke-WebRequest -Uri "$BaseUrl/health" -UseBasicParsing -TimeoutSec 5 -SkipCertificateCheck
        if ($r.StatusCode -eq 200) {
            Write-Host "  Backend is healthy (attempt $i/$MaxRetries)" -ForegroundColor Green
            $healthy = $true
            break
        }
    } catch {
        Write-Host "  Waiting for backend... (attempt $i/$MaxRetries)" -ForegroundColor DarkYellow
    }
    Start-Sleep -Seconds $RetryInterval
}

if (-not $healthy) {
    Write-Host "[FATAL] Backend not reachable after $MaxRetries attempts. Aborting." -ForegroundColor Red
    exit 1
}

# ─── Step 2: Smoke test endpoints ───
Write-Host "`n─── Step 2: Endpoint smoke tests ───" -ForegroundColor Yellow

$endpoints = @(
    @{Name="Health Check"; Url="$BaseUrl/health"; ValidStatuses=@(200)}
    @{Name="Metrics"; Url="$BaseUrl/metrics"; ValidStatuses=@(200)}
    @{Name="API Docs (Swagger)"; Url="$BaseUrl/docs"; ValidStatuses=@(200)}
    @{Name="Opportunities"; Url="$BaseUrl/api/v1/opportunities"; ValidStatuses=@(200, 401)}
    @{Name="Workflows"; Url="$BaseUrl/api/v1/workflows"; ValidStatuses=@(200, 401)}
    @{Name="RAG Documents"; Url="$BaseUrl/api/v1/rag/documents"; ValidStatuses=@(200, 401)}
    @{Name="Revenue Dashboard"; Url="$BaseUrl/api/v1/revenue/dashboard"; ValidStatuses=@(200, 401)}
    @{Name="Pipeline Summary"; Url="$BaseUrl/api/v1/pipeline/summary"; ValidStatuses=@(200, 401)}
    @{Name="NBA Recommendations"; Url="$BaseUrl/api/v1/opportunities/test-opp/nba"; ValidStatuses=@(200, 401)}
)

foreach ($ep in $endpoints) {
    $result = Test-Endpoint -Name $ep.Name -Url $ep.Url -ValidStatuses $ep.ValidStatuses
    $results += $result
    if ($result.Result -eq "PASS") { $passed++ } else { $failed++ }
}

# ─── Summary ───
Write-Host "`n─── Summary ───" -ForegroundColor Yellow
Write-Host "  Total: $($results.Count)" -ForegroundColor White
Write-Host "  Passed: $passed" -ForegroundColor Green
Write-Host "  Failed: $failed" -ForegroundColor $(if ($failed -eq 0) { "Green" } else { "Red" })

if ($failed -gt 0) {
    Write-Host "`nFailed endpoints:" -ForegroundColor Red
    foreach ($r in $results | Where-Object { $_.Result -eq "FAIL" }) {
        Write-Host "  - $($r.Name): $($r.Url)" -ForegroundColor Red
        if ($r.Error) { Write-Host "    Error: $($r.Error)" -ForegroundColor DarkRed }
    }
}

# ─── Write results to file ───
$reportPath = Join-Path $PSScriptRoot "..\docs\SMOKE_TEST_RESULTS_v0.8.json"
Write-Host "Full results:"
$results | Format-Table -AutoSize -Property Name, Result, Status, Url
$results | ConvertTo-Json | Set-Content -Path $reportPath -Encoding UTF8
Write-Host "`nDetailed results saved to: $reportPath" -ForegroundColor Gray

if ($failed -gt 0) {
    exit 1
}
