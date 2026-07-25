<#
.SYNOPSIS
  SalesOS pre-deploy gates (Wave 12) - fail closed before staging/prod traffic.

.DESCRIPTION
  Fails (exit 1) if any hard gate fails:
    1. Alembic drift (current != heads) via check_alembic_head.py
    2. Backend /health not ok
    3. SALESOS_TESTING set to a truthy / trap value in the target env
  Optional:
    -RunUnitTests  -> docker-exec pytest tests/unit (heavy; opt-in)

  Does NOT deploy. Does NOT run alembic upgrade. Does NOT claim Production GO.

.PARAMETER BackendUrl
  Health probe base URL (default: http://localhost:8000)

.PARAMETER ComposeFile
  Path to docker-compose.yml used for exec (default: salesos/docker-compose.yml)

.PARAMETER BackendService
  Compose service name for backend (default: backend)

.PARAMETER SkipDocker
  Skip docker compose exec; run alembic check on host and only probe HTTP health

.PARAMETER RunUnitTests
  Also run unit pytest in the backend container (optional gate)

.PARAMETER HealthTimeoutSec
  HTTP timeout for /health (default: 15)

.EXAMPLE
  .\scripts\pre-deploy-gates.ps1
  .\scripts\pre-deploy-gates.ps1 -RunUnitTests
  .\scripts\pre-deploy-gates.ps1 -BackendUrl http://staging-api:8000 -SkipDocker
#>
[CmdletBinding()]
param(
    [string]$BackendUrl = "http://localhost:8000",
    [string]$ComposeFile = "",
    [string]$BackendService = "backend",
    [switch]$SkipDocker,
    [switch]$RunUnitTests,
    [int]$HealthTimeoutSec = 15
)

$ErrorActionPreference = "Stop"
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$salesosRoot = Split-Path -Parent $scriptDir

if (-not $ComposeFile) {
    $ComposeFile = Join-Path $salesosRoot "docker-compose.yml"
}

$script:failed = 0
$script:passed = 0
$script:warnings = 0

function Write-GateHeader {
    Write-Host ""
    Write-Host "============================================" -ForegroundColor Cyan
    Write-Host "  SalesOS Pre-Deploy Gates (Wave 12)" -ForegroundColor Cyan
    Write-Host "  $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')" -ForegroundColor Cyan
    Write-Host "  Classification: NOT Production GO" -ForegroundColor DarkYellow
    Write-Host "============================================" -ForegroundColor Cyan
    Write-Host ""
}

function Write-Gate {
    param([string]$Name, [string]$Status, [string]$Detail = "")
    $color = switch ($Status) {
        "PASS" { "Green" }
        "FAIL" { "Red" }
        "WARN" { "DarkYellow" }
        "SKIP" { "Gray" }
        default { "White" }
    }
    $detailStr = if ($Detail) { " - $Detail" } else { "" }
    Write-Host ("  [{0}] {1}{2}" -f $Status, $Name, $detailStr) -ForegroundColor $color
    switch ($Status) {
        "PASS" { $script:passed++ }
        "FAIL" { $script:failed++ }
        "WARN" { $script:warnings++ }
    }
}

function Test-SalesosTestingTrap {
    param([AllowEmptyString()][string]$Value, [string]$Source)
    $raw = if ($null -eq $Value) { "" } else { $Value.Trim() }
    if ($raw -eq "") {
        Write-Gate "SALESOS_TESTING ($Source)" "PASS" "unset/empty (safe)"
        return
    }
    $lower = $raw.ToLowerInvariant()
    # Explicit testing mode - must never ship in deploy target
    if ($lower -in @("1", "true", "yes", "on")) {
        Write-Gate "SALESOS_TESTING ($Source)" "FAIL" "testing mode enabled ('$raw')"
        return
    }
    # Historic trap: non-empty "off" values (e.g. "0") were truthy in older boot paths
    if ($lower -in @("0", "false", "no", "off")) {
        Write-Gate "SALESOS_TESTING ($Source)" "FAIL" "trap value '$raw' (use empty/unset; compose sets SALESOS_TESTING=`"`")"
        return
    }
    Write-Gate "SALESOS_TESTING ($Source)" "FAIL" "unexpected non-empty value '$raw'"
}

function Invoke-ComposeExec {
    param([string]$Command)
    $args = @(
        "compose", "-f", $ComposeFile, "exec", "-T", $BackendService,
        "sh", "-c", $Command
    )
    # Native docker stderr must not terminate under $ErrorActionPreference=Stop
    $prevEap = $ErrorActionPreference
    $ErrorActionPreference = "Continue"
    $output = & docker @args 2>&1
    $exit = $LASTEXITCODE
    $ErrorActionPreference = $prevEap
    $text = ($output | ForEach-Object { "$_" }) -join "`n"
    return [PSCustomObject]@{ ExitCode = $exit; Output = $text.Trim() }
}

Write-GateHeader
Write-Host "  BackendUrl:    $BackendUrl"
Write-Host "  ComposeFile:   $ComposeFile"
Write-Host "  SkipDocker:    $SkipDocker"
Write-Host "  RunUnitTests:  $RunUnitTests"
Write-Host ""

# --- Gate 0: SALESOS_TESTING on host (always) ---
Write-Host "[1/4] SALESOS_TESTING trap check" -ForegroundColor Yellow
Test-SalesosTestingTrap -Value $env:SALESOS_TESTING -Source "host"

if (-not $SkipDocker) {
    if (-not (Test-Path $ComposeFile)) {
        Write-Gate "Compose file" "FAIL" "not found: $ComposeFile"
    } else {
        try {
            $null = docker info 2>$null
            if ($LASTEXITCODE -ne 0) { throw "docker unavailable" }
            $envProbe = Invoke-ComposeExec -Command 'printf %s "${SALESOS_TESTING-}"'
            if ($envProbe.ExitCode -ne 0) {
                Write-Gate "SALESOS_TESTING (container)" "FAIL" "compose exec failed: $($envProbe.Output)"
            } else {
                Test-SalesosTestingTrap -Value $envProbe.Output -Source "container"
            }
        } catch {
            Write-Gate "Docker probe" "FAIL" $_.Exception.Message
        }
    }
} else {
    Write-Gate "SALESOS_TESTING (container)" "SKIP" "SkipDocker set"
}

# --- Gate 1: Alembic drift ---
Write-Host "`n[2/4] Alembic current == heads" -ForegroundColor Yellow
$alembicOk = $false
if (-not $SkipDocker -and (Test-Path $ComposeFile)) {
    $alembic = Invoke-ComposeExec -Command "python scripts/check_alembic_head.py"
    if ($alembic.ExitCode -eq 0) {
        Write-Gate "Alembic drift" "PASS" ($alembic.Output -replace "`r?`n", " | ")
        $alembicOk = $true
    } else {
        Write-Gate "Alembic drift" "FAIL" ($alembic.Output -replace "`r?`n", " | ")
    }
} else {
    $backendDir = Join-Path $salesosRoot "backend"
    $checkScript = Join-Path $backendDir "scripts\check_alembic_head.py"
    if (-not (Test-Path $checkScript)) {
        Write-Gate "Alembic drift" "FAIL" "check_alembic_head.py missing"
    } else {
        Push-Location $backendDir
        try {
            $out = & python scripts/check_alembic_head.py 2>&1 | Out-String
            if ($LASTEXITCODE -eq 0) {
                Write-Gate "Alembic drift" "PASS" ($out.Trim() -replace "`r?`n", " | ")
                $alembicOk = $true
            } else {
                Write-Gate "Alembic drift" "FAIL" ($out.Trim() -replace "`r?`n", " | ")
            }
        } catch {
            Write-Gate "Alembic drift" "FAIL" $_.Exception.Message
        } finally {
            Pop-Location
        }
    }
}

# --- Gate 2: /health ok ---
Write-Host "`n[3/4] Health endpoint" -ForegroundColor Yellow
$healthUrl = "$BackendUrl".TrimEnd("/") + "/health"
try {
    $resp = Invoke-WebRequest -Uri $healthUrl -UseBasicParsing -TimeoutSec $HealthTimeoutSec
    $body = $resp.Content
    $statusOk = $resp.StatusCode -eq 200
    $jsonOk = $false
    try {
        $j = $body | ConvertFrom-Json
        if ($j.status -eq "ok" -or $j.status -eq "healthy") { $jsonOk = $true }
        # Some probes return plain "ok" or nested database status
        if (-not $jsonOk -and $body -match '"status"\s*:\s*"ok"') { $jsonOk = $true }
    } catch {
        if ($body.Trim() -eq "ok") { $jsonOk = $true }
    }
    if ($statusOk -and $jsonOk) {
        Write-Gate "/health" "PASS" "HTTP $($resp.StatusCode); status ok"
    } elseif ($statusOk) {
        Write-Gate "/health" "FAIL" "HTTP 200 but status not ok: $body"
    } else {
        Write-Gate "/health" "FAIL" "HTTP $($resp.StatusCode): $body"
    }
} catch {
    Write-Gate "/health" "FAIL" "$healthUrl - $($_.Exception.Message)"
}

# --- Gate 3: optional unit tests ---
Write-Host "`n[4/4] Unit pytest (optional)" -ForegroundColor Yellow
if (-not $RunUnitTests) {
    Write-Gate "Unit pytest" "SKIP" "pass -RunUnitTests to enable"
} elseif ($SkipDocker) {
    Write-Gate "Unit pytest" "FAIL" "RunUnitTests requires Docker (omit -SkipDocker)"
} else {
    $pytest = Invoke-ComposeExec -Command "SALESOS_TESTING=true python -m pytest tests/unit -q --tb=line"
    if ($pytest.ExitCode -eq 0) {
        Write-Gate "Unit pytest" "PASS" "exit 0"
    } else {
        Write-Gate "Unit pytest" "FAIL" "exit $($pytest.ExitCode) - $($pytest.Output.Substring(0, [Math]::Min(400, $pytest.Output.Length)))"
    }
}

# --- jsonschema advisory (non-blocking once declared in pyproject) ---
Write-Host "`n[advisory] jsonschema import" -ForegroundColor Yellow
if (-not $SkipDocker -and (Test-Path $ComposeFile)) {
    # PS single-quoted arg -> sh sees: python -c 'import jsonschema; print(1)'
    $js = Invoke-ComposeExec -Command 'python -c ''import jsonschema; print(1)'''
    if ($js.ExitCode -eq 0 -and $js.Output -match '1') {
        Write-Gate "jsonschema (container)" "PASS" "import ok"
    } else {
        Write-Gate "jsonschema (container)" "WARN" "not installed in image - declared in pyproject.toml; until rebuild: docker compose exec backend pip install 'jsonschema>=4.22' | probe=$($js.ExitCode) $($js.Output)"
    }
} else {
    Write-Gate "jsonschema (container)" "SKIP" "SkipDocker or no compose"
}

Write-Host ""
Write-Host "--------------------------------------------" -ForegroundColor Cyan
Write-Host ("  Passed: {0}  Failed: {1}  Warnings: {2}" -f $script:passed, $script:failed, $script:warnings)
if ($script:failed -gt 0) {
    Write-Host "  RESULT: FAIL - do not open traffic" -ForegroundColor Red
    Write-Host "--------------------------------------------" -ForegroundColor Cyan
    exit 1
}
Write-Host "  RESULT: PASS (gates green; still not Production GO)" -ForegroundColor Green
Write-Host "--------------------------------------------" -ForegroundColor Cyan
if (-not $alembicOk) {
    # Should already have failed; belt-and-suspenders
    exit 1
}
exit 0
