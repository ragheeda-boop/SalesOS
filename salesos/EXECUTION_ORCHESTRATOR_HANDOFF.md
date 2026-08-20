# EXECUTION ORCHESTRATOR — HANDOFF BRIEF

**Date:** 2026-08-08  
**Prepared by:** Chief Audit Architect  
**For:** Execution Orchestrator Agent

---

## YOUR ROLE

You are an **executor**, not an analyst. Your job is to follow the Controlled Remediation Plan exactly. You do not re-audit. You do not redesign. You execute gates in sequence.

## YOUR CONSTRAINTS

1. **No production-affecting change may merge or deploy before the prerequisite gate is closed**
2. **Gate 0 is strictly read-only** — observe, capture, compare, report. Do NOT fix anything.
3. **Runtime Evidence → Decision → Documentation** — never the reverse
4. **DO NOT TOUCH** list is in effect for Gates 0-3 (auth, RLS, CSRF, JWT, migrations, CI 1-5, UI v5, tokens, canonical architecture, AGENTS.md, ADR-108)
5. **No product expansion** until Gates 0-3 are CLOSED

## YOUR STARTING POINT

```
Gate 0: Runtime Truth
  Status: NOT STARTED
  Blocker: Human access to Railway/Vercel dashboards required
  Tasks: B-01 through B-05
  Output: PRODUCTION_TRUTH.md
```

## YOUR FIRST SESSION

### Step 1: Obtain Runtime Access

You need one of:
- Railway dashboard access (project: SalesOS)
- Vercel dashboard access (project: SalesOS)
- SSH/exec access to Railway containers
- Or: a human who can run the verification commands and provide output

### Step 2: Execute Gate 0 Tasks

| Task | Command / Action | Record Output |
|------|-----------------|---------------|
| B-01 | Railway dashboard → PostgreSQL → Backups tab | Backup status, schedule, retention, last backup |
| B-02 | `SHOW wal_level; SHOW archive_mode; SHOW archive_command;` | Actual WAL configuration |
| B-03 | `alembic current` | Migration head hash + number |
| B-04 | Vercel dashboard → Deployments | Latest deployment commit + timestamp |
| B-05 | `curl /api/v1/version` | Deployed commit, schema_version, openapi_hash |

### Step 3: Write PRODUCTION_TRUTH.md

Template:

```markdown
# PRODUCTION TRUTH

**Captured:** [timestamp]
**Evidence Level:** E5/E6

## B-01: Railway Backup
- Status: [EXISTS / NOT EXISTS]
- Schedule: [daily / none]
- Retention: [days]
- Last backup: [timestamp]
- Evidence: [screenshot/API response]

## B-02: PostgreSQL WAL
- wal_level: [main / replica]
- archive_mode: [on / off]
- archive_command: [command or empty]
- Evidence: [SQL output]

## B-03: Alembic Head
- Head on disk: 0052
- Head in production: [hash from alembic current]
- Match: [YES / NO]
- Evidence: [command output]

## B-04: Vercel Deployment
- Latest deployment: [commit hash]
- Timestamp: [timestamp]
- Status: [ready / building / error]
- Evidence: [dashboard/API]

## B-05: Deployed Commit
- Commit: [hash]
- Version: [from /api/v1/version]
- Schema version: [present / absent]
- OpenAPI hash: [64 hex chars]
- Evidence: [curl output]

## Discrepancies
[List any gaps between documentation claims and runtime reality]
```

### Step 4: Declare Gate 0 CLOSED

Only when ALL 5 items have E5/E6 evidence and PRODUCTION_TRUTH.md is written.

## THEN: Proceed to Gate 1

Gate 1 tasks are in `CONTROLLED_REMEDIATION_PLAN_2026-08-08.md` Section "GATE 1 — PRODUCTION SAFETY". Follow them exactly.

## REFERENCE DOCUMENTS

| Document | Location | Purpose |
|----------|----------|---------|
| Controlled Remediation Plan | `salesos/reports/CONTROLLED_REMEDIATION_PLAN_2026-08-08.md` | Your execution plan |
| Enterprise Audit Report | `salesos/reports/ENTERPRISE_AUDIT_REPORT_2026-08-08.md` | Background evidence |
| Audit Verification Report | `salesos/reports/AUDIT_VERIFICATION_REPORT_2026-08-08.md` | Verification evidence |
| This handoff | `salesos/EXECUTION_ORCHESTRATOR_HANDOFF.md` | Your starting instructions |

## REMEMBER

- You do NOT re-audit
- You do NOT redesign architecture
- You do NOT expand product scope
- You DO execute gates in sequence
- You DO record evidence artifacts
- You DO follow the DO NOT TOUCH list
- You DO escalate blockers without fixing them in Gate 0

**Your first output must be PRODUCTION_TRUTH.md with E5/E6 evidence for B-01 through B-05.**
