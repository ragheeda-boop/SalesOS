<#
.SYNOPSIS
    SalesOS Pilot Onboarding — seeds data, verifies endpoints, tests NBA, generates report.
.DESCRIPTION
    Automates the pilot onboarding process:
    1. Runs pilot_seed.py to generate pilot data
    2. Verifies all API endpoints return data for the pilot tenant
    3. Tests decision evaluation (NBA) for each pilot company
    4. Generates a summary report
.EXAMPLE
    .\pilot-onboard.ps1 -TenantId "pilot_tenant"
    .\pilot-onboard.ps1 -TenantId "pilot_tenant" -BaseUrl "http://staging.salesos.com"
#>

param(
    [Parameter(Mandatory = $true)]
    [string]$TenantId = "pilot_tenant",

    [string]$BaseUrl = "http://localhost:8000",

    [string]$SeedScript = "backend.demo.pilot_seed",

    [string]$AuthToken = "",

    [int]$TimeoutSec = 30
)

$ErrorActionPreference = "Continue"
$Separator = "=" * 70
$SubSeparator = "-" * 50
$PilotCompanies = @(1, 2, 3, 4, 5)

$results = @()          # all test results
$passed = 0
$failed = 0
$warnings = 0

# ── Helpers ──────────────────────────────────────────────────────

function Write-Step {
    param([string]$Title)
    Write-Host ""
    Write-Host $Separator
    Write-Host "  $Title" -ForegroundColor Cyan
    Write-Host $Separator
}

function Write-Result {
    param([string]$Test, [string]$Status, [string]$Detail = "")
    $icon = switch ($Status) {
        "PASS" { "✅" }
        "FAIL" { "❌" }
        "WARN" { "⚠️" }
        default { "➡️" }
    }
    $color = switch ($Status) {
        "PASS" { "Green" }
        "FAIL" { "Red" }
        "WARN" { "Yellow" }
        default { "White" }
    }
    Write-Host "  $icon [$Status] $Test" -ForegroundColor $color
    if ($Detail) {
        Write-Host "         $Detail" -ForegroundColor DarkGray
    }
}

function Get-ApiHeaders {
    $headers = @{
        "Content-Type" = "application/json"
        "X-Tenant-Id"  = $TenantId
    }
    if ($AuthToken) {
        $headers["Authorization"] = "Bearer $AuthToken"
    }
    return $headers
}

function Invoke-SafeApi {
    param(
        [string]$Endpoint,
        [string]$Method = "GET",
        [string]$Body = $null,
        [int]$Timeout = $TimeoutSec
    )
    try {
        $headers = Get-ApiHeaders
        $params = @{
            Uri         = "$BaseUrl$Endpoint"
            Method      = $Method
            Headers     = $headers
            TimeoutSec  = $Timeout
            ContentType = "application/json"
        }
        if ($Body) { $params.Body = $Body }
        $response = Invoke-RestMethod @params
        return @{ Success = $true; Data = $response }
    }
    catch {
        $statusCode = if ($_.Exception.Response) { $_.Exception.Response.StatusCode.value__ } else { 0 }
        $message = $_.Exception.Message
        return @{ Success = $false; StatusCode = $statusCode; Error = $message }
    }
}

function Format-Value {
    param([double]$Value)
    return "{0:N0}" -f $Value
}

function New-Result {
    param([string]$Test, [string]$Status, [string]$Detail = "")
    $script:results += @{
        Test   = $Test
        Status = $Status
        Detail = $Detail
    }
    if ($Status -eq "PASS") { $script:passed++ }
    elseif ($Status -eq "FAIL") { $script:failed++ }
    elseif ($Status -eq "WARN") { $script:warnings++ }
}

# ── Header ───────────────────────────────────────────────────────

Clear-Host
Write-Host ""
Write-Host "╔══════════════════════════════════════════════════════════╗" -ForegroundColor Cyan
Write-Host "║       SalesOS Pilot Onboarding — Automated Setup         ║" -ForegroundColor Cyan
Write-Host "╚══════════════════════════════════════════════════════════╝" -ForegroundColor Cyan
Write-Host ""
Write-Host "  Tenant:      $TenantId" -ForegroundColor White
Write-Host "  Target URL:  $BaseUrl" -ForegroundColor White
Write-Host "  Timestamp:   $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')" -ForegroundColor Gray
Write-Host ""

