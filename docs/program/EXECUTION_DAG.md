# Execution DAG — Current Program State

> **Living classification** of what is READY / BLOCKED / PARALLEL as of records close **2026-08-01** (post **DEC-120** Railway R-14 reopen).  
> Authority: evidence + `SPRINT_05_DELIVERY_BOARD.md` + `RISK_REGISTER.md` + Sprint plans + `docs/audit/ga-engineering-audit/` + Principal Audit.  
> Honesty labels: **CI GREEN not met**. **Phase 0 (DEC-008 RLS / R-14) exit = NO-GO** (DEC-086 GO **withdrawn** by DEC-120). **Production GA / External pilot = NO-GO**. STORY-02-01 **DONE** under revised AC (DEC-044 — 47 policies). **Do not reopen STORY-02-01.**

---

## Legend

| Class | Meaning |
|---|---|
| **READY** | Unblocked for execution; next eligible work |
| **BLOCKED** | Cannot proceed without named external/authorization dependency or unfinished gate |
| **PARALLEL** | May run alongside critical-path work; disjoint files / no shared gate ownership |
| **LANDED** | Code/docs on `origin/master`; may still need validation evidence |

---

## Critical path (Phase 0 → Phase 1)

```
Security P0 (historical) → RLS / STORY-02-01 (DONE, DEC-044 @ 47) ──► closed
                                               │
                                               └── Railway R-14 (S04-04) ──► REOPENED (DEC-120)
                                                     │
                                                     ▼
                                          Phase 0 (DEC-008) exit = NO-GO
                                          (production GA still NO-GO)
```

**Phase 0 (DEC-008 tenant-isolation / R-14) critical-path gate = NO-GO residual (multi-tenant).** DEC-120 A–E + tip RLS align on Railway prod (`9664e9fc`, `salesos_app`, alembic `d1a8c35e7f09`, policies **67**, E bare/wrong-tenant **0** vs owner **141221**, single-tenant caveat). Criterion **2.3 CLOSED CONDITIONAL** (DEC-126; residual *multi-tenant live split not re-proven*). Tip-align does not upgrade 2.3. STORY-02-01 **CLOSED** (DEC-044). Local/CI/compose R-14 remediations retained.

**Does not equal production GO.** ga-engineering-audit executive summary remains **production no-go**. **CI GREEN not met.**

---

## Architecture Validation verdict (2026-08-01; amended DEC-120)

| Gate | Verdict | Evidence |
|---|---|---|
| Phase 0 (DEC-008 RLS / R-14) | **NO-GO** (DEC-086 GO withdrawn) | DEC-120; Principal Audit; S04-04 REOPENED; R-14 Railway REOPENED |
| Production GA | **NO-GO** | Audit `00-EXECUTIVE-SUMMARY.md`; PRODUCTION_PLAN DoD incomplete; **CI GREEN not met** |
| External pilot | **NO-GO** | Same; no soak/browser/GA DoD evidence |
| Pilot-ready with conditions | **Not claimed** | Conditions unmet |

---

## BLOCKED

| Item | Class | Blocked on | Notes |
|---|---|---|---|
| **S04-04 / Railway R-14** | BLOCKED (critical path) | Remediation slices A–E + live re-proof (DEC-120) | Dual honesty: env ≠ runtime RLS; password rotate human/ops |
| **CI-08** GHCR 403 | BLOCKED | Packages linked to SalesOS (API) but Deploy Staging `30721601875` push still **403** (DEC-104 Option A incomplete — Actions access Write) | Also blocks primary image promote path for Railway; alternate = Railway build-from-GitHub |
| **CI-09** deploy path (Railway+Vercel) | **READY_FOR_REVIEW** | DEC-149 + production secrets + Validation PASS | Orchestrator Queue — VALIDATION_PASS 30723120473 (Railway up + health HTTP 200 + Vercel FE); recommend CLOSE / CLOSED CONDITIONAL; staging deferred; no VPS_*; **not auto-CLOSED** — P2 |
| **CI GREEN (full incl. publish)** | BLOCKED | Stage 6 GHCR push (CI-08) + Stage 7 + residual reds | Blocks production GO |
| **CI GREEN (code path)** | REPORTING ONLY | Stages 1–5 on a named run | DEC-104 interim honesty |

---

## READY (Sprint 05 / 06+ — parallel; Phase 0 still NO-GO)

