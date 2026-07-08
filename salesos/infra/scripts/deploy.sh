#!/usr/bin/env bash
# SalesOS Deployment Script
# Usage:
#   ./deploy.sh                          # Deploy with defaults
#   REGISTRY=ghcr.io ./deploy.sh        # Custom registry
#   IMAGE_TAG=v1.0.0 ./deploy.sh        # Specific version
#
# Prerequisites:
#   - Docker & Docker Compose installed on VPS
#   - .env.production present in project root
#   - DOMAIN DNS pointing to VPS
#
set -euo pipefail

APP_DIR="${APP_DIR:-/opt/salesos}"
REGISTRY="${REGISTRY:-ghcr.io}"
IMAGE_NAMESPACE="${IMAGE_NAMESPACE:-ragheeda-boop/salesos}"
IMAGE_TAG="${IMAGE_TAG:-latest}"
COMPOSE_FILE="docker-compose.prod.yml"

echo "=== SalesOS Deployment ==="
echo "  Registry:   $REGISTRY"
echo "  Namespace:  $IMAGE_NAMESPACE"
echo "  Tag:        $IMAGE_TAG"
echo "  Target:     $APP_DIR"
echo ""

# 1. Ensure target directory exists
mkdir -p "$APP_DIR"

# 2. Copy required files if not present (first-time setup)
if [ ! -f "$APP_DIR/.env.production" ]; then
    echo "[!] No .env.production found at $APP_DIR/.env.production"
    echo "    Create one from .env.production.template and re-run."
    exit 1
fi

# 3. Copy compose file & infra
cp "$COMPOSE_FILE" "$APP_DIR/"
cp -r infra "$APP_DIR/" 2>/dev/null || true

# 4. Build and push images (local build, or rely on CI)
if [ "${CI:-false}" != "true" ]; then
    echo "--- Building backend image ---"
    docker build \
        -t "$REGISTRY/$IMAGE_NAMESPACE/backend:$IMAGE_TAG" \
        -t "$REGISTRY/$IMAGE_NAMESPACE/backend:latest" \
        -f backend/Dockerfile backend/

    echo "--- Building frontend image ---"
    docker build \
        -t "$REGISTRY/$IMAGE_NAMESPACE/frontend:$IMAGE_TAG" \
        -t "$REGISTRY/$IMAGE_NAMESPACE/frontend:latest" \
        -f frontend/Dockerfile frontend/

    echo "--- Pushing images ---"
    docker push "$REGISTRY/$IMAGE_NAMESPACE/backend:$IMAGE_TAG"
    docker push "$REGISTRY/$IMAGE_NAMESPACE/backend:latest"
    docker push "$REGISTRY/$IMAGE_NAMESPACE/frontend:$IMAGE_TAG"
    docker push "$REGISTRY/$IMAGE_NAMESPACE/frontend:latest"
fi

# 5. Deploy on VPS
cd "$APP_DIR"

echo "--- Pulling images on VPS ---"
docker compose -f "$COMPOSE_FILE" pull

echo "--- Starting services ---"
docker compose -f "$COMPOSE_FILE" up -d --remove-orphans

echo "--- Cleaning up old images ---"
docker image prune -f

echo ""
echo "=== Deployment complete ==="
echo "  Backend:  https://api.$(grep DOMAIN .env.production | head -1 | cut -d= -f2)/health"
echo "  Frontend: https://$(grep DOMAIN .env.production | head -1 | cut -d= -f2)"
