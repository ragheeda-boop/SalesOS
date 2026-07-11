#!/bin/bash
echo "========================================"
echo " SalesOS v1.0 — Startup"
echo "========================================"
echo ""

if [ ! -f .env ]; then
  echo "[1/3] Creating .env from .env.example..."
  cp .env.example .env
else
  echo "[1/3] .env already exists"
fi

echo "[2/3] Installing frontend dependencies..."
cd frontend && npm ci --ignore-scripts 2>/dev/null
cd ..

echo "[3/3] Starting services..."
echo ""
echo " Frontend: http://localhost:3000"
echo " Backend:  http://localhost:8000"
echo " Grafana:  http://localhost:3001"
echo ""
docker compose up --build
