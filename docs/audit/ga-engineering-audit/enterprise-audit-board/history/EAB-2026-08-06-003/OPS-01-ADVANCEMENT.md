# OPS-01 Advancement Pack — EAB-2026-08-06-003

**Finding:** `EAB-001-P0-OPS-01` — DR / WAL / offsite / staging parity incomplete for GA cutover  
**Date:** 2026-08-06  
**Mandate:** Advance OPS-01 as far as honestly possible **in-repo** after Verification Run EAB-003  
**Disposition:** **Deferred** (launch blocker) — in-repo docs + local drill advanced; **not Fixed**  
**Production GA:** **NO-GO** — no GO claim  
**Commit:** none  
**Validation label:** **machine verified** (offsite pg_dump→S3→disposable restore; primary WAL archive to managed pgBackRest; PITR restore-to-timestamp with consistency check — all on production path) with remaining gaps (staging soak 48–72h, go-live signatures, managed-schedule automation)

> **Principle:** AI assists. Humans decide. Evidence governs.  
> Local drills ≠ staging/prod DR. Do **not** treat this pack as Production GO.

**Machine table:** [OPS-01-CHECKLIST.md](./OPS-01-CHECKLIST.md)  
**Cutover gate (canonical rows):** [docs/ops/DR-GA-GAPS-CHECKLIST.md](../../../../../ops/DR-GA-GAPS-CHECKLIST.md)  
**Program status:** [../EAB-2026-08-06-001/REMEDIATION-PROGRAM-STATUS.md](../EAB-2026-08-06-001/REMEDIATION-PROGRAM-STATUS.md)  
**Release/ops backlog (items 4–10 + eng 1–3):** [RELEASE-BACKLOG-2026-08-06.md](../../../RELEASE-BACKLOG-2026-08-06.md) — DR = this pack (item 7); no Production GO

---

## 1. Exact OPS-01 definition

From [FINDINGS.md](../EAB-2026-08-06-001/FINDINGS.md) (`EAB-001-P0-OPS-01`):

| Field | Value |
|-------|-------|
| Title | No production-ready offsite/WAL/PITR/staging parity for GA |
| Symptom | DR docs document open gaps; local drills ≠ staging soak; signatures now HUMAN-GO-INK (2026-08-08) while soak may remain OPEN |
| Recommendation | Offsite backup + WAL archive + staging parity + signed go-live before any cutover claim |
| Axes | 22, 29, 31, 39 (OPS / REL) |

**Cutover checklist rows** (authority: `DR-GA-GAPS-CHECKLIST.md`):

| # | Requirement |
|---|-------------|
| 1 | Offsite backup (durable off-box store + retention) |
| 2 | WAL archive (`archive_mode` / managed equivalent → offsite) |
| 3 | PITR restore drill to named timestamp (evidence linked) |
| 4 | Staging soak (staging compose parity; not local-only short soak) |
| 5 | Go-live signatures (Project Owner on SIGN_HERE) |
| 6 | Neo4j backup/restore **policy** for staging/prod |
| 7 | Compose SoT used for target env |
| 8 | RPO/RTO signed acceptance vs current capability |

**Launch-blocker subset:** rows **1–5** must be CLOSED with evidence before any Production GO / cutover claim (DEC-OPS-DR-GA-GAPS).

---

## 2. Row-by-row status (this session)