| Item | Class | Why ready now | Notes |
|---|---|---|---|
| **S04-04 remediation A** | READY | Wiring commit identified | `5e7023f` introduced `app_database_url` / `APP_POSTGRES_*` consumption |
| **S04-04 remediation B** | READY (path choice) | Image promote | GHCR path BLOCKED (CI-08); alternate Railway GitHub build/redeploy |
| **S04-04 remediation A–E** | **Evidence landed** | Prod `9664e9fc` / `salesos_app` / alembic `d1a8` / policies **67** / E bare=0 | Single-tenant caveat residual; tip RLS align via owner SSH |
| **DB-05** Schema reconciliation | **COMPLETE** | Slice 0–4 CLOSED (7.1–7.5); **Slice 5a–5g COMPLETE**; **7.6 CLOSED** (DEC-130h) @ `250bcb5`; head `a4f7c29e1b80`; check exit 0; prod tip was `d1a8` / POLICY_COUNT **67** | Phase 0 DB Schema **6/6**; residual KEEP `ix_graph_nodes_search` non-blocking; prior “prod on 59” residual cleared (`c842245`) |
| **Optional Jest 30 evidence** | BACKLOG | DEC-108 deferred | STOP silent major |
| **STORY-02-02** browser/E2E | **CLOSED** (DEC-095) | Redirect AC | **CI GREEN not met** |
| **Sprint 04 Category B (B1–B7)** | **CLOSED** (COMPLETE) | DEC-110; B1–B7 CLOSED (DEC-112/114/115/116/117/118/119); live policies **59** | Does not restore Phase 0 GO (DEC-120) |
| **JWT audience consumption** | **CLOSED** (DEC-093) | 14/14 unit PASS | |
| **Contract tests expansion** | IN PROGRESS / PARALLEL | DEC-094 + DEC-106 | Park OK |

---

## DONE / closed (story AC)

