# Phase 0 Exit Checklist

> **Status:** ALL items must be satisfied simultaneously before Phase 0 exit is declared.
> **Rule:** No partial credit. Phase 1 does not start until every item below is verified with command evidence.
> **Authority:** `MASTER_EXECUTION_PLAN.md` §9, `PRODUCT_ROADMAP.md` Phase 0 Go/No-Go Criteria, `IMPLEMENTATION_SEQUENCE.md` position 1-3, DEC-008.
> **Last updated:** 2026-08-01 (DEC-147 criterion 3.5 Stage 5 Security Scan **READY FOR REVIEW**; DEC-146a 9.3 **CLOSED**; ADR-036 Applied **COMPLETE 4/4**; Eng Stability **COMPLETE 4/4**; Phase 0 **43/54**; residuals EOS **4.1/4.8** ARB · CI **3.7/3.8** + CI-08/09; EOS Audit Complete 6/8; ADR Drift Complete 5/5; Capability Drift Complete 4/4)
>
> ## Operating State
>
> ```
> STATE = EXECUTION
> Architecture = FROZEN
> Program = ACTIVE
> Engineering = STABILIZING
> AI Runtime = DEFERRED
> ```
>
> **Sprint success = number of exit criteria CLOSED, not number of stories completed.**
> **Rule: No work accepted unless it directly closes a criterion from this checklist.**

---

## Current Verdict

**Phase 0 = NO-GO** (CI-08/CI-09; Security residuals; Capability/ADR drift)

Blocked on: **CI-08** (GHCR 403), **CI GREEN not met**. R-14 Railway **2.3 CLOSED CONDITIONAL** (multi-tenant live split residual). Security **1.5 CLOSED CONDITIONAL** (post-align Security Scan pip-audit field-verify PENDING).

---

## Exit Criteria

### 1. Security P0 Remediation

| # | Criterion | Evidence Required | Status |
|---|-----------|-------------------|--------|
| 1.1 | Decision Center cross-tenant IDOR fixed | Regression test PASS, independent review signed | ✅ VERIFIED/CLOSED — Arch PASS + Validation PASS @ `31f3aee` (DEC-124); Orchestrator 2026-08-01 |
| 1.2 | Webhook SSRF fixed (URL allowlist) | Regression test PASS, re-verified against Integration Hub caller | ✅ VERIFIED/CLOSED — Arch PASS + Validation PASS (Docker SSRF suite 32 passed, 54 deselected) @ `fd8699d` (DEC-125); Orchestrator DEC-125a 2026-08-01; residual: staging SSRF pentest OPEN (non-blocking) |
| 1.3 | CSRF bypass via `X-API-Key` fixed | Regression test PASS | ✅ VERIFIED/CLOSED — Arch PASS + Validation PASS (Docker CSRF suite 11 passed; DEC-085 untouched) @ `5db0756` (DEC-127); Orchestrator DEC-127a 2026-08-01 |
| 1.4 | Cross-tenant regression test template established | Harness reusable by every subsequent epic | ✅ STORY-01-04 (Sprint 02) |
| 1.5 | SAST + dependency vulnerability scan wired into CI | `security-scan.yml` + `ci.yml` security jobs green | ✅ VERIFIED/CLOSED **CONDITIONAL** — Arch PASS + Validation PASS_CONDITIONAL @ `fa266b5` (DEC-128); workflow honesty + named single ignore PASS; pre-land Stage 5 / Security Scan corroboration PASS via gh; residual: *post-align Security Scan pip-audit field-verify PENDING until tip containing `fa266b5` is pushed and Security Scan pip-audit SUCCESS with poetry export + 1 ignored (ecdsa)*. DEC-085 untouched. Orchestrator DEC-128a 2026-08-01 |

**Owner:** Security Eng / CTO  
**Reference:** `PROGRAM_PLAN.md` EPIC-01, `CANONICAL_ARCHITECTURE.md` §14

---

### 2. RLS & Tenant Isolation

