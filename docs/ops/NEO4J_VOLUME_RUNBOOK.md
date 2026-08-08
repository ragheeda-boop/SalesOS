# Neo4j Volume Runbook

> **Status:** PREPARED (dev drill executed 2026-08-08)
> **Scope:** SalesOS — dev, staging, production
> **Related:** [ADR-108](../adr/0108-neo4j-keep-offline.md) (Neo4j offline in v1.0)
> **Last updated:** 2026-08-08 (dev drill results added)

---

## Context

Neo4j 5-community runs as a single-node instance in all environments. Per ADR-108 it carries **zero production traffic** in v1.0, but the container and its volumes exist and must be managed.

This runbook covers volume operations **exercised on staging first**, then applied to production.

| Resource | Value |
|----------|-------|
| Image | `neo4j:5-community` |
| Volumes | `neo4j_data` (persistent), `neo4j_logs` (append-only) |
| Docker named volumes | `neo4j_data`, `neo4j_logs` |
| Backup image | `neo4j:5-community` (cypher-shell / neo4j-admin built-in) |
| Prod resource limits | 1-2 CPUs, 2-4 GB RAM |

---

## Volume Layout

### Container mappings

```
neo4j container
  ├── /data       ←  neo4j_data    (graph store, indexes, transaction logs)
  └── /logs       ←  neo4j_logs    (debug.log, query.log, security.log)
```

### What lives on each volume

| Volume | Contents | Criticality |
|--------|----------|:-----------:|
| `neo4j_data` | Graph store (`neo4j` database), fulltext indexes (`company_fulltext`, `person_fulltext`), transaction logs | HIGH |
| `neo4j_logs` | `debug.log`, `query.log`, `security.log` — diagnostic only | LOW |

### Disk usage profile (dev baseline)

```
/data/databases/neo4j/  —  grows with inserted nodes/relationships
/data/transactions/     —  rotated automatically; keep 2-3 days headroom
```

**Warning threshold:** 70% of volume allocation
**Critical threshold:** 85% of volume allocation
**Action at critical:** Take backup immediately, then expand (or purge old data per ADR-108).

---

## Backup Procedures

### Scheduled backup (production — via `backup` service)

The production compose includes a `backup` service that runs `backup-neo4j.sh` nightly at **04:00 UTC**:

```bash
# cron in backup container (docker-compose.prod.yml)
echo "0 4 * * * /usr/local/bin/backup-neo4j" >> /etc/crontabs/root
```

The script (`infra/scripts/backup-neo4j.sh`) tries two methods:

1. **Online (preferred):** `cypher-shell` with `CALL apoc.export.cypher.all()` — no restart, exports Cypher statements
2. **Offline (fallback):** `neo4j-admin database dump neo4j` — requires read-only mode restart

Retention: 7 days (`RETENTION_DAYS=7`), output path: `$BACKUP_DIR/neo4j_YYYYMMDD_HHMMSS.dump`

### Manual backup (any environment)

```bash
# Set credentials
export NEO4J_PASSWORD="<password>"
export BACKUP_DIR="/opt/salesos/backups/neo4j"

# Run backup script from host
docker compose -f docker-compose.prod.yml exec backup /usr/local/bin/backup-neo4j

# Or run directly against the Neo4j container
docker compose -f docker-compose.yml exec neo4j \
  neo4j-admin database dump neo4j --to-path=/tmp/neo4j_dump.dump

# Copy dump to host
docker compose -f docker-compose.yml cp neo4j:/tmp/neo4j_dump.dump ./neo4j_backup_$(date +%Y%m%d_%H%M).dump
```

### Verify backup integrity

```bash
# Check file size > 0
stat --format=%s neo4j_backup_*.dump

# For cypher-shell exports: verify first 3 lines parse as Cypher
head -3 neo4j_backup_*.dump | grep -q "CREATE\|MERGE" && echo "cypher-shell backup looks valid"

# For neo4j-admin dumps: check magic bytes
file neo4j_backup_*.dump | grep -q "Neo4j" && echo "neo4j-admin dump looks valid"
```

---

## Restore Procedures

### Restore to existing volume (in-place)

```bash
# 1. Stop Neo4j
docker compose -f docker-compose.yml stop neo4j

# 2. Clear existing data (keep logs)
docker compose -f docker-compose.yml run --rm -v neo4j_data:/data alpine sh -c "rm -rf /data/databases /data/transactions"

# 3. Restore from neo4j-admin dump
docker compose -f docker-compose.yml run --rm \
  -v neo4j_data:/data \
  -v ./neo4j_backup_20260808_040000.dump:/tmp/restore.dump \
  neo4j:5-community neo4j-admin database load neo4j --from-path=/tmp/restore.dump --overwrite-destination=true

# 4. Start Neo4j
docker compose -f docker-compose.yml start neo4j

# 5. Wait for healthy
docker compose -f docker-compose.yml exec neo4j cypher-shell -u neo4j -p "$NEO4J_PASSWORD" "RETURN 1"

# 6. Rebuild fulltext indexes (they are created at app startup via neo4j_repository.py)
# The backend's ensure_indexes() will recreate them on next connection
docker compose -f docker-compose.yml restart backend
```

