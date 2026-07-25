#!/bin/bash
# Load a Neo4j dump into a DISPOSABLE Docker volume and optionally boot a
# temporary container to verify. Does NOT stop or modify primary Neo4j data.
# NON-PROD only.
#
# Usage (from salesos/):
#   bash infra/scripts/restore-neo4j-load-drill-compose.sh
#
# Env:
#   BACKUP_VOLUME       default: salesos_backup_data
#   DUMP_SUBDIR         default: neo4j_wave10_dr
#   DRILL_VOLUME        default: salesos_neo4j_load_drill
#   NEO4J_IMAGE         default: neo4j:5-community
#   SKIP_BOOT=1         load only (skip temporary server + cypher check)
#   KEEP_TEMP=1         leave neo4j-wave10-load-drill running (default: stop/rm)
set -euo pipefail

BACKUP_VOLUME="${BACKUP_VOLUME:-salesos_backup_data}"
DUMP_SUBDIR="${DUMP_SUBDIR:-neo4j_wave10_dr}"
DRILL_VOLUME="${DRILL_VOLUME:-salesos_neo4j_load_drill}"
NEO4J_IMAGE="${NEO4J_IMAGE:-neo4j:5-community}"
TEMP_NAME="${TEMP_NAME:-neo4j-wave10-load-drill}"

echo "[$(date -u +%Y-%m-%dT%H:%M:%SZ)] Creating/resetting disposable volume $DRILL_VOLUME"
docker volume create "$DRILL_VOLUME" >/dev/null
docker run --rm -v "${DRILL_VOLUME}:/data" alpine:3.20 \
  sh -c "rm -rf /data/* /data/.[!.]* 2>/dev/null; mkdir -p /data; chown -R 7474:7474 /data"

echo "[$(date -u +%Y-%m-%dT%H:%M:%SZ)] neo4j-admin database load neo4j from /backups/${DUMP_SUBDIR}"
docker run --rm \
  -v "${DRILL_VOLUME}:/data" \
  -v "${BACKUP_VOLUME}:/backups" \
  --user neo4j \
  "$NEO4J_IMAGE" \
  neo4j-admin database load neo4j \
    --from-path="/backups/${DUMP_SUBDIR}" \
    --overwrite-destination=true

if [ "${SKIP_BOOT:-0}" = "1" ]; then
  echo "[$(date -u +%Y-%m-%dT%H:%M:%SZ)] SKIP_BOOT=1 — load done; primary untouched"
  exit 0
fi

docker rm -f "$TEMP_NAME" >/dev/null 2>&1 || true
echo "[$(date -u +%Y-%m-%dT%H:%M:%SZ)] Booting temporary $TEMP_NAME (NEO4J_AUTH=none; no ports required)"
docker run -d --name "$TEMP_NAME" \
  -v "${DRILL_VOLUME}:/data" \
  -e NEO4J_AUTH=none \
  -e NEO4J_server_memory_heap_initial__size=512m \
  -e NEO4J_server_memory_heap_max__size=512m \
  "$NEO4J_IMAGE" >/dev/null

cleanup() {
  if [ "${KEEP_TEMP:-0}" != "1" ]; then
    echo "[$(date -u +%Y-%m-%dT%H:%M:%SZ)] Stopping temporary $TEMP_NAME"
    docker stop "$TEMP_NAME" >/dev/null 2>&1 || true
    docker rm "$TEMP_NAME" >/dev/null 2>&1 || true
  fi
}
trap cleanup EXIT

ok=0
for i in $(seq 1 40); do
  sleep 5
  if docker exec "$TEMP_NAME" cypher-shell "RETURN 1 AS ok;" >/dev/null 2>&1; then
    ok=1
    echo "[$(date -u +%Y-%m-%dT%H:%M:%SZ)] cypher RETURN 1 OK"
    docker exec "$TEMP_NAME" cypher-shell --format plain "MATCH (n) RETURN count(n) AS nodes;" || true
    break
  fi
done

if [ "$ok" != "1" ]; then
  echo "ERROR: temporary Neo4j did not accept cypher in time" >&2
  docker logs --tail 80 "$TEMP_NAME" >&2 || true
  exit 1
fi

echo "[$(date -u +%Y-%m-%dT%H:%M:%SZ)] Load-verify finished (primary Neo4j was not stopped)"