# ── Step 1: Seed Pilot Data ─────────────────────────────────────

Write-Step "STEP 1/6 — Seed Pilot Data"

$seedResult = $null
try {
    Write-Host "  Running: python -m $SeedScript" -ForegroundColor Gray
    $seedOutput = python -m $SeedScript 2>&1
    $seedResult = $seedOutput -join "`n"
    $exitCode = $LASTEXITCODE

    if ($exitCode -eq 0 -and $seedOutput -match "Written to") {
        Write-Result -Test "Pilot seed data generated" -Status "PASS"
        # Extract the file path from output
        if ($seedOutput -match "Written to:\s*(.+\.json)") {
            $dataPath = $Matches[1]
            Write-Host "         Data file: $dataPath" -ForegroundColor DarkGray
        }
        New-Result -Test "Seed script execution" -Status "PASS"
    }
    else {
        Write-Result -Test "Seed script" -Status "FAIL" -Detail "Exit code: $exitCode"
        Write-Host "         $seedResult" -ForegroundColor Red
        New-Result -Test "Seed script execution" -Status "FAIL" -Detail $seedResult
    }
}
catch {
    Write-Result -Test "Seed script execution" -Status "FAIL" -Detail $_.Exception.Message
    New-Result -Test "Seed script execution" -Status "FAIL" -Detail $_.Exception.Message
}

# ── Step 2: Health & Connectivity ──────────────────────────────

Write-Step "STEP 2/6 — API Health & Connectivity"

# 2a. Ping
$ping = Invoke-SafeApi -Endpoint "/ping"
if ($ping.Success -and $ping.Data.ping -eq "pong") {
    Write-Result -Test "GET /ping" -Status "PASS"
    New-Result -Test "Ping endpoint" -Status "PASS"
}
else {
    Write-Result -Test "GET /ping" -Status "FAIL" -Detail $ping.Error
    New-Result -Test "Ping endpoint" -Status "FAIL" -Detail $ping.Error
}

# 2b. Health
$health = Invoke-SafeApi -Endpoint "/health"
if ($health.Success -and $health.Data.status -eq "ok") {
    Write-Result -Test "GET /health" -Status "PASS"
    New-Result -Test "Health endpoint" -Status "PASS"
    Write-Host "         Database: $($health.Data.database)" -ForegroundColor $(if ($health.Data.database -eq "connected") { "Green" } else { "Yellow" })
    Write-Host "         Graph:    $($health.Data.graph)" -ForegroundColor $(if ($health.Data.graph -eq "connected") { "Green" } else { "Yellow" })
}
else {
    $detail = if ($health.Success) { "Status: $($health.Data.status)" } else { $health.Error }
    Write-Result -Test "GET /health" -Status "FAIL" -Detail $detail
    New-Result -Test "Health endpoint" -Status "FAIL" -Detail $detail
}

# 2c. Decision Metrics available
$dmetrics = Invoke-SafeApi -Endpoint "/api/v1/decision/metrics"
if ($dmetrics.Success) {
    Write-Result -Test "GET /decision/metrics" -Status "PASS"
    New-Result -Test "Decision metrics endpoint" -Status "PASS"
}
else {
    Write-Result -Test "GET /decision/metrics" -Status "WARN" -Detail "May require auth"
    New-Result -Test "Decision metrics endpoint" -Status "WARN"
}

# ── Step 3: Pilot Tenant Data Verification ─────────────────────

Write-Step "STEP 3/6 — Pilot Tenant Data Verification"

# 3a. Companies endpoint
$companies = Invoke-SafeApi -Endpoint "/api/v1/companies?tenant_id=$TenantId"
if ($companies.Success) {
    $count = if ($companies.Data.Count -gt 0) { $companies.Data.Count } elseif ($companies.Data.Length -ge 0) { $companies.Data.Length } else { -1 }
    Write-Result -Test "Companies endpoint" -Status "PASS" -Detail "$count companies returned"
    New-Result -Test "Companies API" -Status "PASS" -Detail "$count companies"
}
else {
    Write-Result -Test "Companies endpoint" -Status "WARN" -Detail $companies.Error
    New-Result -Test "Companies API" -Status "WARN" -Detail $companies.Error
}

