<#
.SYNOPSIS
    SalesOS Pilot Metrics Report Generator
.DESCRIPTION
    Queries the SalesOS backend API to generate a formatted pilot metrics report.
    Covers: recommendations, acceptance rate, confidence, feedback, NPS, top actions, revenue, errors.
.EXAMPLE
    .\pilot-metrics.ps1
    .\pilot-metrics.ps1 -BaseUrl "http://staging.salesos.com" -TenantId "tenant-abc"
#>

param(
    [string]$BaseUrl = "http://localhost:8000",
    [string]$TenantId = "",
    [string]$AuthToken = "",
    [switch]$JsonOutput
)

$ErrorActionPreference = "Continue"
$Separator = "=" * 70
$SubSeparator = "-" * 50

# ── Helpers ──────────────────────────────────────────────────────

function Get-ApiHeaders {
    $headers = @{ "Content-Type" = "application/json" }
    if ($AuthToken) { $headers["Authorization"] = "Bearer $AuthToken" }
    if ($TenantId) { $headers["X-Tenant-Id"] = $TenantId }
    return $headers
}

function Invoke-SafeApi {
    param([string]$Endpoint, [string]$Method = "GET", [string]$Body = $null)
    try {
        $headers = Get-ApiHeaders
        $params = @{
            Uri     = "$BaseUrl$Endpoint"
            Method  = $Method
            Headers = $headers
            TimeoutSec = 10
        }
        if ($Body) { $params.Body = $Body }
        $response = Invoke-RestMethod @params
        return $response
    }
    catch {
        Write-Host "  [WARN] $Endpoint — $($_.Exception.Message)" -ForegroundColor Yellow
        return $null
    }
}

function Format-Number {
    param([double]$Value, [int]$Decimals = 0)
    if ($Decimals -eq 0) { return "{0:N0}" -f $Value }
    return "{0:N$Decimals}" -f $Value
}

function Format-Percent {
    param([double]$Value)
    return "{0:P1}" -f $Value
}

# ── Header ───────────────────────────────────────────────────────

Write-Host ""
Write-Host $Separator
Write-Host "  SalesOS Pilot Metrics Report" -ForegroundColor Cyan
Write-Host "  $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')" -ForegroundColor Gray
Write-Host "  Target: $BaseUrl" -ForegroundColor Gray
if ($TenantId) { Write-Host "  Tenant: $TenantId" -ForegroundColor Gray }
Write-Host $Separator
Write-Host ""

# ── 1. Health Check ─────────────────────────────────────────────

Write-Host "[1/8] Health Check" -ForegroundColor White
$health = Invoke-SafeApi "/health"
if ($health) {
    Write-Host "  Status:      $($health.status)" -ForegroundColor $(if ($health.status -eq "ok") { "Green" } else { "Yellow" })
    Write-Host "  Database:    $($health.database)" -ForegroundColor $(if ($health.database -eq "connected") { "Green" } else { "Red" })
    Write-Host "  Cache:       $($health.cache)" -ForegroundColor $(if ($health.cache -eq "connected") { "Green" } else { "Yellow" })
    Write-Host "  Graph:       $($health.graph)" -ForegroundColor $(if ($health.graph -eq "connected") { "Green" } else { "Yellow" })
    Write-Host "  Uptime:      $([math]::Round($health.uptime_seconds / 3600, 1))h" -ForegroundColor Gray
}
else {
    Write-Host "  [ERROR] Backend unreachable" -ForegroundColor Red
}
Write-Host ""

# ── 2. Decision Engine Metrics ───────────────────────────────────