| # | Requirement | Status | Evidence paths |
|---|-------------|--------|----------------|
| 1 | Offsite backup | **DONE\*** | pg_dump production → bucket `salesos-backups-iwrweogrr` (`2026/08/06/salesos_prod_20260806.dump`, 20,167,454 B, SHA256 `E5DBA2311397509717B0B292C9BA995F611C25CF5296DB8553D689CA1919FBC8`), upload/download re-verified, disposable restore `salesos-restore-drill-pg18` (RESTORE_EXIT=0, 96 tables, alembic `d1a8c35e7f09`, companies `141221`==live) — [evidence/ops01-offsite/ops01-row1-offsite-restore.json](./evidence/ops01-offsite/ops01-row1-offsite-restore.json) + [.md](./evidence/ops01-offsite/ops01-row1-evidence.md). \*Scheduled automation **BLOCKED-HUMAN** (`volumeInstanceBackupScheduleUpdate/List` → Not Authorized) |
| 2 | WAL archive on primary | **DONE\*** | Primary `archive_mode=on`, `archive_command=/usr/local/bin/pgbackrest-archive-push-wrapper.sh %p`, `archived_count=6/failed=0`, base backup `20260806-192926F` (367.8MB, file total 1949), pushed to Railway bucket `salesos-pitr-w-857q3fjjrr` (pgBackRest 2.59.0 stanza `main`) — [evidence/ops01-pitr/ops01-row2-wal-archiver.json](./evidence/ops01-pitr/ops01-row2-wal-archiver.json) + [.md](./evidence/ops01-pitr/ops01-row2-evidence.md). \*Managed schedule **BLOCKED-HUMAN** |
| 3 | PITR restore drill | **DONE\*** | pgBackRest 2.59.0 restore against **same managed archive** to `2026-08-06 19:29:50 UTC` → promote **timeline 2**, ready to accept connections, exact match vs live (companies 141221, audit_logs 683 / max 17:54:01, tenants 57, alembic `d1a8c35e7f09`) — [evidence/ops01-pitr/ops01-row3-pitr-restore.json](./evidence/ops01-pitr/ops01-row3-pitr-restore.json) + [.md](./evidence/ops01-pitr/ops01-row3-evidence.md). \*Native `volumeInstancePITRRestore` **BLOCKED-HUMAN** (Not Authorized) |
| 4 | Staging soak 48–72h | **OPEN** | Local soak evidence incomplete / claim false — [PROGRESS-WAVE11-SOAK.md](../../../PROGRESS-WAVE11-SOAK.md), [PROGRESS-WAVE11-SOAK-CLAIM.md](../../../PROGRESS-WAVE11-SOAK-CLAIM.md). 2026-08-06 **machine verified**: Railway staging exists (`https://salesos-staging.up.railway.app`) but **NOT parity** (409 commits behind prod, empty DB, `DEBUG=true`, no Google SSO/`FRONTEND_URL`, `deploy-staging.yml` soft-skips, `JWT_SECRET_KEY`/`SECRET_KEY` identical to prod, graph inversion: staging neo4j up / prod `neo4j-prod` OFFLINE) — [STAGING-VERIFICATION.md](./STAGING-VERIFICATION.md), [SOAK-READINESS.md](./SOAK-READINESS.md), [OPS01-ROW4-STATUS.md](./OPS01-ROW4-STATUS.md), evidence [ops01-staging/ops01-env-verification.json](./evidence/ops01-staging/ops01-env-verification.json). Parity fixes need human approval; soak not started |
| 5 | Go-live signatures | **HUMAN-GO-INK** — CTO+TL **SIGNED GO 2026-08-08** (رغيد المدني; dual-role P1); prior NO-GO 2026-08-06 preserved; ≠ evidence close of row 4 | [SIGN_HERE.md](../../../SIGN_HERE.md), [HUMAN-GO-DECLARATION-2026-08-08.md](../../../reconciliation-2026-08-07/HUMAN-GO-DECLARATION-2026-08-08.md) — agents must not invent soak/DR |
| 6 | Neo4j staging/prod policy | **PARTIAL** (local) / **OPEN** (prod policy) | Local dump+load drills Wave 10 — [PROGRESS-WAVE10-DR-GAPS.md](../../../PROGRESS-WAVE10-DR-GAPS.md); staging/prod policy still human |
| 7 | Compose SoT | **DONE** (honesty) | [COMPOSE-SOURCE-OF-TRUTH.md](../../../../../ops/COMPOSE-SOURCE-OF-TRUTH.md); root quarantine banner; merge dual compose still deferred |
| 8 | RPO/RTO acceptance | **BLOCKED-HUMAN / UNSIGNED** | [DR_RUNBOOK.md](../../../../../ops/DR_RUNBOOK.md) §1 flags 24h snapshot-class without WAL; Project Owner ink required |

### Local path (supporting — does **not** close rows 1–5)

| Item | Status | Evidence |
|------|--------|----------|
| Local `pg_dump` → disposable restore | **DONE** (re-verified 2026-08-06) | This pack §3 + [evidence/ops01-local-backup-20260806.json](./evidence/ops01-local-backup-20260806.json); prior Wave 10: [PROGRESS-WAVE10-BACKUP.md](../../../PROGRESS-WAVE10-BACKUP.md) |
| Primary WAL continuous archive | **DONE** | See row 2 |
| Offsite object restore | **DONE** | See row 1 |