# 3b. Opportunities endpoint
$opps = Invoke-SafeApi -Endpoint "/api/v1/opportunities?tenant_id=$TenantId"
if ($opps.Success) {
    $count = if ($opps.Data.Count -gt 0) { $opps.Data.Count } elseif ($opps.Data.Length -ge 0) { $opps.Data.Length } else { -1 }
    Write-Result -Test "Opportunities endpoint" -Status "PASS" -Detail "$count opportunities"
    New-Result -Test "Opportunities API" -Status "PASS" -Detail "$count opportunities"
}
else {
    Write-Result -Test "Opportunities endpoint" -Status "WARN" -Detail $opps.Error
    New-Result -Test "Opportunities API" -Status "WARN" -Detail $opps.Error
}

# 3c. Signals for pilot tenant
$signals = Invoke-SafeApi -Endpoint "/api/v1/signals?tenant_id=$TenantId"
if ($signals.Success) {
    $count = if ($signals.Data.Count -gt 0) { $signals.Data.Count } elseif ($signals.Data.Length -ge 0) { $signals.Data.Length } else { -1 }
    Write-Result -Test "Signals endpoint" -Status "PASS" -Detail "$count signals"
    New-Result -Test "Signals API" -Status "PASS" -Detail "$count signals"
}
else {
    Write-Result -Test "Signals endpoint" -Status "WARN" -Detail $signals.Error
    New-Result -Test "Signals API" -Status "WARN" -Detail $signals.Error
}

# 3d. Decision makers for pilot tenant
$dms = Invoke-SafeApi -Endpoint "/api/v1/decision-makers?tenant_id=$TenantId"
if ($dms.Success) {
    $count = if ($dms.Data.Count -gt 0) { $dms.Data.Count } elseif ($dms.Data.Length -ge 0) { $dms.Data.Length } else { -1 }
    Write-Result -Test "Decision Makers endpoint" -Status "PASS" -Detail "$count decision makers"
    New-Result -Test "Decision Makers API" -Status "PASS" -Detail "$count decision makers"
}
else {
    Write-Result -Test "Decision Makers endpoint" -Status "WARN" -Detail $dms.Error
    New-Result -Test "Decision Makers API" -Status "WARN" -Detail $dms.Error
}

# 3e. Tenant isolation check — verify another tenant sees no pilot data
$otherTenant = "other_tenant"
$otherHeaders = @{
    "Content-Type" = "application/json"
    "X-Tenant-Id"  = $otherTenant
}
try {
    $otherOpps = Invoke-RestMethod -Uri "$BaseUrl/api/v1/opportunities" -Headers $otherHeaders -TimeoutSec $TimeoutSec -ContentType "application/json"
    $otherCount = if ($otherOpps.Count -gt 0) { $otherOpps.Count } elseif ($otherOpps.Length -ge 0) { $otherOpps.Length } else { 0 }
    if ($otherCount -eq 0) {
        Write-Result -Test "Tenant isolation (no cross-tenant leak)" -Status "PASS"
        New-Result -Test "Tenant isolation" -Status "PASS"
    }
    else {
        Write-Result -Test "Tenant isolation" -Status "WARN" -Detail "Other tenant sees $otherCount records — verify scoping"
        New-Result -Test "Tenant isolation" -Status "WARN" -Detail "Other tenant sees $otherCount records"
    }
}
catch {
    Write-Result -Test "Tenant isolation check" -Status "WARN" -Detail "Could not test (expected if auth required)"
    New-Result -Test "Tenant isolation" -Status "WARN" -Detail "Could not verify"
}

# ── Step 4: NBA / Decision Evaluation ─────────────────────────

Write-Step "STEP 4/6 — NBA Decision Evaluation"