| Item | Class | Notes |
|---|---|---|
| **S04-04** Railway R-14 | **REOPENED** (DEC-120) | Was CLOSED DEC-016; contradicted by Tier-1 audit |
| **R-14** Railway | **REOPENED** | Local/CI/compose retained; Railway live isolation not proven |
| **STORY-02-01** (RLS rollout) | **DONE** (revised AC) | DEC-044 @ **47**. **Do not reopen.** |
| **S04-01 / S04-05 / S04-06** | **COMPLETE** | Adversarial suites |
| **CI-16 / CI-20 / CI-19 / CI-22 / CI-14** | **CLOSED** | As previously recorded |
| **Jest-debt** / **R-23** | **CLOSED** | DEC-077 |
| **Security P0 1.3** CSRF X-API-Key | **CLOSED** (DEC-127a) | Arch+Val PASS @ `5db0756`; Phase 0 **22/54** (superseded to **24/54**) |
| **Security P0 1.5** SAST + deps | **CLOSED CONDITIONAL** (DEC-128a) | Arch PASS + Val PASS_CONDITIONAL @ `fa266b5`; residual: post-align Security Scan pip-audit field-verify PENDING; Phase 0 **23/54** (superseded to **24/54**) |
| **DB-05 7.4** companies KEEP | **CLOSED** (DEC-129a) | Arch+Val PASS @ `4aacd6d`; KEEP no DROP; head `d1a8c35e7f09`; Phase 0 **24/54** |
| **DB-05 7.6** alembic check | **CLOSED** (DEC-130h) | Arch+Val PASS @ `250bcb5` / DEC-130g; check exit 0 @ `a4f7c29e1b80`; phased 5a–5g; Phase 0 **25/54** (superseded to **26/54** by DEC-131a); do **not** claim Phase 0 GO |
| **Capability 5.4** `/api/v1/capabilities` tested | **CLOSED** (DEC-131a) | Arch+Val PASS @ `65e82cc` / DEC-131; Docker **4 passed**; DEC-085 untouched; Phase 0 **26/54** (superseded to **34/54** by DEC-139a); Capability Drift COMPLETE; do **not** claim Phase 0 GO |
| **Capability 5.1** single SoT designated | **CLOSED** (DEC-132a) | Arch+Val PASS (light) @ `8e105fe` / DEC-132; decorator framework = canonical runtime SoT (kebab); secondaries SDK/YAML/CAP-###; DEC-085 untouched; Phase 0 **27/54** (superseded to **34/54** by DEC-139a); Capability Drift COMPLETE; do **not** claim Phase 0 GO |
| **Capability 5.2** CAP-###→kebab join map | **CLOSED** (DEC-133a) | Arch+Val PASS (light) @ `81b593f` / DEC-133; `--join-map-only` exit 0; 10/30/3; DEC-085 untouched; CAP-037 refine non-blocking; Phase 0 **28/54** (superseded to **34/54** by DEC-139a); Capability Drift COMPLETE; do **not** claim Phase 0 GO |
| **Capability 5.3** SoT-oriented validate exit 0 | **CLOSED** (DEC-134a) | Arch+Val PASS (light) @ `6a98999` / DEC-134; host+Docker default exit **0**; `--legacy-equality` exit 2 diagnostic; DEC-085 untouched; INFO residuals SDK/YAML extras + unmapped CAPs; Phase 0 **29/54** (superseded to **34/54** by DEC-139a); Capability Drift COMPLETE **4/4**; do **not** claim Phase 0 GO |
| **ADR Drift 6.1** ADR-025..028 index paths | **CLOSED** (DEC-135a) | Arch+Val PASS (light) @ `4997ae4` / DEC-135; path-exists + Status Accepted; `docs/adr/index.md` File paths registered; Phase 0 **30/54** (superseded to **34/54** by DEC-139a); ADR Drift Complete **1/5** (superseded to **5/5 COMPLETE**); residual broader EOS (**4.5**); do **not** claim Phase 0 GO |
| **ADR Drift 6.2** ADR-029 phantom | **CLOSED** (DEC-136a) | Arch+Val PASS (light) @ `a1ce473` / DEC-136; Not Issued disposition @ `docs/adr/0029-number-never-issued.md` + index row; numbering gap documented; DEC-085 untouched; Phase 0 **31/54** (superseded to **34/54** by DEC-139a); ADR Drift Complete **2/5** (superseded to **5/5 COMPLETE**); residual broader EOS (**4.5**); do **not** claim Phase 0 GO |
| **ADR Drift 6.3** ADR-033/034 status | **CLOSED** (DEC-137a) | Arch+Val PASS (light) @ `bcd7aa6` / DEC-137; index Status **Proposed** matches file headers; dates → `2026-07-17`; no invented Accepted; DEC-085 untouched; Phase 0 **32/54** (superseded to **34/54** by DEC-139a); ADR Drift Complete **3/5** (superseded to **5/5 COMPLETE**); residual broader EOS (**4.5**); do **not** claim Phase 0 GO |
| **ADR Drift 6.4** ADR-032/0032 naming | **CLOSED** (DEC-138a) | Arch+Val PASS (light) @ `8a3c92e` / DEC-138; naming bridge ADR-032 + alias ADR-0032; index File/Status/date aligned (Proposed; no invented Accepted); submodule filename retained as alias; DEC-085 untouched; Phase 0 **33/54** (superseded to **34/54** by DEC-139a); ADR Drift Complete **4/5** (superseded to **5/5 COMPLETE**); residual broader EOS (**4.5**); do **not** claim Phase 0 GO |
| **ADR Drift 6.5** ADR-036 all indexes | **CLOSED** (DEC-139a) | Arch+Val PASS (light) @ `aaeaff3` / DEC-139; Status Accepted matches file header + 9.1 (not invented); `docs/adr/index.md` + `.engineering/27_ADR_INDEX.md` registered; engineering-os index N/A; DEC-085 untouched; Phase 0 **34/54** (superseded to **36/54** by DEC-141a); ADR Drift COMPLETE **5/5**; residual note superseded: **4.5 CLOSED**; **9.2 CLOSED**; do **not** claim Phase 0 GO |
| **EOS Audit 4.5** `.engineering/` committed | **CLOSED** (DEC-140a) | Arch+Val PASS (light) @ `5b2e4c2` / DEC-140; 33 tracked / 0 untracked; pin residual cleared by DEC-142a; DEC-085 untouched; Phase 0 **35/54** (superseded to **39/54** by DEC-142a); EOS Audit Complete **6/8**; residuals **4.1/4.8**; do **not** claim Phase 0 GO |
| **ADR-036 Applied 9.2** program↔engineering bridges | **CLOSED** (DEC-141a) | Arch+Val PASS (light) @ `7b618da` / DEC-141; bridges `ENGINEERING_LAYER_BRIDGE.md` ↔ `.engineering/33_PROGRAM_LAYER_BRIDGE.md` (pointers only); DEC-085 untouched; Phase 0 **36/54** (superseded to **39/54** by DEC-142a); ADR-036 Applied Complete **3/4**; residuals EOS **4.1/4.8** · Eng Stability **8.1–8.3**; do **not** claim Phase 0 GO |
| **EOS Audit 4.2/4.4/4.7** fingerprint re-pin | **CLOSED** (DEC-142a) | Arch+Val PASS (light) @ `637d051` / DEC-142; tip pin `9fa8e9f`; Alembic `a4f7c29e1b80`; EvidenceLevel **Measured**; Revalidation **Active**; script `.engineering/measure_fingerprint.py`; DEC-085 untouched; Phase 0 **36/54 → 39/54** (superseded to **40/54** by DEC-143a); EOS Audit Complete **3 → 6** / Open **5 → 2**; residuals **4.1/4.8** ARB · Eng Stability **8.2/8.3** (**8.1 CLOSED** DEC-143a); do **not** claim Phase 0 GO |
| **Eng Stability 8.1** engineering-os clean | **CLOSED** (DEC-143a) | Arch+Val PASS (light: pin `b82b9fb`, clean tree) @ `89502ef` / DEC-143; discarded malformed unreviewed `capability-registry.yaml` append (outside YAML fence); parent gitlink unchanged; no submodule push; DEC-085 untouched; Phase 0 **39/54 → 40/54** (superseded to **43/54** by DEC-146a); Eng Stability Complete **1 → 2** / Open **3 → 2** (superseded to Complete **4** / Open **0**); residual EOS **4.1/4.8**; do **not** claim Phase 0 GO |
| **Eng Stability 8.3** arch rules in CI | **CLOSED CONDITIONAL** (DEC-144a) | Arch CONDITIONAL + Val PASS_CONDITIONAL @ `868a98c` / DEC-144; independent `test-architecture` + `arch-compliance.ps1` critical; Docker **36 passed**; local **95.8%**; gh Arch Compliance success @ `30704321096`; residual: *tip `test-architecture` SUCCESS PENDING until tip containing `868a98c` is pushed*; DEC-085 untouched; Phase 0 **40/54 → 41/54** (superseded to **43/54** by DEC-146a); Eng Stability Complete **2 → 3** / Open **2 → 1** (superseded to Complete **4** / Open **0**); residual EOS **4.1/4.8**; do **not** claim Phase 0 GO / CI GREEN / unconditional CLOSED |
| **Eng Stability 8.2** agent coordination | **CLOSED CONDITIONAL** (DEC-145a) | Arch PASS_CONDITIONAL + Val PASS_CONDITIONAL @ `5bc0bf2` / DEC-145; caps (`max_parallel_workers=8`, `max_agents_total=12`, roles **4**, DEC-107 READY **2/3**); namespacing + conflict/lock rules; `.ai/` org baseline committed; light exercise DEC-107 + `21` workers; residual: *at-scale live soak at max_parallel_workers=8 not field-proven*; DEC-085 untouched; Phase 0 **41/54 → 42/54** (superseded to **43/54** by DEC-146a); Eng Stability Complete **3 → 4** / Open **1 → 0** (cluster **COMPLETE 4/4**); residual EOS **4.1/4.8**; do **not** claim Phase 0 GO / CI GREEN / unconditional CLOSED |
| **ADR-036 Applied 9.3** `.ai/` runtime deferred | **CLOSED** (DEC-146a) | Arch PASS + Val PASS (light) @ `922528f` / tip pin `1f99628` / DEC-146; org baseline ≠ Agent OS; triggers in ADR-036 + `.ai/README`; `runtime-spec.yaml` SPECIFICATION; DEC-085 untouched; Phase 0 **42/54 → 43/54**; ADR-036 Applied Complete **3 → 4** / Open **1 → 0** (cluster **COMPLETE 4/4**); residual EOS **4.1/4.8** ARB · CI **3.x** + CI-08/09; do **not** claim Phase 0 GO / CI GREEN |
| **CI/CD 3.5** Stage 5 Security Scan | **CLOSED CONDITIONAL** (DEC-147a) | Arch PASS_CONDITIONAL + Val PASS_CONDITIONAL @ `5d558af` / pin `a6488f2` / DEC-147; gh Stage 5 + Security Scan SUCCESS @ `c842245` (`30704321096` / `30704321107`); ecdsa named ignore; Semgrep **11** alembic residual; residual: *post-align Security Scan pip-audit PENDING until tip containing `fa266b5` is pushed*; does **not** auto-close **3.8**; DEC-085 untouched; Phase 0 **43/54 → 44/54**; CI/CD Complete **4 → 5** / Open **5 → 4**; do **not** claim Phase 0 GO / CI GREEN / finding-zero / unconditional CLOSED |
| **CI/CD 3.8** CI GREEN (code path) | **CLOSED CONDITIONAL** (DEC-148a) | Arch PASS_CONDITIONAL + Val PASS_CONDITIONAL @ `14fce5f` / DEC-148; local ruff 0.4.10 check+format exit 0; last push `c842245` / `30704321096` Stage 1 Lint FAILURE (6× E501) → Stages 3 BE/4 SKIPPED; residual: *tip Stages 1–5 same-run PENDING until tip containing `14fce5f` is pushed* (Stage 3/4 may still fail when unblocked); historical Stages 1–5 SUCCESS @ `7ba137b` / `30689682988` (not tip); does **not** close **3.6–3.11** / **3.9**; DEC-085 untouched; Phase 0 **44/54 → 45/54**; CI/CD Complete **5 → 6** / Open **4 → 3**; do **not** claim Phase 0 GO / CI GREEN / unconditional CLOSED |

