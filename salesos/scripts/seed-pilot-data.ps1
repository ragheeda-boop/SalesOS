<#
.SYNOPSIS
    Seeds pilot data (companies, graph relationships) for all 3 pilot tenants.
.DESCRIPTION
    Runs the seed_data.py and seed_graph.py scripts for each pilot tenant,
    setting the SALESOS_TENANT environment variable for tenant-scoped seeding.
.PARAMETER ApiUrl
    Backend API base URL (default: http://localhost:8000)
#>

param(
    [string]$ApiUrl = "http://localhost:8000"
)

$ErrorActionPreference = "Continue"

$tenants = @("pilot-a", "pilot-b", "pilot-c")

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  SalesOS Pilot Data Seeding" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "  API:       $ApiUrl" -ForegroundColor White
Write-Host "  Tenants:   $($tenants.Count)" -ForegroundColor White
Write-Host "  Timestamp: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')" -ForegroundColor Gray
Write-Host ""

$allSuccess = $true
$results = @()

foreach ($t in $tenants) {
    Write-Host "========================================" -ForegroundColor Cyan
    Write-Host "  Seeding tenant: $t" -ForegroundColor White
    Write-Host "========================================" -ForegroundColor Cyan
    Write-Host ""

    # Set tenant context
    $env:SALESOS_TENANT = $t
    $env:SALESOS_TENANT_SLUG = $t
    Write-Host "  [ENV] SALESOS_TENANT=$t" -ForegroundColor Gray

    # --- Seed company data ---
    Write-Host ""
    Write-Host "  Running seed_data.py..." -ForegroundColor White
    try {
        $seedOutput = python backend/scripts/seed_data.py --tenant $t 2>&1
        $exitCode = $LASTEXITCODE

        if ($exitCode -eq 0) {
            Write-Host "  [OK] seed_data.py completed for $t" -ForegroundColor Green
            $results += @{ Tenant = $t; Script = "seed_data"; Status = "success" }
        }
        else {
            Write-Host "  [FAIL] seed_data.py failed (exit code: $exitCode)" -ForegroundColor Red
            Write-Host "  $seedOutput" -ForegroundColor DarkGray
            $results += @{ Tenant = $t; Script = "seed_data"; Status = "failed" }
            $allSuccess = $false
        }
    }
    catch {
        Write-Host "  [FAIL] seed_data.py error: $($_.Exception.Message)" -ForegroundColor Red
        $results += @{ Tenant = $t; Script = "seed_data"; Status = "error" }
        $allSuccess = $false
    }

    # --- Seed graph data ---
    Write-Host ""
    Write-Host "  Running seed_graph.py..." -ForegroundColor White
    try {
        $graphOutput = python backend/scripts/seed_graph.py --tenant $t 2>&1
        $exitCode = $LASTEXITCODE

        if ($exitCode -eq 0) {
            Write-Host "  [OK] seed_graph.py completed for $t" -ForegroundColor Green
            $results += @{ Tenant = $t; Script = "seed_graph"; Status = "success" }
        }
        else {
            Write-Host "  [WARN] seed_graph.py returned exit code $exitCode (may be non-critical)" -ForegroundColor Yellow
            Write-Host "  $graphOutput" -ForegroundColor DarkGray
            $results += @{ Tenant = $t; Script = "seed_graph"; Status = "warning" }
        }
    }
    catch {
        Write-Host "  [WARN] seed_graph.py error: $($_.Exception.Message)" -ForegroundColor Yellow
        $results += @{ Tenant = $t; Script = "seed_graph"; Status = "warning" }
    }

    # --- Verify data via API ---
    Write-Host ""
    Write-Host "  Verifying seeded data via API..." -ForegroundColor White

    try {
        $headers = @{
            "Content-Type" = "application/json"
            "X-Tenant-Id"  = $t
        }
        $companies = Invoke-RestMethod -Uri "$ApiUrl/api/v1/companies" -Method Get -Headers $headers -TimeoutSec 15
        $count = 0
        if ($companies -is [array]) { $count = $companies.Count }
        Write-Host "  [OK] Companies: $count" -ForegroundColor Green
    }
    catch {
        Write-Host "  [WARN] Could not verify companies: $($_.Exception.Message)" -ForegroundColor Yellow
    }

    Write-Host ""
}

# --- Summary ---

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  SEEDING SUMMARY" -ForegroundColor White
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

$successes = 0
$warnings = 0
$failures = 0

foreach ($r in $results) {
    if ($r.Status -eq "success") { $successes++ }
    elseif ($r.Status -eq "warning") { $warnings++ }
    else { $failures++ }
}

$color = "Green"
if ($failures -gt 0) { $color = "Red" }
elseif ($warnings -gt 0) { $color = "Yellow" }

Write-Host "  Results:  $successes succeeded, $warnings warnings, $failures failures" -ForegroundColor $color
Write-Host "  Tenants:  $($tenants -join ', ')" -ForegroundColor Gray
Write-Host ""

# Clean up env
Remove-Item -Path env:SALESOS_TENANT -ErrorAction SilentlyContinue
Remove-Item -Path env:SALESOS_TENANT_SLUG -ErrorAction SilentlyContinue

if ($failures -eq 0) {
    Write-Host "  Pilot data seeded for all tenants!" -ForegroundColor Green
    Write-Host "  Next: Run .\verify-pilot-deployment.ps1 -ApiUrl $ApiUrl" -ForegroundColor Gray
    exit 0
}
else {
    Write-Host "  Some seeding failed. Review output above." -ForegroundColor Yellow
    exit 1
}
