# DEC-138 — ADR-032/0032 naming unification (Phase 0 criterion 6.4)

> **Status:** **Accepted** — Criterion **6.4 VERIFIED/CLOSED** via DEC-138a (Arch+Val PASS @ `8a3c92e`)  
> **Date:** 2026-08-01  
> **Board:** Backend Lead / ADR Drift (SalesOS) — api-worker land + Orchestrator CLOSE  
> **Story / risk:** Phase 0 Exit Criterion **6.4** · ADR Drift naming drift (registry ADR-032 vs filename ADR-0032)  
> **Authority:** PHASE_0_EXIT_CHECKLIST §6.4 · DEC-138a · ARB review protocol  
> **Out of scope this land:** ADR-036 multi-index (6.5) · inventing Accepted on ADR-032 · submodule file rename · auth/CSRF weaken · DEC-085 · Production GO · CI GREEN

---

## 1. Decision

Resolve criterion **6.4** by **unifying on registry ID ADR-032** (checklist: “Single naming convention across `docs/adr/` and `engineering-os/adr/`”) — not by inventing a second ADR body, and not by renaming the submodule file this land.

| Pin | Value |
|---|---|
| Evidence required | Single naming convention across `docs/adr/` and `engineering-os/adr/` |
| Observation | Index ID `ADR-032` vs body/title/filename `ADR-0032`; index Status Accepted vs file Proposed; date 2026-07-10 vs file 2026-07-17 |
| Disposition | Canonical ID **ADR-032**; `ADR-0032` = historical alias; product-root naming bridge + index File/Status/date honesty |
| Files | `docs/adr/0032-widget-sdk-reconciliation.md` · `docs/adr/index.md` |
| Criterion state | **VERIFIED/CLOSED** (DEC-138a) |

### Gate definition (honest)

| Check | Pass? |
|---|---|
| Registry / citation ID is **ADR-032** (not a parallel ADR-0032 decision) | **Yes** |
| `docs/adr/0032-widget-sdk-reconciliation.md` exists and declares Alias ADR-0032 | **Yes** |
| Index File column points at product-root bridge; body path documented | **Yes** |
| Index Status matches body header (**Proposed**) — no invented Accepted | **Yes** |
| Submodule filename `ADR-0032-*` retained as documented alias (no rename) | **Yes** |
| DEC-085 / auth untouched | **Yes** |
| `.engineering/27_ADR_INDEX.md` conflict #10 re-pin | **Residual** — tree untracked (criterion **4.5**); non-blocking for 6.4 |

**Not claimed:** Production GO · CI GREEN · Phase 0 exit · closing 6.5 · ADR-032 Accepted · submodule rename.

---

## 2. Alternatives considered

| Option | Verdict |
|---|---|
| (a) Rename `engineering-os/adr/ADR-0032-*` → `ADR-032-*` in submodule | Deferred — submodule pointer + citation churn; dirty unrelated `capability-registry.yaml`; docs-only land preferred |
| (b) Change registry ID to ADR-0032 to match filename | Rejected — breaks index series ADR-025..035 (`ADR-NNN` 3-digit) and peers ADR-001/003/012 |
| (c) Leave dual IDs undocumented | Rejected — fails 6.4 |
| (d) Duplicate full ADR body under `docs/adr/` | Rejected — two sources of truth |
| (e) Naming bridge + alias + index File/Status/date align | **Approved** — unifies convention without inventing Accepted or submodule rename |

---

## 3. Validation

| Check | Result |
|---|---|
| `docs/adr/0032-widget-sdk-reconciliation.md` exists · ID ADR-032 · Alias ADR-0032 | **Yes** |
| `engineering-os/adr/ADR-0032-widget-sdk-reconciliation.md` exists · title ADR-0032 · Status Proposed | **Yes** (`Test-Path`) |
| Index ID ADR-032 · Status Proposed · date 2026-07-17 · File → docs/adr bridge | **Yes** (this land) |
| Auth / DEC-085 | **Untouched** |
| Label | **light validated** (filesystem + index/bridge naming; no full CI / no Production GO) |

**Production GO not claimed. CI GREEN not met.** Closed via DEC-138a after Arch+Val PASS.

---

## 4. Records

- Phase 0 criterion **6.4** → **VERIFIED/CLOSED** (DEC-138a)
- Phase 0 **32/54 → 33/54**
- ADR Drift Complete **3 → 4** / Open **2 → 1**
- ADR Drift residual: **6.5** (036 all indexes) still OPEN
- EOS **4.5** / `.engineering/` re-pin of `27_ADR_INDEX.md` (conflicts #4/#5/#10 narrative) = follow-on
- **Not claimed:** Production GO · CI GREEN · Phase 0 exit

---

## 5. Evidence Package

| ID | Artifact | Location |
|----|----------|----------|
| EV-001 | Naming bridge (ADR-032 + Alias ADR-0032) | `docs/adr/0032-widget-sdk-reconciliation.md` |
| EV-002 | Canonical body (filename ADR-0032; Status Proposed) | `engineering-os/adr/ADR-0032-widget-sdk-reconciliation.md` |
| EV-003 | Index naming + Status/date align | `docs/adr/index.md` |
| EV-004 | This DEC | `docs/program/decisions/DEC-138-CRITERION-6-4-ADR-032-NAMING.md` |

---

## 6. Rollback

| Step | Action |
|------|--------|
| 1 | Revert land commit (bridge + index + DEC-138 program crumbs) |
| 2 | No auth/DB behavior to undo |
| Expected impact | 6.4 returns OPEN (ADR-032 vs ADR-0032 dual naming) |

---

## 7. Risk

| Surface | Level | Note |
|---------|-------|------|
| Readers still cite ADR-0032 only | LOW after land | Alias documented; future submodule rename optional |
| Index was Accepted; now Proposed | LOW | Honesty vs file header; D-016 Approved ≠ ADR Accepted |
| Overclaim Production GO / CI GREEN | LOW | 6.4 CLOSED does not imply Phase 0 GO |

---

## 8. Architecture next?

| Question | Recommendation |
|---|---|
| Close 6.4? | **Done** — DEC-138a @ Arch+Val PASS on `8a3c92e` |
| Next PARALLEL | **6.5** (ADR-036 all indexes) after ADR-036 body + `27_ADR_INDEX`; optional submodule rename ADR-0032→ADR-032 later |
| Do not | Invent Accepted · claim Production GO / CI GREEN · close 6.5 without evidence |
