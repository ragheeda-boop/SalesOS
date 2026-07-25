<#
.SYNOPSIS
  Wave 13 - authenticated frontend UI smoke (Playwright, chromium).

.DESCRIPTION
  Registers a disposable @example.com user via API (same contract as smoke-auth.ps1),
  then runs e2e/smoke-auth-ui.spec.ts against local FE. Captures page probe JSON under
  salesos/frontend/test-results/smoke-ui/. Does not print JWTs. Light validated only -
  never claims Production GO.

.EXAMPLE
  .\scripts\smoke-ui.ps1
  .\scripts\smoke-ui.ps1 -BaseUrl http://localhost:8000 -FrontendUrl http://localhost:3000
  .\scripts\smoke-ui.ps1 -Email smoke.ui.probe9@example.com -Password 'SmokeAuthPass123!' -SkipRegister
  # Existing account via env (do not commit secrets):
  $env:SMOKE_EMAIL='…'; $env:SMOKE_PASSWORD='…'; .\scripts\smoke-ui.ps1 -SkipRegister
#>

param(
    [string]$BaseUrl = "http://127.0.0.1:8000",
    [string]$FrontendUrl = "http://127.0.0.1:3000",
    [string]$Email = "",
    [string]$Password = "SmokeAuthPass123!",
    [switch]$SkipRegister
)

$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $PSScriptRoot
$frontend = Join-Path $root "frontend"
$reportDir = Join-Path $frontend "test-results\smoke-ui"

# Prefer process env over defaults (never hardcode demo/prod secrets in repo).
if (-not $Email -and $env:SMOKE_EMAIL) { $Email = $env:SMOKE_EMAIL }
if ($env:SMOKE_PASSWORD) { $Password = $env:SMOKE_PASSWORD }

if (-not $Email) {
    $suffix = [guid]::NewGuid().ToString("N").Substring(0, 8)
    $Email = "smoke.ui.$suffix@example.com"
}

function Write-Utf8NoBom {
    param([string]$Path, [string]$Value)
    $utf8 = New-Object System.Text.UTF8Encoding $false
    [System.IO.File]::WriteAllText($Path, $Value, $utf8)
}

$acctLabel = if ($SkipRegister) { "existing (SkipRegister / SMOKE_* env)" } else { "disposable local" }
Write-Host "========== SalesOS UI Smoke (Wave 13) ==========" -ForegroundColor Cyan
Write-Host "BaseUrl:     $BaseUrl"
Write-Host "FrontendUrl: $FrontendUrl"
Write-Host "Email:       $Email ($acctLabel)"
Write-Host ""

# Preflight (curl is more reliable than IWR against Docker Desktop ports)
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
$healthCode = Get-HttpCode ($BaseUrl.TrimEnd('/') + "/health")
if ($healthCode -eq 200) {
    Write-Host "  [PASS] API /health" -ForegroundColor Green
} else {
    Write-Host "  [FAIL] API /health (got $healthCode)" -ForegroundColor Red
    exit 1
}
$feCode = Get-HttpCode ($FrontendUrl.TrimEnd('/') + "/")
if ($feCode -eq 200) {
    Write-Host "  [PASS] Frontend /" -ForegroundColor Green
} else {
    Write-Host "  [FAIL] Frontend / (got $feCode)" -ForegroundColor Red
    exit 1
}


if (-not $SkipRegister) {
    Write-Host ""
    Write-Host "--- Register disposable user ---" -ForegroundColor Yellow
    $tmp = Join-Path ([System.IO.Path]::GetTempPath()) ("salesos-smoke-ui-" + [guid]::NewGuid().ToString("N"))
    New-Item -ItemType Directory -Force -Path $tmp | Out-Null
    $regPath = Join-Path $tmp "register.json"
    $regObj = @{ email = $Email; password = $Password; full_name = "Wave13 UI Smoke" } | ConvertTo-Json -Compress
    Write-Utf8NoBom -Path $regPath -Value $regObj
    try {
        # Identity register can take 30-60s under local Docker load.
        $reg = Invoke-WebRequest -Uri ($BaseUrl.TrimEnd('/') + "/api/v1/identity/register") `
            -Method POST -InFile $regPath -ContentType "application/json" `
            -UseBasicParsing -TimeoutSec 120
        $ok = $reg.StatusCode -in 200, 201
        $tokenPresent = $reg.Content -match '"access_token"'
        if ($ok -and $tokenPresent) {
            Write-Host "  [PASS] POST /api/v1/identity/register ($($reg.StatusCode), token_present)" -ForegroundColor Green
        } else {
            Write-Host "  [FAIL] POST /api/v1/identity/register ($($reg.StatusCode))" -ForegroundColor Red
            exit 1
        }
    } catch {
        $code = $null
        if ($_.Exception.Response) { $code = [int]$_.Exception.Response.StatusCode }
        if ($code -eq 429) {
            Write-Host "  [FAIL] register rate_limited (429) - wait ~60s and re-run" -ForegroundColor Red
            exit 1
        }
        if ($code -eq 409 -or ($_.ErrorDetails.Message -match 'already|exists')) {
            Write-Host "  [WARN] register conflict - continuing with provided email/password" -ForegroundColor Yellow
        } else {
            Write-Host "  [FAIL] register - $_" -ForegroundColor Red
            exit 1
        }
    } finally {
        if (Test-Path $tmp) { Remove-Item -Recurse -Force -LiteralPath $tmp -ErrorAction SilentlyContinue }
    }
} else {
    Write-Host "  [SKIP] register (-SkipRegister)" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "--- Playwright smoke (chromium) ---" -ForegroundColor Yellow
New-Item -ItemType Directory -Force -Path $reportDir | Out-Null

$env:E2E_USER_EMAIL = $Email
$env:E2E_USER_PASSWORD = $Password
$env:API_BASE_URL = $BaseUrl
$env:BASE_URL = $FrontendUrl
$env:SMOKE_UI_REPORT_DIR = $reportDir

Push-Location $frontend
try {
    # Reuse existing FE; do not start a second npm run dev from playwright webServer when possible.
    # CI=false + reuseExistingServer is already set in playwright.config for non-CI.
    & npx playwright test --config playwright.smoke.config.ts --project=chromium --reporter=list
    $pwExit = $LASTEXITCODE
} finally {
    Pop-Location
    Remove-Item Env:E2E_USER_PASSWORD -ErrorAction SilentlyContinue
}

$reportJson = Join-Path $reportDir "smoke-auth-ui-report.json"
if (Test-Path $reportJson) {
    Write-Host ""
    Write-Host "Report: $reportJson" -ForegroundColor Cyan
    try {
        $j = Get-Content $reportJson -Raw | ConvertFrom-Json
        Write-Host ("PASS pages={0} FAIL pages={1}" -f $j.passCount, $j.failCount)
        foreach ($p in $j.pages) {
            $st = if ($p.ok) { "PASS" } else { "FAIL" }
            Write-Host ("  [{0}] {1} -> {2} ({3})" -f $st, $p.path, $p.finalUrl, ($p.notes -join '; '))
        }
    } catch {
        Write-Host "  (could not parse report JSON)" -ForegroundColor Yellow
    }
}

Write-Host ""
if ($pwExit -ne 0) {
    Write-Host "OVERALL: FAIL (Playwright exit $pwExit)" -ForegroundColor Red
    Write-Host "Validation: light validated only - NOT Production GO" -ForegroundColor Yellow
    exit $pwExit
}
Write-Host "OVERALL: PASS" -ForegroundColor Green
Write-Host "Validation: light validated only - NOT Production GO" -ForegroundColor Yellow
exit 0
