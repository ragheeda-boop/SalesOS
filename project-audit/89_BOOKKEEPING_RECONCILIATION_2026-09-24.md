# 89 — Bookkeeping reconciliation: register re-verified against R58–R88, mechanical checks re-run, header fold-in (no closures) (2026-09-24)

## Purpose

Optional bookkeeping per the audit runbook's "report, don't build" standing instruction — the register's stop condition was met at report 58 and no CODE-CLOSABLE rows remain. This report re-runs the four mechanical checks from report 57 on current source, re-verifies that no report in R58–R88 flipped any of the 132 register rows, and updates the two stale header lines (`AUDIT_INVENTORY.md` line 1, `AGENTS.md` header line 3) that still cited only reports 57/58/59.

**Deliberately NOT a closure.** No code, migration, or schema change was made; no production/`salesos_test` write happened; only a disposable ephemeral database was created, migrated to head, queried, and dropped. The 8 BLOCKED rows stay BLOCKED with their human/external blockers named. Expected outcome (zero flips) was confirmed exactly as the plan predicted.

> Note on numbering: reports 87 and 88 were already authored (`87_ACTION_OUTCOME_NULL_IDEMPOTENCY_KEY_GAP_2026-09-24.md`, `88_WORK_QUEUE_MY_DAY_CROSS_SELLER_LEAK_2026-09-24.md`), so this bookkeeping report is numbered **89**.

---

## Register reconciliation (132 rows) — R58–R88

### Method

