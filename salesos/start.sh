#!/bin/bash
set -euo pipefail

echo "========================================"
echo " SalesOS v1.0 — Startup"
echo "========================================"
echo ""

# Check Docker availability
if ! command -v docker &>/dev/null; then
  echo "[ERROR] Docker is not installed. Install Docker Desktop: https://docs.docker.com/get-docker/"
  exit 1
fi

if ! docker info &>/dev/null 2>&1; then
  echo "[ERROR] Docker daemon is not running. Start Docker Desktop and try again."
  exit 1
fi

if ! command -v docker &>/dev/null || ! docker compose version &>/dev/null 2>&1; then
  echo "[ERROR] Docker Compose v2 is required. Update Docker Desktop."
  exit 1
fi

# Create .env if missing
if [ ! -f .env ]; then
  echo "[1/3] Creating .env from .env.example..."
  cp .env.example .env
  echo "      Edit .env and set POSTGRES_PASSWORD before starting services."
else
  echo "[1/3] .env already exists"
fi

echo "[2/3] Installing frontend dependencies..."
if [ -d frontend ] && [ -f frontend/package.json ]; then
  cd frontend && npm ci --ignore-scripts 2>/dev/null
  cd ..
else
  echo "      Skipping (frontend directory not found)"
fi

echo "[3/3] Starting services..."
echo ""
echo " Frontend: http://localhost:3000"
echo " Backend:  http://localhost:8000"
echo " Grafana:  http://localhost:3001"
echo " Neo4j:    http://localhost:7475"
echo ""
docker compose up --build