| # | Criterion | Evidence Required | Status |
|---|-----------|-------------------|--------|
| 2.1 | RLS policies on all Category-A tables | 47 policies verified (DEC-044) | ✅ STORY-02-01 DONE |
| 2.2 | RLS policies on all Category-B join tables | 59 total policies live (DEC-119: B1–B7 COMPLETE) | ✅ Category B COMPLETE |
| 2.3 | R-14 Railway: `salesos_app` role live, BYPASSRLS removed | Slices D (prod image) + E (bypass-probe PASS) | ✅ VERIFIED/CLOSED **CONDITIONAL** — D+E @ `9664e9fc` / crumb `84c5163`; tip-align `d1a8c35e7f09` / crumb `c842245`; `salesos_app`; `rolbypassrls=False`; policies **67**; bare/wrong-tenant=0; residual: *multi-tenant live split not re-proven* (1 tenant) — tip-align does **not** clear this. Arch CONDITIONAL + Validation PASS_CONDITIONAL. Orchestrator 2026-08-01 |
| 2.4 | R-14 Local/CI/Compose/Staging | Bypass-probe isolates on `salesos_app` | ✅ DEC-014/015 + Slice C |
| 2.5 | Cross-tenant adversarial suite 100% PASS | `test_adversarial_rls.py` 7/7 + remaining 15/15 | ✅ S04-01, S04-05, S04-06 |
| 2.6 | `middleware.ts` server-side auth live | Browser redirect probe PASS (DEC-095) | ✅ STORY-02-02 |
| 2.7 | JWT Owner/Tenant audience split live | 14/14 unit PASS (DEC-093) | ✅ STORY-02-03 |

**Owner:** Chief Architect / Backend Lead  
**Reference:** `PROGRAM_PLAN.md` EPIC-02, DEC-044, DEC-120

---

### 3. CI/CD Green

| # | Criterion | Evidence Required | Status |
|---|-----------|-------------------|--------|
| 3.1 | Stage 1: Backend Lint green | `ruff check` exits 0 (DEC-036) | ✅ CI-10 |
| 3.2 | Stage 2: Backend Types green | MyPy exits 0 (DEC-096) | ✅ CI-20 |
| 3.3 | Stage 3: Frontend Unit Tests green | 196/196 suites PASS (DEC-077) | ✅ Jest-debt |
| 3.4 | Stage 4: Backend Unit + Integration green | `pytest` 2700+ PASS, `-n auto` | ✅ CI-22 follow-on |
| 3.5 | Stage 5: Security Scan green | pip-audit (named ignore only), Bandit, Gitleaks, Semgrep residual-only | 🟡 READY FOR REVIEW — DEC-147 @ land SHA (pending); CI Stage 5 + Security Scan SUCCESS @ `c842245` (`30704321096` / `30704321107`); ecdsa named ignore (DEC-057/090/098); Semgrep residual **11** alembic (DEC-105); residual: *post-align Security Scan pip-audit field-verify PENDING until tip containing `fa266b5` is pushed*; does **not** auto-close **3.8**; DEC-085 untouched; do **not** claim VERIFIED/CLOSED / Production GO / CI GREEN until Arch+Val+Orchestrator |
| 3.6 | Stage 6: Docker Build + Push green | Backend + Frontend images build + push | ⬜ CI-08 BLOCKED (GHCR 403) |
| 3.7 | Stage 7: E2E green | Playwright specs PASS with real backend services | ⬜ CI e2e job has no services |
| 3.8 | Full pipeline: CI GREEN (code path) | Stages 1–5 all green on same run | ⬜ |
| 3.9 | Full pipeline: CI GREEN (incl. publish) | Stages 1–7 all green on same run | ⬜ CI-08 BLOCKED |
| 3.10 | CI-08 GHCR 403 resolved | Stage 6 push succeeds (DEC-104 Option A) | ⬜ Ops/human |
| 3.11 | CI-09 VPS SSH/secrets provisioned | Deploy workflows functional | ⬜ Ops/human |

**Owner:** DevOps/SRE Lead  
**Reference:** `SPRINT_05_DELIVERY_BOARD.md`, `12_CI_CATALOG.md`, DEC-104

---

### 4. EngineeringOS Audit Pass