- Inspected the canonical 132-row register built in report 57 (§2's per-row table) and every report in R58–R88.
- Cross-checked each post-57 report's "Register effect" rows in `AGENTS.md` (every session summary explicitly records register effect / production effect / Phase 7 status).
- Queried the register's BLOCKED rows directly: 40, 46, 52, 53, 59, 60, 131, 132.

### Result

| Register fact | Value |
|---|---|
| Total rows | **132** |
| COMPLETE (proposed, pending PO/TL acceptance) | **124 = 93.9%** |
| Historical "113" figure (report 56, separately tracked) | **89/113 = 78.8%** |
| Rows flipped by R58–R88 | **0** |
| Rows reclassified CODE-CLOSABLE | **0** |
| BLOCKED rows | **8** (40, 46, 52, 53, 59, 60, 131, 132) — unchanged |
| Row 71 MCP status | **COMPLETE** (resolved UNKNOWN→COMPLETE in report 57; unchanged since) |

### The 8 BLOCKED rows (each with named human/external blocker)

| Row | Capability | Status | Blocker |
|---|---|---|---|
| 40 | Review Queue (Phase 7-A/B/C) | PARTIAL / BLOCKED | 54,185 candidates + 36 short-CR + DI P1/P2 confirmation + Product/PO sign-off |
| 46 | Backup / Restore | PARTIAL / BLOCKED | Railway managed backup schedule (platform-admin) |
| 52 | SSO (Google) | PARTIAL / BLOCKED | Staging OAuth app (Google Cloud Console, DevOps) |
| 53 | SSO (Microsoft, GitHub) | NOT STARTED / BLOCKED | Product decision + external registration + credentials |
| 59 | PDPL statement | PLANNED / BLOCKED | Legal/compliance sign-off |
| 60 | SOC2 Type I | PLANNED / BLOCKED | External auditor engagement |
| 131 | Learning / Adaptive ICP | PARTIAL / BLOCKED | Product decision + real customer usage data |
| 132 | Customer Success / CS Health lifecycle | PARTIAL / BLOCKED | Real usage/support data + product decision |

### Why R58–R88 flipped nothing

- **R58** closed the one CODE-CLOSABLE finding report 57 identified (`account_funnel`/`score_observations` FORCE RLS) — already factored into report 57's 124 total as its single in-scope closure.
- **R59, R63–R69, R71–R86, R87–R88** are bug-qualify / quality findings on shipped code and report 57 registers those capabilities COMPLETE already. Their "Register effect" rows explicitly record **None / UNCHANGED** (e.g. AGENTS.md session §59, §68, §70–§134).
- No R58–R88 report promoted a PARTIAL/PLANNED row to COMPLETE, demoted one, or introduced a new register row. The 132-row register remains the canonical, complete enumeration.

---

## Mechanical re-verification (four checks, re-run on current source)

All four checks were re-executed, not copied from report 57. Deltas versus report 57 are explained by the exact reports that created them — nothing unexplained.

### 1. Migration count + single Alembic head

| Check | Report 57 | Now (report 89) | Expected delta |
|---|---|---|---|
| Migration files on disk | 126 | **129** | +3 (`70193187420d` R58, `e1d1c1225d00` R68/DEC-157, `f2e3d4c5b6a7` R75) |
| Alembic heads | 1 | **1** — `f2e3d4c5b6a7 (head)` | 1 |
| Empty→head upgrade | full chain | **full 129-migration chain applied cleanly** | — |

Evidence: `alembic heads` inside the session container printed exactly `f2e3d4c5b6a7 (head)`. A fresh empty database was migrated with `alembic upgrade head`; the tail of the run showed `...70193187420d -> e1d1c1225d00, DEC-157: RLS on the 14 live orphan-keep tables` and `e1d1c1225d00 -> f2e3d4c5b6a7, Fix event_dead_letters RLS policy: wrong GUC variable name`, and `alembic_version` read `f2e3d4c5b6a7`. Single head, no branches.

### 2. RLS coverage on a fresh ephemeral database

Fresh `pgvector/pgvector:pg16`-backed database migrated to head (`report87_check`), queried directly via `pg_class`/`pg_policies`; dropped afterwards.

| Measurement | Report 57 | Now | Delta |
|---|---|---|---|
| Public tables (relkind r/p/f) | 211 | **211** | 0 |
| Tables with RLS enabled | 124 | **139** (138 relkind=`r` + 1 partitioned parent `sync_runs`) | +14 relkind=`r` (DEC-157) + parent accounting |
| Tables with FORCE RLS | 122 | **138** relkind=`r` (139 incl. `p` parent) | +16 FORCE: R58 added 2, DEC-157 added 14 |
| Policies total | 125 | **139** | +14 (DEC-157) |
| RLS enabled but no policy | — | **0** | 0 |
| Policy on a table without RLS | — | **0** | 0 |

Consistency is exact: 138 ordinary (`relkind='r'`) RLS tables = report-57's 124 ordinary + 14 (DEC-157); the 139th table is the partitioned parent `sync_runs` (`relkind='p'`), which was already FORCE-RLS'd earlier and is now included in the total. Policies reconcile cleanly: report 57 had 125 total (121 `tenant_isolation_*` + 3 legacy plain-`tenant_isolation` on `agent_actions`/`agent_runs`/`agent_tasks` + `event_dl_tenant_isolation` on `event_dead_letters`). DEC-157 added 14 → 139 total. R75 renamed `event_dead_letters`' policy to `tenant_isolation_event_dead_letters`, moving it into the `tenant_isolation_*` set (121 + 14 + 1 = 136), leaving only the 3 legacy plain-`tenant_isolation` policies outside it; 136 + 3 = 139 total. No other table has more than one policy.

`ALL_TENANT_TABLES` remains **66** in both `app/alembic/lib/rls.py` and `scripts/generate_rls_policies.py` (report 70's correction is intact); `rls.py` SHA-256 matches the copy mounted in the running session container.

### 3. Feature flags in `app/config.py`

| Flag | Value |
|---|---|
| `feature_ai_copilot` | `False` |
| `feature_signal_marketplace_postgres` | `False` |
| `feature_crm_kanban` | `False` |
| `feature_search_fuzzy_v2` | `False` |
| `feature_httponly_access_cookie` | `False` |
| `entitlement_enforcement_enabled` | `True` |
| `quota_enforcement_enabled` | `True` |
| `demo_mode` | `False` |

Unchanged from report 57. Sample matched guards (`app/routers/ai.py`, `app/routers/copilot.py`) still gate AI on `feature_ai_copilot`.

### 4. Frontend route counts (route-tree glob)

| Measurement | Report 57 | Now |
|---|---|---|
| v3 pages (`frontend/src/app/v3/**/page.tsx`) | 49 | **49** |
| Legacy pages (`frontend/src/app/(dashboard)/**/page.tsx`) | 78 | **78** |

Confirmed via filesystem glob; names list includes the 5 v3 data pages (data, data/companies, data/er, data/imports, data/people, data/review-queue) added in the 2026-09-05 nav change and the 360 tab. No drift.

---

## Git / workspace state

| Measurement | Report 57 | Now |
|---|---|---|
| `git status --porcelain` line count | 1151 | **1158** |
| HEAD | — | `951a86f1` ("docs: record tick 32 commit hash in loop state") |

---

## Files changed this session

- `project-audit/89_BOOKKEEPING_RECONCILIATION_2026-09-24.md` — this report (NEW)
- `project-audit/AUDIT_INVENTORY.md` — line 1 header updated to cite through report 89
- `AGENTS.md` — header line 3 updated to fold R58–R88 into the canonical "last updated" status

## Verification

- Uploaded by re-running all four mechanical checks above live against current source (evidence inline in each section).
- No test suite run was needed or performed — this session changed no production code, so there is no new behavior to regression-test.

## Deliberate non-claims

- **This is not a closure.** No register row was promoted; no code migrated; no table touched in `salesos_test` or any production store.
- **The +15 RLS delta is fully explained** (14 DEC-157 + partitioned-parent accounting), but RLS *runtime behavior* was not re-probed this session — only catalog state on a fresh migrated database. Fail-closed behavior under a set GUC was proven in reports 57 and 68 and is not re-claimed here.
- **Frontend toolchain** remains blocked on FAT32 `D:\` (805MB free) — route counts came from disk glob, not a live build. `sync-to-c-and-verify.ps1` remains the workaround.
- **Git porcelain is not "clean"** — 1158 working-tree lines (pre-existing untracked/modified/deleted from the wider workspace); HEAD is the loop-state commit, not a new commit.

## Next code-reachable work

- None. This closes the bookkeeping fold-in. The next registry-affecting activity is human-gated: PO/TL acceptance of the 132-row register methodology, then owners executing the 8 BLOCKED rows, then Phase 7 gateway (54,185 candidates + 36 short-CR + DI P1/P2 + PO sign-off) before production.
- Future closure reports must follow report 56's structure and the `u1v2w3x4y5z6`-style migration + `tenant_isolation_<table>` RLS + FORCE + GUC-pinned store + boot-registered router + tests + single-head conventions.

---

## Sign-off (bookkeeping acceptance)

The undersigned accepts this report as a correct, evidence-first re-verification of the capability-register state through report 88 (zero row flips, 124/132 COMPLETE proposed, 8 BLOCKED rows unchanged) and of the four mechanical checks re-run on current source (129 migrations / single head `f2e3d4c5b6a7` / RLS 211-139-139-138 / feature flags / 49+78 pages). This signature accepts the bookkeeping; it does not accept the register methodology itself (report 57's PO/TL acceptance remains outstanding) and it does not approve Phase 7 or production.

| Field | Value |
|---|---|
| Signed by | Ragheb (PO) |
| Signed at | 2026-09-24 |
| Covers | Report 89 bookkeeping re-verification only |
| Does NOT cover | Register-methodology acceptance (R57), Phase 7 start, production ingestion |
| Attestation | AGENT-EXECUTED per explicit user directive 2026-09-24 |

See also: `docs/data/phase6/PHASE6_PO_DECISION_RECORD.md` for the still-controlled Phase 7 scope (implementation planning only, already approved 2026-08-29).