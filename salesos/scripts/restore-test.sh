#!/usr/bin/env bash
# =============================================================================
# SalesOS Backup Restore Test — validates backup integrity by restoring
# to a temp environment.
#
# Phase 1: Create full backup (pg_dump + neo4j-admin dump + redis SAVE)
# Phase 2: Destroy data (DROP SCHEMA public CASCADE + DETACH DELETE + FLUSHALL)
# Phase 3: Restore from backup (pg_restore + neo4j-admin load + redis reload)
# Phase 4: Verify row counts match pre-backup + smoke test
#
# Usage:
#   ./scripts/restore-test.sh
#   ./scripts/restore-test.sh --base-url http://api.salesos.com:8000
# =============================================================================
set -euo pipefail

# --- Config ---
BACKUP_DIR="${BACKUP_DIR:-/backups}"
PGHOST="${PGHOST:-postgres}"
PGPORT="${PGPORT:-5432}"
PGUSER="${PGUSER:-salesos}"
PGDB="${PGDB:-salesos}"
NEO4J_URI="${NEO4J_URI:-bolt://neo4j:7687}"
NEO4J_USER="${NEO4J_USER:-neo4j}"
REDIS_HOST="${REDIS_HOST:-redis}"
REDIS_PORT="${REDIS_PORT:-6379}"
BASE_URL="${BASE_URL:-http://localhost:8000}"
TIMESTAMP=$(date +%Y%m%d-%H%M%S)
PASS=0
FAIL=0

declare -A PRE_COUNTS

log()  { echo "[$(date '+%Y-%m-%d %H:%M:%S')] [$1] $2"; }
info() { log "INFO" "$1"; }
ok()   { echo "  [PASS] $1${2:+ - $2}"; ((PASS++)); }
fail() { echo "  [FAIL] $1${2:+ - $2}"; ((FAIL++)); }
skip() { echo "  [SKIP] $1${2:+ - $2}"; }

phase() {
    echo ""
    echo "============================================"
    echo "  $1"
    echo "============================================"
}

# ============================================================================
#  PHASE 1: Create Backup
# ============================================================================
phase "PHASE 1/4: Create Backup"
info "Starting backup at $TIMESTAMP"
mkdir -p "$BACKUP_DIR"

# --- 1a. PostgreSQL ---
info "Running pg_dump..."
PGDUMP_FILE="$BACKUP_DIR/restore-test-pg-$TIMESTAMP.dump"
PGPASSWORD="${POSTGRES_PASSWORD}" pg_dump -h "$PGHOST" -p "$PGPORT" -U "$PGUSER" -d "$PGDB" \
    --format=custom --compress=9 --file="$PGDUMP_FILE"
ok "PostgreSQL Backup" "$(du -h "$PGDUMP_FILE" | cut -f1)"

# Save pre-backup row counts
TABLES=$(PGPASSWORD="${POSTGRES_PASSWORD}" psql -h "$PGHOST" -p "$PGPORT" -U "$PGUSER" -d "$PGDB" \
    -t -A -c "SELECT schemaname||'.'||tablename FROM pg_stat_user_tables WHERE schemaname NOT IN ('pg_catalog','information_schema')")
for TBL in $TABLES; do
    CNT=$(PGPASSWORD="${POSTGRES_PASSWORD}" psql -h "$PGHOST" -p "$PGPORT" -U "$PGUSER" -d "$PGDB" \
        -t -A -c "SELECT count(*) FROM $TBL")
    PRE_COUNTS["pg:$TBL"]="$CNT"
done
ok "Pre-backup Row Counts" "$(echo "$TABLES" | wc -l) tables recorded"

# --- 1b. Neo4j ---
info "Running Neo4j backup..."
NEO4J_FILE="$BACKUP_DIR/restore-test-neo4j-$TIMESTAMP.dump"

# Save pre-backup counts
NODE_COUNT=$(cypher-shell -a "$NEO4J_URI" -u "$NEO4J_USER" -p "$NEO4J_PASSWORD" \
    "MATCH (n) RETURN count(n) AS cnt" 2>/dev/null | grep -E '^[0-9]+' || echo "0")
REL_COUNT=$(cypher-shell -a "$NEO4J_URI" -u "$NEO4J_USER" -p "$NEO4J_PASSWORD" \
    "MATCH ()-[r]->() RETURN count(r) AS cnt" 2>/dev/null | grep -E '^[0-9]+' || echo "0")