| # | Criterion | Evidence Required | Status |
|---|-----------|-------------------|--------|
| 4.1 | All B1–B7 findings resolved | ARB re-audit returns PASS | ⬜ B1–B7 corrected in v3.1; not re-audited |
| 4.2 | Fingerprint matches pinned commit | Alembic head, framework versions, structural counts verified | ✅ VERIFIED/CLOSED — Arch PASS + Validation PASS (light) @ `637d051` (DEC-142a); re-measure pin `9fa8e9f`; Alembic head `a4f7c29e1b80`; FastAPI `>=0.136.0,<0.142.0`; migrations **69**; DEC-085 untouched; Orchestrator 2026-08-01; do **not** claim Production GO / CI GREEN |
| 4.3 | No invented surfaces | All cataloged API/Module paths exist in repo | ✅ VERIFIED (ARB 2026-08-01; B4 confirmed; filesystem audit PASS) |
| 4.4 | EvidenceLevel justified | Counts use measured methods, not narrative | ✅ VERIFIED/CLOSED — Arch PASS + Validation PASS (light) @ `637d051` (DEC-142a); EvidenceLevel **Measured** (methods in `23` + `.engineering/measure_fingerprint.py`); not ARB “Repository Verified”; DEC-085 untouched; Orchestrator 2026-08-01; do **not** claim Production GO / CI GREEN |
| 4.5 | `.engineering/` committed to git | Not untracked | ✅ VERIFIED/CLOSED — Arch PASS + Validation PASS (light: 33 tracked, 0 untracked; DEC-085 untouched) @ `5b2e4c2` (DEC-140a); pin residual cleared by DEC-142a (**4.2/4.7 CLOSED**); Orchestrator 2026-08-01; do **not** claim Production GO / CI GREEN |
| 4.6 | Lock protocol verified | `21_RUNTIME_STATE.json` mirrors `22_FILE_LOCKS.json` | ✅ VERIFIED (ARB 2026-08-01; 21 mirrors 22; bootstrap lock released) |
| 4.7 | Staleness protocol active | Fingerprint re-validated at current HEAD | ✅ VERIFIED/CLOSED — Arch PASS + Validation PASS (light) @ `637d051` (DEC-142a); Revalidation **Active**; `measure_fingerprint.py` + `23.comparison_protocol`; re-validated at tip `9fa8e9f`; DEC-085 untouched; Orchestrator 2026-08-01; do **not** claim Production GO / CI GREEN |
| 4.8 | Independent ARB re-audit = PASS | New validation report with no CRITICAL findings | ⬜ |

**Owner:** OpenCode / ARB  
**Reference:** `32_EOS_VALIDATION_AUDIT.md`, `00_PROJECT_CONSTITUTION.md`

---

### 5. Capability Registry — Drift Resolution

| # | Criterion | Evidence Required | Status |
|---|-----------|-------------------|--------|
| 5.1 | Single source of truth established | One registry (catalog / decorator / SDK / YAML) designated canonical | ✅ VERIFIED/CLOSED — Arch PASS + Validation PASS (light) @ `8e105fe` (DEC-132a); decorator framework = canonical runtime SoT (kebab IDs); pins `CAPABILITY_REGISTRY_SOT*`; secondaries = SDK / YAML / CAP-### catalog; DEC-085 untouched; Orchestrator 2026-08-01 |
| 5.2 | `CAP-###` mapped to runtime kebab IDs | Automation can join registries | ✅ VERIFIED/CLOSED — Arch PASS + Validation PASS (light) @ `81b593f` (DEC-133a); join map `cap_to_kebab_join.yaml` (10 direct / 30 unmapped / 3 decorator-only); `--join-map-only` exit 0; DEC-085 untouched; CAP-037→`capability-framework` semantic-join refine = non-blocking residual; Orchestrator 2026-08-01 |
| 5.3 | Registry sync/validate scripts aligned | `validate_capability_registries.py` exits 0 | ✅ VERIFIED/CLOSED — Arch PASS + Validation PASS (light) @ `6a98999` (DEC-134a); SoT-oriented gate (joined secondaries subset-of decorator SoT via join map); host+Docker default exit **0**; `--legacy-equality` exit **2** (diagnostic, not close gate); DEC-085 untouched; non-blocking INFO residuals: SDK/YAML extras + unmapped CAPs + CAP-037 refine; Orchestrator 2026-08-01 |
| 5.4 | `/api/v1/capabilities` tested | Test exercises decorator registry endpoint | ✅ VERIFIED/CLOSED — Arch PASS + Validation PASS @ `65e82cc` (DEC-131a); ASGI contract `tests/contract/test_capabilities_api.py`; Docker **4 passed**; DEC-085 untouched; Orchestrator 2026-08-01 |

