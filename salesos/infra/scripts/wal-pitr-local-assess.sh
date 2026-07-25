#!/bin/bash
# Local NON-PROD WAL / PITR readiness assessment for SalesOS compose Postgres.
# Read-only by default — does NOT enable archive_mode, alter data, or touch production.
#
# Usage (from host with docker):
#   bash salesos/infra/scripts/wal-pitr-local-assess.sh
#   PG_CONTAINER=salesos-postgres-1 bash salesos/infra/scripts/wal-pitr-local-assess.sh
#
# Optional evidence file:
#   EVIDENCE_OUT=/path/to/evidence.txt bash .../wal-pitr-local-assess.sh
set -euo pipefail

PG_CONTAINER="${PG_CONTAINER:-salesos-postgres-1}"
DB_USER="${DB_USER:-salesos}"
DB_NAME="${DB_NAME:-salesos}"
EVIDENCE_OUT="${EVIDENCE_OUT:-}"

if ! docker inspect "$PG_CONTAINER" >/dev/null 2>&1; then
  echo "ERROR: container not found: $PG_CONTAINER (local compose only)" >&2
  exit 1
fi

run_psql() {
  docker exec "$PG_CONTAINER" psql -U "$DB_USER" -d "$DB_NAME" "$@"
}

emit() {
  echo "$*"
  if [ -n "$EVIDENCE_OUT" ]; then
    echo "$*" >> "$EVIDENCE_OUT"
  fi
}

if [ -n "$EVIDENCE_OUT" ]; then
  mkdir -p "$(dirname "$EVIDENCE_OUT")"
  : > "$EVIDENCE_OUT"
fi

emit "=== SalesOS local WAL/PITR assessment (NON-PROD) ==="
emit "timestamp_utc=$(date -u +%Y-%m-%dT%H:%M:%SZ)"
emit "container=$PG_CONTAINER"
emit ""

emit "-- settings --"
run_psql -c "SHOW wal_level;"
run_psql -c "SHOW archive_mode;"
run_psql -c "SHOW archive_command;"
run_psql -c "SHOW archive_timeout;"
run_psql -c "SHOW max_wal_senders;"
run_psql -c "SHOW wal_keep_size;"
emit ""

emit "-- archiver stats --"
run_psql -c "SELECT archived_count, last_archived_wal, last_archived_time, failed_count, last_failed_wal FROM pg_stat_archiver;"
emit ""

emit "-- replication privilege (needed for pg_basebackup drills) --"
run_psql -c "SELECT rolname, rolreplication FROM pg_roles WHERE rolname = current_user;"
emit ""

ARCHIVE_MODE=$(run_psql -Atc "SHOW archive_mode;")
WAL_LEVEL=$(run_psql -Atc "SHOW wal_level;")

emit "-- verdict --"
emit "wal_level=$WAL_LEVEL archive_mode=$ARCHIVE_MODE"
if [ "$ARCHIVE_MODE" = "off" ]; then
  emit "STATUS: PITR NOT CONFIGURED locally — RPO remains daily pg_dump snapshot (~24h)."
  emit "NOTE: Do not claim production PITR. See runbooks/wal-pitr-local-drill.md for optional local-safe next steps."
else
  emit "STATUS: archive_mode is ON — still require successful archive + restore drill evidence before PITR claims."
fi
emit "CTO decision stub: docs/audit/ga-engineering-audit/PROGRESS-WAVE10-DR-GAPS.md (PROD-W10-003)"