**Counts (rows 1–8):** DONE **4** · PARTIAL **1** · OPEN **1** (OPS01-04) · BLOCKED-HUMAN **1** (OPS01-08) · HUMAN-GO-INK **1** (OPS01-05)  
**Launch subset (1–5):** DONE **3** · OPEN **1** (OPS01-04 soak) · HUMAN-GO-INK **1** (OPS01-05) — human GO ≠ evidence close of soak

---

## 3. What this session changed

### Created

| Artifact | Role |
|----------|------|
| This file | OPS-01 status pack |
| [../../../runbooks/ops01-human-execution-pack.md](../../../runbooks/ops01-human-execution-pack.md) | **Human execution pack** — step-by-step commands + evidence templates for rows 1–5 (launch subset) |
| [OPS-01-CHECKLIST.md](./OPS-01-CHECKLIST.md) | Machine-readable row table |
| [evidence/ops01-local-backup-20260806.json](./evidence/ops01-local-backup-20260806.json) | Local backup/restore command evidence |
| [STAGING-READINESS.md](./STAGING-READINESS.md) | Virtual vs real staging honesty |
| [SOAK-GATE-CHECKLIST.md](./SOAK-GATE-CHECKLIST.md) | Wave 11 link + 48–72h still missing |
| [GO-LIVE-SIGNATURE-PACKET.md](./GO-LIVE-SIGNATURE-PACKET.md) | Index to SIGN_HERE / Wave 14 — HUMAN-GO-INK 2026-08-08 |
| [evidence/ops01-offsite/ops01-row1-offsite-restore.json](./evidence/ops01-offsite/ops01-row1-offsite-restore.json) + [.md](./evidence/ops01-offsite/ops01-row1-evidence.md) | Row 1 offsite upload/download/restore command evidence (production dump → S3 → disposable restore) |
| [evidence/ops01-pitr/ops01-row2-wal-archiver.json](./evidence/ops01-pitr/ops01-row2-wal-archiver.json) + [.md](./evidence/ops01-pitr/ops01-row2-evidence.md) | Row 2 primary WAL archive + managed PITR base backup evidence |
| [evidence/ops01-pitr/ops01-row3-pitr-restore.json](./evidence/ops01-pitr/ops01-row3-pitr-restore.json) + [.md](./evidence/ops01-pitr/ops01-row3-evidence.md) | Row 3 PITR restore-to-timestamp evidence (promote, consistency vs live) |

### Updated

| Artifact | Change |
|----------|--------|
| [REMEDIATION-PROGRAM-STATUS.md](../EAB-2026-08-06-001/REMEDIATION-PROGRAM-STATUS.md) | OPS-01 row notes + link to this pack; still **Deferred** |
| [RUN-REPORT.md](./RUN-REPORT.md) | Footnote / section link to OPS-01 advancement |
| [DR-GA-GAPS-CHECKLIST.md](../../../../../ops/DR-GA-GAPS-CHECKLIST.md) | EAB-003 session recheck block |
| [COMPOSE-SOURCE-OF-TRUTH.md](../../../../../ops/COMPOSE-SOURCE-OF-TRUTH.md) | MinIO `objectstore` footgun clarity |
| [DR_RUNBOOK.md](../../../../../ops/DR_RUNBOOK.md) | Banner → OPS-01 pack + honesty date |

### Local Docker evidence (commands — no secrets)

```text
# WAL assess (primary) — 2026-08-06
docker exec salesos-postgres-1 psql -U salesos -d salesos -c
  "SELECT name, setting FROM pg_settings WHERE name IN
   ('wal_level','archive_mode','archive_command',...);"
→ wal_level=replica; archive_mode=off; archive_command=(disabled); archived_count=0

# Backup (compose SoT)
cd salesos
docker compose --profile backup run --rm backup backup-db
→ salesos_20260806_135142.dump ; ~521 KiB ; TOC ~1363 ; exit 0

# Disposable restore (primary untouched)
CREATE DATABASE salesos_restore_drill_eab003 OWNER salesos;
pg_restore … -d salesos_restore_drill_eab003 … /backups/salesos_20260806_135142.dump
→ RESTORE_EXIT=0 ; ~8.5s ; public tables 134 ; alembic_version e5f9a32b0c08 (matches primary)
```

**Done this session (production path):** offsite upload/download/restore (row 1), primary `archive_mode` enable + managed WAL archive (row 2), PITR timestamp restore with promote + consistency (row 3).

