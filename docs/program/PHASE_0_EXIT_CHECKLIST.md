# Phase 0 Exit Checklist

> **Status:** ALL items must be satisfied simultaneously before Phase 0 exit is declared.
> **Rule:** No partial credit. Phase 1 does not start until every item below is verified with command evidence.
> **Authority:** `MASTER_EXECUTION_PLAN.md` §9, `PRODUCT_ROADMAP.md` Phase 0 Go/No-Go Criteria, `IMPLEMENTATION_SEQUENCE.md` position 1-3, DEC-008.
> **Last updated:** 2026-08-02 (**PARALLEL EXECUTION — FREEZE COMPLIANT** under [DEC-151](decisions/DEC-151-PHASE-0-GOVERNANCE-FREEZE.md); prior DEC-150 **Option B** / DEC-149a; Phase 0 pin **48/54 NO-GO**; no Production GO)
>
> ## Operating State
>
> ```
> STATE = PARALLEL EXECUTION — FREEZE COMPLIANT
> Architecture = FROZEN
> Governance = FROZEN          # DEC-151 — Phase 0 Governance Freeze
> Program = ACTIVE             # residual hard OPEN only: 3.7, 3.9, 4.1, 4.8
> Engineering = STABILIZING
> AI Runtime = DEFERRED
> Score = 48/54 PINNED        # until agents close criteria with evidence
> ```
>
> **Governance freeze (DEC-151):** No organizational redesign, deployment-topology DECs superseding DEC-149, or criterion rewrites except completing hard OPEN **3.7 / 3.9 / 4.1 / 4.8** with field evidence, plus bugfixes / evidence crumbs that do not change architecture or supersede DEC-149/150. Forbidden without ARB reverse: new deploy topology, reopening GHCR as Phase 0 gate, inventing ARB PASS on **4.1/4.8**.
>
> **Frozen stack (reaffirm):** [DEC-149](decisions/DEC-149-CANONICAL-DEPLOY-RAILWAY-VERCEL.md) Railway+Vercel canonical deploy · [DEC-150](decisions/DEC-150-STAGE-6-GHCR-POST-DEC-149.md) Option B Stage 6 GHCR retired · [DEC-151](decisions/DEC-151-PHASE-0-GOVERNANCE-FREEZE.md) governance freeze. **Hard OPEN ⬜:** **3.7**, **3.9**, **4.1**, **4.8** only.
>
> ### Coordination map — three freeze-compliant workstreams (2026-08-02)
>
> | Stream | Criterion | Owner | Mandate | Close rule |
> |--------|-----------|-------|---------|------------|
> | **A** | **3.9** CI GREEN (DEC-149 topology) | DevOps / Validation | Tip Stages 1–5 same-run field-fix + retain Railway/Vercel deploy evidence; **no** Stage 6 GHCR | Evidence-only; 3.11 CONDITIONAL does **not** auto-close |
> | **B** | **3.7** Stage 7 E2E | DevOps / Backend | Playwright path with real backend services; decoupled from GHCR Stage 6 | Do **not** fake local green as CLOSE |
> | **C** | **4.1 / 4.8** ARB evidence pack | ARB / OpenCode | Pack ready: [`ARB_PHASE0_4_1_4_8_EVIDENCE_PACK.md`](ARB_PHASE0_4_1_4_8_EVIDENCE_PACK.md) — **READY FOR ARB** | ARB returns PASS/FAIL only — **No invent PASS** / not CLOSED |
>
> **Sprint success = number of exit criteria CLOSED, not number of stories completed.**
> **Rule: No work accepted unless it directly closes a criterion from this checklist.**

---

## Current Verdict

**Phase 0 = NO-GO** (EOS ARB **4.1/4.8**; CI GREEN under DEC-149 topology **3.9** not met; Stage 7 E2E **3.7** OPEN; CI-09 / **3.11 CLOSED CONDITIONAL** — does not clear Phase 0)

