<#
.SYNOPSIS
  Wave 11 soak/parity readiness gate wrapper (Windows).
.DESCRIPTION
  Invokes salesos/scripts/wave11-soak-gate.py against local/staging URLs.
  Does NOT claim Production GO or 48–72h soak complete.

.EXAMPLE
  .\scripts\wave11-soak-gate.ps1
  .\scripts\wave11-soak-gate.ps1 -ApiUrl http://localhost:8000 -FrontendUrl http://localhost:3000
  .\scripts\wave11-soak-gate.ps1 -Loop -IntervalSec 300 -DurationHours 48
#>
param(
    [string]$ApiUrl = "http://localhost:8000",
    [string]$FrontendUrl = "http://localhost:3000",
    [string]$ComposeDir = "",
    [string]$BackendService = "backend",
    [switch]$SkipAlembic,
    [switch]$SkipFlags,
    [switch]$Loop,
    [int]$IntervalSec = 300,
    [double]$DurationHours = 48,
    [string]$EvidenceDir = ""
)

$ErrorActionPreference = "Stop"
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$py = Join-Path $scriptDir "wave11-soak-gate.py"

if (-not (Test-Path $py)) {
    throw "Missing $py"
}

if (-not $ComposeDir) {
    $ComposeDir = Split-Path -Parent $scriptDir
}

$argsList = @(
    $py,
    "--api", $ApiUrl,
    "--fe", $FrontendUrl,
    "--compose-dir", $ComposeDir,
    "--backend-service", $BackendService
)
if ($SkipAlembic) { $argsList += "--skip-alembic" }
if ($SkipFlags) { $argsList += "--skip-flags" }
if ($EvidenceDir) { $argsList += @("--evidence-dir", $EvidenceDir) }
if ($Loop) {
    $argsList += @("--loop", "--interval", "$IntervalSec", "--duration-hours", "$DurationHours")
}

$python = Get-Command python -ErrorAction SilentlyContinue
if (-not $python) { $python = Get-Command py -ErrorAction SilentlyContinue }
if (-not $python) { throw "Python not found on PATH" }

& $python.Source @argsList
exit $LASTEXITCODE
