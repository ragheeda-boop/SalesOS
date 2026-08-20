#!/bin/bash
set -euo pipefail

# SalesOS Entrypoint - handles API, Celery Worker, Celery Beat
# Determines service type from SERVICE_ROLE environment variable or first argument

set -euo pipefail

# Priority: 1st argument > SERVICE_ROLE env var > default "api"
SERVICE_ROLE="${1:-${SERVICE_ROLE:-api}}"

case "${SERVICE_ROLE}" in
    "worker")
        echo "Starting Celery Worker..."
        exec celery -A app.celery_app worker \
            --loglevel=info \
            --concurrency=2 \
            --max-tasks-per-child=1000
        ;;
    "beat")
        echo "Starting Celery Beat..."
        exec celery -A app.celery_app beat \
            --loglevel=info
        ;;
    "api"|"")
        echo "Starting API Server (Uvicorn)..."
        exec python -m uvicorn app.main:app \
            --host 0.0.0.0 \
            --port "${PORT:-8000}"
        ;;
    *)
        echo "Unknown SERVICE_ROLE: ${SERVICE_ROLE}"
        echo "Valid options: worker, beat, api"
        exit 1
        ;;
esac