### Restore from cypher-shell export

```bash
# cypher-shell exports are executable Cypher — pipe them in
docker compose -f docker-compose.yml exec -T neo4j \
  cypher-shell -u neo4j -p "$NEO4J_PASSWORD" < neo4j_backup_cypher.dump
```

### Point-in-time restore (PITR)

```
NOT SUPPORTED in community edition.
Neo4j 5-community lacks incremental/transaction-log backup.
Recovery point is the last daily dump (up to 24h data loss).
Consider Neo4j AuraDB or Enterprise for PITR requirements.
```

---

## Volume Expansion

### Docker local-driver volume (default)

```bash
# 1. Stop Neo4j
docker compose -f docker-compose.yml stop neo4j

# 2. Backup volume contents
docker run --rm -v neo4j_data:/data -v "$(pwd)/backups:/backups" \
  alpine tar czf /backups/neo4j_data_backup.tar.gz -C /data .

# 3. Remove old volume
docker compose -f docker-compose.yml down -v neo4j  # WARNING: destroys volume

# 4. Recreate volume with explicit size (requires overlay2 with dm.basesize)
docker volume create --name neo4j_data --opt size=10G

# 5. Restore data
docker run --rm -v neo4j_data:/data -v "$(pwd)/backups:/backups" \
  alpine tar xzf /backups/neo4j_data_backup.tar.gz -C /data

# 6. Start Neo4j
docker compose -f docker-compose.yml up -d neo4j
```

### Cloud provider volume (staging/prod)

```bash
# AWS EBS: resize via console/CLI, then extend filesystem inside container
# do not use this; migrate to a larger instance/volume instead

# GCP Persistent Disk: resize via console, then extend filesystem
gcloud compute disks resize neo4j-data --size=20GB --zone=<zone>

# After resize, restart Neo4j — Docker detects new size automatically
docker compose -f docker-compose.prod.yml restart neo4j
```

---

## Migration (to new host/region)

### Full volume migration

```bash
# SOURCE host — export the volume
docker run --rm -v neo4j_data:/data -v "$(pwd)/export:/export" \
  alpine tar czf /export/neo4j_migrate.tar.gz -C /data .

# Transfer to TARGET host
scp neo4j_migrate.tar.gz target-host:/opt/salesos/

# TARGET host — import
docker volume create neo4j_data
docker run --rm -v neo4j_data:/data -v /opt/salesos:/import \
  alpine tar xzf /import/neo4j_migrate.tar.gz -C /data

# Start Neo4j on target
docker compose -f docker-compose.prod.yml up -d neo4j
```

---

## Health Verification

### Quick check (HTTP)

```bash
# Dev (remapped port 7475)
curl -s http://localhost:7475 | jq .neo4j_version

# Prod (internal, via docker compose exec)
docker compose -f docker-compose.prod.yml exec neo4j \
  cypher-shell -u "$NEO4J_USER" -p "$NEO4J_PASSWORD" "RETURN 1"
```

### Full health checklist

```bash
# 1. Container running
docker compose ps neo4j | grep -q "Up" && echo "✓ Container up"

# 2. HTTP reachable
curl -sf http://localhost:7475 > /dev/null && echo "✓ HTTP reachable"

# 3. Bolt reachable (from backend)
docker compose exec backend python -c "
from neo4j import GraphDatabase
d = GraphDatabase.driver('bolt://neo4j:7687', auth=('neo4j', '$NEO4J_PASSWORD'))
with d.session() as s:
    print('✓ Bolt reachable:', s.run('RETURN 1').single())
"

# 4. Indexes present
docker compose exec neo4j cypher-shell -u neo4j -p "$NEO4J_PASSWORD" \
  "SHOW INDEXES YIELD name, type, labelsOrTypes" && echo "✓ Indexes listed"

# 5. Backend /health reports neo4j_available
curl -s http://localhost:8000/api/v1/health | jq .graph.neo4j_available
```

### Expected output (dev)

```
✓ Container up
✓ HTTP reachable
✓ Bolt reachable
✓ Indexes listed
neo4j_available: true
```

---

## Disk Space Monitoring

### Check volume usage

```bash
# Docker volume disk usage
docker system df -v | grep neo4j_data

# Inside container
docker compose exec neo4j du -sh /data/databases/neo4j /data/transactions
```

### Alert thresholds

