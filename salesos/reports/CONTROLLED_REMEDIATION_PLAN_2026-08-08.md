# SALESOS — CONTROLLED REMEDIATION PLAN

**Date:** 2026-08-08  
**Authority:** Enterprise Audit Report + Audit Verification Report  
**Mode:** GATE-CONTROLLED EXECUTION — no workstream may open outside defined gates  
**SSOT:** This document + `reports/ENTERPRISE_AUDIT_REPORT_2026-08-08.md` + `reports/AUDIT_VERIFICATION_REPORT_2026-08-08.md`

---

## GOVERNANCE RULE

```
Runtime Evidence → Decision → Documentation
```

NOT:

```
Documentation → Assumption → Implementation
```

No document may claim "DONE" without corresponding evidence artifact.  
No gate may be skipped.  
No product expansion work may begin until Gates 0-3 are CLOSED.

### Parallelism Rule

> **No production-affecting change may merge or deploy before the prerequisite gate is closed.**

Preparation work (PRs, test branches, documentation drafts) may proceed in parallel IF:
- The branch is not merged to master/main
- No deployment is triggered
- The work is clearly labeled `GATE-N-PREPARATION`

This allows parallelism without breaking governance.

---

## CURRENT STATE VERDICT

```
SALESOS IS NOT BLOCKED BY ARCHITECTURE.
SALESOS IS BLOCKED BY OPERATIONAL ASSURANCE AND GOVERNANCE INTEGRITY.
```

| Layer | Status | Verdict |
|-------|--------|---------|
| Core Application | Auth/Tenancy/Company/Contact/Employee/Pipeline/Analytics/Workflow all E5 | GO WITH CONDITIONS |
| Production Operations | No backup, no WAL, no Alertmanager, no monitoring verification | NO-GO |
| Regression Protection | 29/30 E2E specs dead, no frontend coverage gate | NO-GO |
| Documentation Governance | 22 contradictions, stale claims, score shopping | NO-GO |
| Product Expansion | AI/GTM/V3/Marketplace all stubs | BLOCKED |

---

## GATE 0 — RUNTIME TRUTH

**Objective:** Establish what actually exists in production. No code changes. No documentation changes. Pure verification.

**Duration:** 1 session (human required for Railway/Vercel access)  
**Owner:** Platform + Backend  
**Blocker for:** Everything

### Gate 0 Strict Rules

> **Gate 0 Agent is PROHIBITED from fixing anything, even if CRITICAL issues are discovered.**

The purpose is:

```
Observe → Capture → Compare → Report
```

NOT:

```
Observe → Fix → Re-test
```

If a CRITICAL finding emerges (e.g., backup missing, WAL off), it is recorded in PRODUCTION_TRUTH.md and escalated to Gate 1. The Gate 0 agent does NOT create fixes, patches, or PRs. This preserves the evidence baseline.

### Tasks

| # | Task | How | Evidence Required | Pass Criteria |
|---|------|-----|-------------------|---------------|
| B-01 | Verify Railway backup status | Railway dashboard → PostgreSQL service → Backups tab | Screenshot or API response showing backup schedule | Backup exists with schedule, retention, last backup timestamp |
| B-02 | Verify PostgreSQL WAL config | `docker compose exec postgres psql -U salesos -c "SHOW wal_level; SHOW archive_mode; SHOW archive_command;"` or Railway console | SQL output | If `archive_mode=off`: WAL is NOT configured (update docs accordingly) |
| B-03 | Verify Alembic head | `docker compose exec backend alembic current` or Railway console | Migration head hash | Record actual head; compare to disk (0052) and docs (0051) |
| B-04 | Verify Vercel deployment | Vercel dashboard → SalesOS project → Deployments | Deployment list with commit hashes | Latest deployment matches expected commit |
| B-05 | Verify deployed commit | `curl https://<backend-url>/api/v1/version` | JSON response with commit, schema_version, openapi_hash | Commit matches latest master, schema present |

### Gate Closure

Output: `PRODUCTION_TRUTH.md` containing:
- Actual backup status (yes/no, schedule, retention)
- Actual WAL level (main/replica, archive on/off)
- Actual Alembic head (hash + number)
- Actual Vercel deployment (commit + timestamp)
- Actual deployed commit (hash + version)
- Any discrepancies with documentation

**Gate 0 is CLOSED when PRODUCTION_TRUTH.md is written and all 5 items have E5/E6 evidence.**

---

