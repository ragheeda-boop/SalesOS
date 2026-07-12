<#
.SYNOPSIS
    SalesOS Pilot Verification — lightweight health and data check for staging.
.DESCRIPTION
    Tests backend health, decision engine NBA evaluation, opportunity pipeline,
    task management, and NBA generation for each of the 5 pilot companies.
    Produces a pass/fail summary per company.
.EXAMPLE
    .\pilot-verify.ps1 -BaseUrl http://staging-url:8000 -TenantId pilot_tenant
    .\pilot-verify.ps1 -BaseUrl http://localhost:8000 -TenantId pilot_tenant -AuthToken "eyJ..."
#>

param(
    [Parameter(Mandatory = $true)]
    [string]$BaseUrl,

    [Parameter(Mandatory = $true)]
    [string]$TenantId,

    [string]$AuthToken = "",

    [int]$TimeoutSec = 15
)

$ErrorActionPreference = "Continue"
$Separator = "=" * 60
$SubSeparator = "-" * 40

$results = @()
$passed = 0
$failed = 0
$warnings = 0

$PilotCompanies = @(
    @{ Id = 1; Name = "Gulf Energy" }
    @{ Id = 2; Name = "Atheer Telecom" }
    @{ Id = 3; Name = "Al Rajhi Financial" }
    @{ Id = 4; Name = "Al Salam Medical" }
    @{ Id = 5; Name = "Bayanat Tech" }
)

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
        "PASS" { "PASS" }
        "FAIL" { "FAIL" }
        "WARN" { "WARN" }
        default { "INFO" }
    }
    $color = switch ($Status) {
        "PASS" { "Green" }
        "FAIL" { "Red" }
        "WARN" { "Yellow" }
        default { "White" }
    }
    Write-Host "  [$icon] $Test" -ForegroundColor $color
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
Write-Host "║        SalesOS Pilot Verification — Lightweight Check   ║" -ForegroundColor Cyan
Write-Host "╚══════════════════════════════════════════════════════════╝" -ForegroundColor Cyan
Write-Host ""
Write-Host "  Tenant:      $TenantId" -ForegroundColor White
Write-Host "  Target URL:  $BaseUrl" -ForegroundColor White
Write-Host "  Timestamp:   $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')" -ForegroundColor Gray
Write-Host ""

# ── Step 1: Health Check ─────────────────────────────────────────

Write-Step "STEP 1/5 — Backend Health"

$ping = Invoke-SafeApi -Endpoint "/ping"
if ($ping.Success -and $ping.Data.ping -eq "pong") {
    Write-Result -Test "Backend ping" -Status "PASS"
    New-Result -Test "Backend ping" -Status "PASS"
}
else {
    Write-Result -Test "Backend ping" -Status "FAIL" -Detail $ping.Error
    New-Result -Test "Backend ping" -Status "FAIL" -Detail $ping.Error
    Write-Host ""
    Write-Host "  Cannot continue — backend unreachable." -ForegroundColor Red
    exit 1
}

$health = Invoke-SafeApi -Endpoint "/api/v1/health"
if ($health.Success -and $health.Data.status -eq "ok") {
    Write-Result -Test "Backend health" -Status "PASS" -Detail "db=$($health.Data.database) graph=$($health.Data.graph)"
    New-Result -Test "Backend health" -Status "PASS"
}
else {
    $detail = if ($health.Success) { "Status: $($health.Data.status)" } else { $health.Error }
    Write-Result -Test "Backend health" -Status "FAIL" -Detail $detail
    New-Result -Test "Backend health" -Status "FAIL" -Detail $detail
}

# ── Step 2: Pilot Data Availability ─────────────────────────────

Write-Step "STEP 2/5 — Pilot Data Availability"

$companies = Invoke-SafeApi -Endpoint "/api/v1/companies?tenant_id=$TenantId"
$companyCount = 0
if ($companies.Success) {
    $companyCount = if ($companies.Data.Count -gt 0) { $companies.Data.Count } elseif ($companies.Data.Length -ge 0) { $companies.Data.Length } else { 0 }
    $status = if ($companyCount -ge 5) { "PASS" } elseif ($companyCount -gt 0) { "WARN" } else { "FAIL" }
    Write-Result -Test "Companies ($companyCount found)" -Status $status -Detail "Expected at least 5"
    New-Result -Test "Companies data" -Status $status -Detail "$companyCount companies"
}
else {
    Write-Result -Test "Companies endpoint" -Status "WARN" -Detail $companies.Error
    New-Result -Test "Companies data" -Status "WARN" -Detail $companies.Error
}

