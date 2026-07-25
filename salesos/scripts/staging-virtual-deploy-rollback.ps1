<#
.SYNOPSIS
  Deploy / rollback TABLETOP on LOCAL VIRTUAL staging (NOT cloud).

.DESCRIPTION
  1. Records current backend/frontend image digests
  2. Tags them as staging-virtual-prev (rollback pin)
  3. Force-recreates app services (deploy analogue, --no-deps)
  4. Recreates pinned to prev tags (rollback analogue)
  5. Writes evidence JSON under docs/audit/ga-engineering-audit/evidence/wave12-staging-virtual/

  Does not touch soak on :8000/:3000. Does not claim Production GO / cloud staging DONE.

.PARAMETER EvidenceDir
  Override evidence directory.
#>
[CmdletBinding()]
param(
    [string]$EvidenceDir = ""
)

$ErrorActionPreference = "Stop"
$SalesosRoot = Split-Path -Parent $PSScriptRoot
$RepoRoot = Split-Path -Parent $SalesosRoot
$ComposeFile = Join-Path $SalesosRoot "infra\staging\docker-compose.staging-virtual.yml"
$EnvFile = Join-Path $SalesosRoot ".env.staging.local"
$Project = "salesos-staging-local"
$Utc = (Get-Date).ToUniversalTime().ToString("yyyy-MM-ddTHHmmssZ")

if (-not $EvidenceDir) {
    $EvidenceDir = Join-Path $RepoRoot "docs\audit\ga-engineering-audit\evidence\wave12-staging-virtual"
}
New-Item -ItemType Directory -Force -Path $EvidenceDir | Out-Null

function Get-ImageId([string]$ref) {
    $id = docker image inspect $ref --format "{{.Id}}" 2>$null
    if (-not $id) { throw "Image not found: $ref" }
    return $id.Trim()
}

function Probe-Health([string]$url) {
    try {
        $r = Invoke-WebRequest -Uri $url -UseBasicParsing -TimeoutSec 8
        return @{ ok = ($r.StatusCode -eq 200); status = [int]$r.StatusCode; error = $null }
    } catch {
        return @{ ok = $false; status = 0; error = $_.Exception.Message }
    }
}

function Invoke-ComposeToLog {
    param(
        [Parameter(Mandatory = $true)][string[]]$ComposeArgs,
        [Parameter(Mandatory = $true)][string]$LogPath
    )
    $prev = $ErrorActionPreference
    $ErrorActionPreference = "Continue"
    $lines = @()
    & docker compose @ComposeArgs 2>&1 | ForEach-Object {
        $line = "$_"
        $lines += $line
        Write-Host $line
    }
    $code = $LASTEXITCODE
    $ErrorActionPreference = $prev
    ($lines + @("exit_code=$code")) -join [Environment]::NewLine | Set-Content -Path $LogPath -Encoding utf8
    return $code
}

Write-Host "=== LOCAL VIRTUAL STAGING DEPLOY/ROLLBACK TABLETOP ===" -ForegroundColor Cyan
Write-Host "Honesty: local virtual only - cloud staging still BLOCKED for GA."

if (-not (Test-Path $EnvFile)) {
    throw "Missing $EnvFile - run staging-virtual-up.ps1 first"
}

$backendRef = "salesos-backend:latest"
$frontendRef = "salesos-frontend:local"
Get-Content $EnvFile | ForEach-Object {
    if ($_ -match '^\s*BACKEND_IMAGE=(.+)$') { $backendRef = $Matches[1].Trim() }
    if ($_ -match '^\s*FRONTEND_IMAGE=(.+)$') { $frontendRef = $Matches[1].Trim() }
}

$preBackend = Get-ImageId $backendRef
$preFrontend = Get-ImageId $frontendRef

Write-Host "Pre digests:"
Write-Host ("  backend  {0} -> {1}" -f $backendRef, $preBackend)
Write-Host ("  frontend {0} -> {1}" -f $frontendRef, $preFrontend)

docker tag $backendRef "salesos-backend:staging-virtual-prev"
docker tag $frontendRef "salesos-frontend:staging-virtual-prev"
$prevBackend = Get-ImageId "salesos-backend:staging-virtual-prev"
$prevFrontend = Get-ImageId "salesos-frontend:staging-virtual-prev"

$preHealthApi = Probe-Health "http://127.0.0.1:8001/health"
$preHealthFe = Probe-Health "http://127.0.0.1:3002"

$prePath = Join-Path $EvidenceDir "pre-$Utc.json"
@{
    kind = "local-virtual-staging-tabletop"
    phase = "pre"
    utc = $Utc
    project = $Project
    honesty = "NOT cloud/VPS staging; Production NO-GO unchanged"
    images = @{
        backend_ref = $backendRef
        frontend_ref = $frontendRef
        backend_id = $preBackend
        frontend_id = $preFrontend
        rollback_pin_backend = "salesos-backend:staging-virtual-prev"
        rollback_pin_frontend = "salesos-frontend:staging-virtual-prev"
        rollback_pin_backend_id = $prevBackend
        rollback_pin_frontend_id = $prevFrontend
        note_historical_wave12_digests = "Prior tabletop digests 4d7efe7e / ed834c95 were not present on host; pins recorded from current local images."
    }
    health = @{ api_8001 = $preHealthApi; fe_3002 = $preHealthFe }
} | ConvertTo-Json -Depth 6 | Set-Content -Path $prePath -Encoding utf8