**Owner:** Shared / Chief Architect  
**Reference:** `29_CAPABILITY_REGISTRY.md` §4, DEBT-ARC-003 / E-21

---

### 6. ADR Index — Drift Resolution

| # | Criterion | Evidence Required | Status |
|---|-----------|-------------------|--------|
| 6.1 | ADR-025/026/027/028: files exist OR index corrected | No index entry claiming "Accepted" without a file | ✅ VERIFIED/CLOSED — Arch PASS + Validation PASS (light: path-exists + Status Accepted) @ `4997ae4` (DEC-135a); files @ `salesos/backend/docs/adr/0025..0028-*.md`; `docs/adr/index.md` File column + location registered; residual **4.5 CLOSED** (DEC-140a); ADR Drift cluster COMPLETE **5/5** (DEC-139a); Orchestrator 2026-08-01; do **not** claim Production GO / CI GREEN |
| 6.2 | ADR-029 phantom resolved | Numbering gap closed or documented | ✅ VERIFIED/CLOSED — Arch PASS + Validation PASS (light: path-exists + Status Not Issued + no Accepted-without-file) @ `a1ce473` (DEC-136a); disposition **Not Issued** @ `docs/adr/0029-number-never-issued.md`; `docs/adr/index.md` row registered (not Accepted); no binding architecture invented; residual **4.5 CLOSED** (DEC-140a); ADR Drift cluster COMPLETE **5/5** (DEC-139a); Orchestrator 2026-08-01; do **not** claim Production GO / CI GREEN |
| 6.3 | ADR-033/034 status conflicts resolved | Index status matches file header status | ✅ VERIFIED/CLOSED — Arch PASS + Validation PASS (light: index Status == file header Proposed for 033/034; no Accepted-without-evidence) @ `bcd7aa6` (DEC-137a); `docs/adr/index.md` Status **Proposed** matches file headers; dates → `2026-07-17`; no invented Accepted; residual **4.5 CLOSED** (DEC-140a); ADR Drift cluster COMPLETE **5/5** (DEC-139a); Orchestrator 2026-08-01; do **not** claim Production GO / CI GREEN |
| 6.4 | ADR-032/0032 naming unified | Single naming convention across `docs/adr/` and `engineering-os/adr/` | ✅ VERIFIED/CLOSED — Arch PASS + Validation PASS (light) @ `8a3c92e` (DEC-138a); naming bridge `docs/adr/0032-widget-sdk-reconciliation.md` (canonical ID **ADR-032**; alias ADR-0032); index File/Status/date aligned (Status **Proposed** matches body; no invented Accepted); submodule filename retained as documented alias (no rename); DEC-085 untouched; residual **4.5 CLOSED** (DEC-140a); ADR Drift cluster COMPLETE **5/5** (DEC-139a); Orchestrator 2026-08-01; do **not** claim Production GO / CI GREEN |
| 6.5 | ADR-036 registered in all indexes | `docs/adr/index.md` + `27_ADR_INDEX.md` | ✅ VERIFIED/CLOSED — Arch PASS + Validation PASS (light) @ `aaeaff3` (DEC-139a); body `docs/adr/0036-engineering-organization-layer-separation.md` (Status **Accepted** matches file header + criterion 9.1; not invented); `docs/adr/index.md` Active ADRs row; `.engineering/27_ADR_INDEX.md` master row + conflict #13 RESOLVED; engineering-os has no separate ADR index (N/A); DEC-085 untouched; ADR Drift cluster COMPLETE **5/5**; residual **4.5 CLOSED** (DEC-140a); **9.2 CLOSED** (DEC-141a); Orchestrator 2026-08-01; do **not** claim Production GO / CI GREEN |