| Metric | Condition | Alert | Action |
|--------|-----------|-------|--------|
| `neo4j_data` usage | > 70% | S3 (low) | Plan expansion |
| `neo4j_data` usage | > 85% | S2 (medium) | Take backup, expand within 4h |
| `neo4j_data` usage | > 95% | S1 (high) | Immediate backup + expansion or stop writes |
| `neo4j_logs` usage | > 2 GB | Info | Rotate/archive logs |
| Neo4j restart | fails > 3 times in 10 min | S2 | Check disk space, lock files, corrupt store |

### Log rotation

```bash
# Compress and rotate logs older than 7 days
docker compose exec neo4j sh -c "
  cd /logs
  find . -name '*.log' -mtime +7 -exec gzip {} \;
"
```

---

## Troubleshooting

### Neo4j fails to start after restart

**Symptom:** Container exits immediately, logs show `StoreLockException` or `Unable to lock store`.

```
# 1. Check for stale lock files (from unclean shutdown)
docker compose exec neo4j ls -la /data/databases/neo4j/neostore.lock

# 2. Remove lock file (safe after confirming no other instance runs)
docker compose exec neo4j rm -f /data/databases/neo4j/neostore.lock

# 3. If persistent: restore from last known-good backup
./infra/scripts/backup-neo4j.sh --restore
```

### Corrupt data store

**Symptom:** `Database is in an inconsistent state` in logs.

```
# 1. Attempt consistency check
docker compose exec neo4j neo4j-admin database check neo4j

# 2. If check fails: restore from backup (see Restore section)
# 3. If no backup available (dev only): delete and re-seed
docker compose exec neo4j rm -rf /data/databases/neo4j
docker compose restart neo4j
docker compose exec backend python -m demo.seed_graph
```

### Volume full (no space left on device)

```
# 1. Free emergency space — remove transaction logs (lose recent txns)
docker compose exec neo4j neo4j-admin database check neo4j --force

# 2. Expand volume (see Volume Expansion section)

# 3. If emergency: restore to a larger volume
```

---

## Integration Points

| System | Reference | Notes |
|--------|-----------|-------|
| Backend startup | `runtime/knowledge_graph_runtime/service.py` | Creates `AsyncGraphDatabase.driver` with connection pool |
| Index creation | `runtime/knowledge_graph_runtime/repository/neo4j_repository.py` | `ensure_indexes()` on startup, creates `company_fulltext` + `person_fulltext` |
| Graph queries | `sdk/graph.py` | `GraphService` with SQL fallback |
| Health endpoint | `app/main.py` `/api/v1/health` | Reports `graph.neo4j_available` |
| Seed script | `demo/seed_graph.py` | Synchronous one-off seeding (dev only) |
| Backup service | `docker-compose.prod.yml` `backup` | Nightly cron at 04:00 UTC |
| DR Runbook | [DR_RUNBOOK.md](DR_RUNBOOK.md) | Scenario 3: Infrastructure failure, Section 5.3 Full Stack Restore |
| Degraded mode | [DEGRADED_MODE_MATRIX.md](DEGRADED_MODE_MATRIX.md) | Neo4j REQUIRED; graph queries 503 on down |

---

## Honesty Banner

### Dev Drill Results (2026-08-08)

| Metric | Value |
|--------|-------|
| Environment | Local dev Docker (`salesos-neo4j-1`, `neo4j:5-community`) |
| Pre-backup node count | 4 (2 Company: TestCorp, AcmeLtd; 2 Person: Alice, Bob) |
| Backup method | `neo4j-admin database dump` (offline — DB stopped) |
| Dump size | 48 files, 257.9 MB |
| Backup duration | 2.9 seconds |
| Wipe method | `rm -rf /data/databases/* /data/transactions/*` |
| Restore method | `neo4j-admin database load --overwrite-destination=true` |
| Restore duration | 1.4 seconds |
| Post-restore node count | 4 (matched — 2 Company, 2 Person exactly restored) |
| Indexes post-restore | `company_fulltext` ONLINE, `person_fulltext` ONLINE |
| Neo4j health | healthy (cypher-shell RETURN 1) |
| APOC available | NO (community image) — online backup requires APOC plugin |

### Honesty Banner

| Assertion | Status | Evidence |
|-----------|:------:|----------|
| Backup script exists | YES | `infra/scripts/backup-neo4j.sh` |
| Backup has been tested (restore drill) | **DEV** | Local Docker drill 2026-08-08; 48 files, 257.9 MB, RTO 1.4s restore; staging drill still pending |
| Volume expansion has been tested | **NO** | Not yet simulated |
| Backup integrity verified | **DEV** | Full wipe + restore + node count parity confirmed on local dev |
| Offsite backup configured | **NO** | Local volume only; S3 copy not automated |
| Neo4j carries production data | **NO** | ADR-108: offline in v1.0 |
| PITR supported | **NO** | Community edition limitation |

**Validation status:** dev drill executed; staging drill pending.