Push-Location $SalesosRoot
$deployOk = $false
$rollbackOk = $false
$deployLog = Join-Path $EvidenceDir "deploy-$Utc.log"
$rollbackLog = Join-Path $EvidenceDir "rollback-$Utc.log"
try {
    Write-Host "Deploy analogue: force-recreate backend/frontend (--no-deps --no-build)..."
    $env:BACKEND_IMAGE = $backendRef
    $env:FRONTEND_IMAGE = $frontendRef
    $null = Invoke-ComposeToLog -LogPath $deployLog -ComposeArgs @(
        "-p", $Project, "-f", $ComposeFile, "--env-file", $EnvFile,
        "up", "-d", "--no-deps", "--no-build", "--force-recreate", "backend", "frontend"
    )

    Start-Sleep -Seconds 10
    $postDeployApi = Probe-Health "http://127.0.0.1:8001/health"
    $postDeployFe = Probe-Health "http://127.0.0.1:3002"
    $deadline = (Get-Date).AddMinutes(4)
    while ((-not $postDeployApi.ok -or -not $postDeployFe.ok) -and (Get-Date) -lt $deadline) {
        Start-Sleep -Seconds 5
        $postDeployApi = Probe-Health "http://127.0.0.1:8001/health"
        $postDeployFe = Probe-Health "http://127.0.0.1:3002"
    }
    $deployOk = [bool]$postDeployApi.ok
    Write-Host ("Post-deploy API ok={0} FE ok={1}" -f $postDeployApi.ok, $postDeployFe.ok)

    Write-Host "Rollback analogue: recreate with staging-virtual-prev tags..."
    $env:BACKEND_IMAGE = "salesos-backend:staging-virtual-prev"
    $env:FRONTEND_IMAGE = "salesos-frontend:staging-virtual-prev"
    $null = Invoke-ComposeToLog -LogPath $rollbackLog -ComposeArgs @(
        "-p", $Project, "-f", $ComposeFile, "--env-file", $EnvFile,
        "up", "-d", "--no-deps", "--no-build", "--force-recreate", "backend", "frontend"
    )

    Start-Sleep -Seconds 10
    $postRollbackApi = Probe-Health "http://127.0.0.1:8001/health"
    $postRollbackFe = Probe-Health "http://127.0.0.1:3002"
    $deadline2 = (Get-Date).AddMinutes(4)
    while ((-not $postRollbackApi.ok -or -not $postRollbackFe.ok) -and (Get-Date) -lt $deadline2) {
        Start-Sleep -Seconds 5
        $postRollbackApi = Probe-Health "http://127.0.0.1:8001/health"
        $postRollbackFe = Probe-Health "http://127.0.0.1:3002"
    }
    $rollbackOk = [bool]$postRollbackApi.ok
    Write-Host ("Post-rollback API ok={0} FE ok={1}" -f $postRollbackApi.ok, $postRollbackFe.ok)

    $postBackend = Get-ImageId "salesos-backend:staging-virtual-prev"
    $postFrontend = Get-ImageId "salesos-frontend:staging-virtual-prev"

    $complete = @{
        kind = "local-virtual-staging-tabletop"
        phase = "complete"
        utc = $Utc
        project = $Project
        honesty = @{
            local_virtual_staging = "DONE (this tabletop)"
            cloud_vps_staging = "BLOCKED / still required for GA staging line"
            production = "NO-GO"
            soak_48h = "NOT touched (ports :8000/:3000 preserved)"
        }
        ports = @{ api = 8001; frontend = 3002; postgres = 5433; redis = 6380 }
        results = @{
            deploy_analogue_ok = $deployOk
            rollback_analogue_ok = $rollbackOk
            frontend_post_deploy_ok = [bool]$postDeployFe.ok
            frontend_post_rollback_ok = [bool]$postRollbackFe.ok
            overall_api = ($deployOk -and $rollbackOk)
        }
        images = @{
            pre_backend = $preBackend
            pre_frontend = $preFrontend
            post_rollback_backend = $postBackend
            post_rollback_frontend = $postFrontend
            pin_tags = @("salesos-backend:staging-virtual-prev", "salesos-frontend:staging-virtual-prev")
        }
        health = @{
            pre_api = $preHealthApi
            pre_fe = $preHealthFe
            post_deploy_api = $postDeployApi
            post_deploy_fe = $postDeployFe
            post_rollback_api = $postRollbackApi
            post_rollback_fe = $postRollbackFe
        }
        evidence_files = @{
            pre = $prePath
            deploy_log = $deployLog
            rollback_log = $rollbackLog
        }
    }
    $completePath = Join-Path $EvidenceDir "tabletop-complete-$Utc.json"
    $complete | ConvertTo-Json -Depth 8 | Set-Content -Path $completePath -Encoding utf8
    Write-Host "Evidence: $completePath"
    if (-not ($deployOk -and $rollbackOk)) {
        Write-Warning "Tabletop completed with API failures - see evidence JSON."
        exit 1
    }
    Write-Host "Tabletop PASS (local virtual only; API health after deploy+rollback)."
} finally {
    Pop-Location
    Remove-Item Env:BACKEND_IMAGE -ErrorAction SilentlyContinue
    Remove-Item Env:FRONTEND_IMAGE -ErrorAction SilentlyContinue
}