$opps = Invoke-SafeApi -Endpoint "/api/v1/opportunities?tenant_id=$TenantId"
$oppCount = 0
if ($opps.Success) {
    $oppCount = if ($opps.Data.Count -gt 0) { $opps.Data.Count } elseif ($opps.Data.Length -ge 0) { $opps.Data.Length } else { 0 }
    $status = if ($oppCount -ge 10) { "PASS" } elseif ($oppCount -gt 0) { "WARN" } else { "FAIL" }
    Write-Result -Test "Opportunities ($oppCount found)" -Status $status -Detail "Expected at least 10"
    New-Result -Test "Opportunities data" -Status $status -Detail "$oppCount opportunities"
}
else {
    Write-Result -Test "Opportunities endpoint" -Status "WARN" -Detail $opps.Error
    New-Result -Test "Opportunities data" -Status "WARN" -Detail $opps.Error
}

$signals = Invoke-SafeApi -Endpoint "/api/v1/signals?tenant_id=$TenantId"
if ($signals.Success) {
    $signalCount = if ($signals.Data.Count -gt 0) { $signals.Data.Count } elseif ($signals.Data.Length -ge 0) { $signals.Data.Length } else { 0 }
    $status = if ($signalCount -ge 15) { "PASS" } elseif ($signalCount -gt 0) { "WARN" } else { "FAIL" }
    Write-Result -Test "Signals ($signalCount found)" -Status $status -Detail "Expected at least 15"
    New-Result -Test "Signals data" -Status $status -Detail "$signalCount signals"
}
else {
    Write-Result -Test "Signals endpoint" -Status "WARN" -Detail $signals.Error
    New-Result -Test "Signals data" -Status "WARN" -Detail $signals.Error
}

$dms = Invoke-SafeApi -Endpoint "/api/v1/decision-makers?tenant_id=$TenantId"
if ($dms.Success) {
    $dmCount = if ($dms.Data.Count -gt 0) { $dms.Data.Count } elseif ($dms.Data.Length -ge 0) { $dms.Data.Length } else { 0 }
    $status = if ($dmCount -ge 10) { "PASS" } elseif ($dmCount -gt 0) { "WARN" } else { "FAIL" }
    Write-Result -Test "Decision Makers ($dmCount found)" -Status $status -Detail "Expected at least 10"
    New-Result -Test "Decision Makers data" -Status $status -Detail "$dmCount decision makers"
}
else {
    Write-Result -Test "Decision Makers endpoint" -Status "WARN" -Detail $dms.Error
    New-Result -Test "Decision Makers data" -Status "WARN" -Detail $dms.Error
}

# ── Step 3: NBA Evaluation Per Company ─────────────────────────

Write-Step "STEP 3/5 — NBA Evaluation (per company)"

$nbaResults = @()
foreach ($company in $PilotCompanies) {
    $cid = $company.Id
    $cname = $company.Name

    $nbaResult = Invoke-SafeApi -Endpoint "/api/v1/decision/evaluate" -Method POST -Body "{`"company_id`": $cid, `"tenant_id`": `"$TenantId`"}"

    if ($nbaResult.Success -and $nbaResult.Data) {
        $action = $nbaResult.Data.action
        $confidence = $nbaResult.Data.confidence

        $status = if ($confidence -and $confidence -ge 0.5) { "PASS" } else { "WARN" }
        Write-Result -Test "NBA — $cname" -Status $status -Detail "Action: $action | Confidence: $confidence"
        New-Result -Test "NBA: $cname" -Status $status -Detail "Action=$action, Confidence=$confidence"

        $nbaResults += @{
            CompanyId   = $cid
            CompanyName = $cname
            Action      = $action
            Confidence  = $confidence
            Status      = $status
        }
    }
    else {
        Write-Result -Test "NBA — $cname" -Status "FAIL" -Detail $nbaResult.Error
        New-Result -Test "NBA: $cname" -Status "FAIL" -Detail $nbaResult.Error

        $nbaResults += @{
            CompanyId   = $cid
            CompanyName = $cname
            Action      = "N/A"
            Confidence  = 0
            Status      = "FAIL"
        }
    }
}

# ── Step 4: Pipeline & Tasks ───────────────────────────────────

Write-Step "STEP 4/5 — Pipeline & Tasks"

$pipeline = Invoke-SafeApi -Endpoint "/api/v1/pipeline/summary?tenant_id=$TenantId"
if ($pipeline.Success) {
    $pval = $pipeline.Data.total_value
    Write-Result -Test "Pipeline summary" -Status "PASS" -Detail "Total: SAR $(if ($pval) { "{0:N0}" -f $pval } else { 'N/A' })"
    New-Result -Test "Pipeline summary" -Status "PASS"
}
else {
    Write-Result -Test "Pipeline summary" -Status "WARN" -Detail $pipeline.Error
    New-Result -Test "Pipeline summary" -Status "WARN" -Detail $pipeline.Error
}

