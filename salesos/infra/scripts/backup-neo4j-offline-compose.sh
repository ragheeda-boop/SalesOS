#!/bin/bash
# Offline Neo4j dump for local Docker Compose (Community) when APOC is absent.
# Stops the compose neo4j service briefly, dumps via neo4j-admin into the backup
# volume, then starts neo4j again. NON-PROD only — do not run against production.
#
# Usage (from salesos/):
#   bash infra/scripts/backup-neo4j-offline-compose.sh
#
# Env:
#   COMPOSE_FILE          default: docker-compose.yml
#   NEO4J_SERVICE         default: neo4j
#   NEO4J_DATA_VOLUME     default: salesos_neo4j_data
#   BACKUP_VOLUME         default: salesos_backup_data
#   DUMP_SUBDIR           default: neo4j_wave10_dr
#   NEO4J_IMAGE           default: neo4j:5-community
#   SKIP_STOP=1           refuse to proceed (safety) unless unset/0
set -euo pipefail

COMPOSE_FILE="${COMPOSE_FILE:-docker-compose.yml}"
NEO4J_SERVICE="${NEO4J_SERVICE:-neo4j}"
NEO4J_DATA_VOLUME="${NEO4J_DATA_VOLUME:-salesos_neo4j_data}"
BACKUP_VOLUME="${BACKUP_VOLUME:-salesos_backup_data}"
DUMP_SUBDIR="${DUMP_SUBDIR:-neo4j_wave10_dr}"
NEO4J_IMAGE="${NEO4J_IMAGE:-neo4j:5-community}"

if [ "${ALLOW_NEO4J_STOP:-}" != "1" ]; then
  echo "Refusing: set ALLOW_NEO4J_STOP=1 to acknowledge brief Neo4j downtime (NON-PROD)." >&2
  exit 2
fi

echo "[$(date -u +%Y-%m-%dT%H:%M:%SZ)] Preparing dump dir on $BACKUP_VOLUME/$DUMP_SUBDIR"
docker run --rm -v "${BACKUP_VOLUME}:/backups" alpine:3.20 \
  sh -c "mkdir -p /backups/${DUMP_SUBDIR} && chmod 777 /backups/${DUMP_SUBDIR}"

echo "[$(date -u +%Y-%m-%dT%H:%M:%SZ)] Stopping compose service $NEO4J_SERVICE"
docker compose -f "$COMPOSE_FILE" stop "$NEO4J_SERVICE"

cleanup_start() {
  echo "[$(date -u +%Y-%m-%dT%H:%M:%SZ)] Starting compose service $NEO4J_SERVICE"
  docker compose -f "$COMPOSE_FILE" start "$NEO4J_SERVICE" || true
}
trap cleanup_start EXIT

echo "[$(date -u +%Y-%m-%dT%H:%M:%SZ)] neo4j-admin database dump neo4j -> /backups/${DUMP_SUBDIR}"
docker run --rm \
  -v "${NEO4J_DATA_VOLUME}:/data" \
  -v "${BACKUP_VOLUME}:/backups" \
  --user neo4j \
  "$NEO4J_IMAGE" \
  neo4j-admin database dump neo4j \
    --to-path="/backups/${DUMP_SUBDIR}" \
    --overwrite-destination=true

docker run --rm -v "${BACKUP_VOLUME}:/backups" alpine:3.20 \
  sh -c "ls -lah /backups/${DUMP_SUBDIR}; wc -c /backups/${DUMP_SUBDIR}/neo4j.dump"

echo "[$(date -u +%Y-%m-%dT%H:%M:%SZ)] Dump finished OK (trap will restart neo4j)"
