# DEC-144 — Architecture rules enforced in CI (Phase 0 criterion 8.3)

> **Status:** **Accepted** — Cursor packaging **COMPLETE** · Criterion 8.3 = **VERIFIED/CLOSED CONDITIONAL** (DEC-144a; Architecture CONDITIONAL · Validation PASS_CONDITIONAL). Residual: tip `test-architecture` SUCCESS PENDING until tip containing `868a98c` is pushed.  
> **Date:** 2026-08-01  
> **Board:** Backend Lead / Engineering Stability (SalesOS) — api-worker land  
> **Story / risk:** Phase 0 Exit Criterion **8.3** · Architecture rules enforced in CI  
> **Authority:** PHASE_0_EXIT_CHECKLIST §8.3 · DEC-143 residual · `.engineering/17_TESTING_MAP.md` · DEC-144a Orchestrator  
> **Out of scope this land:** Eng Stability **8.2** · EOS **4.1/4.8** ARB · inventing `arch-compliance.py` · CI-08/CI-09 ops · auth/CSRF weaken · DEC-085 · Production GO · CI GREEN · Phase 0 exit · unconditional CLOSED

---

## 1. Decision

Resolve criterion **8.3** by making both architecture gates **critical CI jobs** with honest artifact naming:

| Gate | Artifact (as-built) | CI job | Pre-land evidence |
|---|---|---|---|
| Backend layering / fitness | `salesos/backend/tests/test_architecture.py` | **NEW** `test-architecture` (“Stage 5: Architecture Rules”) | Docker: **36 passed** (exit 0) |
| Frontend / domain compliance | `salesos/scripts/arch-compliance.ps1` (not `.py`) | Existing `arch-compliance` | Local PASS **95.8%** ≥ 95%; gh run `30704321096` job **Stage 5: Arch Compliance = success** @ `c842245` |

Checklist evidence text corrected: `test_architecture.py` + `arch-compliance.ps1` (prior `.py` name was a docs drift — no `arch-compliance.py` in tree).

### Gate definition (honest)

| Check | Pass? |
|---|---|
| `arch-compliance.ps1` wired as critical CI job | **Yes** — already present; remains critical on builds + CI Summary |
| `test_architecture.py` independent critical CI job | **Yes** — added; no `needs:` on lint/unit (survives lint skip) |
| Local / Docker fitness green | **Yes** — Docker `poetry run pytest tests/test_architecture.py` → **36 passed** |
| Local compliance ≥ 95% | **Yes** — **95.8%** (6 medium DP-5.1 residuals; non-blocking for % gate) |
| Field-verify of new `test-architecture` job on tip | **Pending push** — prefer not push this land |
| Full CI GREEN / Production GO | **No** |
| Agent coordination at scale (8.2) | **No** — residual **8.2** |

**Not claimed:** Production GO · CI GREEN · Phase 0 exit · unconditional CLOSED · closing 8.2 / 4.1 / 4.8.

---

## 2. Alternatives considered

| Option | Verdict |
|---|---|
| (a) Docs-only close while `test_architecture` only runs inside skipped unit stage | Rejected — lint failure skips unit; architecture unenforced |
| (b) Invent `arch-compliance.py` duplicate of `.ps1` | Rejected — existing pwsh gate already green in CI |
| (c) Claim VERIFIED/CLOSED / CI GREEN this land | Rejected — Arch+Val + Orchestrator; tip field-verify pending |
| (d) Wire independent `test-architecture` + record evidence for existing `arch-compliance` | **Approved** |

---

## 3. Validation

| Check | Result |
|---|---|
| Docker narrow pytest | `docker compose exec -T backend poetry run pytest tests/test_architecture.py -v --tb=short` → **36 passed**, exit **0** |
| Local `arch-compliance.ps1` | Overall **95.8%** PASS (target 95%); 0 critical / 0 high; 6 medium DP-5.1 |
| gh corroboration (pre-existing job) | CI run `30704321096` @ `c842245` — **Stage 5: Arch Compliance = success** (overall CI still failure on other stages) |
| Auth / DEC-085 | **Untouched** |
| Label | **light validated** (Docker narrow + local ps1 + gh job success); tip `test-architecture` field-verify **not validated** until push |

**Production GO not claimed. CI GREEN not met.**

---

## 4. Records

- Phase 0 criterion **8.3** → **VERIFIED/CLOSED CONDITIONAL** (DEC-144a; Phase 0 **41/54**)
- Eng Stability Complete **2 → 3** / Open **2 → 1**
- Residual (non-blocking for 8.3 CONDITIONAL): *tip `test-architecture` SUCCESS PENDING until tip containing `868a98c` is pushed*
- Residuals (cluster): Eng Stability **8.2** · EOS **4.1** / **4.8** ARB · CI-08/CI-09 ops
- **Not claimed:** Production GO · CI GREEN · Phase 0 exit · unconditional CLOSED

---

## 5. Evidence Package

| ID | Artifact | Location |
|----|----------|----------|
| EV-001 | Independent architecture pytest job | `.github/workflows/ci.yml` → `test-architecture` |
| EV-002 | Existing compliance job (pwsh) | `.github/workflows/ci.yml` → `arch-compliance` |
| EV-003 | Fitness tests | `salesos/backend/tests/test_architecture.py` |
| EV-004 | Compliance script | `salesos/scripts/arch-compliance.ps1` |
| EV-005 | This DEC | `docs/program/decisions/DEC-144-CRITERION-8-3-ARCH-RULES-IN-CI.md` |
| EV-006 | Checklist / board / DAG crumbs | `PHASE_0_EXIT_CHECKLIST.md` · `SPRINT_05_DELIVERY_BOARD.md` · `EXECUTION_DAG.md` · `DECISION_LOG.md` |

---

## 6. Rollback

| Step | Action |
|------|--------|
| 1 | Revert land commit (workflow + docs) |
| 2 | Criterion 8.3 returns OPEN / prior residual note |
| Expected impact | Architecture fitness again only runs inside `test-backend` (skippable) |

---

## 7. Risk

| Surface | Level | Note |
|---------|-------|------|
| Tip CI field-verify pending | MED | Prefer not push; Orchestrator may keep CONDITIONAL until job success observed |
| Medium DP-5.1 FE residuals | LOW | % gate still PASS; do not invent Decision Platform GA |
| Poetry install cost on runner | LOW | Same cache key as other backend jobs |
| Overclaim unconditional CLOSED / CI GREEN | LOW | CLOSED CONDITIONAL only; tip field-verify PENDING |

---

## 8. Architecture next?

| Question | Recommendation |
|---|---|
| Close 8.3? | **CLOSED CONDITIONAL** via DEC-144a (Arch CONDITIONAL + Val PASS_CONDITIONAL); tip SUCCESS does not auto-upgrade |
| Next PARALLEL | Eng Stability **8.2** · EOS **4.1/4.8** ARB |
| Do not | Claim Phase 0 GO · CI GREEN · unconditional CLOSED · invent `arch-compliance.py` · weaken auth / DEC-085 |