$tasks = Invoke-SafeApi -Endpoint "/api/v1/tasks?tenant_id=$TenantId"
if ($tasks.Success) {
    $taskCount = if ($tasks.Data.Count -gt 0) { $tasks.Data.Count } elseif ($tasks.Data.Length -ge 0) { $tasks.Data.Length } else { 0 }
    $status = if ($taskCount -ge 5) { "PASS" } elseif ($taskCount -gt 0) { "WARN" } else { "FAIL" }
    Write-Result -Test "Tasks ($taskCount found)" -Status $status -Detail "Expected at least 5"
    New-Result -Test "Tasks data" -Status $status -Detail "$taskCount tasks"
}
else {
    Write-Result -Test "Tasks endpoint" -Status "WARN" -Detail $tasks.Error
    New-Result -Test "Tasks data" -Status "WARN" -Detail $tasks.Error
}

$timeline = Invoke-SafeApi -Endpoint "/api/v1/timeline?tenant_id=$TenantId"
if ($timeline.Success) {
    $tlCount = if ($timeline.Data.Count -gt 0) { $timeline.Data.Count } elseif ($timeline.Data.Length -ge 0) { $timeline.Data.Length } else { 0 }
    $status = if ($tlCount -ge 5) { "PASS" } elseif ($tlCount -gt 0) { "WARN" } else { "FAIL" }
    Write-Result -Test "Timeline events ($tlCount found)" -Status $status -Detail "Expected at least 5"
    New-Result -Test "Timeline events" -Status $status -Detail "$tlCount events"
}
else {
    Write-Result -Test "Timeline endpoint" -Status "WARN" -Detail $timeline.Error
    New-Result -Test "Timeline events" -Status "WARN" -Detail $timeline.Error
}

$metrics = Invoke-SafeApi -Endpoint "/api/v1/decision/metrics"
if ($metrics.Success) {
    Write-Result -Test "Decision metrics" -Status "PASS"
    New-Result -Test "Decision metrics" -Status "PASS"
}
else {
    Write-Result -Test "Decision metrics" -Status "WARN" -Detail $metrics.Error
    New-Result -Test "Decision metrics" -Status "WARN" -Detail $metrics.Error
}

$evt = Invoke-SafeApi -Endpoint "/api/v1/event-runtime/stats"
if ($evt.Success) {
    $dlq = $evt.Data.dead_letter_count
    $dlqStatus = if ($dlq -eq 0) { "PASS" } else { "WARN" }
    Write-Result -Test "Event Runtime stats" -Status $dlqStatus -Detail "Dead letters: $dlq"
    New-Result -Test "Event Runtime" -Status $dlqStatus -Detail "DLQ=$dlq"
}
else {
    Write-Result -Test "Event Runtime stats" -Status "WARN" -Detail $evt.Error
    New-Result -Test "Event Runtime" -Status "WARN" -Detail $evt.Error
}

# ── Step 5: Summary ─────────────────────────────────────────────

Write-Step "STEP 5/5 — Summary Report"

$totalChecks = $results.Count
$passRate = if ($totalChecks -gt 0) { "{0:P0}" -f ($passed / $totalChecks) } else { "N/A" }

Write-Host ""
Write-Host "  ┌─────────────────────────────────────────────────────────┐" -ForegroundColor Cyan
Write-Host "  │              Pilot Verification Results                  │" -ForegroundColor Cyan
Write-Host "  ├─────────────────────────────────────────────────────────┤" -ForegroundColor Cyan
Write-Host "  │  Total checks:  $($totalChecks.ToString().PadRight(41))│" -ForegroundColor White
Write-Host "  │  Passed:        $($passed.ToString().PadRight(41))│" -ForegroundColor Green
Write-Host "  │  Failed:        $($failed.ToString().PadRight(41))│" -ForegroundColor $(if ($failed -gt 0) { "Red" } else { "White" })
Write-Host "  │  Warnings:      $($warnings.ToString().PadRight(41))│" -ForegroundColor Yellow
Write-Host "  │  Pass rate:     $($passRate.ToString().PadRight(41))│" -ForegroundColor $(if ($passRate -ge "80%") { "Green" } else { "Yellow" })
Write-Host "  └─────────────────────────────────────────────────────────┘" -ForegroundColor Cyan

if ($nbaResults.Count -gt 0) {
    Write-Host ""
    Write-Host "  ── NBA Results ──" -ForegroundColor Cyan
    foreach ($nr in $nbaResults) {
        $ico = if ($nr.Status -eq "PASS") { " + " } else { " X " }
        $icoColor = if ($nr.Status -eq "PASS") { "Green" } else { "Red" }
        Write-Host "  $ico $($nr.CompanyName.PadRight(22)) $($nr.Action.PadRight(30)) conf: $($nr.Confidence)" -ForegroundColor $icoColor
    }
}

Write-Host ""
if ($failed -eq 0 -and $warnings -eq 0) {
    Write-Host "  ALL CHECKS PASSED — Pilot ready" -ForegroundColor Green
    exit 0
}
else {
    Write-Host "  $failed failure(s), $warnings warning(s) — review before proceeding" -ForegroundColor Yellow
    exit 1
}
