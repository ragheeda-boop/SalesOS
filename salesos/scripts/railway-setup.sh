#!/bin/bash
# Railway Setup Script for SalesOS Backend
# Run this from the salesos/ root directory
#
# IMPORTANT: Root Directory in Railway dashboard must be EMPTY (repo root).
# The railway.json at repo root handles all path resolution.
#
# This script creates 3 Railway services:
#   1. backend - FastAPI API server
#   2. worker  - Celery background worker
#   3. beat    - Celery beat scheduler

set -e

echo "============================================"
echo "  SalesOS Railway Deployment Setup"
echo "============================================"
echo ""

# Check Railway CLI
if ! command -v railway &> /dev/null; then
    echo "[!] Railway CLI not found."
    echo "    npm install -g @railway/cli"
    echo "    railway login"
    exit 1
fi

# Check login
if ! railway whoami &> /dev/null; then
    echo "[!] Not logged in."
    railway login
fi

echo "[*] Logged in as: $(railway whoami)"
echo ""

# Link or create project
echo "[*] Linking Railway project..."
railway project link 2>/dev/null || railway project new

# ============================================
# Generate secrets
# ============================================
echo ""
echo "[*] Generating secrets..."
SECRET_KEY=$(python -c "import secrets; print(secrets.token_hex(32))" 2>/dev/null || openssl rand -hex 32)
JWT_SECRET_KEY=$(python -c "import secrets; print(secrets.token_hex(64))" 2>/dev/null || openssl rand -hex 64)

echo "    SECRET_KEY=$SECRET_KEY"
echo "    JWT_SECRET_KEY=$JWT_SECRET_KEY"
echo ""

# ============================================
# SERVICE 1: Backend API
# ============================================
echo "==========================================="
echo "[1/3] Creating Backend API service..."
echo "==========================================="

railway service new --name backend 2>/dev/null || echo "Service 'backend' already exists"

railway variables set \
    ENV=production \
    DEBUG=false \
    SECRET_KEY="$SECRET_KEY" \
    JWT_SECRET_KEY="$JWT_SECRET_KEY" \
    NEO4J_PASSWORD="" \
    EVENT_BUS_TYPE=in_memory \
    FEATURE_AI_COPILOT=false \
    FEATURE_SEARCH_FUZZY_V2=false \
    FEATURE_CRM_KANBAN=false \
    DEMO_MODE=false \
    LOG_LEVEL=INFO \
    SERVICE_VERSION=5.1.0 \
    POSTGRES_PORT=5432

echo "[✓] Backend service configured"
echo ""

# ============================================
# SERVICE 2: Celery Worker
# ============================================
echo "==========================================="
echo "[2/3] Creating Celery Worker service..."
echo "==========================================="

railway service new --name worker 2>/dev/null || echo "Service 'worker' already exists"

railway variables set \
    ENV=production \
    DEBUG=false \
    SECRET_KEY="$SECRET_KEY" \
    JWT_SECRET_KEY="$JWT_SECRET_KEY" \
    NEO4J_PASSWORD="" \
    EVENT_BUS_TYPE=in_memory \
    CELERY_TASK_TIME_LIMIT=600 \
    CELERY_TASK_SOFT_TIME_LIMIT=300 \
    CELERY_WORKER_MAX_TASKS_PER_CHILD=1000 \
    POSTGRES_PORT=5432

echo "[✓] Worker service configured"
echo ""

# ============================================
# SERVICE 3: Celery Beat
# ============================================
echo "==========================================="
echo "[3/3] Creating Celery Beat service..."
echo "==========================================="

railway service new --name beat 2>/dev/null || echo "Service 'beat' already exists"

railway variables set \
    ENV=production \
    DEBUG=false \
    SECRET_KEY="$SECRET_KEY" \
    JWT_SECRET_KEY="$JWT_SECRET_KEY" \
    NEO4J_PASSWORD="" \
    CELERY_RESULT_EXPIRES=86400 \
    POSTGRES_PORT=5432

echo "[✓] Beat service configured"
echo ""

# ============================================
# Databases
# ============================================
echo "==========================================="
echo "Adding PostgreSQL..."
echo "==========================================="
railway add --plugin PostgreSQL 2>/dev/null || echo "PostgreSQL already added"

echo ""
echo "==========================================="
echo "Adding Redis..."
echo "==========================================="
railway add --plugin Redis 2>/dev/null || echo "Redis already added"

echo ""
echo "============================================"
echo "  SETUP COMPLETE"
echo "============================================"
echo ""
echo "CRITICAL: Root Directory in Railway dashboard"
echo "================================================"
echo "For ALL services (backend, worker, beat):"
echo "  Root Directory = [LEAVE EMPTY] (repo root)"
echo ""
echo "The railway.json at repo root handles all paths."
echo "Do NOT set Root Directory to 'backend'."
echo ""
echo "For 'worker' service — set Start Command:"
echo "  celery -A app.celery_app worker --loglevel=info --concurrency=2 --max-tasks-per-child=1000"
echo ""
echo "For 'beat' service — set Start Command:"
echo "  celery -A app.celery_app beat --loglevel=info"
echo ""
echo "Add custom domain to 'backend' service:"
echo "  Settings → Networking → Custom Domain"
echo ""
echo "Secrets (save these now):"
echo "    SECRET_KEY=$SECRET_KEY"
echo "    JWT_SECRET_KEY=$JWT_SECRET_KEY"
echo ""