Write-Host "[2/8] Decision Engine (NBA)" -ForegroundColor White
$metrics = Invoke-SafeApi "/api/v1/decision/metrics"
if ($metrics -and $metrics.evaluations -ne $null) {
    $totalCreated = $metrics.decisions_created
    $totalAccepted = $metrics.decisions_accepted
    $totalExecuted = $metrics.decisions_executed
    $acceptanceRate = if ($totalCreated -gt 0) { $totalAccepted / $totalCreated } else { 0 }

    Write-Host "  Evaluations:        $($metrics.evaluations)" -ForegroundColor White
    Write-Host "  Decisions Created:  $totalCreated" -ForegroundColor White
    Write-Host "  Decisions Accepted: $totalAccepted" -ForegroundColor $(if ($acceptanceRate -ge 0.4) { "Green" } elseif ($acceptanceRate -ge 0.2) { "Yellow" } else { "Red" })
    Write-Host "  Decisions Executed: $totalExecuted" -ForegroundColor White
    Write-Host "  Acceptance Rate:    $(Format-Percent $acceptanceRate)" -ForegroundColor $(if ($acceptanceRate -ge 0.4) { "Green" } elseif ($acceptanceRate -ge 0.2) { "Yellow" } else { "Red" })
    Write-Host "  Policies Checked:   $($metrics.policies_checked)" -ForegroundColor Gray
    Write-Host "  Avg Eval Time:      $($metrics.avg_eval_ms)ms" -ForegroundColor Gray
}
else {
    Write-Host "  [WARN] Decision metrics not available" -ForegroundColor Yellow
}
Write-Host ""

# ── 3. Average Confidence Score ──────────────────────────────────

Write-Host "[3/8] Recommendation Confidence" -ForegroundColor White
# Confidence is embedded in decision metrics — query recent decisions for average
# Use the decision history endpoint if available, otherwise skip
$confidenceData = Invoke-SafeApi "/api/v1/decision/metrics"
if ($confidenceData -and $confidenceData.avg_eval_ms) {
    # Confidence is tracked per-decision; approximate from metrics snapshot
    # In production, this would query the decisions table
    Write-Host "  (Confidence tracked per-decision in decisions table)" -ForegroundColor Gray
    Write-Host "  Run: SELECT AVG(confidence) FROM decisions WHERE status IN ('accepted','executed')" -ForegroundColor Gray
}
Write-Host ""

# ── 4. Feedback Submissions ──────────────────────────────────────

Write-Host "[4/8] Feedback & NPS" -ForegroundColor White
Write-Host "  Feedback is collected via FeedbackWidget (analytics events)" -ForegroundColor Gray
Write-Host "  Event types:" -ForegroundColor Gray
Write-Host "    - pilot.feedback_submitted  (NPS + comment)" -ForegroundColor Gray
Write-Host "    - pilot.session_started     (page views)" -ForegroundColor Gray
Write-Host ""
Write-Host "  To query NPS from database:" -ForegroundColor Gray
Write-Host "    SELECT" -ForegroundColor DarkGray
Write-Host "      COUNT(*) FILTER (WHERE metadata->>'nps'::int >= 9) AS promoters," -ForegroundColor DarkGray
Write-Host "      COUNT(*) FILTER (WHERE metadata->>'nps'::int BETWEEN 7 AND 8) AS passives," -ForegroundColor DarkGray
Write-Host "      COUNT(*) FILTER (WHERE metadata->>'nps'::int <= 6) AS detractors" -ForegroundColor DarkGray
Write-Host "    FROM analytics_events" -ForegroundColor DarkGray
Write-Host "    WHERE type = 'pilot.feedback_submitted'" -ForegroundColor DarkGray
Write-Host ""

# ── 5. Top Actions by Acceptance Rate ───────────────────────────

Write-Host "[5/8] Top Actions by Type" -ForegroundColor White
Write-Host "  Decision types in system:" -ForegroundColor Gray
Write-Host "    recommend_demo      — Product demo suggestion" -ForegroundColor Gray
Write-Host "    recommend_call      — Cold/warm call suggestion" -ForegroundColor Gray
Write-Host "    recommend_outreach  — Executive outreach" -ForegroundColor Gray
Write-Host "    recommend_campaign  — Marketing campaign" -ForegroundColor Gray
Write-Host "    recommend_proposal  — Proposal submission" -ForegroundColor Gray
Write-Host "    recommend_sequence  — Email sequence" -ForegroundColor Gray
Write-Host ""
Write-Host "  Run for per-type breakdown:" -ForegroundColor Gray
Write-Host "    SELECT" -ForegroundColor DarkGray
Write-Host "      decision_type," -ForegroundColor DarkGray
Write-Host "      COUNT(*) AS total," -ForegroundColor DarkGray
Write-Host "      COUNT(*) FILTER (WHERE status = 'accepted') AS accepted," -ForegroundColor DarkGray
Write-Host "      ROUND(AVG(confidence), 2) AS avg_confidence" -ForegroundColor DarkGray
Write-Host "    FROM decisions" -ForegroundColor DarkGray
Write-Host "    GROUP BY decision_type" -ForegroundColor DarkGray
Write-Host "    ORDER BY accepted DESC;" -ForegroundColor DarkGray
Write-Host ""