---

## PARALLEL (safe; Phase 0 still blocked on S04-04)

| Track | Class | Justification |
|---|---|---|
| Contract tests, optional Jest 30 | PARALLEL / PARKED | Do **not** close Phase 0 rows; DEC-094/106 expansion + Jest 30 = backlog only while hard OPEN are ARB/ops |
| EOS **4.1/4.8**, CI **3.6/3.7/3.9–3.11**, tip field-verify | **BLOCKED** (Cursor) | **2026-08-02 BLOCKED inventory:** no Cursor-closeable criterion; **4.1/4.8** ARB (do not invent); **3.6/3.9/3.10** ops CI-08; **3.11** CI-09 **READY_FOR_REVIEW** (VALIDATION_PASS 30723120473 health green; Orchestrator CLOSE pending; Validation PENDING); **3.7** Stage-6-dep; **3.8** / **3.5** tip push field-verify PENDING; Phase 0 **45/54**; do **not** claim Phase 0 GO / CI GREEN / fake CLOSE |
| Owner Admin / commercial FE | PARALLEL | Must not weaken auth/CSRF/RBAC; must **not** market production GO |

**Swarm dispatch (DEC-107):** Keep agents on independent PARALLEL READY ownership while S04-04 remediation / CI-08/09 ops proceed.