## GATE 1 — PRODUCTION SAFETY

**Objective:** Ensure production data is protected and failures are visible.

**Duration:** 2-4 hours coding + verification  
**Owner:** Platform  
**Blocker for:** Gate 2  
**Depends on:** Gate 0 CLOSED

### 1A — Backup Fix

**Definition of Done: backup → verify → restore → validate**

> A backup that has never been restored is NOT a backup. Build success alone is insufficient.

| # | Task | Files | Acceptance | Verification |
|---|------|-------|------------|--------------|
| 1A-1 | Fix backup Dockerfile COPY paths | `infra/docker/backup/Dockerfile` | Image builds successfully | `docker build -f infra/docker/backup/Dockerfile .` succeeds |
| 1A-2 | Define canonical backup mechanism | `docker-compose.prod.yml` backup service | One backup service with correct scripts | `docker compose config` validates |
| 1A-3 | Generate backup | Run backup against test DB | Backup artifact created | File exists, size > 0 |
| 1A-4 | Validate backup artifact | Check file integrity | Schema count matches, data sample correct | Automated check exits 0 |
| 1A-5 | Restore into isolated DB | Restore backup into separate PostgreSQL instance | Schema + data restored | `pg_restore` exits 0, tables present |
| 1A-6 | Validate restored data | Query restored DB | Row counts match, referential integrity holds | Automated validation exits 0 |
| 1A-7 | Record evidence | `PRODUCTION_TRUTH.md` update | Backup + restore chain documented with timestamps | No ambiguity |
| 1A-8 | Document backup RPO/RTO | `PRODUCTION_TRUTH.md` update | RPO and RTO explicitly stated from measured restore time | RPO/RTO based on actual restore, not design |

### 1B — WAL/PITR Decision

**Critical rule:** Option B (accept daily pg_dump) may NOT be labeled "PITR". The documentation must be explicit:

```
Backup:
  [Daily logical backup / WAL archiving]

RPO:
  [~24 hours / Point-in-time]

PITR:
  [AVAILABLE / NOT AVAILABLE]

Restore:
  [Verified / Not Verified]

Business Acceptance:
  [Accepted / Not Accepted]
```

| # | Task | Decision Required | Files | Acceptance |
|---|------|-------------------|-------|------------|
| 1B-1 | Choose WAL posture | **Option A:** Configure WAL archiving (requires S3 + archive_command) **Option B:** Accept daily pg_dump RPO (~24h) — **MUST NOT be labeled PITR** | Either compose files (A) or ADR (B) | Explicit decision documented with evidence |
| 1B-2 | If Option A: Add WAL config to compose | `docker-compose.prod.yml` postgres command args | `wal_level=replica`, `archive_mode=on`, `archive_command` | `SHOW` queries confirm |
| 1B-3 | If Option B: Create ADR | `docs/adr/0110-backup-and-recovery-posture.md` | Rationale, accepted RPO (~24h), migration trigger, explicit "PITR: NOT AVAILABLE" | ADR reviewed and merged |
| 1B-4 | Fix documentation claims | `GA_STATUS.md`, `SIGN_HERE.md` | Remove "DONE" claims for WAL/PITR until E5 evidence exists. Replace with actual state from Gate 0 | No unverified "DONE" claims remain |

### 1C — Monitoring Completion

**Definition of Done:** Configured ≠ Operating. The test must prove the full signal path:

```
Synthetic critical alert
       ↓
Prometheus (fires)
       ↓
Alertmanager (routes)
       ↓
Slack / Email / PagerDuty (delivers)
       ↓
Human receives (confirms)
       ↓
Evidence artifact (timestamp)
```

| # | Task | Files | Acceptance | Verification |
|---|------|-------|------------|--------------|
| 1C-1 | Add Alertmanager to prod compose | `docker-compose.prod.yml` | Alertmanager service present with routing config | `docker compose config` includes alertmanager |
| 1C-2 | Verify alert routing | `infra/docker/monitoring/alertmanager/alertmanager.yml` | Slack/email/PagerDuty routes defined | Config file present and valid |
| 1C-3 | Create synthetic critical alert | Add temporary Prometheus rule (e.g., `vector(1) > 0` always fires) | Alert fires → Alertmanager routes → notification received | Human confirms receipt with timestamp |
| 1C-4 | Remove synthetic alert | Remove temporary rule | Alert stops firing | No residual alerts |
| 1C-5 | Document monitoring coverage | `PRODUCTION_TRUTH.md` update | List of what is monitored, what is not, what was tested | No gaps between config and reality |

