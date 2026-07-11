@echo off
echo ========================================
echo  SalesOS v1.0 — Startup
echo ========================================
echo.

REM Check Docker availability
where docker >nul 2>nul
if %ERRORLEVEL% neq 0 (
  echo [ERROR] Docker is not installed. Install Docker Desktop: https://docs.docker.com/get-docker/
  exit /b 1
)

docker info >nul 2>nul
if %ERRORLEVEL% neq 0 (
  echo [ERROR] Docker daemon is not running. Start Docker Desktop and try again.
  exit /b 1
)

REM Create .env if missing
if not exist .env (
  echo [1/3] Creating .env from .env.example...
  copy .env.example .env
  echo       Edit .env and set POSTGRES_PASSWORD before starting services.
) else (
  echo [1/3] .env already exists
)

echo [2/3] Installing dependencies...
if exist frontend\package.json (
  cd frontend
  call npm ci --ignore-scripts 2>nul
  cd ..
) else (
  echo       Skipping (frontend directory not found)
)

echo [3/3] Starting services...
echo.
echo  Frontend: http://localhost:3000
echo  Backend:  http://localhost:8000
echo  Grafana:  http://localhost:3001
echo  Neo4j:    http://localhost:7475
echo.
docker compose up --build
