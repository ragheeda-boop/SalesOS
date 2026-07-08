#!/bin/bash
set -euo pipefail

if [ $# -lt 1 ]; then
    echo "Usage: $0 <backup_file.dump>"
    exit 1
fi

BACKUP_FILE="$1"
DB_NAME="${DB_NAME:-salesos}"
DB_USER="${DB_USER:-salesos}"

if [ ! -f "$BACKUP_FILE" ]; then
    echo "Backup file not found: $BACKUP_FILE"
    exit 1
fi

pg_restore -U "$DB_USER" -d "$DB_NAME" \
    --clean \
    --if-exists \
    --no-owner \
    --no-acl \
    "$BACKUP_FILE"

echo "Database restored from: $BACKUP_FILE"