### Gate Closure

Output: Updated `PRODUCTION_TRUTH.md` with:
- Backup: WORKING / NOT WORKING + evidence (build + run + backup + verify + restore + validate)
- WAL: CONFIGURED / ACCEPTED + evidence (explicitly labeled, NOT "PITR" if Option B)
- Monitoring: COMPLETE / PARTIAL + evidence (including test alert with timestamp)
- Test alert: RECEIVED / NOT RECEIVED + evidence

**Gate 1 is CLOSED when all of:**
1. Backup image builds successfully
2. Backup generated, verified, and **restored into isolated DB** successfully
3. WAL posture explicitly decided and documented (Option A: configured; Option B: accepted with ADR — NOT labeled PITR)
4. Alertmanager present in prod compose
5. Synthetic test alert fired → routed → received by human (with timestamp evidence)
6. PRODUCTION_TRUTH.md updated with all evidence artifacts

---

## GATE 2 — REGRESSION PROTECTION

**Objective:** Ensure code changes cannot silently break existing functionality.

**Duration:** 2-3 hours coding + CI verification  
**Owner:** QA + Frontend + Backend  
**Blocker for:** Gate 3  
**Depends on:** Gate 1 CLOSED

### 2A — E2E Critical Path

| # | Task | Files | Acceptance | Verification |
|---|------|-------|------------|--------------|
| 2A-1 | Enable 5 critical E2E specs in CI | `.github/workflows/e2e-stage7.yml` or `.github/workflows/ci.yml` | 5 specs run on every PR to master/main | CI log shows 5 specs passing |
| 2A-2 | Specs to enable | `e2e/01-login.spec.ts`, `02-dashboard.spec.ts`, `04-company-detail.spec.ts`, `05-create-opportunity.spec.ts`, `11-contacts-crud.spec.ts` | Each spec passes against real backend | Playwright report shows PASS |
| 2A-3 | Verify smoke-auth-ui scope | `e2e/smoke-auth-ui.spec.ts` | Document what it actually tests (navigation smoke, not interaction) | Scope documented in test file header comment |

### 2B — Coverage Gates

| # | Task | Files | Acceptance | Verification |
|---|------|-------|------------|--------------|
| 2B-1 | Add frontend coverage threshold | `salesos/frontend/jest.config.js` | `coverageThreshold: { global: { branches: 60, functions: 60, lines: 60, statements: 60 } }` | `npm test` fails if coverage drops below 60% |
| 2B-2 | Align backend coverage gate | `.github/workflows/ci.yml` line 201 | Change `--cov-fail-under=55` to `--cov-fail-under=65` (match pyproject.toml) | CI uses 65% |
| 2B-3 | Verify per-domain minimums | `scripts/check-coverage.ps1` | Script exists and checks per-domain thresholds | Script runs successfully |

### 2C — False Confidence Cleanup

| # | Task | Decision Required | Acceptance |
|---|------|-------------------|------------|
| 2C-1 | Label simulated tests honestly | `tests/unit/test_story_14_01_load_slo.py`, `test_story_14_02_chaos_resilience.py` | Add file-level comment: "SIMULATION ONLY — not production validation" | Comment present |
| 2C-2 | Label mocked E2E honestly | `src/__tests__/end-to-end.test.tsx` | Add file-level comment: "MOCKED — does not test real API" | Comment present |
| 2C-3 | Label demo tests honestly | `tests/unit/test_demo.py` | Add file-level comment: "DEMO INFRASTRUCTURE — no production value" | Comment present |

### Gate Closure

Output: CI pipeline passing with:
- 5 E2E specs green
- Frontend coverage ≥ 60%
- Backend coverage ≥ 65%
- No false confidence labels missing

**Gate 2 is CLOSED when CI shows all of the above passing.**

---

## GATE 3 — GOVERNANCE FREEZE

**Objective:** Establish one truth per domain. Eliminate contradictions.

**Duration:** 2-4 hours (documentation only, no code)  
**Owner:** Architecture + Documentation  
**Blocker for:** Gate 4  
**Depends on:** Gate 2 CLOSED

### 3A — Contradiction Resolution