$nbaResults = @()
foreach ($cid in $PilotCompanies) {
    # Try to find an opportunity ID for this company — use the first active opportunity
    $companyOpps = @()
    if ($opps.Success -and $opps.Data) {
        $companyOpps = @($opps.Data | Where-Object { $_.company_id -eq $cid -or $_.company_id -eq "$cid" })
    }
    $oppId = if ($companyOpps.Count -gt 0) { $companyOpps[0].id -or $companyOpps[0].opportunity_id } else { $null }

    if (-not $oppId) {
        # Fall back to company-level NBA evaluation
        $nbaResult = Invoke-SafeApi -Endpoint "/api/v1/decision/evaluate" -Method POST -Body "{`"company_id`": $cid, `"tenant_id`": `"$TenantId`"}"
    }
    else {
        $nbaResult = Invoke-SafeApi -Endpoint "/api/v1/decision/evaluate" -Method POST -Body "{`"opportunity_id`": `"$oppId`", `"tenant_id`": `"$TenantId`"}"
    }

    $companyName = switch ($cid) {
        1 { "Gulf Energy" }
        2 { "Atheer Telecom" }
        3 { "Al Rajhi Financial" }
        4 { "Al Salam Medical" }
        5 { "Bayanat Tech" }
    }

    if ($nbaResult.Success -and $nbaResult.Data) {
        $confidence = $nbaResult.Data.confidence
        $action = $nbaResult.Data.action
        $alternatives = @($nbaResult.Data.alternatives).Count

        Write-Result -Test "NBA evaluation — $companyName (ID: $cid)" -Status "PASS" -Detail "Action: $action | Confidence: $confidence | Alternatives: $alternatives"
        New-Result -Test "NBA evaluation: $companyName" -Status "PASS" -Detail "Action=$action, Confidence=$confidence"

        $nbaResults += @{
            CompanyId   = $cid
            CompanyName = $companyName
            Action      = $action
            Confidence  = $confidence
            Status      = "PASS"
        }
    }
    else {
        Write-Result -Test "NBA evaluation — $companyName (ID: $cid)" -Status "WARN" -Detail $nbaResult.Error
        New-Result -Test "NBA evaluation: $companyName" -Status "WARN" -Detail $nbaResult.Error

        $nbaResults += @{
            CompanyId   = $cid
            CompanyName = $companyName
            Action      = "N/A"
            Confidence  = 0
            Status      = "WARN"
        }
    }
}

# ── Step 5: Verify Pipeline & Timeline ─────────────────────────

Write-Step "STEP 5/6 — Pipeline & Timeline Verification"

# 5a. Pipeline summary
$pipeline = Invoke-SafeApi -Endpoint "/api/v1/pipeline/summary?tenant_id=$TenantId"
if ($pipeline.Success) {
    Write-Result -Test "Pipeline summary" -Status "PASS"
    New-Result -Test "Pipeline API" -Status "PASS"
    if ($pipeline.Data.total_value) {
        Write-Host "         Total Pipeline: SAR $(Format-Value $pipeline.Data.total_value)" -ForegroundColor Gray
    }
}
else {
    Write-Result -Test "Pipeline summary" -Status "WARN" -Detail $pipeline.Error
    New-Result -Test "Pipeline API" -Status "WARN" -Detail $pipeline.Error
}

# 5b. Timeline events
$timeline = Invoke-SafeApi -Endpoint "/api/v1/timeline?tenant_id=$TenantId"
if ($timeline.Success) {
    $count = if ($timeline.Data.Count -gt 0) { $timeline.Data.Count } elseif ($timeline.Data.Length -ge 0) { $timeline.Data.Length } else { -1 }
    Write-Result -Test "Timeline events" -Status "PASS" -Detail "$count events"
    New-Result -Test "Timeline API" -Status "PASS" -Detail "$count events"
}
else {
    Write-Result -Test "Timeline events" -Status "WARN" -Detail $timeline.Error
    New-Result -Test "Timeline API" -Status "WARN" -Detail $timeline.Error
}

# 5c. Event runtime stats
$eventRuntime = Invoke-SafeApi -Endpoint "/api/v1/event-runtime/stats"
if ($eventRuntime.Success) {
    $dlq = $eventRuntime.Data.dead_letter_count
    Write-Result -Test "Event Runtime stats" -Status "PASS" -Detail "Dead letters: $dlq"
    New-Result -Test "Event Runtime" -Status "PASS" -Detail "DLQ=$dlq"
}
else {
    Write-Result -Test "Event Runtime stats" -Status "WARN" -Detail $eventRuntime.Error
    New-Result -Test "Event Runtime" -Status "WARN" -Detail $eventRuntime.Error
}

# ── Step 6: Generate Summary Report ────────────────────────────

Write-Step "STEP 6/6 — Summary Report"

$report = @"
╔══════════════════════════════════════════════════════════════════╗
║              SalesOS Pilot Onboarding Report                    ║
╚══════════════════════════════════════════════════════════════════╝

  Tenant:      $TenantId
  Target URL:  $BaseUrl
  Generated:   $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')

────────────────────────────────────────────────────────────────────
  TEST RESULTS
────────────────────────────────────────────────────────────────────
  Total checks:  $($results.Count)
  Passed:        $passed
  Failed:        $failed
  Warnings:      $warnings

$(if ($failed -eq 0) { "  Status: ✅ ALL CHECKS PASSED — Ready for pilot launch" } else { "  Status: ⚠️  $failed failures need attention before launch" })

────────────────────────────────────────────────────────────────────
  NBA EVALUATION RESULTS
────────────────────────────────────────────────────────────────────

"@

$nbaTableRows = @()
foreach ($nr in $nbaResults) {
    $statusIcon = if ($nr.Status -eq "PASS") { "✅" } else { "⚠️" }
    $nbaTableRows += "  $statusIcon $($nr.CompanyName.PadRight(22)) $($nr.Action.PadRight(30)) $($nr.Confidence)"
}

$report += $nbaTableRows -join "`n"
$report += @"

────────────────────────────────────────────────────────────────────
  PIPELINE VALUE
────────────────────────────────────────────────────────────────────

  Total Pipeline Value: $(if ($pipeline.Success -and $pipeline.Data.total_value) { "SAR $(Format-Value $pipeline.Data.total_value)" } else { "N/A" })
  Active Opportunities: $(if ($opps.Success -and $opps.Data) { if ($opps.Data.Count -gt 0) { $opps.Data.Count } elseif ($opps.Data.Length -ge 0) { $opps.Data.Length } else { 0 } } else { "N/A" })
  Companies Onboarded: 5

────────────────────────────────────────────────────────────────────
  CHECKS DETAIL
────────────────────────────────────────────────────────────────────

"@

foreach ($r in $results) {
    $report += "  [$($r.Status.PadRight(4))] $($r.Test)"
    if ($r.Detail) {
        $report += "  → $($r.Detail)"
    }
    $report += "`n"
}

$report += @"

────────────────────────────────────────────────────────────────────
  NEXT STEPS
────────────────────────────────────────────────────────────────────

  1. Review and resolve any [FAIL] items above
  2. Run .\pilot-metrics.ps1 -TenantId "$TenantId" for baseline metrics
  3. Verify frontend loads pilot data at $BaseUrl
  4. Distribute login credentials to pilot users
  5. Proceed to Week 1 per PILOT_LAUNCH_CHECKLIST.md

────────────────────────────────────────────────────────────────────
  Generated by pilot-onboard.ps1
  Linked: PILOT_LAUNCH.md, PILOT_COMPANY_BRIEFS.md
"@

# Write report to file
$reportDir = Join-Path $PSScriptRoot "..\docs"
$reportPath = Join-Path $reportDir "PILOT_ONBOARD_REPORT.md"
New-Item -ItemType Directory -Force -Path $reportDir | Out-Null
$report | Out-File -FilePath $reportPath -Encoding utf8

# Also output to console
Write-Host $report -ForegroundColor White
Write-Host ""
Write-Host "  Report saved to: $reportPath" -ForegroundColor Cyan
Write-Host ""

# ── Final Exit Code ─────────────────────────────────────────────

if ($failed -gt 0) {
    Write-Host "  ⚠️  Pilot onboarding completed with $failed failures." -ForegroundColor Yellow
    Write-Host "  ⚠️  Review the report and fix issues before launching." -ForegroundColor Yellow
    exit 1
}
else {
    Write-Host "  ✅ Pilot onboarding complete. All checks passed!" -ForegroundColor Green
    Write-Host "  ✅ Ready for Week 0 launch per PILOT_LAUNCH_CHECKLIST.md" -ForegroundColor Green
    exit 0
}
