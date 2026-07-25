<#
.SYNOPSIS
  Start LOCAL VIRTUAL staging stack (NOT cloud / VPS staging).

.DESCRIPTION
  Compose project: salesos-staging-local
  Ports: API :8001  FE :3002  Postgres :5433  Redis :6380
  Light profile: postgres + redis + migrations + backend + frontend

  Does not touch primary soak stack on :8000 / :3000.
  Does not satisfy GA cloud-staging GO criteria.

.PARAMETER SkipEnvCopy
  Do not auto-copy .env.staging.local.example when .env.staging.local is missing.

.PARAMETER FreeMonitoring
  Stop primary-compose monitoring containers (grafana/prometheus/alertmanager/exporters)
  to free RAM. Does NOT stop backend/frontend/postgres/redis/neo4j/kafka (soak path).
#>
[CmdletBinding()]
param(
    [switch]$SkipEnvCopy,
    [switch]$FreeMonitoring
)

$ErrorActionPreference = "Stop"
$SalesosRoot = Split-Path -Parent $PSScriptRoot
$ComposeFile = Join-Path $SalesosRoot "infra\staging\docker-compose.staging-virtual.yml"
$EnvFile = Join-Path $SalesosRoot ".env.staging.local"
$EnvExample = Join-Path $SalesosRoot ".env.staging.local.example"
$Project = "salesos-staging-local"

Write-Host "=== LOCAL VIRTUAL STAGING UP ===" -ForegroundColor Cyan
Write-Host "Honesty: local stand-in only - NOT cloud/VPS staging. Production remains NO-GO."
Write-Host "Project: $Project"
Write-Host "Ports:   API :8001  FE :3002  PG :5433  Redis :6380"
Write-Host ""

if (-not (Test-Path $ComposeFile)) {
    throw "Missing compose file: $ComposeFile"
}

if (-not (Test-Path $EnvFile)) {
    if ($SkipEnvCopy) {
        throw "Missing $EnvFile (copy from .env.staging.local.example first)"
    }
    if (-not (Test-Path $EnvExample)) {
        throw "Missing env example: $EnvExample"
    }
    Copy-Item $EnvExample $EnvFile
    Write-Host "Created .env.staging.local from example (local placeholders only)."
}

$clashPorts = @(8001, 3002, 5433, 6380)
foreach ($p in $clashPorts) {
    $busy = Get-NetTCPConnection -LocalPort $p -State Listen -ErrorAction SilentlyContinue
    if ($busy) {
        Write-Warning "Host port $p already listening - virtual staging may fail to bind."
    }
}

foreach ($p in @(8000, 3000)) {
    $busy = Get-NetTCPConnection -LocalPort $p -State Listen -ErrorAction SilentlyContinue
    if ($busy) {
        Write-Host "OK: primary/soak port :$p in use - virtual stack will not bind it."
    }
}

if ($FreeMonitoring) {
    Write-Host "Freeing primary monitoring containers (not soak app)..."
    Push-Location $SalesosRoot
    try {
        docker compose stop grafana prometheus alertmanager postgres-exporter redis-exporter 2>&1 | Out-Host
    } finally {
        Pop-Location
    }
}

$os = Get-CimInstance Win32_OperatingSystem
$freeGb = [math]::Round($os.FreePhysicalMemory / 1MB, 2)
Write-Host ("Free RAM before up: {0} GB" -f $freeGb)
if ($freeGb -lt 1.0) {
    Write-Warning ("Low free RAM ({0} GB). Prefer -FreeMonitoring or stop unused containers. Light profile still may OOM." -f $freeGb)
}