| # | Task | Source | Acceptance |
|---|------|--------|------------|
| 3A-1 | Apply HISTORICAL banner to stale WAL/PITR claims | `GA_STATUS.md` line ~55, `SIGN_HERE.md` line ~31 | Both contain: `> HISTORICAL: WAL/PITR claim superseded by PRODUCTION_TRUTH.md (2026-08-08). Actual state: [from Gate 0].` |
| 3A-2 | Apply HISTORICAL banner to stale security scores | All documents with scores other than latest | Each contains supersession note with date and source |
| 3A-3 | Apply HISTORICAL banner to stale GO/NO-GO claims | `docs/vnext/reports/GO_NO_GO_DECISION.md`, prior `GA_CHECKLIST.md` | `> SUPERSEDED by Enterprise Audit Report 2026-08-08` |
| 3A-4 | Fix PROJECT_BIBLE maturity score | `docs/PROJECT_BIBLE.md` line 73 | Change 7.5/10 to match audit evidence or add: `> STALE: Audit baseline 53/100 supersedes this score` |
| 3A-5 | Resolve Alembic head claim | `GA_STATUS.md` | Update to match PRODUCTION_TRUTH.md |

### 3B — Source of Truth Consolidation

| # | Task | Domain | Canonical Source | Deprecate |
|---|------|--------|-----------------|-----------|
| 3B-1 | Product | PRODUCT_BIBLE.md (narrative) + PROJECT_BIBLE.md (engineering) | Mark one as primary, other as derived | — |
| 3B-2 | Architecture | `salesos/CANONICAL_ARCHITECTURE.md` | Already canonical | — |
| 3B-3 | Roadmap | `docs/ROADMAP_5_YEARS.md` + `salesos/platform/ROADMAP.md` | Consolidate or mark one | — |
| 3B-4 | GO/NO-GO | `reports/ENTERPRISE_AUDIT_REPORT_2026-08-08.md` | This audit supersedes all prior | Archive prior GO/NO-GO docs |

### 3C — Orphan Code Cleanup

| # | Task | Files | Decision | Acceptance |
|---|------|-------|----------|------------|
| 3C-1 | Archive 7 orphan frontend packages | `frontend/packages/charts-v3/`, `layouts/`, `theme/`, `providers/`, `widgets/`, `workspace-generator/`, `platform/` | Move to `archive/frontend-packages/` | No imports reference them |
| 3C-2 | Clean repository pollution | `.tmp-*` files, `.mypy_cache_*` dirs, `benchmark.db`, `celerybeat-schedule` | Add to `.gitignore` + remove tracked copies | `git status` clean |
| 3C-3 | Decide Decision Engine canonical location | 4 locations: `domains/decision_center/`, `runtime/decision_runtime/`, `domains/decision/`, `frontend/platform/decision/` | Pick one as canonical, mark others deprecated | Decision documented in ADR |
| 3C-4 | Document Kafka in-memory acceptance | New ADR | Explicit acceptance of current-scale ephemeral event bus | ADR merged |

### Gate Closure

Output: `GOVERNANCE_STATUS.md` containing:
- All 22 contradictions resolved (HISTORICAL banner or correction applied)
- Source of Truth map (one per domain)
- Orphan code archived or removed
- Decision Engine canonical location chosen

**Gate 3 is CLOSED when GOVERNANCE_STATUS.md is written and all contradictions have resolution.**

---

## GATE 4 — PRODUCT DECISIONS

**Objective:** Make product-level decisions based on validated foundation. This is a **Decision Gate**, not a Development Gate.

**Duration:** Decision session + ADR creation  
**Owner:** Product + Engineering  
**Depends on:** Gates 0-3 CLOSED

> Gate 4 produces ADRs (decisions), not code. Implementation begins only after each ADR is approved and scheduled.

### Decision Process

For each item:

```
ADR (Decision)
  ↓
If GO: Validate → Pilot → GO/NO-GO → Implementation
If NO-GO: Document rationale, close
```

### Decisions Required

| Item | Decision | Options | Output | Implementation Only After |
|------|----------|---------|--------|--------------------------|
| AI Copilot | Validate real OpenAI API | A) Enable after validation B) Keep gated | ADR + validation results | ADR approved + validation pass |
| Signal Marketplace | Build or Remove | A) Implement 15 methods B) Remove module | ADR | ADR approved |
| V3 Design System | Complete or Archive | A) Complete V3 B) Archive V3 | ADR | ADR approved |
| GTM Intelligence | Build by priority | A) Implement ICP/Enrichment/Outreach B) Defer | ADR | ADR approved + product priority |
| Kafka | Deploy or accept in-memory | A) Deploy Kafka B) Accept in-memory | ADR | ADR approved |
| Neo4j | Keep offline or deploy | A) Keep offline per ADR-108 B) Deploy | ADR (update or new) | Business case proven |

