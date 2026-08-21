#!/usr/bin/env bash
# Railway rollback — redeploy previous successful deployment.
#
# Usage:
#   scripts/railway_rollback.sh                    # rollback staging
#   scripts/railway_rollback.sh --environment prod  # rollback production
#
# Requires: RAILWAY_TOKEN env var + railway CLI installed.
# Safety: prompts for confirmation before rollback; logs deployment before/after.
set -euo pipefail

ENV="${ENV:-staging}"
SERVICE=""
PROJECT_ID="${RAILWAY_PROJECT_ID:-}"
DRY_RUN=false

while [[ $# -gt 0 ]]; do
  case "$1" in
    --environment|-e) ENV="$2"; shift 2 ;;
    --service|-s)     SERVICE="$2"; shift 2 ;;
    --project|-p)     PROJECT_ID="$2"; shift 2 ;;
    --dry-run)        DRY_RUN=true; shift ;;
    -h|--help)
      echo "Usage: $0 [--environment staging|prod] [--service SERVICE_ID] [--project PROJECT_ID] [--dry-run]"
      exit 0
      ;;
    *) echo "Unknown option: $1"; exit 1 ;;
  esac
done

if [[ -z "${RAILWAY_TOKEN:-}" ]]; then
  echo "::error::RAILWAY_TOKEN not set" >&2
  exit 1
fi

echo "=== Railway Rollback ==="
echo "Environment: ${ENV}"
echo "Project:     ${PROJECT_ID:-<default>}"
echo "Service:     ${SERVICE:-<default>}"
echo "Dry run:     ${DRY_RUN}"
echo ""

# Build common args
ARGS=()
[[ -n "$PROJECT_ID" ]] && ARGS+=(--project "$PROJECT_ID")
[[ -n "$ENV" ]]        && ARGS+=(--environment "$ENV")
[[ -n "$SERVICE" ]]    && ARGS+=(--service "$SERVICE")

# Show current deployment
echo "--- Current deployment ---"
railway status "${ARGS[@]}" 2>/dev/null || echo "(could not fetch status)"
echo ""

if [[ "$DRY_RUN" == "true" ]]; then
  echo "[dry-run] Would run: railway rollback ${ARGS[*]}"
  exit 0
fi

# Confirm
read -rp "Rollback ${ENV}? [y/N] " confirm
if [[ "${confirm}" != "y" && "${confirm}" != "Y" ]]; then
  echo "Aborted."
  exit 0
fi

echo "--- Executing rollback ---"
railway rollback "${ARGS[@]}"

echo ""
echo "--- Verifying ---"
railway status "${ARGS[@]}" 2>/dev/null || echo "(could not fetch status)"

echo ""
echo "Rollback complete. Verify health at the service URL."
