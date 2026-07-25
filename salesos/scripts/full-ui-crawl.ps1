<#
.SYNOPSIS
  Wave 13 - full authenticated UI crawl (Playwright chromium).

.DESCRIPTION
  Logs in with SMOKE_EMAIL / SMOKE_PASSWORD (or -Email/-Password), crawls primary
  nav + deep routes, clicks visible in-app controls, writes evidence JSON.
  Does NOT print passwords. Does NOT kill soak processes. Light validated only -
  never claims Production GO.

.EXAMPLE
  $env:SMOKE_EMAIL='admin@salesos.io'
  $env:SMOKE_PASSWORD='***'
  .\scripts\full-ui-crawl.ps1

  .\scripts\full-ui-crawl.ps1 -Email admin@salesos.io
  # password from SMOKE_PASSWORD env
#>

param(
    [string]$BaseUrl = "http://127.0.0.1:8000",
    [string]$FrontendUrl = "http://127.0.0.1:3000",
    [string]$Email = "",
    [string]$Password = "",
    [string]$ReportDir = "",
    [int]$MaxClicks = 8
)

$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $PSScriptRoot
$frontend = Join-Path $root "frontend"
$repoRoot = Split-Path -Parent $root
$defaultEvidence = Join-Path $repoRoot "docs\audit\ga-engineering-audit\evidence\wave13-full-ui-crawl"

if (-not $Email -and $env:SMOKE_EMAIL) { $Email = $env:SMOKE_EMAIL }
if (-not $Email -and $env:E2E_USER_EMAIL) { $Email = $env:E2E_USER_EMAIL }
if (-not $Password -and $env:SMOKE_PASSWORD) { $Password = $env:SMOKE_PASSWORD }
if (-not $Password -and $env:E2E_USER_PASSWORD) { $Password = $env:E2E_USER_PASSWORD }

if (-not $ReportDir) {
    if ($env:CRAWL_REPORT_DIR) { $ReportDir = $env:CRAWL_REPORT_DIR }
    else { $ReportDir = $defaultEvidence }
}

if (-not $Email -or -not $Password) {
    Write-Host "ERROR: Set SMOKE_EMAIL + SMOKE_PASSWORD (or -Email and password via env)." -ForegroundColor Red
    Write-Host "Passwords must not be committed; use env vars only." -ForegroundColor Yellow
    exit 2
}

function Get-HttpCode([string]$Url) {
    $prev = $ErrorActionPreference
    $ErrorActionPreference = "Continue"
    $codeRaw = & curl.exe -sS --max-time 60 -o NUL -w "%{http_code}" $Url 2>$null
    $exit = $LASTEXITCODE
    $ErrorActionPreference = $prev
    if ($exit -ne 0) { return 0 }
    $raw = ("$codeRaw").Trim()
    if ($raw -match '(\d{3})$') { return [int]$Matches[1] }
    return 0
}

Write-Host "========== SalesOS Full UI Crawl (Wave 13) ==========" -ForegroundColor Cyan
Write-Host "BaseUrl:     $BaseUrl"
Write-Host "FrontendUrl: $FrontendUrl"
Write-Host "Email:       $Email (password from env - not printed)"
Write-Host "ReportDir:   $ReportDir"
Write-Host "MaxClicks:   $MaxClicks"
Write-Host "Note:        Read-only browse vs soak; do not kill PID on :8000/:3000"
Write-Host ""

$healthCode = Get-HttpCode ($BaseUrl.TrimEnd('/') + "/health")
if ($healthCode -eq 200) {
    Write-Host "  [PASS] API /health" -ForegroundColor Green
} else {
    Write-Host "  [FAIL] API /health (got $healthCode)" -ForegroundColor Red
    exit 1
}
$feCode = Get-HttpCode ($FrontendUrl.TrimEnd('/') + "/login")
if ($feCode -eq 200) {
    Write-Host "  [PASS] Frontend /login" -ForegroundColor Green
} else {
    Write-Host "  [FAIL] Frontend /login (got $feCode)" -ForegroundColor Red
    exit 1
}

New-Item -ItemType Directory -Force -Path $ReportDir | Out-Null
$screenshots = Join-Path $ReportDir "screenshots"
New-Item -ItemType Directory -Force -Path $screenshots | Out-Null

$env:E2E_USER_EMAIL = $Email
$env:E2E_USER_PASSWORD = $Password
$env:API_BASE_URL = $BaseUrl
$env:BASE_URL = $FrontendUrl
$env:CRAWL_REPORT_DIR = $ReportDir
$env:CRAWL_MAX_CLICKS = "$MaxClicks"

Write-Host ""
Write-Host "--- Playwright full UI crawl (chromium) ---" -ForegroundColor Yellow
Push-Location $frontend
try {
    & npx playwright test --config playwright.full-crawl.config.ts --project=chromium --reporter=list
    $pwExit = $LASTEXITCODE
} finally {
    Pop-Location
    Remove-Item Env:E2E_USER_PASSWORD -ErrorAction SilentlyContinue
    Remove-Item Env:SMOKE_PASSWORD -ErrorAction SilentlyContinue
}

$reportJson = Join-Path $ReportDir "full-ui-crawl-report.json"
if (Test-Path $reportJson) {
    Write-Host ""
    Write-Host "Report: $reportJson" -ForegroundColor Cyan
    try {
        $j = Get-Content $reportJson -Raw | ConvertFrom-Json
        Write-Host ("PASS={0} FAIL={1} clicks={2} coverage~{3}%" -f $j.passCount, $j.failCount, $j.clicksAttempted, $j.coverageEstimatePct)
        foreach ($p in $j.pages) {
            $st = if ($p.ok) { "PASS" } else { "FAIL" }
            Write-Host ("  [{0}] {1} ({2})" -f $st, $p.path, ($p.notes -join '; '))
        }
        if ($j.criticalFailures -and $j.criticalFailures.Count -gt 0) {
            Write-Host ""
            Write-Host "Critical page failures:" -ForegroundColor Yellow
            foreach ($c in $j.criticalFailures) {
                Write-Host ("  - {0}: {1}" -f $c.path, ($c.notes -join '; '))
            }
        }
    } catch {
        Write-Host "  (could not parse report JSON)" -ForegroundColor Yellow
    }
} else {
    Write-Host "  [WARN] report JSON missing: $reportJson" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "Validation: light validated UI crawl - NOT Production GO" -ForegroundColor Yellow
if ($null -eq $pwExit) { $pwExit = 1 }
if ($pwExit -ne 0) {
    Write-Host "OVERALL: FAIL (Playwright exit $pwExit)" -ForegroundColor Red
    exit $pwExit
}
Write-Host "OVERALL: PASS (soft nav majority gate)" -ForegroundColor Green
exit 0