### Gate Closure

**Gate 4 is CLOSED when each item above has:**
1. An ADR with explicit decision (GO/NO-GO/DEFER)
2. Rationale documented
3. If GO: validation plan defined
4. If NO-GO: rationale recorded for future reference

---

## EXECUTION SEQUENCE

```
Gate 0 (Runtime Truth)
  │
  ├── B-01: Railway backup status
  ├── B-02: PostgreSQL WAL config
  ├── B-03: Alembic head
  ├── B-04: Vercel deployment
  └── B-05: Deployed commit
  │
  ▼
Gate 1 (Production Safety)
  │
  ├── 1A: Backup fix
  ├── 1B: WAL/PITR decision
  └── 1C: Monitoring completion
  │
  ▼
Gate 2 (Regression Protection)
  │
  ├── 2A: Enable 5 E2E critical
  ├── 2B: Coverage gates
  └── 2C: False confidence cleanup
  │
  ▼
Gate 3 (Governance Freeze)
  │
  ├── 3A: Contradiction resolution
  ├── 3B: Source of Truth consolidation
  └── 3C: Orphan code cleanup
  │
  ▼
Gate 4 (Product Expansion)
  │
  ├── AI: Validate → Pilot → Enable
  ├── Signal Marketplace: Build or Remove
  ├── V3: Complete or Archive
  ├── GTM: Build by priority
  ├── Kafka: Deploy or accept
  └── Neo4j: Keep offline or deploy
```

---

## DO NOT TOUCH (During Gates 0-3)

| Component | Reason |
|-----------|--------|
| Auth/Identity | Production-grade, security-sensitive |
| RLS policies (71) | Verified with adversarial tests |
| CSRF middleware | Verified with contract tests |
| JWT RS256 | Production-grade |
| Database migrations (82+) | Schema history |
| CI stages 1-5 | Working correctly |
| @salesos/ui v5.0 | Production-ready |
| @salesos/tokens | Foundation of design system |
| CANONICAL_ARCHITECTURE.md | Architecture SSOT |
| AGENTS.md | Governance document |
| ADR-108 (Neo4j offline) | Deliberate decision |

---

## SUCCESS CRITERIA

### After Gate 0:
- PRODUCTION_TRUTH.md exists with E5/E6 evidence for all 5 items

### After Gate 1:
- Backup image builds and runs
- Backup generated, verified, and **restored into isolated DB** with evidence
- WAL posture explicitly decided (configured OR accepted with ADR — NOT labeled PITR if Option B)
- Alertmanager present in prod compose
- Synthetic test alert fired → routed → received by human (timestamp evidence)
- No unverified "DONE" claims in documentation

### After Gate 2:
- 5 E2E specs pass in CI on every PR
- Frontend coverage ≥ 60%
- Backend coverage ≥ 65%
- Simulated/mocked tests honestly labeled

### After Gate 3:
- 22 contradictions resolved (banner or correction)
- One Source of Truth per domain
- Orphan code archived
- Decision Engine canonical location chosen
- Kafka in-memory acceptance documented

### After Gate 4:
- Each product expansion item has an ADR decision
- No expansion work begins without Gate 0-3 closure

---

## DEFINITION OF DONE

The remediation is complete when:

1. PRODUCTION_TRUTH.md reflects runtime reality (not documentation claims)
2. Backup works end-to-end: **build → run → backup → verify → restore into isolated DB → validate → evidence artifact**
3. WAL posture is explicit: **configured (Option A) OR accepted with ADR (Option B) — never mislabeled as PITR if Option B**
4. Monitoring alerts reach humans: **Prometheus → Alertmanager → Slack/email/PagerDuty → human confirms with timestamp**
5. 5 E2E specs protect against regressions (passing in CI on every PR)
6. Coverage gates enforced (FE ≥ 60%, BE ≥ 65%)
7. 22 contradictions resolved (HISTORICAL banner or correction)
8. One source of truth per domain
9. No stale "DONE" claims without evidence artifacts
10. Gate 4 ADRs written for each product expansion item

---

*This plan is the single execution document. The Enterprise Audit Report and Audit Verification Report are its evidence base. No workstream may open outside these gates.*
