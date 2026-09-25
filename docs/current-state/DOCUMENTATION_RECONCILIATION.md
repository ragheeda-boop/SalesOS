# DOCUMENTATION RECONCILIATION — 2026-08-24

**Total .md files in repo:** ~970 (docs/) + ~255 (salesos/) + ~248 (engineering-os/) + ~17 (.ai/) + ~31 (.engineering/) + ~11 (archive/) = ~1,532

---

## KEEP (Authoritative — Do Not Modify)

| File | Authority |
|------|-----------|
| `AGENTS.md` | Master workspace guide for humans and agents |
| `docs/PROJECT_BIBLE.md` | Highest engineering authority |
| `docs/audit/ga-engineering-audit/FINAL_GO_NOGO_ASSESSMENT.md` | Authoritative current assessment |
| `docs/audit/ga-engineering-audit/00-EXECUTIVE-SUMMARY.md` | Scorecard authority |
| `docs/audit/ga-engineering-audit/SALESOS_MASTER_CLOSURE_SEQUENCE.md` | Locked closure order |
| `docs/audit/ga-engineering-audit/AI_HONESTY.md` | AI honesty statement |
| `docs/audit/ga-engineering-audit/PHASE1_GATE_EVIDENCE_PACK.md` | Phase 1 evidence |
| `docs/audit/ga-engineering-audit/PHASE2_GATE_EVIDENCE_PACK.md` | Phase 2 evidence |
| `docs/audit/ga-engineering-audit/PHASE3_GATE_EVIDENCE_PACK.md` | Phase 3 evidence |
| `docs/audit/ga-engineering-audit/PHASE4_GATE_EVIDENCE_PACK.md` | Phase 4 evidence |
| `docs/audit/ga-engineering-audit/PHASE4F_EVIDENCE_PACK.md` | Phase 4F evidence |
| All 28 ADRs in `docs/adr/` | Architecture decisions |
| `docs/audit/star-audit/` (20 numbered files) | Complementary audit |
| `docs/ops/` (23 files) | Operational runbooks |
| `docs/audit/ga-engineering-audit/PROGRESS-WAVE*.md` | Wave progress tracking |
| `docs/audit/ga-engineering-audit/enterprise-audit-board/` | Audit board history |

## UPDATE (Stale References Need Fixing)

| File | Issue | Fix Needed |
|------|-------|------------|
| `README.md` | Version refs may be stale | Verify version references |
| `PRODUCT_BIBLE.md` | Explicitly not GA gate | No change needed (KEEP) |
| `REPO_TOPOLOGY_AUDIT.md` | Superseded by ADR-100 | ARCHIVE |
| `docs/PROJECT_MANIFEST.md` | Superseded by PROJECT_BIBLE.md | ARCHIVE |
| `docs/FEATURE_STATUS.md` | May have stale claims | Review and update |
| `docs/PROJECT_STATUS.md` | May have stale claims | Review and update |
| `docs/ROADMAP_5_YEARS.md` | May conflict with program milestones | Review |
| `salesos/CHANGELOG.md` | Verify version alignment | Review |

## ARCHIVE (Confirmed Obsolete)

| File/Directory | Reason | Superseded By |
|----------------|--------|---------------|
| `docs/vnext/reports/GO_NO_GO_DECISION.md` | False GO claim | `docs/audit/ga-engineering-audit/FINAL_GO_NOGO_ASSESSMENT.md` |
| `docs/vnext/reports/GA_CHECKLIST.md` | False GO claim | `docs/audit/ga-engineering-audit/FINAL_GO_NOGO_ASSESSMENT.md` |
| `docs/vnext/` (entire directory) | Nearly all SUPERSEDED | `docs/audit/ga-engineering-audit/` |
| `REPO_TOPOLOGY_AUDIT.md` | Superseded | `docs/adr/0100-repository-canonicalization.md` |
| `docs/PROJECT_MANIFEST.md` | Superseded | `docs/PROJECT_BIBLE.md` |
| `docs/audit/legacy-reports/` | Old audit reports | `docs/audit/ga-engineering-audit/` |
| `docs/v2/` | Old UX vision docs | `docs/design/` |
| `outputs/SalesOS_Phase1B_Evidence.md` | Outdated evidence | N/A |
| `packages/data/*.md` (16 files) | Outdated pipeline reports | N/A |

## DELETE (Debug Artifacts)

| File | Reason |
|------|--------|
| `salesos/_fails.txt` | Debug artifact |
| `salesos/backend/test_login.py` | Debug test |
| `salesos/backend/test_pool.py` | Debug test |

## SUPERSEDE (Mark Clearly)

| File | Status | Replacement |
|------|--------|-------------|
| `docs/vnext/GO_NO_GO_DECISION.md` | SUPERSEDED 2026-07-22 | ga-engineering-audit |
| `docs/vnext/GA_CHECKLIST.md` | SUPERSEDED 2026-07-22 | ga-engineering-audit |

## KEEP BUT NOTE HISTORICAL

| File | Note |
|------|------|
| `docs/audit/star-audit/` | Complementary audit, not authority |
| `engineering-os/` | Active governance platform |
| `.ai/` | Active agent configs |
| `.engineering/` | Auto-generated coordination |
| `migration-log/` | Historical reorg record |
| `archive/` | Already archived content |
