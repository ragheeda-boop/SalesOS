# Release / Ops Backlog Status — 2026-08-06

**Product:** SalesOS  
**Authority:** [ga-engineering-audit](./README.md) + [GA_STATUS.md](./GA_STATUS.md) + OPS-01 pack  
**Production GA:** **NO-GO** — unchanged  
**Commit:** none (this pack is documentation only)  
**Validation label:** **not validated** for cloud/staging/soak/offsite closes; evidence is inventory + cross-link only  

> **Principle:** AI assists. Humans decide. Evidence governs.  
> Do **not** fake-close BLOCKED-HUMAN / cloud items. Local compose ≠ staging. Local soak loops ≠ 48–72h cloud soak.

---

## Summary counts (items 4–10)

| Status | Count | Items |
|--------|------:|-------|
| **OPEN** | 2 | #5 staging pentest; #8 prod health (kafka residual + Neo4j re-check) |
| **PARTIAL** | 2 | #7 Backup DR; #9 FE Vercel publish |
| **BLOCKED-HUMAN** | 2 | #4 staging cloud deploy/tabletop; #10 credential rotation |
| **IN_PROGRESS** | 1 | #6 soak 48–72h (claim still false; final proof + TL review missing) |
| **DONE / closed** | **0** | — |

**Launch-adjacent:** items 4–7 and 10 are OPS-01 / Wave 11–12 blockers or related; none close Production GO.

**Engineering-owned (items 1–3):** tracked separately below as **IN_PROGRESS** by eng agents — not counted in the table above.

---

## Items 1–3 — Engineering in progress (cross-link only)

These are **not** primarily cloud/ops-human blockers. They remain owned by engineering agents. Do not treat as Production GO enablers alone.

| # | Item | Status | Evidence / notes | Agent can | Human must |
|---|------|--------|------------------|-----------|------------|
| **1** | Owner login (DEC-093) | **IN_PROGRESS** / mint path **DONE (light)** | [DEC-093](../../program/decisions/DEC-093-JWT-AUDIENCE-CONSUMPTION-CLOSED.md) — Owner mint `POST /api/v1/identity/owner/login` + FE `/admin/login` closed **light validated** 2026-08-06; browser E2E / field CI not claimed | Keep audience split green; residual refresh-family / adjacent admin routes | Provide interactive passwords for authenticated E2E if required; do not forge SIGN_HERE |
| **2** | Gmail / Calendar sync | **IN_PROGRESS** | [GA_STATUS.md](./GA_STATUS.md) blocker #2; [LIVE-QA-RECHECK-2026-07-30.md](./LIVE-QA-RECHECK-2026-07-30.md) — Sync buttons no network; OAuth connected on `ratlfintech`, not `muhide.com` | Wire FE sync triggers; fix CommHub paths; unit/contract tests | Google consent on intended account; live connect smoke |
| **3** | OAuth URL cleanup | **IN_PROGRESS** | [PROGRESS-COMMHUB-ACTIVITY.md](./PROGRESS-COMMHUB-ACTIVITY.md) (`urlencode` redirect_uri); residual redirect/host hygiene | Harden redirect_uri encoding / config-only redirects; tests | Confirm Google Cloud console redirect URIs match live FE/BE hosts |

**Next (1–3):** Continue eng tracks in parallel with ops backlog; do not block swarm on GitHub Environments alone ([DEC-107](../../program/decisions/DEC-107-SWARM-ALWAYS-ON-PARALLEL-READY.md) spirit).

---

## Item 4 — Staging cloud deploy + rollback tabletop

| Field | Value |
|-------|--------|
| **Status** | **BLOCKED-HUMAN** |
| **What exists** | Local compose tabletop **DONE** — [PROGRESS-WAVE12-TABLETOP.md](./PROGRESS-WAVE12-TABLETOP.md); local virtual staging stand-in — [PROGRESS-WAVE12-STAGING-VIRTUAL.md](./PROGRESS-WAVE12-STAGING-VIRTUAL.md); prep/unblock docs — [PROGRESS-WAVE12-STAGING.md](./PROGRESS-WAVE12-STAGING.md), [PROGRESS-WAVE12-STAGING-UNBLOCK.md](./PROGRESS-WAVE12-STAGING-UNBLOCK.md), [STAGING-READINESS.md](./enterprise-audit-board/history/EAB-2026-08-06-003/STAGING-READINESS.md) |
| **Cloud gap** | Probe (2026-07-22): GitHub Environments **`total_count: 0`**; no `STAGING_*` secrets; cloud deploy/rollback **not executed** — [evidence/wave12-staging/](./evidence/wave12-staging/) |
| **Agent can** | Keep runbooks/workflows aligned; re-probe Environments API (names only); document fill-in checklist |
| **Human must** | Create GH Environment `staging` + secrets (or Railway staging path per DEC-149); run **real** deploy + rollback tabletop with evidence under `evidence/wave12-staging/` |
| **Next action** | Ops: provision staging target + secrets → execute cloud tabletop → link evidence. Do **not** treat local tabletop as staging close. |