**Owner:** Human / Chief Architect  
**Reference:** `27_ADR_INDEX.md` §4, `28_ADR_DEPENDENCY_MAP.md` §6

---

### 7. Database Schema Reconciliation

| # | Criterion | Evidence Required | Status |
|---|-----------|-------------------|--------|
| 7.1 | All tenant-scoped tables have CREATE TABLE migrations | Zero tables in R-09 missing CREATE | ✅ DEC-113 (Slice 1: 0 remaining) |
| 7.2 | ORM↔DB type alignment complete | `emails`/`meetings` UUID aligned (DEC-121) | ✅ Slice 2 |
| 7.3 | Index names aligned | `ix_rev_*` → `ix_*` rename (DEC-122) | ✅ Slice 3 |
| 7.4 | Companies dead-column DROP resolved | `search_vector` FTS preserved; DEC decision recorded | ✅ VERIFIED/CLOSED — Arch PASS + Validation PASS @ `4aacd6d` (DEC-129a); KEEP (no DROP; ORM restore); head `d1a8c35e7f09`; Docker **4 passed**; DEC-085 untouched; Orchestrator 2026-08-01 |
| 7.5 | Deferred-8 tables have RLS enabled | RLS policies on tables currently without them | ✅ VERIFIED/CLOSED — Arch PASS + Validation PASS @ `578e4f2` (DEC-123a); live POLICY_COUNT **67** (prod tip-align `d1a8c35e7f09` / crumb `c842245` cleared prior “prod may still be on 59” residual); Orchestrator 2026-08-01 |
| 7.6 | `alembic check` exits clean | Zero drift between ORM and DB | ✅ VERIFIED/CLOSED — Arch PASS + Validation PASS @ `250bcb5` (DEC-130h); phased Slices 5a–5g (DEC-130…DEC-130g); live Docker `alembic check` **exit 0** @ head `a4f7c29e1b80`; True DROP DEC **0**; DEC-085 untouched; residual `ix_graph_nodes_search` KEEP via `include_object` (non-blocking); Orchestrator 2026-08-01 |

**Owner:** Backend Lead  
**Reference:** `13_DATABASE_CATALOG.md`, R-20, DB-05

---

### 8. Engineering Stability

| # | Criterion | Evidence Required | Status |
|---|-----------|-------------------|--------|
| 8.1 | `engineering-os/` submodule clean | No uncommitted changes | ✅ VERIFIED/CLOSED — Arch PASS + Validation PASS (light: pin `b82b9fb`, clean tree) @ `89502ef` (DEC-143a); discarded malformed unreviewed `capability-registry.yaml` append (outside YAML fence); parent gitlink unchanged; DEC-085 untouched; Eng Stability cluster **COMPLETE 4/4** (DEC-145a); residual EOS **4.1/4.8** OPEN; Orchestrator 2026-08-01; do **not** claim Production GO / CI GREEN |
| 8.2 | Agent coordination protocol exercised | Multi-agent parallel work completed without conflict | ✅ VERIFIED/CLOSED CONDITIONAL — Arch PASS_CONDITIONAL + Validation PASS_CONDITIONAL @ `5bc0bf2` (DEC-145a); caps (`max_parallel_workers=8`, `max_agents_total=12`, permanent roles **4**, DEC-107 min/prefer READY **2/3**); namespaced workers + conflict/lock rules; `.ai/` org baseline committed (ARB-003); light exercise DEC-107 + `21` workers; residual: *at-scale live soak at max_parallel_workers=8 not field-proven*; DEC-085 untouched; Eng Stability cluster **COMPLETE 4/4**; EOS **4.1/4.8** OPEN; Orchestrator 2026-08-01; do **not** claim Production GO / CI GREEN / unconditional CLOSED |
| 8.3 | Architecture rules enforced in CI | `test_architecture.py` + `arch-compliance.ps1` green (critical CI jobs) | ✅ VERIFIED/CLOSED CONDITIONAL — Arch CONDITIONAL + Validation PASS_CONDITIONAL @ `868a98c` (DEC-144a); independent `test-architecture` job wired; Docker **36 passed**; local ps1 **95.8%** PASS; gh `arch-compliance` success @ run `30704321096`; residual: *tip `test-architecture` SUCCESS PENDING until tip containing `868a98c` is pushed*; DEC-085 untouched; Eng Stability cluster **COMPLETE 4/4** (DEC-145a); EOS **4.1/4.8** OPEN; Orchestrator 2026-08-01; do **not** claim Production GO / CI GREEN / unconditional CLOSED |
| 8.4 | No stale locks in `22_FILE_LOCKS.json` | All bootstrap locks released | ✅ VERIFIED (ARB 2026-08-01; zero write locks; TTL rule active) |