Blocked on: **CI GREEN not met** (**3.9** redefined post–DEC-150 B — Stages 1–5 + Railway/Vercel deploy evidence; **does not** require Stage 6 GHCR), Stage 7 E2E **3.7** (no real services — **not** GHCR-dep), EOS **ARB** re-audit. **CI-08 / Stage 6 GHCR publish retired as Phase 0 gate** (DEC-150 Option B Accepted; residual GHCR 403 = legacy/non-blocking). CI-09 / **3.11 CLOSED CONDITIONAL** (DEC-149a; FE Git-primary; staging deferred). R-14 Railway **2.3 CLOSED CONDITIONAL** (multi-tenant live split residual). Security **1.5** / CI GREEN path residuals unchanged.

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
| 3.5 | Stage 5: Security Scan green | pip-audit (named ignore only), Bandit, Gitleaks, Semgrep residual-only | ✅ VERIFIED/CLOSED **CONDITIONAL** — Arch PASS_CONDITIONAL + Validation PASS_CONDITIONAL @ `5d558af` / pin `a6488f2` (DEC-147a); CI Stage 5 + Security Scan SUCCESS @ `c842245` (`30704321096` / `30704321107`); ecdsa named ignore (DEC-057/090/098); Semgrep residual **11** alembic (DEC-105); residual: *post-align Security Scan pip-audit field-verify PENDING until tip containing `fa266b5` is pushed*; does **not** auto-close **3.8**; DEC-085 untouched; Orchestrator 2026-08-01; do **not** claim Production GO / CI GREEN / finding-zero / unconditional CLOSED |
| 3.6 | Canonical deploy validation (Railway+Vercel) — *was Stage 6 GHCR Docker Build+Push* | Live deploy evidence under DEC-149 topology (not GHCR `:latest`/SHA push) | ✅ **CLOSED — SUPERSEDED** (DEC-150 **Option B** Accepted) — Stage 6 GHCR publish **no longer** a Phase 0 required capability after DEC-149. Deploy validation evidence lives at **3.11** / CI-09 (DEC-149a CLOSED CONDITIONAL @ `c3507ed` / [30723120473](https://github.com/ragheeda-boop/SalesOS/actions/runs/30723120473)). Traceability: DEC-150 B + DEC-149. Residual field GHCR 403 @ `30721601875` = **legacy/non-blocking** (not a close gate). Do **not** claim field GHCR green / Production GO / full CI GREEN. Companion [`decisions/DEC-150-STAGE-6-GHCR-POST-DEC-149.md`](decisions/DEC-150-STAGE-6-GHCR-POST-DEC-149.md) |
| 3.7 | Stage 7: E2E green | Playwright specs PASS with real backend services | ⬜ OPEN — CI e2e job has no real backend services. **Reframe (DEC-150 B):** no longer Stage-6-GHCR-dep; Stage 6 GHCR quarantined; E2E may run after Stages 1–5 when services exist. Do **not** fake local green as 3.7 CLOSE |
| 3.8 | Full pipeline: CI GREEN (code path) | Stages 1–5 all green on same run | ✅ VERIFIED/CLOSED **CONDITIONAL** — tip field-verify cleared @ `5fafbe9` / [30724762973](https://github.com/ragheeda-boop/SalesOS/actions/runs/30724762973): Stages 1–5 all **SUCCESS** (includes Stage 4 xdist fix `3547177`); prior DEC-148a residual PENDING cleared. Overall CI workflow still **failure** (Stage 7 only → **3.7**). Does **not** auto-close **3.7**; DEC-085 untouched; do **not** claim Stages 1–7 / Production GO / unconditional CLOSED |
| 3.9 | Full pipeline: CI GREEN (DEC-149 topology) | Stages 1–5 same-run green **and** Deploy Production (Railway+Vercel) evidence — **does not** require Stage 6 GHCR / Stages 1–7 GHCR publish | ✅ VERIFIED/CLOSED **CONDITIONAL** (DEC-152) — tip `5fafbe9`: CI Stages 1–5 same-run **SUCCESS** [30724762973](https://github.com/ragheeda-boop/SalesOS/actions/runs/30724762973); Deploy Production **SUCCESS** [30724762967](https://github.com/ragheeda-boop/SalesOS/actions/runs/30724762967) (Railway + Health Gate + Vercel FE); Security Scan **SUCCESS** [30724762982](https://github.com/ragheeda-boop/SalesOS/actions/runs/30724762982); Stage 6 **SKIPPED** (quarantined DEC-150 B). Residuals: *overall CI red on Stage 7 (**3.7** OPEN); FE Git-primary (3.11); staging deferred*. Does **not** close **3.7** / invent **4.1/4.8**. Companion [`decisions/DEC-152-CRITERION-3-9-CI-GREEN-TOPOLOGY-FIELD-VERIFY.md`](decisions/DEC-152-CRITERION-3-9-CI-GREEN-TOPOLOGY-FIELD-VERIFY.md). Do **not** claim Production GO / Stages 1–7 green / unconditional CLOSED |
| 3.10 | CI-08 GHCR 403 resolved — *retired as Phase 0 exit* | N/A — Stage 6 GHCR push SUCCESS no longer required (was DEC-104 Option A) | ✅ **CLOSED — SUPERSEDED** (DEC-150 **Option B** Accepted) — CI-08 mandatory GHCR publish retired as Phase 0 exit criterion. Field residual GHCR 403 @ [`30721601875`](https://github.com/ragheeda-boop/SalesOS/actions/runs/30721601875) = **legacy/non-blocking** tech debt (not ops close gate). Traceability: DEC-150 B + DEC-149. Do **not** claim field GHCR green. Companion [`decisions/DEC-150-STAGE-6-GHCR-POST-DEC-149.md`](decisions/DEC-150-STAGE-6-GHCR-POST-DEC-149.md) |
| 3.11 | CI-09 deploy path (Railway+Vercel; was VPS SSH) | Canonical deploy functional under accepted topology | ✅ VERIFIED/CLOSED **CONDITIONAL** (DEC-149a) — Arch prior PASS + Validation PASS @ `c3507ed` / [30723120473](https://github.com/ragheeda-boop/SalesOS/actions/runs/30723120473): Railway up ✓; Health Gate HTTP 200 ✓; Vercel FE Git-primary ✓; DEC-149 §6 production names present (repo). Residuals: *FE verified via Git-primary (not Vercel CLI prod); staging deferred (single-env DEC-149); no VPS*. Canonical deploy evidence for post–DEC-150 B **3.6** supersession. Does **not** auto-close **3.9** / **3.7**. DEC-085 untouched. Orchestrator 2026-08-02; do **not** claim Production GO / CI GREEN / unconditional CLOSED |

**Owner:** DevOps/SRE Lead  
**Reference:** `SPRINT_05_DELIVERY_BOARD.md`, `12_CI_CATALOG.md`, DEC-104

---

### 4. EngineeringOS Audit Pass

| # | Criterion | Evidence Required | Status |
|---|-----------|-------------------|--------|
| 4.1 | All B1–B7 findings resolved | ARB re-audit returns PASS | ⬜ **READY FOR ARB** — evidence pack [`ARB_PHASE0_4_1_4_8_EVIDENCE_PACK.md`](ARB_PHASE0_4_1_4_8_EVIDENCE_PACK.md); v3.1/DEC-142 corrections assembled; **not CLOSED**; ARB must return PASS or FAIL only — **do not invent** |
| 4.2 | Fingerprint matches pinned commit | Alembic head, framework versions, structural counts verified | ✅ VERIFIED/CLOSED — Arch PASS + Validation PASS (light) @ `637d051` (DEC-142a); re-measure pin `9fa8e9f`; Alembic head `a4f7c29e1b80`; FastAPI `>=0.136.0,<0.142.0`; migrations **69**; DEC-085 untouched; Orchestrator 2026-08-01; do **not** claim Production GO / CI GREEN |
| 4.3 | No invented surfaces | All cataloged API/Module paths exist in repo | ✅ VERIFIED (ARB 2026-08-01; B4 confirmed; filesystem audit PASS) |
| 4.4 | EvidenceLevel justified | Counts use measured methods, not narrative | ✅ VERIFIED/CLOSED — Arch PASS + Validation PASS (light) @ `637d051` (DEC-142a); EvidenceLevel **Measured** (methods in `23` + `.engineering/measure_fingerprint.py`); not ARB “Repository Verified”; DEC-085 untouched; Orchestrator 2026-08-01; do **not** claim Production GO / CI GREEN |
| 4.5 | `.engineering/` committed to git | Not untracked | ✅ VERIFIED/CLOSED — Arch PASS + Validation PASS (light: 33 tracked, 0 untracked; DEC-085 untouched) @ `5b2e4c2` (DEC-140a); pin residual cleared by DEC-142a (**4.2/4.7 CLOSED**); Orchestrator 2026-08-01; do **not** claim Production GO / CI GREEN |
| 4.6 | Lock protocol verified | `21_RUNTIME_STATE.json` mirrors `22_FILE_LOCKS.json` | ✅ VERIFIED (ARB 2026-08-01; 21 mirrors 22; bootstrap lock released) |
| 4.7 | Staleness protocol active | Fingerprint re-validated at current HEAD | ✅ VERIFIED/CLOSED — Arch PASS + Validation PASS (light) @ `637d051` (DEC-142a); Revalidation **Active**; `measure_fingerprint.py` + `23.comparison_protocol`; re-validated at tip `9fa8e9f`; DEC-085 untouched; Orchestrator 2026-08-01; do **not** claim Production GO / CI GREEN |
| 4.8 | Independent ARB re-audit = PASS | New validation report with no CRITICAL findings | ⬜ **READY FOR ARB** — same pack [`ARB_PHASE0_4_1_4_8_EVIDENCE_PACK.md`](ARB_PHASE0_4_1_4_8_EVIDENCE_PACK.md); new independent report **missing** until ARB authors it; **not CLOSED**; ARB must return PASS or FAIL only — **do not invent** |

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
| 3. CI/CD Green | 11 | 9 | 0 | 2 |
| 4. EOS Audit Pass | 8 | 6 | 0 | 2 |
| 5. Capability Drift | 4 | 4 | 0 | 0 |
| 6. ADR Drift | 5 | 5 | 0 | 0 |
| 7. DB Schema | 6 | 6 | 0 | 0 |
| 8. Engineering Stability | 4 | 4 | 0 | 0 |
| 9. ADR-036 Applied | 4 | 4 | 0 | 0 |
| **TOTAL** | **54** | **48** | **0** | **5** |

**Scoreboard honesty (2026-08-02):** Phase 0 pin **46/54 → 48/54** (DEC-150 Option B closes **3.6** / **3.10** as **CLOSED — SUPERSEDED**; not field GHCR green). RLS cluster Open **1** = **2.3** CLOSED CONDITIONAL multi-tenant residual tracked as scoreboard open (criterion row stays ✅ CONDITIONAL — **not** a hard ⬜; do **not** fake unconditional CLOSE). Hard OPEN ⬜ rows = **4** (**3.7**, **3.9**, **4.1**, **4.8**). Cluster Open cells (1+2+2=5) matches TOTAL Open **5** (prior 2.3 arithmetic debt absorbed). CI-08 / Stage 6 GHCR no longer Blocked. **GOVERNANCE FROZEN** ([DEC-151](decisions/DEC-151-PHASE-0-GOVERNANCE-FREEZE.md)) — **score PINNED 48/54** until agents close hard OPEN with evidence (orchestration: PARALLEL EXECUTION — FREEZE COMPLIANT). **Phase 0 remains NO-GO. No Production GO. No CI GREEN.**

---

## Remaining — Cursor BLOCKED inventory (2026-08-02, post DEC-151 GOVERNANCE FROZEN)

**GOVERNANCE FROZEN** ([DEC-151](decisions/DEC-151-PHASE-0-GOVERNANCE-FREEZE.md)). No Phase 0 criterion is Cursor-closeable without ARB invent (EOS), E2E services work (**3.7**), tip field-verify (**3.9** / **3.8** residual), or human push. **3.6 / 3.10 CLOSED — SUPERSEDED** (DEC-150 Option B). CI-09 / **3.11 CLOSED CONDITIONAL** (DEC-149a). Optional contract-test expansion / Jest 30 = PARALLEL backlog only. DEC-085 untouched. **No fake CLOSE. No Phase 0 COMPLETE. No Production GO. No CI GREEN.**

| # | Criterion | Owner | Block class | Why blocked / next action |
|---|-----------|-------|-------------|---------------------------|
| 3.7 | Stage 7 E2E green | DevOps / Backend | **E2E services** | Playwright needs real backend services; **decoupled from GHCR Stage 6** (DEC-150 B); do not fake local green as 3.7 CLOSE |
| 3.9 | CI GREEN (DEC-149 topology) | DevOps / Validation | **tip field-verify** | Needs tip Stages 1–5 same-run + retained Railway/Vercel deploy evidence; **does not** require Stage 6 GHCR; 3.11 CONDITIONAL does not auto-close 3.9 |
| 4.1 | B1–B7 findings resolved | OpenCode / **ARB** | **ARB — READY FOR ARB** | Pack [`ARB_PHASE0_4_1_4_8_EVIDENCE_PACK.md`](ARB_PHASE0_4_1_4_8_EVIDENCE_PACK.md); ARB returns PASS/FAIL only — **do not invent** / **not CLOSED** |
| 4.8 | Independent ARB re-audit = PASS | OpenCode / **ARB** | **ARB — READY FOR ARB** | Same pack; new report required, no CRITICAL — **do not invent** / **not CLOSED** |
| 3.8 residual | tip Stages 1-5 same-run | Validation / push | **push field-verify** | Criterion **CLOSED CONDITIONAL** (DEC-148a); prior `d1dcce4` / `30720732268` Stage 2 mypy FAILURE; tip Stages 1-5 same-run PENDING field-verify; CONDITIONAL stands; gates **3.9** |
| 3.5 / 1.5 residual | Security Scan pip-audit post-align | Validation / push | **push field-verify** | Criteria **CLOSED CONDITIONAL**; PENDING push tip containing `fa266b5` — field-verify poetry export + 1 ignored (ecdsa); does **not** auto-close **3.8** |

Adjacent non-blocking residuals: **8.3** tip `test-architecture` PENDING push `868a98c`; **8.2** at-scale soak; **2.3** multi-tenant live split; legacy GHCR 403 (retired Phase 0 gate).

---

## Blocked Items (cannot proceed without external action)

| Item | Blocked By | Action Needed |
|------|-----------|---------------|
| CI-08 GHCR 403 (mandatory Phase 0) | **GOVERNANCE COMPLETED** (DEC-150 Option B) | Stage 6 GHCR publish retired as Phase 0 gate. Residual field 403 = legacy/non-blocking. No ops GHCR fix required for Phase 0 exit. |
| CI-09 (criterion 3.11) | **CLOSED CONDITIONAL** (DEC-149a) | Deploy 30723120473 @ c3507ed SUCCESS; FE Git-primary; staging deferred; no VPS. Residual for unconditional: optional Vercel CLI + staging when provisioned. No Production GO. |
| R-14 multi-tenant residual (non-blocking for 2.3 CONDITIONAL) | Second-tenant fixture (prefer staging) | Optional: re-run Slice E differential for unconditional PASS |
| 1.5 post-align Security Scan pip-audit (non-blocking for 1.5 CONDITIONAL) | Push tip containing `fa266b5` | Field-verify Security Scan pip-audit SUCCESS with poetry export + 1 ignored (ecdsa) — does **not** upgrade to unconditional CLOSED until observed |
| 8.3 tip `test-architecture` (non-blocking for 8.3 CONDITIONAL) | Push tip containing `868a98c` | Field-verify Stage 5 `test-architecture` SUCCESS — does **not** upgrade to unconditional CLOSED until observed |
| 8.2 at-scale soak (non-blocking for 8.2 CONDITIONAL) | Live soak at `max_parallel_workers=8` | Concurrent-writer soak at worker ceiling — does **not** upgrade to unconditional CLOSED until field-proven |
| 3.5 post-align Security Scan pip-audit (non-blocking for 3.5 CLOSED CONDITIONAL) | Push tip containing `fa266b5` | Field-verify Security Scan pip-audit SUCCESS with poetry export + 1 ignored (ecdsa) — same residual as 1.5 DEC-128a; does **not** upgrade to unconditional CLOSED until observed; does **not** auto-close **3.8** |
| 3.8 tip Stages 1-5 same-run (non-blocking for 3.8 CLOSED CONDITIONAL) | Push tip containing `14fce5f` (done: `d1dcce4`) + mypy fix | Prior: Stage 1 SUCCESS / Stage 2 mypy FAILURE @ `30720732268`; tip Stages 1-5 same-run PENDING field-verify; CONDITIONAL stands; gates **3.9** (topology CI GREEN — no GHCR) |
| EOS **4.1** / **4.8** | Independent ARB (**READY FOR ARB**) | Evidence pack ready; ARB returns PASS/FAIL only — Cursor must **not** invent ARB close |
| CI **3.7** | E2E services (not GHCR) | Decoupled from Stage 6 (DEC-150 B); park until Playwright has real backend services |

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
- `docs/program/RISK_REGISTER.md` — R-01 through R-2