---

## LANDED (master) — adjacency crumbs

| Story / item | SHA | Records status | Validation |
|---|---|---|---|
| DEC-120 Railway R-14 reopen + Principal Audit | *(this land)* | **Accepted / REOPENED** | **docs / light validated** (encodes Tier-1 audit) |
| S04-04 / DEC-016 Railway R-14 (historical close) | `7232979` | **Superseded consequence** | Infra verified; security closure contradicted |
| S04-05 / S04-06 / Category B B1–B7 COMPLETE / CI closes | tip | As prior | See board; Cat B = DEC-119 POLICY_COUNT **59** |

---

## Board progress fraction

**24/25** Complete/Closed on tracked Sprint 05 board fraction (**S04-04 REOPENED**). Adjacent closed: **Jest-debt / R-23**. **Phase 0 critical path blocked:** **S04-04 / Railway R-14**. Also blocked: CI-08 (P0 ops). CI-09 (P2 **READY_FOR_REVIEW** VALIDATION_PASS 30723120473 — Orchestrator CLOSE pending).

---

## Update rule

When a story changes READY↔BLOCKED↔COMPLETE, update this file in the same records commit as `SPRINT_05_DELIVERY_BOARD.md` / `DECISION_LOG.md`. Never claim **production GO** or **CI GREEN** without command evidence. Never reopen STORY-02-01 after DEC-044. Phase 0 (DEC-008) **GO** ≠ production GA GO — and Phase 0 GO is currently **withdrawn** (DEC-120).