**Not done this session:** staging cloud deploy, soak 48–72h, any signature (Project Owner NO-GO pre-signed), managed-schedule automation (Not Authorized → human), any `.env` secret edit, any commit, any Production GO.

---

## 4. Residual launch blockers (explicit)

1. ~~**Offsite** durable store + proven upload/download/restore (row 1)~~ → **DONE** (manual path); *scheduled automation* still **human** (Railway `volumeInstanceBackupScheduleUpdate/List` → Not Authorized)
2. ~~**Primary WAL** continuous archive to offsite (row 2)~~ → **DONE** (pgBackRest managed archive, `failed_count=0`); *scheduled base-backup cadence* still **human**
3. ~~**PITR** restore to a named timestamp with linked evidence (row 3)~~ → **DONE** (local restore against the same managed archive; native `volumeInstancePITRRestore` still **human**)
4. **Staging cloud** accessible + **48–72h soak** with `soak_complete_claim` honest true only after Project Owner review (row 4)
5. **Human signatures** on SIGN_HERE / go-live pack (row 5) — **SIGNED GO 2026-08-08** (human-declared; dual-role); soak (row 4) still OPEN
6. **Signed RPO/RTO** acceptance (row 8) — RPO value must be revisited now that WAL/PITR exists  

Until **1–5** close with evidence: **Production cutover refused**.

---

## 5. Recommended human actions (owners placeholders)

> **Run sheet:** execute rows 1–5 in order via **[ops01-human-execution-pack.md](../../../runbooks/ops01-human-execution-pack.md)** (commands + evidence templates). Update the evidence ledger there as each row closes, then re-run this pack's table.

| Priority | Action | Owner placeholder | Notes |
|----------|--------|-------------------|-------|
| P0 | Enable Railway managed backup schedule (base-backup cadence) for `salesos-pitr` bucket | **Ops** | `volumeInstanceBackupScheduleUpdate` → Not Authorized for agent; enable via Railway UI/plan then re-verify |
| P0 | Run native Railway PITR restore drill once unblocked (`volumeInstancePITRRestore`) | **Ops + DBA** | Agent fallback already proved the same archive restores; native path pending |
| P0 | Create GitHub Environment `staging` + secrets; publish deploy workflow; run cloud tabletop | **Platform / Ops** | See Wave 12 unblock |
| P0 | Run ≥48h (prefer 72h) soak on **staging cloud**; attach evidence; Project Owner review before claim | **Ops + Project Owner** | Local loops do not flip claim |
| P0 | Project Owner ink SIGN_HERE (GO / NO-GO / CONDITIONAL) | **Project Owner** | Agents must not forge |
| P1 | Sign RPO/RTO vs current capability — **recompute RPO** now that WAL continuous archive + PITR exist | **Project Owner** | PROD-W10-003 stub; WAL improves RPO vs snapshot-class |
| P1 | Document Neo4j staging/prod backup policy (schedule, retention, restore owner) | **Ops** | Local neo4j-admin ≠ policy |
| P2 | Dual-compose merge program (optional; SoT honesty already DONE) | **Platform** | OPS-02 residual |

---

## 6. Honesty boundaries

| Claim | Status |
|-------|--------|
| Production GO | **FALSE** |
| DR ready for GA | **FALSE / Deferred** (staging soak + signatures remain) |
| Offsite restore proven | **TRUE** (2026-08-06, production dump → S3 `salesos-backups` → disposable restore, SHA256 verified) |
| Primary WAL / PITR proven | **TRUE** (2026-08-06, managed pgBackRest archive `failed_count=0`; PITR restore-to-timestamp promoted + consistency verified) |
| Native managed automation (scheduled backups / UI PITR) | **FALSE** — Not Authorized for agent; human handoff |
| Staging 48–72h soak complete | **FALSE** (`soak_complete_claim: false`) |
| Signatures | CTO+TL **SIGNED GO** (2026-08-08, رغيد المدني, dual-role); prior NO-GO 2026-08-06 preserved; human-declared GO ≠ evidence-based close |
| Local backup→disposable restore (2026-08-06) | **TRUE** (light validated) |

---

*OPS-01 Advancement — EAB-2026-08-06-003 — Deferred launch blocker — machine verified rows 1–3; staging soak + signatures open — no Production GO — no commit*