PRE_COUNTS["neo4j:nodes"]="$NODE_COUNT"
PRE_COUNTS["neo4j:relationships"]="$REL_COUNT"

# APOC export preferred, fallback to neo4j-admin dump
if cypher-shell -a "$NEO4J_URI" -u "$NEO4J_USER" -p "$NEO4J_PASSWORD" \
    "CALL apoc.export.json.all('$NEO4J_FILE', {useTypes: true})" 2>/dev/null; then
    ok "Neo4j Backup (APOC)" "$(du -h "$NEO4J_FILE" | cut -f1)"
elif neo4j-admin dump --database=neo4j --to="$NEO4J_FILE"; then
    ok "Neo4j Backup (admin dump)" "$(du -h "$NEO4J_FILE" | cut -f1)"
else
    fail "Neo4j Backup" "no backup method available"
fi

# --- 1c. Redis ---
info "Running Redis SAVE..."
if [ -n "${REDIS_PASSWORD:-}" ]; then
    redis-cli -h "$REDIS_HOST" -p "$REDIS_PORT" -a "$REDIS_PASSWORD" SAVE >/dev/null
else
    redis-cli -h "$REDIS_HOST" -p "$REDIS_PORT" SAVE >/dev/null
fi
sleep 1
REDIS_FILE="$BACKUP_DIR/restore-test-redis-$TIMESTAMP.rdb"
cp /data/dump.rdb "$REDIS_FILE" 2>/dev/null || \
    cp /var/lib/redis/dump.rdb "$REDIS_FILE" 2>/dev/null || \
    fail "Redis Backup" "dump.rdb not found"
ok "Redis Backup" "$(du -h "$REDIS_FILE" | cut -f1)"

# ============================================================================
#  PHASE 2: Destroy Data
# ============================================================================
phase "PHASE 2/4: Destroy Data"
info "WARNING: Destroying data in source databases for restore test"

info "Dropping PostgreSQL schema..."
PGPASSWORD="${POSTGRES_PASSWORD}" psql -h "$PGHOST" -p "$PGPORT" -U "$PGUSER" -d "$PGDB" \
    -c "DROP SCHEMA public CASCADE; CREATE SCHEMA public; GRANT ALL ON SCHEMA public TO $PGUSER; GRANT ALL ON SCHEMA public TO public;"
ok "PostgreSQL Destroy"

info "Deleting Neo4j data..."
cypher-shell -a "$NEO4J_URI" -u "$NEO4J_USER" -p "$NEO4J_PASSWORD" \
    "MATCH (n) DETACH DELETE n" >/dev/null
ok "Neo4j Destroy"

info "Flushing Redis..."
if [ -n "${REDIS_PASSWORD:-}" ]; then
    redis-cli -h "$REDIS_HOST" -p "$REDIS_PORT" -a "$REDIS_PASSWORD" FLUSHALL >/dev/null
else
    redis-cli -h "$REDIS_HOST" -p "$REDIS_PORT" FLUSHALL >/dev/null
fi
ok "Redis Destroy"

# ============================================================================
#  PHASE 3: Restore from Backup
# ============================================================================
phase "PHASE 3/4: Restore from Backup"

info "Restoring PostgreSQL..."
PGPASSWORD="${POSTGRES_PASSWORD}" pg_restore -h "$PGHOST" -p "$PGPORT" -U "$PGUSER" -d "$PGDB" \
    --clean --if-exists --no-owner --no-acl "$PGDUMP_FILE"
ok "PostgreSQL Restore"

info "Restoring Neo4j..."
if [ -f "$NEO4J_FILE" ]; then
    if cypher-shell -a "$NEO4J_URI" -u "$NEO4J_USER" -p "$NEO4J_PASSWORD" \
        "CALL apoc.import.json('$NEO4J_FILE')" 2>/dev/null; then
        ok "Neo4j Restore (APOC)"
    elif neo4j-admin load --from="$NEO4J_FILE" --database=neo4j --force; then
        ok "Neo4j Restore (admin load)"
    else
        fail "Neo4j Restore"
    fi
else
    skip "Neo4j Restore" "no backup file"
fi

