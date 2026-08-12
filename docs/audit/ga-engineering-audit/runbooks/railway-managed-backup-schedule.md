# Railway Managed Backup Schedule + Native PITR — Human Runbook (HG-04)

**ID:** HG-04 / PROD-OPS01-RAILWAY-SCHEDULE  
**Audience:** Human ops owner with Railway **account/plan authorization** (not agents)  
**Gate card:** [HUMAN-GATE-CARD.md](../completion/HUMAN-GATE-CARD.md) § Gate HG-04  
**Related:** [OPS-01-CHECKLIST.md](../enterprise-audit-board/history/EAB-2026-08-06-003/OPS-01-CHECKLIST.md) · [CTO-REQUIRED-HUMAN-DECISIONS.md](../CTO-REQUIRED-HUMAN-DECISIONS.md) **RC-04** · [DR-ROWS-1-3-CLOSE-PACKET.md](../../../ops/DR-ROWS-1-3-CLOSE-PACKET.md) · [ops01-human-execution-pack.md](./ops01-human-execution-pack.md)

> **Agents cannot authorize Railway account scopes.**  
> GraphQL attempts from agent/opsai sessions returned **Not Authorized** (plan/permission gating). This runbook is for a human who can enable the feature on the Railway workspace/plan, then deposit evidence.

---

## Purpose

Close the **automation residual** left after OPS-01 Rows 1–3 machine drills:

| Capability | GraphQL / API | Prior agent result |
|------------|---------------|--------------------|
| Managed volume backup schedule | `volumeInstanceBackupScheduleUpdate` · `volumeInstanceBackupScheduleList` | **Not Authorized** |
| Native PITR restore | `volumeInstancePITRRestore` | **Not Authorized** |

Drill-proven fallback (already DONE\*): pg_dump→S3 offsite + pgBackRest restore against the **same** managed archive. Native UI/API remains the production operator path once unblocked.

---

## “Not Authorized” class (plan / permission gating)

Treat `Not Authorized` as a **human gating class**, not a product bug in SalesOS:

1. **Plan gating** — Railway plan may not include scheduled volume backups and/or native PITR restore mutations.
2. **Permission gating** — Token/user lacks workspace role (Owner/Admin) or feature flag for volume backup APIs.
3. **Agent scope** — Automation tokens used by agents must **not** be elevated solely to “unblock” agents; a named human ops owner enables the feature, then optionally issues a least-privilege token for read/list verification.

**Do not** interpret agent `Not Authorized` as “backup does not exist.” Rows 1–3 evidence already prove recoverability via authorized paths.

Evidence of prior denial:

- [ops01-row1-evidence.md](../enterprise-audit-board/history/EAB-2026-08-06-003/evidence/ops01-offsite/ops01-row1-evidence.md) — schedule Update/List → Not Authorized  
- [ops01-row3-pitr-restore.json](../enterprise-audit-board/history/EAB-2026-08-06-003/evidence/ops01-pitr/ops01-row3-pitr-restore.json) — `railway_native_pitr.result = "Not Authorized (Railway plan/permission gating)"`

---

## Preconditions (human)

- [ ] Railway workspace Owner (or Admin with backup/PITR feature access) for the SalesOS production project
- [ ] Confirmed plan includes **Volume Backups** / **PITR** (upgrade if required — business decision)
- [ ] Know volume instance ID for production Postgres data volume (Railway UI → service → Volumes)
- [ ] Change window noted if native PITR restore creates a **new** service (non-destructive preferred for first drill)
- [ ] Evidence deposit folder ready (see below) — screenshots + redacted API JSON only; **no secrets**

Target volumes / buckets (from EAB-003 drills — confirm still current in UI):

| Layer | Identifier (as of 2026-08-06 evidence) |
|-------|----------------------------------------|
| Logical offsite bucket | `salesos-backups` / physical `salesos-backups-iwrweogrr` |
| PITR / WAL archive bucket | `salesos-pitr` / physical `salesos-pitr-w-857q3fjjrr` |
| Postgres image (prod) | `ghcr.io/railwayapp-templates/postgres-ssl:18` (pgBackRest-managed) |

---

## Part A — Enable managed backup schedule (UI)

1. Open Railway dashboard → SalesOS **production** project → **Postgres** service.
2. Open the attached **Volume** → **Backups** tab (wording may be “Backups” / “Schedules”).
3. Enable a recurring schedule:
   - Preferred cadence: **DAILY** (or WEEKLY if plan-limited; document choice).
   - Set **retention** to meet ops policy (Row 1 target: **≥ 30 days** for logical/offsite class; volume schedule retention per Railway UI options — record exact value).
4. Save. Confirm schedule shows **enabled** with next run time.
5. Optionally trigger a **manual backup** once to prove the schedule path writes an object.
6. Capture screenshots:
   - Schedule enabled + cadence + retention
   - At least one successful backup listed (or “pending” with ticket if first run is future)

## Part A — Enable managed backup schedule (API / GraphQL)

Use Railway GraphQL (dashboard network tab, or `railway` CLI / authenticated `curl` as the **human**). Replace placeholders; never commit tokens.

### List current schedule

```graphql
query VolumeBackupScheduleList($volumeInstanceId: String!) {
  volumeInstanceBackupScheduleList(volumeInstanceId: $volumeInstanceId) {
    # fields as returned by current Railway schema — capture full JSON
  }
}
```

Or mutation/query name as exposed by schema introspection: **`volumeInstanceBackupScheduleList`**.

### Update / enable schedule

```graphql
mutation VolumeBackupScheduleUpdate($input: VolumeInstanceBackupScheduleUpdateInput!) {
  volumeInstanceBackupScheduleUpdate(input: $input) {
    # capture id, enabled, cadence (DAILY|WEEKLY|MONTHLY), retentionDays / policy fields
  }
}
```

