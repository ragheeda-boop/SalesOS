# Mirrors salesos/frontend source (excluding generated/heavy dirs) to a
# persistent NTFS location on C:, then runs npm ci + the verification
# commands there.
#
# Why this exists: D:\AISalesOS is a FAT32 volume with very little free
# space (see project-audit/61_FRONTEND_TOOLCHAIN_DIAGNOSIS_2026-09-23.md).
# FAT32 cannot hold symlinks/reparse points, which "npm install" needs for
# node_modules/.bin, so no npm install can ever fully succeed directly on
# D:. This script keeps the source of truth on D: (edit and commit there as
# normal) and gives you a real, working node_modules and toolchain on C:.
#
# Usage:
#   powershell -File scripts/sync-to-c-and-verify.ps1
#   powershell -File scripts/sync-to-c-and-verify.ps1 -SkipInstall
#   powershell -File scripts/sync-to-c-and-verify.ps1 -Command "build"
#
# Re-run any time after editing files on D: - robocopy /MIR only copies
# what changed, so repeat runs are fast.

param(
    [string]$Dest = "C:\Users\raghe\dev\SalesOS-frontend",
    [switch]$SkipInstall,
    [string]$Command = "typecheck"
)

$ErrorActionPreference = "Stop"
$Source = Split-Path -Parent $PSScriptRoot

Write-Host ("Source: " + $Source)
Write-Host ("Dest:   " + $Dest)

if (-not (Test-Path $Dest)) {
    New-Item -ItemType Directory -Path $Dest -Force | Out-Null
}

$excludeDirs = @(
    "node_modules", ".next", "coverage", ".turbo", "dist", "build",
    ".git", "node_modules.incomplete-codex-20260920"
)

$robocopyArgs = @(
    $Source, $Dest, "/MIR", "/NFL", "/NDL", "/NJH", "/NJS", "/NP",
    "/XD"
) + $excludeDirs

& robocopy @robocopyArgs
if ($LASTEXITCODE -ge 8) {
    throw ("robocopy failed with exit code " + $LASTEXITCODE)
}
Write-Host ("Sync complete (robocopy exit " + $LASTEXITCODE + ").")

Push-Location $Dest
try {
    if (-not $SkipInstall) {
        Write-Host "Running npm ci..."
        npm ci
        if ($LASTEXITCODE -ne 0) { throw ("npm ci failed with exit code " + $LASTEXITCODE) }
    }

    if ($Command) {
        Write-Host ("Running npm run " + $Command + "...")
        npm run $Command
        if ($LASTEXITCODE -ne 0) { throw ("npm run " + $Command + " failed with exit code " + $LASTEXITCODE) }
    }
}
finally {
    Pop-Location
}

Write-Host ("Done. Working copy is at " + $Dest + ". Edit and commit on D:\AISalesOS as usual, then re-run this script before testing.")