---

## Item 5 — Staging pentest (SSRF / KG residuals)

| Field | Value |
|-------|--------|
| **Status** | **OPEN** |
| **Code** | P0 SSRF/KG fixes **DONE** (code + unit/load local) — [PROGRESS-WAVE2-SEC.md](./PROGRESS-WAVE2-SEC.md), [PROGRESS-WAVE2-SSRF-REDESIGN.md](./PROGRESS-WAVE2-SSRF-REDESIGN.md), [PROGRESS-WAVE2-RESIDUALS.md](./PROGRESS-WAVE2-RESIDUALS.md); live pin redesign noted in Wave 16 |
| **Staging check** | **OPEN** — [runbooks/staging-ssrf-pentest.md](./runbooks/staging-ssrf-pentest.md) not executed on cloud staging |
| **Agent can** | Maintain checklist; re-run local SSRF unit/contract; refuse to invent “pentest PASS” |
| **Human must** | After staging host exists: run SSRF/KG residual checklist; attach dated evidence |
| **Next action** | Unblock item **#4** first; then execute pentest checklist on staging (not laptop-only). |

---

## Item 6 — Soak 48–72h + cloud staging soak

| Field | Value |
|-------|--------|
| **Status** | **IN_PROGRESS** (local historically) / cloud **BLOCKED-HUMAN** for honest close |
| **Claim** | `soak_complete_claim`: **false** — [PROGRESS-WAVE11-SOAK-CLAIM.md](./PROGRESS-WAVE11-SOAK-CLAIM.md), [SOAK-GATE-CHECKLIST.md](./enterprise-audit-board/history/EAB-2026-08-06-003/SOAK-GATE-CHECKLIST.md) |
| **Local 48h** | Plan/checkpoint: [PROGRESS-WAVE11-SOAK-48H.md](./PROGRESS-WAVE11-SOAK-48H.md); SIGN_HERE note historically **140/576** loops (~12.4h/48h) — [SIGN_HERE.md](./SIGN_HERE.md); **not** a completed 48h pass |
| **Cloud** | Staging cloud soak **not started** as GO evidence — needs item #4 host |
| **Agent can** | Keep gate scripts/docs honest; collect local loop summaries without flipping claim; draft TL review template |
| **Human must** | Run ≥48h (prefer 72h) on **staging cloud**; TL review before any claim flip; CTO/TL SIGN_HERE separately |
| **Next action** | Do **not** set `soak_complete_claim: true`. Finish/prove window on staging when available → TL ink → then reassess. |

---

## Item 7 — Backup DR (WAL / PITR / offsite / Neo4j)

