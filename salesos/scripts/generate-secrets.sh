#!/usr/bin/env bash
# ============================================================================
# Kubernetes Secrets Generator for SalesOS Production
# ============================================================================
# Usage: bash generate-secrets.sh
# Output: salesos-secrets.yaml (Sealed Secrets compatible)
# ============================================================================

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
OUTPUT_FILE="$PROJECT_DIR/infra/k8s/secrets-generated.yaml"
ENV_FILE="$PROJECT_DIR/.env.production"

# ── Security: Generate strong random values ────────────────────────
generate_secret() {
    local length="${1:-32}"
    openssl rand -hex "$length" 2>/dev/null || python3 -c "import secrets; print(secrets.token_hex($length))"
}

log() { echo -e "\033[0;34m[$(date +%H:%M:%S)]\033[0m $*"; }
warn() { echo -e "\033[1;33m[!]\033[0m $*"; }

log "SalesOS Kubernetes Secrets Generator"
log "====================================="

# ── Load existing env or generate new values ──────────────────────
declare -A SECRETS

# Load from .env.production if exists
if [ -f "$ENV_FILE" ]; then
    log "Loading secrets from $ENV_FILE..."
    set -a; source "$ENV_FILE" 2>/dev/null || true; set +a
else
    warn ".env.production not found — generating ALL secrets fresh"
fi

# Critical secrets (generate if not set or placeholder)
for key in \
    POSTGRES_PASSWORD:32 \
    NEO4J_PASSWORD:24 \
    SECRET_KEY:64 \
    JWT_SECRET_KEY:64 \
    REDIS_PASSWORD:32 \
    GRAFANA_ADMIN_PASSWORD:16 \
    OPENAI_API_KEY:0 \
    GOOGLE_CLIENT_SECRET:0 \
    MICROSOFT_CLIENT_SECRET:0 \
    SLACK_WEBHOOK_URL:0 \
; do
    IFS=':' read -r key len <<< "$key"
    val="${!key:-}"
    if [ -z "$val" ] || [[ "$val" == *"CHANGE_ME"* ]] || [[ "$val" == *"change-me"* ]]; then
        if [ "$len" = "0" ]; then
            val=""
            warn "$key: Requires external value (set in .env.production)"
        else
            val=$(generate_secret "$len")
            log "Generated $key"
        fi
    fi
    SECRETS[$key]="$val"
done

# Preset non-secret config values
CONFIG_VARS=(
    "POSTGRES_USER:salesos"
    "POSTGRES_DB:salesos"
    "POSTGRES_HOST:postgres"
    "POSTGRES_PORT:5432"
    "NEO4J_URI:bolt://neo4j:7687"
    "NEO4J_USER:neo4j"
    "REDIS_URL:redis://redis:6379/0"
    "EVENT_BUS_TYPE:kafka"
    "KAFKA_BOOTSTRAP_SERVERS:kafka:9092"
    "KAFKA_GROUP_ID:salesos"
    "KAFKA_AUTO_OFFSET_RESET:earliest"
    "ALLOWED_HOSTS:*"
    "SALESOS_ENV:production"
    "SALESOS_DEBUG:false"
    "FEATURE_AI_COPILOT:false"
    "FEATURE_SEARCH_FUZZY_V2:false"
    "FEATURE_CRM_KANBAN:false"
    "DEMO_MODE:false"
    "OTEL_EXPORTER_OTLP_ENDPOINT:http://otel-collector:4317"
    "LOG_LEVEL:INFO"
    "CELERY_TASK_TIME_LIMIT:600"
    "CELERY_TASK_SOFT_TIME_LIMIT:300"
    "CELERY_WORKER_MAX_TASKS_PER_CHILD:1000"
    "CELERY_WORKER_PREFETCH_MULTIPLIER:1"
    "CELERY_RESULT_EXPIRES:86400"
    "CELERY_MAX_RETRIES:3"
    "CELERY_DEFAULT_RETRY_DELAY:60"
    "JWT_ALGORITHM:HS256"
    "JWT_ACCESS_TOKEN_EXPIRE_MINUTES:30"
    "JWT_REFRESH_TOKEN_EXPIRE_DAYS:7"
)

# ── Generate YAML ─────────────────────────────────────────────────
cat > "$OUTPUT_FILE" << 'YAML_HEADER'
# ============================================================================
# SalesOS Kubernetes Secrets — AUTO-GENERATED
# Generated: $(date)
# ============================================================================
# This file contains Kubernetes Secrets for SalesOS production deployment.
# 
# IMPORTANT: 
#   1. Encrypt this file with Sealed Secrets before committing:
#      kubeseal < salesos-secrets.yaml > salesos-sealed-secrets.yaml
#   2. OR use External Secrets Operator with AWS Secrets Manager / Vault.
#   3. NEVER commit this file to git in plaintext.
# ============================================================================

apiVersion: v1
kind: Secret
metadata:
  name: salesos-secrets
  namespace: salesos
  labels:
    app: salesos
    component: secrets
type: Opaque
stringData:
YAML_HEADER

# Write secrets
for key in "${!SECRETS[@]}"; do
    val="${SECRETS[$key]}"
    # Escape YAML special chars
    val="${val//\\/\\\\}"
    val="${val//\"/\\\"}"
    echo "  ${key}: \"${val}\""
done >> "$OUTPUT_FILE"

# ── Generate ConfigMap ────────────────────────────────────────────
CONFIGMAP_FILE="$PROJECT_DIR/infra/k8s/configmap-generated.yaml"
cat > "$CONFIGMAP_FILE" << 'CM_HEADER'
apiVersion: v1
kind: ConfigMap
metadata:
  name: salesos-config
  namespace: salesos
  labels:
    app: salesos
data:
CM_HEADER

for entry in "${CONFIG_VARS[@]}"; do
    IFS=':' read -r key val <<< "$entry"
    echo "  ${key}: \"${val}\""
done >> "$CONFIGMAP_FILE"

# ── Summary ───────────────────────────────────────────────────────
echo ""
log "Generated files:"
log "  Secrets:        $OUTPUT_FILE"
log "  ConfigMap:      $CONFIGMAP_FILE"
echo ""
log "Next steps:"
log "  1. Review generated secrets"
log "  2. Encrypt:    kubeseal < $OUTPUT_FILE > sealed-secrets.yaml"
log "  3. Deploy:     kubectl apply -f $CONFIGMAP_FILE"
log "  4. Deploy:     kubectl apply -f sealed-secrets.yaml"
log "  5. Verify:     kubectl get secrets -n salesos"
