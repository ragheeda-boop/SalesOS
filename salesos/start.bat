@echo off
echo ========================================
echo  SalesOS v1.0 — Startup
echo ========================================
echo.

if not exist .env (
  echo [1/3] Creating .env from .env.example...
  copy .env.example .env
) else (
  echo [1/3] .env already exists
)

echo [2/3] Installing dependencies...
cd frontend
call npm ci --ignore-scripts 2>nul
cd ..

echo [3/3] Starting services...
echo.
echo  Frontend: http://localhost:3000
echo  Backend:  http://localhost:8000
echo  Grafana:  http://localhost:3001
echo.
docker compose up --build