| Field | Value |
|-------|--------|
| **Status** | **PARTIAL-ADVANCED** — rows 1–3 **DONE** (machine verified, production path); row 4 soak + row 5 signatures remain **BLOCKED-HUMAN / UNSIGNED** |
| **Canonical pack** | **[OPS-01-ADVANCEMENT.md](./enterprise-audit-board/history/EAB-2026-08-06-003/OPS-01-ADVANCEMENT.md)** · [OPS-01-CHECKLIST.md](./enterprise-audit-board/history/EAB-2026-08-06-003/OPS-01-CHECKLIST.md) · [DR-GA-GAPS-CHECKLIST.md](../../ops/DR-GA-GAPS-CHECKLIST.md) · **execution run sheet:** [ops01-human-execution-pack.md](./runbooks/ops01-human-execution-pack.md) |
| **Local DONE** | Wave 10 `pg_dump` ~**22 MB** (`salesos_20260722_075349.dump`) + disposable restore — [PROGRESS-WAVE10-BACKUP.md](./PROGRESS-WAVE10-BACKUP.md); EAB-003 re-verify ~521 KiB dump + restore — [evidence/ops01-local-backup-20260806.json](./enterprise-audit-board/history/EAB-2026-08-06-003/evidence/ops01-local-backup-20260806.json) |
| **Row 1 OFF-SITE DONE (2026-08-06)** | Production `pg_dump` (20,167,454 B, SHA256 `E5DBA231…9FBC8`) → bucket **`salesos-backups-iwrweogrr`**, upload/download re-verified, disposable restore `salesos-restore-drill-pg18` (96 tables, alembic `d1a8c35e7f09`, companies `141221`==live) — [ops01-row1-offsite-restore.json](./enterprise-audit-board/history/EAB-2026-08-06-003/evidence/ops01-offsite/ops01-row1-offsite-restore.json) + [.md](./enterprise-audit-board/history/EAB-2026-08-06-003/evidence/ops01-offsite/ops01-row1-evidence.md) |
| **Row 2 WAL DONE (2026-08-06)** | Primary `archive_mode=on` via official `postgres-ssl:18` pgBackRest wrapper → **`salesos-pitr-w-857q3fjjrr`**; `archived_count=6/failed=0`; base backup `20260806-192926F` — [ops01-row2-wal-archiver.json](./enterprise-audit-board/history/EAB-2026-08-06-003/evidence/ops01-pitr/ops01-row2-wal-archiver.json) + [.md](./enterprise-audit-board/history/EAB-2026-08-06-003/evidence/ops01-pitr/ops01-row2-evidence.md) |
| **Row 3 PITR DONE (2026-08-06)** | pgBackRest 2.59.0 restore against the **same managed archive** → `2026-08-06 19:29:50 UTC`, promote **timeline 2**, exact consistency vs live (companies 141221, audit_logs 683, tenants 57) — [ops01-row3-pitr-restore.json](./enterprise-audit-board/history/EAB-2026-08-06-003/evidence/ops01-pitr/ops01-row3-pitr-restore.json) + [.md](./enterprise-audit-board/history/EAB-2026-08-06-003/evidence/ops01-pitr/ops01-row3-evidence.md) |
| **Still OPEN** | Row 4 **staging soak 48–72h**; Row 5 **go-live signatures** (TL UNSIGNED); Neo4j **prod/staging policy** (local dump/load PARTIAL); managed-schedule automation (backup cadence + native `volumeInstancePITRRestore`) **BLOCKED-HUMAN** — Railway API Not Authorized |
| **Agent can** | Docs, disposable drills (done: offsite + WAL + PITR), Neo4j local dump notes |
| **Human must** | Enable Railway managed backup schedule + native PITR restore; run staging cloud soak ≥48–72h + TL review; CTO/TL SIGN_HERE (CTO already signed **NO-GO**); sign RPO/RTO (recompute RPO now WAL exists); Neo4j staging/prod backup policy |
| **Next action** | Execute remaining human P0 table in `ops01-human-execution-pack.md`; keep finding **Deferred** until rows 4–5 + automation evidence-closed. |

---

## Item 8 — Prod health (Kafka / Neo4j)

