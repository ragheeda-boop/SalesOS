<#
.SYNOPSIS
    SalesOS per-domain coverage enforcement script.
    Runs pytest with coverage per domain and validates against minimum thresholds.

.DESCRIPTION
    Checks coverage for each domain against minimums:
      Identity: 88%  |  Company: 80%  |  Search: 93%   |  Timeline: 82%
      CRM: 80%       |  Scoring: 78%  |  AI: 92%       |  Workflow: 95%

.EXAMPLE
    .\scripts\check-coverage.ps1
    .\scripts\check-coverage.ps1 -Domain identity,search
    .\scripts\check-coverage.ps1 -SkipE2E
    .\scripts\check-coverage.ps1 -Json
#>

param(
    [string[]]$Domain = @(),
    [switch]$SkipE2E,
    [switch]$Json,
    [string]$BackendDir = (Join-Path $PSScriptRoot ".." "backend")
)

$ErrorActionPreference = "Stop"
$BackendDir = Resolve-Path $BackendDir

$thresholds = @{
    identity = @{ Min = 88; Paths = @("app/modules/identity") }
    company  = @{ Min = 80; Paths = @("app/modules/company") }
    search   = @{ Min = 93; Paths = @("domains/search") }
    timeline = @{ Min = 82; Paths = @("domains/timeline") }
    crm      = @{ Min = 80; Paths = @("domains/commercial") }
    scoring  = @{ Min = 78; Paths = @("domains/scoring") }
    ai       = @{ Min = 92; Paths = @("app/modules/ai") }
    workflow = @{ Min = 95; Paths = @("domains/workflow") }
}

$targets = if ($Domain.Count -gt 0) {
    $script:thresholds.GetEnumerator() | Where-Object { $_.Key -in $Domain }
} else {
    $script:thresholds.GetEnumerator()
}

$pytestArgs = @("-q", "--no-header", "--tb=short")
if ($SkipE2E) { $pytestArgs += "-m", "not e2e" }

$overallPass = $true
$results = @()

Write-Host "`n=== SalesOS Per-Domain Coverage Check ===" -ForegroundColor Cyan
Write-Host "Backend: $BackendDir`n"

foreach ($entry in $targets) {
    $domain = $entry.Key
    $min = $entry.Value.Min
    $paths = $entry.Value.Paths

    Write-Host "[$domain] Running coverage..." -ForegroundColor Yellow
    $covFile = Join-Path $BackendDir ".coverage_$domain"

    $covSources = ($paths | ForEach-Object { "--cov=$_" }) -join " "
    $cmd = "pytest $covSources --cov-report=term-missing --cov-branch $($pytestArgs -join ' ') --override-ini=cache_dir=.pytest_cache_$domain"
    $cmd += " 2>&1"

    Push-Location $BackendDir
    try {
        $output = Invoke-Expression $cmd
    } finally {
        Pop-Location
    }

    $coveragePct = 0
    $lines = $output -split "`n"
    foreach ($line in $lines) {
        if ($line -match "TOTAL\s+\d+\s+\d+\s+(\d+)%") {
            $coveragePct = [int]$Matches[1]
            break
        }
        if ($line -match "^TOTAL\s+\d+\s+\d+\s+(\d+)%") {
            $coveragePct = [int]$Matches[1]
            break
        }
    }

    $passed = $coveragePct -ge $min
    if (-not $passed) { $overallPass = $false }

    $status = if ($passed) { "PASS" } else { "FAIL" }
    $color = if ($passed) { "Green" } else { "Red" }
    Write-Host "  [$status] $domain : $coveragePct% / $min%" -ForegroundColor $color

    $results += @{
        domain   = $domain
        coverage = $coveragePct
        minimum  = $min
        passed   = $passed
    }
}

Write-Host ""
Write-Host "=== Summary ===" -ForegroundColor Cyan
Write-Host ("{0,-12} {1,>8} {2,>8} {3,>8}" -f "Domain", "Coverage", "Minimum", "Status")
Write-Host ("{0,-12} {1,>8} {2,>8} {3,>8}" -f "--------", "--------", "--------", "------")

foreach ($r in $results) {
    $statusStr = if ($r.passed) { "PASS" } else { "FAIL" }
    Write-Host ("{0,-12} {1,>7}% {2,>7}% {3,>8}" -f $r.domain, $r.coverage, $r.minimum, $statusStr)
}

if ($Json) {
    Write-Host ""
    Write-Host ($results | ConvertTo-Json -Compress)
}

Write-Host ""
if (-not $overallPass) {
    Write-Host "FAIL: One or more domains below minimum coverage." -ForegroundColor Red
    exit 1
} else {
    Write-Host "PASS: All domains meet minimum coverage thresholds." -ForegroundColor Green
    exit 0
}
