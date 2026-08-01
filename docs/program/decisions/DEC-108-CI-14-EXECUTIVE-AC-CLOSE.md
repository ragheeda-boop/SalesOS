# DEC-108 — CI-14 executive AC close: security modernization COMPLETE; Jest 30 optional backlog

> **Status:** **Accepted** — CI-14 **CLOSED** (revised AC)  
> **Date:** 2026-08-01  
> **Board:** Frontend / Deps (SalesOS / AQLIYA)  
> **Story / risk:** CI-14 / R-18  
> **Authority:** DEC-018 (story register) · DEC-062 (plan) · DEC-063 Slice 1 PASS · DEC-072 Slice 2 PASS · DEC-100 Slice 3 STOP (executive alternate) · DEC-035 / DEC-077 Stage 3 field **0** · DEC-107 (swarm: prefer READY work during GHCR wait)  
> **Out of scope this land:** package/lock bumps · Jest 30 execute · Next/React majors · `npm audit --force` · CI-08 GHCR · CI-19 reopen · CI-22 · Railway · DEC-085 `set_config`

---

## 1. Why executive close (preferred over silent Jest 30)

DEC-100 named two next executables: (a) dedicated Jest **30** evidence package, or (b) **executive AC close** without Jest major. Swarm left CI-14 PARALLEL/READY idle during GHCR wait — this DEC executes **(b)** (aligned with DEC-107 always-on READY policy).

| Signal | Evidence |
|---|---|
| R-18 high npm residual | **Cleared** — host `npm audit --audit-level=high` → **0** post Slice 1+2 (DEC-100) |
| Cluster B sharp / GHSA-f88m | **Cleared** — `overrides.sharp >=0.35.0` → lock **0.35.3** under next **15.5.22** (DEC-063 @ `435ba5d`) |
| Cluster A ESLint DoS chain | **Cleared** — eslint **10.8.0** + eslint-config-next **15.5.22** (DEC-072 @ `240f9a8`) |
| Jest 29 patch/minor | **None** — tip of **29.x** = **29.7.0** (already locked) |
| Jest 29→30 security driver | **Absent** — audit **0**; major would be modernization-only |
| Stage 3 contract | Field **0** failing suites (DEC-077); silent Jest 30 risks regression without named evidence |
| Next / React | Unchanged on **15.5.x** / **19.x** — no silent majors |

Silent Jest **29→30** without a Stage 3 **0**-fail evidence package remains **STOP** (DEC-062 / DEC-100).

---

## 2. Revised acceptance criteria (supersedes DEC-018 literal “Upgrade Jest ecosystem” as a close gate)

Original DEC-018 CI-14 register named: Upgrade ESLint · Upgrade Jest · Resolve sharp/libvips · Validate Next compatibility · Update CI security gates.

| AC (revised) | Status |
|---|---|
| Resolve sharp/libvips (≥0.35 under Next 15.5.x; no Next↓14) | **MET** (DEC-063) |
| Upgrade ESLint ecosystem to **10.x** aligned with Next 15.5 | **MET** (DEC-072) |
| Host / Stage 5 `npm audit --audit-level=high` **0** for frontend residual class | **MET** (DEC-100 evidence @ Slice 2 tip) |
| Next stays on **15.5.x**; no React silent major; no `--force` | **MET** |
| Upgrade Jest ecosystem (29→30+) | **DEFERRED** — optional tech-debt backlog; **not** required to close CI-14 |

**Decision:** Accept revised AC. **CLOSE CI-14** as security-modernization complete. Jest **30** is **not** an open CI-14 blocker and **not** an R-18 residual.

---

## 3. What remains (honest backlog — not CI-14 reopen)

| Item | Disposition |
|---|---|
| Dedicated Jest **30** evidence package (pins + Docker Stage 3 **0** fail) | Optional future story / tech-debt — authorize separately |
| CI-08 GHCR push **403** | Ops (DEC-104 Option A) — **not** CI-14 |
| Whole-pipeline **CI GREEN** | **Not met** / **not claimed** |
| Production GO / External pilot | **NO-GO** |

---

## 4. Records this land

- Board: CI-14 → **CLOSED** (DEC-108).  
- R-18: remains **Closed**; crumb text notes CI-14 executive-closed (Jest 30 backlog).  
- DEC-062 / DEC-100: story close pointer → this DEC.  
- No `package.json` / lock / workflow code changes.

---

## 5. Validation

| Check | Result |
|---|---|
| Package / lock / runtime code | **None** this land |
| Prior slice evidence reused | Slice 1+2 field/build evidence + DEC-100 audit **0** |
| Label | **docs only / light validated** (governance close on prior evidence; no new install/audit this land) |
| Whole-pipeline CI GREEN | **Not met** (CI-08) |

**DEC-085 `set_config` untouched. CI-19 CLOSED residual (DEC-105) — do not reopen.**