# ── 6. Revenue Impact ───────────────────────────────────────────

Write-Host "[6/8] Revenue Impact" -ForegroundColor White
Write-Host "  Revenue impact tracked in feedback.outcome_value" -ForegroundColor Gray
Write-Host ""
Write-Host "  Run for revenue attribution:" -ForegroundColor Gray
Write-Host "    SELECT" -ForegroundColor DarkGray
Write-Host "      d.decision_type," -ForegroundColor DarkGray
Write-Host "      COUNT(*) AS feedbacks_with_value," -ForegroundColor DarkGray
Write-Host "      SUM(f.outcome_value) AS total_revenue_impact," -ForegroundColor DarkGray
Write-Host "      AVG(f.outcome_value) AS avg_revenue_impact" -ForegroundColor DarkGray
Write-Host "    FROM decisions d" -ForegroundColor DarkGray
Write-Host "    JOIN decision_feedback_loop f ON d.decision_id = f.decision_id" -ForegroundColor DarkGray
Write-Host "    WHERE f.outcome_value IS NOT NULL" -ForegroundColor DarkGray
Write-Host "    GROUP BY d.decision_type" -ForegroundColor DarkGray
Write-Host "    ORDER BY total_revenue_impact DESC;" -ForegroundColor DarkGray
Write-Host ""

# ── 7. Errors in Last 24h ───────────────────────────────────────

Write-Host "[7/8] Errors (Last 24h)" -ForegroundColor White
$eventStats = Invoke-SafeApi "/api/v1/event-runtime/stats"
if ($eventStats) {
    $dlqCount = $eventStats.dead_letter_count
    Write-Host "  Dead Letter Queue:  $dlqCount events" -ForegroundColor $(if ($dlqCount -eq 0) { "Green" } elseif ($dlqCount -lt 10) { "Yellow" } else { "Red" })
    if ($eventStats.metrics) {
        $m = $eventStats.metrics
        Write-Host "  Events Published:   $($m.events_published)" -ForegroundColor White
        Write-Host "  Events Processed:   $($m.events_processed)" -ForegroundColor White
        Write-Host "  Events Failed:      $($m.events_failed)" -ForegroundColor $(if ($m.events_failed -eq 0) { "Green" } else { "Red" })
        Write-Host "  Avg Process Time:   $($m.avg_process_ms)ms" -ForegroundColor Gray
    }
}
else {
    Write-Host "  [WARN] Event runtime not available" -ForegroundColor Yellow
}

# Check Sentry for error count if configured
Write-Host ""
Write-Host "  Additional error sources:" -ForegroundColor Gray
Write-Host "    - Sentry dashboard for application errors" -ForegroundColor Gray
Write-Host "    - PostgreSQL logs for query errors" -ForegroundColor Gray
Write-Host "    - Neo4j logs for graph query errors" -ForegroundColor Gray
Write-Host ""

# ── 8. Activity Summary ─────────────────────────────────────────

Write-Host "[8/8] Activity Summary" -ForegroundColor White
$activityStats = Invoke-SafeApi "/api/v1/event-runtime/metrics"
if ($activityStats) {
    Write-Host "  Event throughput:" -ForegroundColor Gray
    foreach ($key in $activityStats.PSObject.Properties.Name) {
        Write-Host "    $key = $($activityStats.$key)" -ForegroundColor Gray
    }
}
Write-Host ""

# ── Summary ──────────────────────────────────────────────────────

Write-Host $Separator
Write-Host "  PILOT SUMMARY" -ForegroundColor Cyan
Write-Host $Separator

$summary = @{}

