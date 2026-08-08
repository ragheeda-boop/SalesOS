# DEC-100 — CI-14 Slice 3 STOP: Jest 29→30 is a silent major; no patch/minor path; audit already 0

> **Status:** **Accepted** — Slice 3 **STOPPED**; story later **CLOSED** via DEC-108 executive AC (not via Jest 30)  
> **Date:** 2026-08-01  
> **Board:** Frontend / Deps (SalesOS)  
> **Story / risk:** CI-14 / R-18 Cluster A (Jest leg)  
> **Authority:** DEC-062 plan · DEC-072 Slice 2 PASS (`240f9a8`) · DEC-035 / DEC-077 Stage 3 field **0** · session prefer patch/minor over major when audit allows  
> **Out of scope this land:** package/lock bumps · Jest 30 execute · `npm audit --force` · Next/React majors · CI-22 · Railway · backend Poetry

---

## 1. Slice 3 definition (from DEC-062)

| Field | Value |
|---|---|
| **Name** | Slice 3 — Jest ecosystem major |
| **Intent** | Upgrade Jest toolchain for Cluster A residual / modernization after CI-13 contract |
| **Explicit non-goals** | Audit’s **jest→25** / **ts-jest→27** downgrades; Next↓14; React major; `npm audit --force`; Stage 3 suite remediation (R-23 / Jest-debt — **CLOSED** DEC-077) |

DEC-062 Safe vs STOP matrix: Jest **29 → 30+** = **STOP until dedicated slice**; **→25 is STOP**.

---

## 2. Evidence gate (this session) — why STOP / no package land

| Check | Result |
|---|---|
| Tip | `240f9a8` (Slice 2 ESLint **10.8.0** PASS) |
| Lock | `jest` / `jest-environment-jsdom` **29.7.0**; `ts-jest` **29.4.12**; `next` **15.5.22** |
| Patch/minor on jest 29 line | **None** — registry latest **29.x** = **29.7.0** (already locked) |
| `npm audit --audit-level=high` (host, post Slice 1+2) | **found 0 vulnerabilities** |
| Security driver for Jest major | **Absent** — Cluster A advisories cleared by Slice 2 (eslint 10); sharp cleared by Slice 1 |
| Stage 3 contract | Field **0** failing suites (DEC-077). Jest 30 + jsdom 26 is a behavior/blast-radius major — must not risk Stage 3 green without a dedicated evidence package |
| `ts-jest` peers | **29.4.12** already peers `jest: ^29 \|\| ^30` — compatibility *possible*, not *proven* for this tree |
| Forbidden avoided | No `--force`; no jest→25; no Next/React bump; no lock churn |

Preferring safe patch/minor over major when audit allows → **no executable bump remains inside jest 29**. A Jest **30** land would be a **silent major** without a named evidence package — STOP.

---

## 3. Decision

**STOP** CI-14 Slice 3 execution.

- Do **not** bump `jest`, `jest-environment-jsdom`, or `ts-jest`.  
- Do **not** refresh `package-lock.json` for Slice 3 in this land.  
- Do **not** start CI-22 / backend deps / Railway.  
- Leave CI-14 **IN PROGRESS / OPEN** (Slice 1 PASS; Slice 2 PASS; Slice 3 BLOCKED).  
- **R-18:** residual **high npm advisories cleared** (host `npm audit` **0** after Slice 1+2) → mark **Closed** for advisory residual. Optional Jest 30 modernization is **not** an R-18 blocker.

---

## 4. Next executable (when authorized)

Authorize a **dedicated Slice 3 evidence package** before any lock change:

| Gate | Requirement |
|---|---|
| Target pins | `jest` + `jest-environment-jsdom` **^30.4** (floor named, e.g. **30.4.2**); keep `ts-jest` **^29.4.12** (peers jest 30) **or** prove a later ts-jest if required |
| Next alignment | Stay on **next 15.5.x**; do **not** switch to `next/jest` createJestConfig unless separately planned (known Jest 30.1+ typing friction) |
| Config | Review `jest.config.js` / setup / custom environment for Jest 30 + JSDOM 26 deltas (`testPathPatterns`, matcher aliases, DOM behavior) |
| Evidence | Docker Linux `npm ci` + full `npm test` (Stage 3 equivalent): **0** failing suites / no new failures vs DEC-077 field green; Types/Lint unchanged |
| Forbidden | `--force`; jest→25; ts-jest→27; Next↓14; React major |

**Alternate (executive):** revise CI-14 AC to **CLOSED** without Jest major — security modernization complete (sharp + eslint 10; audit 0); Jest 30 becomes optional tech-debt backlog.

**Executed:** **DEC-108** Accepted — CI-14 **CLOSED** on revised AC; Slice 3 remains **STOPPED** (no Jest lock land).

---

## 5. Validation

| Check | Result |
|---|---|
| Package / lock changes | **None** |
| Host `npm audit --audit-level=high` | **0** vulnerabilities |
| Label | **light validated** (audit + registry version probe); Stage 3 suite **not** re-run (no dep change) |

**CI GREEN not met** (other gates). Whole-pipeline green not claimed. Stage 3 field **0** preserved (no Jest bump).