Push-Location $SalesosRoot
try {
    $env:COMPOSE_PROJECT_NAME = $Project
    # Infra first so we can stamp alembic before app boot (fresh upgrade fails at 0028).
    docker compose -p $Project -f $ComposeFile --env-file $EnvFile up -d --no-build postgres redis
    if ($LASTEXITCODE -ne 0) {
        throw ("docker compose up postgres/redis failed (exit {0})" -f $LASTEXITCODE)
    }

    Write-Host "Waiting for virtual postgres healthy..."
    $pgDeadline = (Get-Date).AddMinutes(2)
    $pgOk = $false
    while ((Get-Date) -lt $pgDeadline) {
        $h = docker inspect salesos-staging-local-postgres-1 --format "{{if .State.Health}}{{.State.Health.Status}}{{end}}" 2>$null
        if ($h -eq "healthy") { $pgOk = $true; break }
        Start-Sleep -Seconds 3
    }
    if (-not $pgOk) {
        throw "Virtual postgres not healthy in time"
    }

    # Stamp-only: avoids broken empty-DB alembic upgrade (0028 company_licenses).
    # Enough for /health (SELECT 1). Auth needs full schema — see optional seed below.
    Write-Host "Stamping alembic_version=0040 on virtual DB (light tabletop; not full migrate)..."
    docker exec salesos-staging-local-postgres-1 psql -U salesos -d salesos -v ON_ERROR_STOP=1 -c @"
CREATE TABLE IF NOT EXISTS alembic_version (
  version_num VARCHAR(32) NOT NULL PRIMARY KEY
);
INSERT INTO alembic_version(version_num)
SELECT '0040'
WHERE NOT EXISTS (SELECT 1 FROM alembic_version);
"@
    if ($LASTEXITCODE -ne 0) {
        throw "alembic stamp SQL failed"
    }

    # If virtual DB has no users table, copy schema-only from primary (read-only dump).
    # Does not copy primary data. Does not touch primary. Required for login/register.
    $hasUsers = docker exec salesos-staging-local-postgres-1 psql -U salesos -d salesos -tAc "SELECT to_regclass('public.users');"
    if (-not ($hasUsers -match 'users')) {
        $primaryPg = docker ps --filter "name=salesos-postgres-1" --format "{{.Names}}" | Select-Object -First 1
        if ($primaryPg) {
            Write-Host "Virtual DB missing users table — applying schema-only dump from primary (no data)..."
            $dump = Join-Path $env:TEMP "salesos-staging-virtual-schema.sql"
            docker exec salesos-postgres-1 pg_dump -U salesos -d salesos --schema-only --no-owner --no-acl | Set-Content -Path $dump -Encoding utf8
            Get-Content $dump -Raw | docker exec -i salesos-staging-local-postgres-1 psql -U salesos -d salesos -v ON_ERROR_STOP=0 | Out-Null
            Write-Host "Schema apply attempted. Verify: docker exec salesos-staging-local-postgres-1 psql -U salesos -d salesos -c '\dt'"
        } else {
            Write-Warning "Primary postgres not running — cannot schema-seed virtual DB. Auth will fail until schema exists."
        }
    }

    docker compose -p $Project -f $ComposeFile --env-file $EnvFile up -d --no-build backend frontend
    if ($LASTEXITCODE -ne 0) {
        # Frontend may wait on backend health; start backend alone then frontend.
        Write-Warning "Combined up returned non-zero; trying backend then frontend..."
        docker compose -p $Project -f $ComposeFile --env-file $EnvFile up -d --no-deps --no-build backend
        if ($LASTEXITCODE -ne 0) {
            throw ("docker compose up backend failed (exit {0})" -f $LASTEXITCODE)
        }
    }

    Write-Host ""
    Write-Host "Waiting for backend health on :8001 ..."
    $deadline = (Get-Date).AddMinutes(4)
    $ok = $false
    while ((Get-Date) -lt $deadline) {
        try {
            $r = Invoke-WebRequest -Uri "http://127.0.0.1:8001/health" -UseBasicParsing -TimeoutSec 5
            if ($r.StatusCode -eq 200) { $ok = $true; break }
        } catch {
            Start-Sleep -Seconds 5
        }
    }
    if (-not $ok) {
        Write-Warning ("Backend :8001 health not 200 within timeout. Check: docker compose -p {0} -f {1} ps" -f $Project, $ComposeFile)
    } else {
        Write-Host "Backend health: 200"
        docker compose -p $Project -f $ComposeFile --env-file $EnvFile up -d --no-deps --no-build frontend | Out-Host

        # Seed demo users into VIRTUAL DB only (idempotent; never targets primary).
        $userCount = docker exec salesos-staging-local-postgres-1 psql -U salesos -d salesos -tAc "SELECT count(*) FROM users WHERE email='admin@salesos.io';" 2>$null
        if ($userCount -match '^\s*0\s*$' -or $userCount -eq $null -or $userCount -eq "") {
            Write-Host "Seeding demo users into virtual staging DB..."
            docker exec salesos-staging-local-backend-1 python scripts/seed_demo_users.py
            if ($LASTEXITCODE -ne 0) {
                Write-Warning "seed_demo_users.py failed — login may not work until users exist."
            }
        } else {
            Write-Host "Demo admin already present in virtual DB — skip seed."
        }

        # FE image is often baked with NEXT_PUBLIC_API_URL=:8000. Patch runtime bundle to :8001.
        Write-Host "Ensuring FE bundle points at localhost:8001 (bake-time NEXT_PUBLIC override)..."
        docker exec -u 0 salesos-staging-local-frontend-1 sh -c "find /app/.next -type f \( -name '*.js' -o -name '*.html' -o -name '*.json' -o -name '*.rsc' \) -print0 2>/dev/null | xargs -0 sed -i 's|localhost:8000|localhost:8001|g'" 2>$null
        docker restart salesos-staging-local-frontend-1 | Out-Null
    }

    try {
        $fe = Invoke-WebRequest -Uri "http://127.0.0.1:3002" -UseBasicParsing -TimeoutSec 10
        Write-Host ("Frontend :3002 status: {0}" -f $fe.StatusCode)
    } catch {
        Write-Warning ("Frontend :3002 probe failed: {0}" -f $_.Exception.Message)
    }

    docker compose -p $Project -f $ComposeFile --env-file $EnvFile ps
    Write-Host ""
    Write-Host "Virtual staging UP (local only). Down: .\scripts\staging-virtual-down.ps1"
} finally {
    Pop-Location
}
