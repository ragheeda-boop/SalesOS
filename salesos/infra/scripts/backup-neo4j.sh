#!/bin/bash
set -euo pipefail

BACKUP_DIR="${BACKUP_DIR:-/backups/neo4j}"
NEO4J_URI="${NEO4J_URI:-bolt://neo4j:7687}"
NEO4J_USER="${NEO4J_USER:-neo4j}"
NEO4J_PASSWORD="${NEO4J_PASSWORD:?Set NEO4J_PASSWORD}"
RETENTION_DAYS="${RETENTION_DAYS:-7}"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
DUMP_FILE="${BACKUP_DIR}/neo4j_${TIMESTAMP}.dump"
LOG_FILE="${BACKUP_DIR}/neo4j_backup.log"

log() {
  echo "[$(date '+%Y-%m-%d %H:%M:%S')] $*" | tee -a "$LOG_FILE"
}

mkdir -p "$BACKUP_DIR"

log "Starting Neo4j backup..."

# Method 1: neo4j-admin database dump (offline — requires restart)
# Method 2: cypher-shell APOC export (online — no restart needed)

# Try online method first via cypher-shell
if command -v cypher-shell &>/dev/null; then
  log "Attempting online backup via cypher-shell..."
  cypher-shell -u "$NEO4J_USER" -p "$NEO4J_PASSWORD" \
    "CALL apoc.export.cypher.all(null, {format: 'cypher-shell', useOptimizations: {unwindCollections: true}})" \
    > "$DUMP_FILE" 2>> "$LOG_FILE" || true
fi

# If online method failed or cypher-shell not available, use neo4j-admin dump
if [ ! -f "$DUMP_FILE" ] || [ ! -s "$DUMP_FILE" ]; then
  log "Online method failed or unavailable, using neo4j-admin database dump..."
  neo4j-admin database dump neo4j --to-path="$DUMP_FILE" 2>> "$LOG_FILE" || {
    log "ERROR: All backup methods failed"
    exit 1
  }
fi

if [ -f "$DUMP_FILE" ] && [ -s "$DUMP_FILE" ]; then
  FILE_SIZE=$(stat -c%s "$DUMP_FILE" 2>/dev/null || stat -f%z "$DUMP_FILE" 2>/dev/null || echo 0)
  FILE_SIZE_MB=$((FILE_SIZE / 1048576))
  log "Backup complete: $(basename "$DUMP_FILE") (${FILE_SIZE_MB}MB)"

  # Cleanup old backups
  find "$BACKUP_DIR" -name "neo4j_*.dump" -mtime +"$RETENTION_DAYS" -delete -print | while read f; do
    log "Cleaned old backup: $f"
  done
else
  log "ERROR: Backup file is empty or missing"
  exit 1
fi
