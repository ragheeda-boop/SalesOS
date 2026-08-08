<#
.SYNOPSIS
  Restart / attach helper for OPS-01 staging soak harness (evidence only).
.DESCRIPTION
  Does NOT flip soak_complete_claim. Does NOT invent 576/576.
  Prefer one live loop only - check PID before starting a second.

.EXAMPLE
  # Status of known soak evidence dir
  .\docs\audit\ga-engineering-audit\runbooks\ops01-soak-restart.ps1 -StatusOnly

  # Restart 72h staging loop (human must confirm no other loop is writing same dir)
  .\docs\audit\ga-engineering-audit\runbooks\ops01-soak-restart.ps1 -Start -DurationHours 72 -FailSoft
#>
param(
    [switch]$StatusOnly,
    [switch]$Start,
    [string]$ApiUrl = "https://salesos-staging.up.railway.app",
    [string]$FrontendUrl = "https://sales-os-jet.vercel.app",
    [double]$DurationHours = 72,
    [int]$IntervalSec = 300,
    [string]$EvidenceDir = "",
    [switch]$FailSoft
)

$ErrorActionPreference = "Stop"
$repo = Resolve-Path (Join-Path $PSScriptRoot "..\..\..\..")
$py = Join-Path $repo "salesos\scripts\wave11-soak-gate.py"
if (-not $EvidenceDir) {
    $EvidenceDir = Join-Path $repo "docs\audit\ga-engineering-audit\enterprise-audit-board\history\EAB-2026-08-06-003\evidence\ops01-staging"
}

Write-Host "REPO=$repo"
Write-Host "EVIDENCE=$EvidenceDir"
Write-Host "soak_complete_claim must remain false until K1-K6 + human TL review"

$loops = @()
if (Test-Path $EvidenceDir) {
    $loops = Get-ChildItem $EvidenceDir -Filter "loop-*.json" -ErrorAction SilentlyContinue | Sort-Object Name
}
Write-Host "loop_json_count=$($loops.Count)"
if ($loops.Count -gt 0) {
    $last = Get-Content $loops[-1].FullName -Raw | ConvertFrom-Json
    Write-Host "last_iteration=$($last.iteration) last_ts=$($last.timestamp) gate_pass=$($last.gate_pass)"
}

$running = Get-CimInstance Win32_Process -Filter "Name='python.exe'" -ErrorAction SilentlyContinue |
    Where-Object { $_.CommandLine -match 'wave11-soak-gate' -and $_.CommandLine -match 'duration-hours' }
if ($running) {
    Write-Host "LIVE_HARNESS:"
    $running | ForEach-Object { Write-Host ("  PID={0} CMD={1}" -f $_.ProcessId, $_.CommandLine) }
} else {
    Write-Host "LIVE_HARNESS: none detected on this host"
}

if ($StatusOnly -or -not $Start) {
    Write-Host "StatusOnly complete. Pass -Start to launch (human confirms no duplicate writer)."
    exit 0
}

if ($running) {
    throw "Refusing -Start while a wave11 soak loop is already running. Stop it first or use -StatusOnly."
}

New-Item -ItemType Directory -Force -Path $EvidenceDir | Out-Null
$python = Get-Command python -ErrorAction SilentlyContinue
if (-not $python) { $python = Get-Command py -ErrorAction SilentlyContinue }
if (-not $python) { throw "Python not on PATH" }

$argsList = @(
    $py,
    "--loop",
    "--interval", "$IntervalSec",
    "--duration-hours", "$DurationHours",
    "--api", $ApiUrl,
    "--fe", $FrontendUrl,
    "--skip-alembic",
    "--skip-flags",
    "--evidence-dir", $EvidenceDir
)
if ($FailSoft) { $argsList += "--fail-soft" }

$joined = ($argsList -join ' ')
Write-Host ("STARTING (not a soak PASS claim): {0} {1}" -f $python.Source, $joined)
& $python.Source @argsList
exit $LASTEXITCODE
