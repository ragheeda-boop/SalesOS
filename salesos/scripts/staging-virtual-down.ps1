<#
.SYNOPSIS
  Stop LOCAL VIRTUAL staging stack (salesos-staging-local).

.DESCRIPTION
  Does not stop primary / soak compose (ports :8000 / :3000).
  Optional -RemoveVolumes deletes virtual staging DB/redis volumes.

.PARAMETER RemoveVolumes
  Pass -v to docker compose down (destroys staging_local_* volumes).
#>
[CmdletBinding()]
param(
    [switch]$RemoveVolumes
)

$ErrorActionPreference = "Stop"
$SalesosRoot = Split-Path -Parent $PSScriptRoot
$ComposeFile = Join-Path $SalesosRoot "infra\staging\docker-compose.staging-virtual.yml"
$Project = "salesos-staging-local"

Write-Host "=== LOCAL VIRTUAL STAGING DOWN ===" -ForegroundColor Cyan
Write-Host "Project: $Project (primary soak untouched)"

if (-not (Test-Path $ComposeFile)) {
    throw "Missing compose file: $ComposeFile"
}

Push-Location $SalesosRoot
try {
    $dcArgs = @("-p", $Project, "-f", $ComposeFile, "down")
    if ($RemoveVolumes) {
        $dcArgs += "--volumes"
        Write-Warning "Removing virtual staging volumes (-v)."
    }
    & docker compose @dcArgs
    if ($LASTEXITCODE -ne 0) {
        throw ("docker compose down failed (exit {0})" -f $LASTEXITCODE)
    }
    Write-Host "Virtual staging DOWN."
} finally {
    Pop-Location
}