**Owner:** OpenCode / Chief Architect  
**Reference:** `25_CHANGE_PROTOCOL.md`, `26_AGENT_COORDINATION.md`

---

### 9. ADR-036 Applied

| # | Criterion | Evidence Required | Status |
|---|-----------|-------------------|--------|
| 9.1 | Four-layer separation documented | ADR-036 Accepted | ✅ |
| 9.2 | `docs/program/` ↔ `.engineering/` bidirectional references | Cross-references exist, no data duplication | ✅ VERIFIED/CLOSED — Arch PASS + Validation PASS (light) @ `7b618da` (DEC-141a); bridges `docs/program/ENGINEERING_LAYER_BRIDGE.md` ↔ `.engineering/33_PROGRAM_LAYER_BRIDGE.md` (pointers only; no catalog/sprint duplication); DEC-085 untouched; residuals EOS **4.1/4.8** · Eng Stability **8.2/8.3** OPEN (**4.2/4.4/4.7 CLOSED** DEC-142a; **8.1 CLOSED** DEC-143a); Orchestrator 2026-08-01; do **not** claim Production GO / CI GREEN |
| 9.3 | `.ai/` explicitly deferred | Documented with trigger condition | ✅ VERIFIED/CLOSED — Arch PASS + Validation PASS (light) @ `922528f` / tip pin `1f99628` (DEC-146a); org baseline ≠ Agent OS runtime; triggers pinned in ADR-036 §`.ai/` Runtime deferral + `.ai/README`; `runtime-spec.yaml` `status: SPECIFICATION`; DEC-085 untouched; ADR-036 Applied cluster **COMPLETE 4/4**; residual EOS **4.1/4.8** ARB · CI **3.x** + CI-08/09; Orchestrator 2026-08-01; do **not** claim Production GO / CI GREEN |
| 9.4 | No further architectural layers introduced before Phase 0 exit | ARB governance rule enforced | ✅ This checklist |

**Owner:** CTO  
**Reference:** `docs/adr/0036-engineering-organization-layer-separation.md`

---

## Summary

| Cluster | Items | Complete | Blocked | Open |
|---------|-------|----------|---------|------|
| 1. Security P0 | 5 | 5 | 0 | 0 |
| 2. RLS & Tenant Isolation | 7 | 6 | 0 | 1 |
| 3. CI/CD Green | 11 | 4 | 2 (CI-08, CI-09) | 5 (incl. 3.5 RFR) |
| 4. EOS Audit Pass | 8 | 6 | 0 | 2 |
| 5. Capability Drift | 4 | 4 | 0 | 0 |
| 6. ADR Drift | 5 | 5 | 0 | 0 |
| 7. DB Schema | 6 | 6 | 0 | 0 |
| 8. Engineering Stability | 4 | 4 | 0 | 0 |
| 9. ADR-036 Applied | 4 | 4 | 0 | 0 |
| **TOTAL** | **54** | **43** | **2** | **9** |

---

## Blocked Items (cannot proceed without external action)