Exact input shape follows Railway’s live schema (introspect before run). Minimum intent:

- `volumeInstanceId` = production volume
- schedule **enabled** = true
- cadence ∈ { `DAILY`, `WEEKLY`, `MONTHLY` }
- retention aligned to policy (≥ 30 days preferred for offsite class)

### Success vs Not Authorized

| Result | Action |
|--------|--------|
| Success + list shows enabled schedule | Deposit JSON under evidence path; continue to Part B |
| **Not Authorized** | Confirm plan upgrade / Owner login; do **not** ask agents to bypass. Record denial JSON with date |

---

## Part B — Native PITR restore path (`volumeInstancePITRRestore`)

**Warning:** Native restore may provision a **new** service. Prefer a drill name and disposable target. Do not overwrite production without an approved incident window.

1. UI path (if available): Volume / Backups → **Restore** / **Point-in-time restore** → choose timestamp → new service name → confirm.
2. API mutation:

```graphql
mutation NativePitrRestore($input: VolumeInstancePITRRestoreInput!) {
  volumeInstancePITRRestore(input: $input) {
    # capture job/service id, status
  }
}
```

Example intent (from prior agent attempt — adjust timestamp to a **commit-bearing** target; idle windows can FATAL as in Row 3 notes):

- `targetTimestamp`: ISO-8601 UTC (pick a time **at or after** a known commit)
- `newServiceName`: e.g. `salesos-pitr-restore-drill-YYYYMMDD`

3. Wait until restored service is healthy; verify row counts / alembic vs expectation (same style as Row 3 evidence table).
4. Tear down drill service after evidence capture (human approval).

Prior denial artifact for reference:

```json
"railway_native_pitr": {
  "graphql_mutation": "volumeInstancePITRRestore",
  "attempt": "targetTimestamp=2026-08-06T19:40:00.000Z, newServiceName=salesos-pitr-restore-drill-20260806",
  "result": "Not Authorized (Railway plan/permission gating)"
}
```

---

## Part C — WAL / archive health policy (`failed_count`)

After schedule enablement, confirm continuous archive health (prod Postgres):

```sql
SELECT archived_count, failed_count, last_archived_wal, last_archived_time
FROM pg_stat_archiver;
```

**Policy (done-when):**

- [ ] `failed_count = 0` (or documented incident + remount if non-zero)
- [ ] `archived_count` increasing over a ≥1h observation window
- [ ] `archive_mode = on` on production primary (compose-local often `off` — do not conflate; see COMPOSE-SOURCE-OF-TRUTH)

Deposit SQL result JSON/screenshot with timestamp.

---

## Evidence deposit path

Deposit **redacted** artifacts here (create dated subfolder if needed):

```
docs/audit/ga-engineering-audit/enterprise-audit-board/history/EAB-2026-08-06-003/evidence/ops01-offsite/
docs/audit/ga-engineering-audit/enterprise-audit-board/history/EAB-2026-08-06-003/evidence/ops01-pitr/
```

Suggested filenames:

| Artifact | Suggested name |
|----------|----------------|
| Schedule Update/List success JSON | `ops01-hg04-backup-schedule-YYYYMMDD.json` |
| Schedule UI screenshots | `ops01-hg04-backup-schedule-YYYYMMDD.png` (or `.md` with image links) |
| Native PITR mutation result | `ops01-hg04-volumeInstancePITRRestore-YYYYMMDD.json` |
| PITR drill verification | `ops01-hg04-pitr-native-verify-YYYYMMDD.json` |
| `pg_stat_archiver` snapshot | `ops01-hg04-wal-failed-count-YYYYMMDD.json` |

**Never commit:** Railway API tokens, AWS keys, `WAL_ARCHIVE_*` secrets, connection strings.

Link new evidence from [OPS-01-CHECKLIST.md](../enterprise-audit-board/history/EAB-2026-08-06-003/OPS-01-CHECKLIST.md) notes and, if Rows 1–3 human CLOSE was signed, refresh residual language on [DR-GA-GAPS-CHECKLIST.md](../../../ops/DR-GA-GAPS-CHECKLIST.md).

---

## Done-when criteria (HG-04 CLOSED)

All must be true with deposited evidence:

1. **Schedule enabled** — `volumeInstanceBackupScheduleList` (or UI equivalent) shows enabled cadence (DAILY/WEEKLY/MONTHLY).
2. **Retention** — documented retention meets policy (≥ 30 days preferred; exact Railway value recorded).
3. **`failed_count` policy** — production `pg_stat_archiver.failed_count = 0` (or signed exception) with dated snapshot.
4. **Native PITR path** — either:
   - successful `volumeInstancePITRRestore` drill with verification JSON, **or**
   - written Project Owner acceptance that native UI remains deferred while pgBackRest path remains the approved restore (RC-04 Option A/C — human ink on CTO register).
5. Human name + date on evidence index (agents do not forge).

Until then: status remains **BLOCKED-HUMAN / Not Authorized** on automation residuals.

---

## Explicit non-goals

- Agents **cannot** authorize Railway account scopes or plan upgrades.
- Completing HG-04 does **not** by itself grant Production GO (soak OPS01-04 and other gates remain).
- Do not delete or contradict Rows 1–3 DONE\* drill JSON when enabling automation.

---

## Ink (human — after done-when)

| Field | Value |
|-------|--------|
| Name | ________________________________ |
| Date (UTC) | ________________________________ |
| Schedule cadence + retention | ________________________________ |
| Native PITR drill ID / defer reason | ________________________________ |
| `failed_count` observed | ________________________________ |
| Signature | ________________________________ |

**Validation label:** not validated until human executes and deposits evidence.  
**Agent role:** documentation only.