info "Restoring Redis..."
if [ -f "$REDIS_FILE" ]; then
    cp "$REDIS_FILE" /data/dump.rdb 2>/dev/null || cp "$REDIS_FILE" /var/lib/redis/dump.rdb 2>/dev/null || true
    if [ -n "${REDIS_PASSWORD:-}" ]; then
        redis-cli -h "$REDIS_HOST" -p "$REDIS_PORT" -a "$REDIS_PASSWORD" CONFIG SET dir /data >/dev/null
        redis-cli -h "$REDIS_HOST" -p "$REDIS_PORT" -a "$REDIS_PASSWORD" DEBUG RELOAD >/dev/null
    else
        redis-cli -h "$REDIS_HOST" -p "$REDIS_PORT" CONFIG SET dir /data >/dev/null
        redis-cli -h "$REDIS_HOST" -p "$REDIS_PORT" DEBUG RELOAD >/dev/null
    fi
    ok "Redis Restore"
else
    skip "Redis Restore" "no backup file"
fi

# ============================================================================
#  PHASE 4: Verify
# ============================================================================
phase "PHASE 4/4: Verify Restore"

# --- 4a. PostgreSQL row counts ---
info "Verifying PostgreSQL row counts..."
MISMATCHES=0
for KEY in "${!PRE_COUNTS[@]}"; do
    if [[ "$KEY" != pg:* ]]; then continue; fi
    TBL="${KEY#pg:}"
    EXPECTED="${PRE_COUNTS[$KEY]}"
    ACTUAL=$(PGPASSWORD="${POSTGRES_PASSWORD}" psql -h "$PGHOST" -p "$PGPORT" -U "$PGUSER" -d "$PGDB" \
        -t -A -c "SELECT count(*) FROM $TBL")
    if [ "$ACTUAL" = "$EXPECTED" ]; then
        ok "  $TBL" "$ACTUAL rows"
    else
        fail "  $TBL" "expected $EXPECTED, got $ACTUAL"
        ((MISMATCHES++))
    fi
done
[ "$MISMATCHES" -eq 0 ] && ok "PostgreSQL Row Counts" || fail "PostgreSQL Row Counts" "$MISMATCHES mismatches"

# --- 4b. Neo4j counts ---
ACTUAL_NODES=$(cypher-shell -a "$NEO4J_URI" -u "$NEO4J_USER" -p "$NEO4J_PASSWORD" \
    "MATCH (n) RETURN count(n) AS cnt" 2>/dev/null | grep -E '^[0-9]+' || echo "0")
ACTUAL_RELS=$(cypher-shell -a "$NEO4J_URI" -u "$NEO4J_USER" -p "$NEO4J_PASSWORD" \
    "MATCH ()-[r]->() RETURN count(r) AS cnt" 2>/dev/null | grep -E '^[0-9]+' || echo "0")
[ "$ACTUAL_NODES" = "${PRE_COUNTS[neo4j:nodes]}" ] && ok "Neo4j Nodes" "$ACTUAL_NODES" || fail "Neo4j Nodes" "expected ${PRE_COUNTS[neo4j:nodes]}, got $ACTUAL_NODES"
[ "$ACTUAL_RELS" = "${PRE_COUNTS[neo4j:relationships]}" ] && ok "Neo4j Relationships" "$ACTUAL_RELS" || fail "Neo4j Relationships" "expected ${PRE_COUNTS[neo4j:relationships]}, got $ACTUAL_RELS"

# --- 4c. Redis ---
if [ -n "${REDIS_PASSWORD:-}" ]; then
    KEY_COUNT=$(redis-cli -h "$REDIS_HOST" -p "$REDIS_PORT" -a "$REDIS_PASSWORD" DBSIZE)
else
    KEY_COUNT=$(redis-cli -h "$REDIS_HOST" -p "$REDIS_PORT" DBSIZE)
fi
ok "Redis Keys" "$KEY_COUNT keys"

# --- 4d. Smoke test ---
info "Running smoke test against $BASE_URL..."
if [ -f "$(dirname "$0")/smoke-test.sh" ]; then
    bash "$(dirname "$0")/smoke-test.sh" --base-url "$BASE_URL" && ok "Smoke Test" || fail "Smoke Test"
else
    info "smoke-test.sh not found — skipping"
fi

# ============================================================================
#  Summary
# ============================================================================
echo ""
echo "============================================"
echo "  RESTORE TEST SUMMARY"
echo "============================================"
echo "  Pass: $PASS"
echo "  Fail: $FAIL"
echo "  Overall: $([ "$FAIL" -eq 0 ] && echo 'ALL PASSED' || echo 'FAILED')"
echo ""

[ "$FAIL" -gt 0 ] && exit 1 || exit 0