| Item | Blocked By | Action Needed |
|------|-----------|---------------|
| CI-08 GHCR 403 | Org-level Packages write permission | Human/ops: grant GHCR write to Actions |
| CI-09 VPS SSH/secrets | Secret provisioning | Ops: provision VPS_HOST, VPS_USER, VPS_SSH_KEY |
| R-14 multi-tenant residual (non-blocking for 2.3 CONDITIONAL) | Second-tenant fixture (prefer staging) | Optional: re-run Slice E differential for unconditional PASS |
| 1.5 post-align Security Scan pip-audit (non-blocking for 1.5 CONDITIONAL) | Push tip containing `fa266b5` | Field-verify Security Scan pip-audit SUCCESS with poetry export + 1 ignored (ecdsa) — does **not** upgrade to unconditional CLOSED until observed |
| 8.3 tip `test-architecture` (non-blocking for 8.3 CONDITIONAL) | Push tip containing `868a98c` | Field-verify Stage 5 `test-architecture` SUCCESS — does **not** upgrade to unconditional CLOSED until observed |
| 8.2 at-scale soak (non-blocking for 8.2 CONDITIONAL) | Live soak at `max_parallel_workers=8` | Concurrent-writer soak at worker ceiling — does **not** upgrade to unconditional CLOSED until field-proven |
| 3.5 post-align Security Scan pip-audit (non-blocking for 3.5 RFR → expected CLOSED CONDITIONAL) | Push tip containing `fa266b5` | Field-verify Security Scan pip-audit SUCCESS with poetry export + 1 ignored (ecdsa) — same residual as 1.5 DEC-128a; does **not** auto-close **3.8** |

---

## Declaration

Phase 0 exit is declared **only when all 54 items above are checked complete** with command evidence referenced.

Per DEC-008: **Zero partial credit. Phase 1 does not start until Phase 0's RLS/security exit criteria are met.**

Per ADR-036 governance rule: **No further architectural layers shall be introduced until Phase 0 Exit Criteria are fully satisfied.**

---

## Engineering Execution Contract (EEC-001)

> **In effect while:** `Architecture = FROZEN`, `Operating State = EXECUTION`
> **Authority:** CTO (ARB session 2026-08-01)

### Rule 1 — Exit Traceability

Every Story must reference the Phase 0 Exit Criterion ID it closes.

```text
Story: ST-{NN}-{NNN}
Closes: P0-SEC-03, P0-CI-02
No other objective.
```

No "exploratory" or "improvement" stories during this phase.

### Rule 2 — PR Traceability

Every Pull Request must include:

```text
Exit Criterion: [ID from this checklist]
Files Changed:  [list]
Evidence:       [command output, CI run number]
Validation:     [not validated | light validated | build validated]
Risk:           [none | R-XX referenced]
Rollback:       [how to revert]
```

### Rule 3 — Definition of Done

A Story is not complete when code is written. It is complete when:

```
Implemented → Tested → Reviewed → Criterion Updated → Evidence Recorded → Checklist Progress Updated
```

### Rule 4 — Freeze Exceptions

Architecture Freeze may only be broken for:
1. A bug blocking closure of a Phase 0 criterion.
2. A formal new ARB decision.

All other architectural changes are deferred to post-Phase-0.

### Rule 5 — Weekly Review

The weekly review question is not "How many Stories did we complete?" but:

> **How many Phase 0 criteria became CLOSED this week? What blocks the rest?**

---

## Agent Bootstrap (minimal read)

New agents joining during EXECUTION state need only:

1. `docs/program/PHASE_0_EXIT_CHECKLIST.md` — what must close, what's allowed
2. `.engineering/21_RUNTIME_STATE.json` — operating state, blockers, locks
3. Layer bridges (ADR-036 / criterion 9.2): `docs/program/ENGINEERING_LAYER_BRIDGE.md` ↔ `.engineering/33_PROGRAM_LAYER_BRIDGE.md`

---

## Related

- `docs/program/PRODUCT_ROADMAP.md` — Phase 0 Go/No-Go Criteria
- `docs/program/EXECUTION_DAG.md` — Live READY/BLOCKED/PARALLEL state
- `docs/program/SPRINT_05_DELIVERY_BOARD.md` — Per-story status
- `docs/program/RISK_REGISTER.md` — R-01 through R-26
- `docs/program/ENGINEERING_LAYER_BRIDGE.md` — Program → Engineering Spec (pointers only)
- `.engineering/33_PROGRAM_LAYER_BRIDGE.md` — Engineering Spec → Program (pointers only)
- `.engineering/32_EOS_VALIDATION_AUDIT.md` — ARB audit findings
- `docs/adr/0036-engineering-organization-layer-separation.md` — Layer separation
