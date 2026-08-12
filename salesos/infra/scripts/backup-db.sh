#!/bin/bash
set -euo pipefail

BACKUP_DIR="${BACKUP_DIR:-/backups}"
DB_NAME="${DB_NAME:-salesos}"
DB_USER="${DB_USER:-salesos}"
DB_HOST="${DB_HOST:-postgres}"
DB_PORT="${DB_PORT:-5432}"
RETENTION_DAYS="${RETENTION_DAYS:-7}"
HEALTHCHECK_URL="${HEALTHCHECK_URL:-}"
S3_BUCKET="${S3_BUCKET:-}"
NOTIFY_WEBHOOK="${NOTIFY_WEBHOOK:-}"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="${BACKUP_DIR}/${DB_NAME}_${TIMESTAMP}.dump"
LOG_FILE="${BACKUP_DIR}/backup.log"

log() {
  echo "[$(date '+%Y-%m-%d %H:%M:%S')] $*" | tee -a "$LOG_FILE"
}

notify() {
  local subject="$1"
  local message="$2"
  if [ -n "$NOTIFY_WEBHOOK" ]; then
    curl -sf -X POST -H "Content-Type: application/json" \
      -d "{\"text\": \"[$subject] $message\"}" \
      "$NOTIFY_WEBHOOK" 2>/dev/null || true
  fi
}

healthcheck() {
  # If HEALTHCHECK_URL is set, require HTTP success — silent swallow hid DR schedule failures.
  if [ -n "$HEALTHCHECK_URL" ]; then
    if curl -sf "$HEALTHCHECK_URL" >/dev/null; then
      log "Healthcheck OK: ${HEALTHCHECK_URL}"
    else
      log "ERROR: Healthcheck failed: ${HEALTHCHECK_URL}"
      notify "Backup Healthcheck Failed" "${DB_NAME} healthcheck failed after backup on $(hostname)"
      return 1
    fi
  fi
}

write_checksum() {
  if command -v sha256sum &>/dev/null; then
    sha256sum "$BACKUP_FILE" | tee "${BACKUP_FILE}.sha256" | tee -a "$LOG_FILE"
  elif command -v shasum &>/dev/null; then
    shasum -a 256 "$BACKUP_FILE" | tee "${BACKUP_FILE}.sha256" | tee -a "$LOG_FILE"
  else
    log "WARN: no sha256sum/shasum — checksum file not written"
  fi
}

cleanup_old() {
  local kept
  kept=$(find "$BACKUP_DIR" -name "${DB_NAME}_*.dump" -mtime +"$RETENTION_DAYS" -delete -print | wc -l)
  if [ "$kept" -gt 0 ]; then
    log "Cleaned up $kept old backups (retention: $RETENTION_DAYS days)"
  fi
}

backup_s3() {
  if [ -n "$S3_BUCKET" ]; then
    local s3_path="${S3_BUCKET}/$(date +%Y/%m)/$(basename "$BACKUP_FILE")"
    if command -v aws &>/dev/null; then
      aws s3 cp "$BACKUP_FILE" "$s3_path" && log "Uploaded to S3: $s3_path" || log "S3 upload failed"
    elif command -v rclone &>/dev/null; then
      rclone copy "$BACKUP_FILE" "$s3_path" && log "Uploaded via rclone: $s3_path" || log "rclone upload failed"
    fi
  fi
}

main() {
  mkdir -p "$BACKUP_DIR"
  log "Starting backup: ${DB_NAME}@${DB_HOST}:${DB_PORT}"

  START_TIME=$(date +%s%N)

  PGPASSWORD="${PGPASSWORD:?Set PGPASSWORD}" pg_dump -h "$DB_HOST" -p "$DB_PORT" \
    -U "$DB_USER" -d "$DB_NAME" \
    --format=custom --compress=9 --file="$BACKUP_FILE"

  DURATION_MS=$(( ($(date +%s%N) - START_TIME) / 1000000 ))
  FILE_SIZE=$(stat -c%s "$BACKUP_FILE" 2>/dev/null || stat -f%z "$BACKUP_FILE" 2>/dev/null || echo 0)
  FILE_SIZE_MB=$(( FILE_SIZE / 1048576 ))

  if [ -f "$BACKUP_FILE" ] && [ "$FILE_SIZE" -gt 0 ]; then
    log "Backup complete: $(basename "$BACKUP_FILE") (${FILE_SIZE_MB}MB, ${DURATION_MS}ms)"
    write_checksum
    cleanup_old
    backup_s3
    healthcheck || exit 1
  else
    log "ERROR: Backup file is empty or missing!"
    notify "Backup Failed" "${DB_NAME} backup failed on $(hostname) — empty output"
    exit 1
  fi
}

main "$@"