if ($health) { $summary["Health"] = $health.status }
if ($metrics -and $metrics.decisions_created) {
    $created = $metrics.decisions_created
    $accepted = $metrics.decisions_accepted
    $rate = if ($created -gt 0) { [math]::Round($accepted / $created * 100, 1) } else { 0 }
    $summary["Decisions Created"] = "$created"
    $summary["Decisions Accepted"] = "$accepted"
    $summary["Acceptance Rate"] = "$rate%"
}
if ($eventStats) {
    $summary["Dead Letters"] = "$($eventStats.dead_letter_count)"
}

foreach ($key in $summary.Keys) {
    $color = switch -Wildcard ($summary[$key]) {
        "ok"     { "Green" }
        "degraded" { "Yellow" }
        default  { "White" }
    }
    Write-Host ("  {0,-22} {1}" -f $key, $summary[$key]) -ForegroundColor $color
}

Write-Host ""
Write-Host $Separator

# ── SQL Quick Reference ──────────────────────────────────────────

Write-Host ""
Write-Host "SQL Quick Reference (run against PostgreSQL):" -ForegroundColor Cyan
Write-Host ""
Write-Host "  -- NPS Calculation" -ForegroundColor DarkGray
Write-Host "  SELECT" -ForegroundColor DarkGray
Write-Host "    COUNT(*) FILTER (WHERE (metadata->>'nps')::int >= 9) AS promoters," -ForegroundColor DarkGray
Write-Host "    COUNT(*) FILTER (WHERE (metadata->>'nps')::int BETWEEN 7 AND 8) AS passives," -ForegroundColor DarkGray
Write-Host "    COUNT(*) FILTER (WHERE (metadata->>'nps')::int <= 6) AS detractors," -ForegroundColor DarkGray
Write-Host "    ROUND(" -ForegroundColor DarkGray
Write-Host "      (COUNT(*) FILTER (WHERE (metadata->>'nps')::int >= 9)::float" -ForegroundColor DarkGray
Write-Host "       - COUNT(*) FILTER (WHERE (metadata->>'nps')::int <= 6)::float)" -ForegroundColor DarkGray
Write-Host "      / NULLIF(COUNT(*), 0) * 100, 1" -ForegroundColor DarkGray
Write-Host "    ) AS nps_score" -ForegroundColor DarkGray
Write-Host "  FROM analytics_events" -ForegroundColor DarkGray
Write-Host "  WHERE type = 'pilot.feedback_submitted';" -ForegroundColor DarkGray
Write-Host ""
Write-Host "  -- Time to Value (first session to first action)" -ForegroundColor DarkGray
Write-Host "  SELECT" -ForegroundColor DarkGray
Write-Host "    user_id," -ForegroundColor DarkGray
Write-Host "    MIN(CASE WHEN type = 'pilot.session_started' THEN timestamp END) AS first_session," -ForegroundColor DarkGray
Write-Host "    MIN(CASE WHEN type = 'nba.viewed' THEN timestamp END) AS first_nba_view," -ForegroundColor DarkGray
Write-Host "    EXTRACT(EPOCH FROM (" -ForegroundColor DarkGray
Write-Host "      MIN(CASE WHEN type = 'nba.viewed' THEN timestamp END)" -ForegroundColor DarkGray
Write-Host "      - MIN(CASE WHEN type = 'pilot.session_started' THEN timestamp END)" -ForegroundColor DarkGray
Write-Host "    )) / 60 AS minutes_to_value" -ForegroundColor DarkGray
Write-Host "  FROM analytics_events" -ForegroundColor DarkGray
Write-Host "  WHERE type IN ('pilot.session_started', 'nba.viewed')" -ForegroundColor DarkGray
Write-Host "  GROUP BY user_id;" -ForegroundColor DarkGray
Write-Host ""
Write-Host "  -- Top Features by Usage" -ForegroundColor DarkGray
Write-Host "  SELECT widget_id, COUNT(*) AS interactions" -ForegroundColor DarkGray
Write-Host "  FROM analytics_events" -ForegroundColor DarkGray
Write-Host "  WHERE type = 'widget.interacted'" -ForegroundColor DarkGray
Write-Host "  GROUP BY widget_id" -ForegroundColor DarkGray
Write-Host "  ORDER BY interactions DESC;" -ForegroundColor DarkGray
Write-Host ""