| Field | Value |
|-------|--------|
| **Status** | **OPEN** (re-check owed) |
| **Kafka** | Live probes still report **`kafka=in_memory`** — spot-checked against Wave 19–21 + EAB-002/003 evidence logs ([PROGRESS-WAVE20-AUTONOMOUS.md](./PROGRESS-WAVE20-AUTONOMOUS.md), [EAB-003 EVIDENCE-LOG](./enterprise-audit-board/history/EAB-2026-08-06-003/EVIDENCE-LOG.md), [GA_STATUS.md](./GA_STATUS.md) blocker #10). Not a GA Kafka claim. |
| **Neo4j prod** | Wave 21: **`graph=connected`** after `neo4j-prod` wiring — [PROGRESS-WAVE21-AUTONOMOUS.md](./PROGRESS-WAVE21-AUTONOMOUS.md), [PROGRESS-WAVE20-AUTONOMOUS.md](./PROGRESS-WAVE20-AUTONOMOUS.md). Earlier re-audit had `graph=unavailable` — **re-check `/health` before any stronger claim**. |
| **Agent can** | Read-only `GET /health` spot-check when approved; document degraded matrix; no silent “Kafka GA” |
| **Human must** | Product decision: Kafka required for GA vs signed degraded `in_memory`; confirm Neo4j prod still connected after any redeploy |
| **Next action** | Ops/eng: fresh `/health` on prod + staging; update this row with dated JSON snippet (no secrets). |

---

## Item 9 — FE Vercel prod publish (lag vs backend)

| Field | Value |
|-------|--------|
| **Status** | **PARTIAL** |
| **What exists** | Canonical FE → Vercel (DEC-149); root-dir `salesos/frontend` — [salesos/frontend/docs/VERCEL_DEPLOY.md](../../../salesos/frontend/docs/VERCEL_DEPLOY.md); Wave 21/23 note READY Git deploys; Wave 24 auto-deploy fix |
| **Gap** | Confirm **prod FE tip** matches backend API contract (no lagging client after Railway BE push) — [GA_STATUS.md](./GA_STATUS.md) blocker #11 |
| **Agent can** | Compare commit SHAs / deployment timestamps (GitHub + Vercel dashboard read-only); document root-dir footguns |
| **Human must** | Approve any prod redeploy; confirm env `NEXT_PUBLIC_*` / API URL parity |
| **Next action** | Spot-check latest Vercel production deployment vs Railway BE tip; record URLs + SHAs (no tokens). |

---

## Item 10 — Credential rotation

| Field | Value |
|-------|--------|
| **Status** | **BLOCKED-HUMAN** |
| **Trigger** | Staging Neo4j / DB URL may have been echoed by CLI (`railway variable list`) — [PROGRESS-WAVE17-GA-PUSH.md](./PROGRESS-WAVE17-GA-PUSH.md) (values **not** recorded in docs by design) |
| **Working-tree / history hygiene** | Wave 22 deleted + gitignored credential-shaped files; **git history may still contain prior versions** — see [QUARANTINE.md](./QUARANTINE.md) |
| **Agent can** | Flag paths; ensure `.gitignore`; **must not** rotate live secrets from agent session into git; **must not** paste secret values into docs |
| **Human must** | Rotate staging Neo4j auth + any DB URL exposed in CLI/history; invalidate old credentials in Railway/Google as needed |
| **Next action** | Ops: rotate → verify app reconnect → note rotation date here (no secret values). |

### Credential leak findings (paths only — no secret values)

| Path | Notes |
|------|--------|
| `cookies.txt` (repo root) | Deleted + gitignored (Wave 22); **history may retain** |
| `login.json` (repo root) | Deleted + gitignored (Wave 22); **history may retain** |
| `salesos/railway-status.json` | Deleted + gitignored (Wave 22); **history may retain** |
| CLI session output (not a repo file) | Wave 17: staging Neo4j / DB URL echo — **rotate in cloud console** |
| Possible untracked patterns (hygiene) | `tmp-dpl-*.json`, other Railway dumps — do not commit; rotate if ever shared |

**Honesty:** Listing paths ≠ confirmed active exploit. Treat as **rotation required until human confirms**.

---

## Cross-links (ops authority)

| Topic | Link |
|-------|------|
| OPS-01 advancement (DR) | [OPS-01-ADVANCEMENT.md](./enterprise-audit-board/history/EAB-2026-08-06-003/OPS-01-ADVANCEMENT.md) |
| OPS-01 checklist | [OPS-01-CHECKLIST.md](./enterprise-audit-board/history/EAB-2026-08-06-003/OPS-01-CHECKLIST.md) |
| Staging readiness honesty | [STAGING-READINESS.md](./enterprise-audit-board/history/EAB-2026-08-06-003/STAGING-READINESS.md) |
| Soak gate | [SOAK-GATE-CHECKLIST.md](./enterprise-audit-board/history/EAB-2026-08-06-003/SOAK-GATE-CHECKLIST.md) |
| Go-live signatures | [GO-LIVE-SIGNATURE-PACKET.md](./enterprise-audit-board/history/EAB-2026-08-06-003/GO-LIVE-SIGNATURE-PACKET.md) — **UNSIGNED** |
| GA scoreboard | [GA_STATUS.md](./GA_STATUS.md) |
| Prod migrate risk (`d1a8`→`e5f9`) | [PROD-MIGRATION-RISK.md](./PROD-MIGRATION-RISK.md) — **REQUIRES MAINTENANCE WINDOW**; migrations **not** run |

---

## Explicit non-claims

| Claim | Status |
|-------|--------|
| Production GO | **FALSE** |
| Staging cloud deploy/rollback complete | **FALSE** |
| Staging SSRF/KG pentest complete | **FALSE** |
| Soak 48–72h complete / claim true | **FALSE** |
| Offsite + WAL/PITR ready for GA | **FALSE** |
| Kafka production bus (not in_memory) | **FALSE** / unproven |
| Credentials rotated | **UNVERIFIED** (human) |

---

*Release backlog inventory — 2026-08-06 — production no-go — no fake closes — no commit*
