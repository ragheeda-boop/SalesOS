#!/bin/bash
# restore-db.sh — PostgreSQL restore with primary-safety guardrails (Wave 10).
#
# Safety: default target is NOT the primary DB. Prefer disposable drill DBs
# (e.g. salesos_restore_drill) as documented in
# docs/audit/ga-engineering-audit/PROGRESS-WAVE10-BACKUP.md.
#
# Usage:
#   restore-db.sh <backup_file.dump> --db <target_db>
#   restore-db.sh <backup_file.dump> --db salesos --force   # wipe primary (explicit only)
#   DB_NAME=salesos_restore_drill restore-db.sh <backup_file.dump>
#
# Env:
#   DB_NAME / --db     Restore target (required unless set via env)
#   DB_USER            Default: salesos
#   DB_HOST            Optional; passed to pg_restore -h when set
#   DB_PORT            Optional; passed to pg_restore -p when set
#   PRIMARY_DB_NAME    Name treated as primary (default: salesos)
#   --force            Required when target equals PRIMARY_DB_NAME
set -euo pipefail

usage() {
  cat <<'EOF'
Usage: restore-db.sh <backup_file.dump> --db <target_database> [--force]

  Restores a PostgreSQL custom-format dump. Default target is NOT primary.

  Required:
    <backup_file.dump>   Path to pg_dump -Fc archive
    --db NAME | DB_NAME  Target database (prefer disposable, e.g. salesos_restore_drill)

  Optional:
    --force              Required to restore into primary (default PRIMARY_DB_NAME=salesos)
    DB_USER              Default: salesos
    DB_HOST / DB_PORT    Passed to pg_restore when set

Disposable restore pattern (local NON-PROD):
  docker exec salesos-postgres-1 psql -U salesos -d postgres \
    -c "CREATE DATABASE salesos_restore_drill OWNER salesos;"
  DB_NAME=salesos_restore_drill restore-db.sh /backups/salesos_YYYYMMDD_HHMMSS.dump
EOF
}

BACKUP_FILE=""
DB_NAME="${DB_NAME:-}"
DB_USER="${DB_USER:-salesos}"
DB_HOST="${DB_HOST:-}"
DB_PORT="${DB_PORT:-}"
PRIMARY_DB_NAME="${PRIMARY_DB_NAME:-salesos}"
FORCE=0

while [ $# -gt 0 ]; do
  case "$1" in
    -h|--help)
      usage
      exit 0
      ;;
    --db)
      if [ $# -lt 2 ]; then
        echo "ERROR: --db requires a database name" >&2
        exit 1
      fi
      DB_NAME="$2"
      shift 2
      ;;
    --force)
      FORCE=1
      shift
      ;;
    --)
      shift
      break
      ;;
    -*)
      echo "ERROR: unknown option: $1" >&2
      usage >&2
      exit 1
      ;;
    *)
      if [ -z "$BACKUP_FILE" ]; then
        BACKUP_FILE="$1"
      else
        echo "ERROR: unexpected argument: $1" >&2
        usage >&2
        exit 1
      fi
      shift
      ;;
  esac
done

if [ -z "$BACKUP_FILE" ]; then
  echo "ERROR: backup file required" >&2
  usage >&2
  exit 1
fi

if [ -z "$DB_NAME" ]; then
  echo "ERROR: restore target not set. Pass --db <name> or set DB_NAME." >&2
  echo "       Refusing to default to primary '${PRIMARY_DB_NAME}'." >&2
  echo "       Prefer disposable: --db salesos_restore_drill" >&2
  exit 1
fi

# Refuse primary before file I/O so operators always see the safety error.
if [ "$DB_NAME" = "$PRIMARY_DB_NAME" ] && [ "$FORCE" -ne 1 ]; then
  echo "ERROR: refusing restore into primary database '${PRIMARY_DB_NAME}'." >&2
  echo "       Use a disposable DB (e.g. --db salesos_restore_drill), or pass --force" >&2
  echo "       only after an approved wipe window on NON-PROD." >&2
  exit 1
fi

if [ ! -f "$BACKUP_FILE" ]; then
  echo "ERROR: Backup file not found: $BACKUP_FILE" >&2
  exit 1
fi

RESTORE_ARGS=(-U "$DB_USER" -d "$DB_NAME" --clean --if-exists --no-owner --no-acl)
if [ -n "$DB_HOST" ]; then
  RESTORE_ARGS=(-h "$DB_HOST" "${RESTORE_ARGS[@]}")
fi
if [ -n "$DB_PORT" ]; then
  RESTORE_ARGS=(-p "$DB_PORT" "${RESTORE_ARGS[@]}")
fi

if [ "$DB_NAME" = "$PRIMARY_DB_NAME" ]; then
  echo "WARNING: restoring into PRIMARY '${PRIMARY_DB_NAME}' with --force" >&2
fi

echo "Restoring '$BACKUP_FILE' → database '$DB_NAME' (user=$DB_USER)..."
pg_restore "${RESTORE_ARGS[@]}" "$BACKUP_FILE"

echo "Database restored from: $BACKUP_FILE → $DB_NAME"
