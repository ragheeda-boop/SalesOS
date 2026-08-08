# DEC-142 — EOS fingerprint re-measure + EvidenceLevel Measured (Phase 0 criteria 4.2 / 4.4 / 4.7)

> **Status:** **VERIFIED/CLOSED** via DEC-142a (Arch PASS + Validation PASS light @ `637d051`)  
> **Date:** 2026-08-01  
> **Board:** Backend Lead / EOS Audit (SalesOS) — api-worker land + Orchestrator CLOSE  
> **Story / risk:** Phase 0 Exit Criteria **4.2** · **4.4** · **4.7**  
> **Authority:** PHASE_0_EXIT_CHECKLIST §4.2 / §4.4 / §4.7 · DEC-140 / DEC-141 residuals · ADR-036 Engineering Spec layer  
> **Out of scope this land:** ARB re-audit (4.1/4.8) · Eng Stability 8.1–8.3 · inventing SoT · auth/CSRF weaken · DEC-085 · Production GO · CI GREEN · Phase 0 exit

---

## 1. Decision

Resolve criteria **4.2**, **4.4**, and **4.7** by **re-measuring** the EOS fingerprint at tip `9fa8e9f`, **re-pinning** `.engineering/` headers, upgrading **EvidenceLevel Heuristic → Measured** (methods recorded; not ARB “Repository Verified”), and activating the **staleness protocol** via `.engineering/measure_fingerprint.py`.

| Pin | Value |
|---|---|
| Measurement tip | `9fa8e9f` / `9fa8e9fc4536d02a1f6a081f9b5bf49c6f59d56e` |
| Prior pin | `c89025a` (46 commits behind) |
| Alembic head (parsed + Docker) | `a4f7c29e1b80` (single head) |
| Migration files | **69** |
| FastAPI constraint | `>=0.136.0,<0.142.0` |
| Tracked files raw / filtered | **3252** / **3241** |
| EvidenceLevel | **Measured** |
| Revalidation | **Active (DEC-142)** |
| Criterion state | **VERIFIED/CLOSED** (DEC-142a) |

### Gate definition (honest)

| Check | Pass? |
|---|---|
| Fingerprint SHA == measurement tip | **Yes** — `23` + headers pin `9fa8e9f` |
| Alembic head verified at pin | **Yes** — parse + `docker compose exec backend alembic heads` → `a4f7c29e1b80 (head)` |
| Framework constraint matches `pyproject.toml` | **Yes** — FastAPI `>=0.136.0,<0.142.0` |
| Structural counts re-measured with recorded methods | **Yes** — see `23` + `measure_fingerprint.py` |
| EvidenceLevel justified (not narrative Heuristic) | **Yes** — **Measured** with methods; **not** “Repository Verified” |
| Staleness protocol active | **Yes** — script + `comparison_protocol` + Revalidation Active |
| DEC-085 / auth untouched | **Yes** |
| Independent ARB re-audit PASS | **No** — residual **4.1** / **4.8** |
| `engineering-os/` submodule clean | **No** — residual **8.1** (dirty `kernel/capability-registry.yaml`) |

**Not claimed:** Production GO · CI GREEN · Phase 0 exit · ARB PASS · closing 8.x / 4.1 / 4.8.

---

## 2. Alternatives considered

| Option | Verdict |
|---|---|
| (a) Docs-only checklist note without re-measure | Rejected — 4.2 requires verified counts/head |
| (b) Claim “Repository Verified” | Rejected — ARB B7 overclaim; needs 4.1/4.8 |
| (c) Re-pin headers only; leave stale head `c9f4…` | Rejected — agents would target wrong Alembic head |
| (d) Claim VERIFIED/CLOSED in this land | Rejected at land — Arch+Val + Orchestrator gate (CLOSED via DEC-142a) |
| (e) Re-measure + Measured + Active protocol + critical catalog head fix | **Approved** |

---

## 3. Validation

| Check | Result |
|---|---|
| Host measure script | `python .engineering/measure_fingerprint.py` (and pre-land `.tmp_eos_fingerprint_measure.py`) → tip facts |
| Docker Alembic | `alembic heads` → `a4f7c29e1b80 (head)` |
| Auth / DEC-085 | **Untouched** |
| Label | **light validated** (measured methods + Docker heads; no full CI / no Production GO) |

**Production GO not claimed. CI GREEN not met.**

---

## 4. Records

- Phase 0 criteria **4.2** / **4.4** / **4.7** → **READY FOR REVIEW** (this DEC) → **CLOSED** (DEC-142a)
- Phase 0 **36/54 → 39/54**; EOS Audit Complete **3 → 6** / Open **5 → 2**
- Residuals: **4.1** / **4.8** ARB · Eng Stability **8.1–8.3** · CI-08/CI-09 ops
- Historical ARB audit `32_EOS_VALIDATION_AUDIT.md` left intact (do not rewrite FAIL record)
- **Not claimed:** Production GO · CI GREEN · Phase 0 exit

---

## 5. Evidence Package

| ID | Artifact | Location |
|----|----------|----------|
| EV-001 | Fingerprint | `.engineering/23_PROJECT_FINGERPRINT.json` |
| EV-002 | Measure script (staleness protocol) | `.engineering/measure_fingerprint.py` |
| EV-003 | Header re-pin + critical catalog head | `.engineering/**` (excl. historical `32`) |
| EV-004 | This DEC | `docs/program/decisions/DEC-142-CRITERION-4-2-4-4-4-7-FINGERPRINT-REPIN.md` |
| EV-005 | Checklist / board / DAG crumbs | `PHASE_0_EXIT_CHECKLIST.md` · `SPRINT_05_DELIVERY_BOARD.md` · `EXECUTION_DAG.md` · `DECISION_LOG.md` |

---

## 6. Rollback

| Step | Action |
|------|--------|
| 1 | Revert land commit |
| 2 | Pin returns to heuristic `c89025a`; EvidenceLevel Heuristic |
| Expected impact | 4.2 / 4.4 / 4.7 return OPEN |

---

## 7. Risk

| Surface | Level | Note |
|---------|-------|------|
| Land commit advances HEAD past pin `9fa8e9f` | LOW | Expected for docs lands; protocol = re-measure when material drift |
| Catalog prose not fully regenerated | LOW | Critical Alembic head/count paths updated; fingerprint is machine SoT |
| Overclaim Repository Verified / CLOSED | LOW | EvidenceLevel = Measured only; CLOSED via DEC-142a after Arch+Val; not ARB Repository Verified |

---

## 8. Architecture next?

| Question | Recommendation |
|---|---|
| Close 4.2 / 4.4 / 4.7? | **Done** — Arch PASS + Validation PASS (light) @ `637d051` → Orchestrator DEC-142a |
| Next PARALLEL | EOS **4.1/4.8** ARB · Eng Stability **8.1–8.3** |
| Do not | Claim Phase 0 GO · CI GREEN · invent ARB PASS · weaken auth / DEC-085 |
