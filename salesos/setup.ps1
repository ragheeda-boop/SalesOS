param(
    [switch]$SkipDockerCheck,
    [switch]$SkipMigrations,
    [switch]$SkipSeed
)

Write-Host "======================================" -ForegroundColor Cyan
Write-Host "  SalesOS - Setup Script" -ForegroundColor Cyan
Write-Host "======================================" -ForegroundColor Cyan
Write-Host ""

# ─── Step 1: Check Docker ──────────────────────────────────
if (-not $SkipDockerCheck) {
    Write-Host "[1/5] Checking Docker..." -ForegroundColor Yellow
    $dockerOk = $false
    try {
        $dockerVersion = docker --version 2>&1
        if ($LASTEXITCODE -eq 0) {
            Write-Host "  Docker found: $dockerVersion" -ForegroundColor Green
            $dockerOk = $true
        }
    } catch {
        Write-Host "  Docker not found." -ForegroundColor Red
        Write-Host "  Install from: https://docs.docker.com/desktop/install/windows-install/" -ForegroundColor Gray
    }

    if (-not $dockerOk) {
        Write-Host "  Trying winget..." -ForegroundColor Yellow
        try {
            winget install Docker.DockerDesktop 2>&1 | Out-Null
            Write-Host "  Docker Desktop installed. Please restart and run this script again." -ForegroundColor Green
            exit 0
        } catch {
            Write-Host "  Please install Docker Desktop manually, then re-run." -ForegroundColor Red
            exit 1
        }
    }
}

# ─── Step 2: Start PostgreSQL via Docker ───────────────────
Write-Host "[2/5] Starting PostgreSQL..." -ForegroundColor Yellow
docker ps --filter "name=salesos-postgres" --format "{{.Names}}" | ForEach-Object {
    if ($_ -eq "salesos-postgres") {
        Write-Host "  PostgreSQL already running." -ForegroundColor Green
        return
    }
}
$pgRunning = docker ps --filter "name=salesos-postgres" --format "{{.Names}}"
if (-not $pgRunning) {
    Write-Host "  Starting PostgreSQL container..." -ForegroundColor Yellow
    docker run -d --name salesos-postgres `
        -e POSTGRES_USER=salesos `
        -e POSTGRES_PASSWORD=salesos_dev_password `
        -e POSTGRES_DB=salesos `
        -p 6432:5432 `
        postgres:16

    if ($LASTEXITCODE -ne 0) {
        Write-Host "  Failed to start PostgreSQL." -ForegroundColor Red
        exit 1
    }
    Write-Host "  Waiting for PostgreSQL to be ready..." -ForegroundColor Yellow
    Start-Sleep -Seconds 5
    $retries = 10
    do {
        $ready = docker exec salesos-postgres pg_isready -U salesos 2>&1
        if ($ready -match "accepting connections") { break }
        Start-Sleep -Seconds 2
        $retries--
    } while ($retries -gt 0)
    Write-Host "  PostgreSQL is ready." -ForegroundColor Green
}

# ─── Step 3: Create Test DB ────────────────────────────────
Write-Host "[3/5] Creating test database..." -ForegroundColor Yellow
docker exec salesos-postgres psql -U salesos -c "CREATE DATABASE salesos_test;" 2>&1 | Out-Null
Write-Host "  Test database ready." -ForegroundColor Green

# ─── Step 4: Run Migrations ────────────────────────────────
if (-not $SkipMigrations) {
    Write-Host "[4/5] Running Alembic migrations..." -ForegroundColor Yellow
    Push-Location salesos\backend
    try {
        $env:POSTGRES_HOST = "localhost"
        $env:POSTGRES_PORT = "6432"
        $env:SALESOS_TESTING = "false"
        poetry run alembic upgrade head
        if ($LASTEXITCODE -eq 0) {
            Write-Host "  Migrations applied successfully." -ForegroundColor Green
        } else {
            Write-Host "  Migrations failed." -ForegroundColor Red
            exit 1
        }
    } finally {
        Pop-Location
    }
}

# ─── Step 5: Seed Data ─────────────────────────────────────
if (-not $SkipSeed) {
    Write-Host "[5/5] Seeding initial data..." -ForegroundColor Yellow
    Push-Location salesos\backend
    try {
        poetry run python -c "
import asyncio
from app.database import async_session
from app.seed import seed_all
async def run():
    async with async_session() as session:
        await seed_all(session)
asyncio.run(run())
print('Seed complete.')
"
        Write-Host "  Seed data inserted." -ForegroundColor Green
    } finally {
        Pop-Location
    }
}

Write-Host ""
Write-Host "======================================" -ForegroundColor Cyan
Write-Host "  Setup complete!" -ForegroundColor Green
Write-Host "======================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Start the server:" -ForegroundColor White
Write-Host "  cd salesos\backend && poetry run uvicorn app.main:app --reload" -ForegroundColor Gray
Write-Host ""
Write-Host "Access the API:" -ForegroundColor White
Write-Host "  http://localhost:8000/docs" -ForegroundColor Gray
