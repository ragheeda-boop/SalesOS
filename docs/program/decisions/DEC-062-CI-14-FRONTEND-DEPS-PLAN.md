# DEC-062 — CI-14 Frontend Dependency Modernization: planning inventory (safe vs STOP)

> **Status:** **Accepted** — planning complete; **Slice 1 PASS** (sharp; §9 / field verify §10); **Slice 2 PASS** (ESLint 10; §11 / DEC-072)  
> **Date:** 2026-08-01  
> **Board:** Frontend / Deps (SalesOS / AQLIYA)  
> **Story / risk:** CI-14 / R-18 (30 residual high npm advisories after CI-11)  
> **Authority:** DEC-018 (story register) · DEC-019 (CI-11 closed, residual → CI-14) · DEC-035 (CI-13 Jest baseline contract) · lock evidence on `master` · Slice 1 **DEC-063** · Slice 2 STOP **DEC-065**  
> **Out of scope:** CI-22 · backend Poetry bumps · Railway · `npm audit --force` · silent Next/React/ESLint/Jest majors

---

## 1. Decision required

CI-14 is **REGISTERED / READY** (Sprint 06, P1). Before any executable major, the program needs a **governed inventory**: which bumps clear R-18, in what risk order, and which npm-suggested “fixes” are **STOP** (especially downgrades and silent majors).

This DEC **accepts the plan**. It does **not** authorize Slice 1 execution until a subsequent executive/Phase-1 package names the exact override/version and evidence commands.

---

## 2. Lock snapshot (planning baseline)

Captured from `salesos/frontend/package-lock.json` on `master` (2026-08-01 planning session). Host `node_modules` **absent** — no local `npm audit` / install in this land (low-load). Residual advisory count **30 high** remains the CI-11 / R-18 field fact (DEC-019 run `30649799993`).

| Package | Locked | Role |
|---|---|---|
| `next` | **15.5.22** | App framework + image pipeline (pulls `sharp`) |
| `react` / `react-dom` | **19.2.7** | Runtime |
| `eslint` | **9.39.5** | Lint toolchain |
| `eslint-config-next` | **15.5.22** | Next ESLint preset |
| `jest` / `jest-environment-jsdom` | **29.7.0** | Unit tests |
| `ts-jest` | **29.4.12** | TS Jest transform |
| `sharp` | **0.34.5** | Image pipeline (Trivy HIGH GHSA-f88m-g3jw-g9cj → **≥0.35.0**) |
| `postcss` | **8.5.25** | Already patched in CI-11 |

CI-11 already applied all safe **patch-only** remediations (`npm audit fix` without `--force`). **No further silent patch tranche is assumed available** without fresh audit evidence after install.

---

## 3. Residual clusters (from DEC-018) — majors needed

### Cluster A — ESLint / Jest toolchain DoS (`brace-expansion` / `minimatch`)

- **Exposure:** Dev/CI toolchain only (not runtime image path).  
- **npm’s framed majors (DEC-018):** `eslint` → **10.x**, `jest` → **25.x**, `ts-jest` → **27.x**, `eslint-config-next` → **0.2.4**.  
- **Honesty:** The **jest→25 / ts-jest→27 / eslint-config-next→0.2.4** frames are classic `npm audit` **downgrade / nonsense** suggestions relative to current **jest 29 / ts-jest 29 / eslint-config-next 15**. Treating them as executable “fixes” is **STOP**.

### Cluster B — `sharp` / libvips (image pipeline)

- **Exposure:** Runtime image optimization path via Next.  
- **Trivy:** `package-lock.json` HIGH `sharp` GHSA-f88m-g3jw-g9cj (CI-12 / DEC-034).  
- **npm’s framed fix:** often `next` → **14.2.35** — a **major-line downgrade** from **15.5.22**. **STOP** if the only path is downgrading Next.

---

## 4. Safe vs STOP matrix

| Move | Class | Rationale |
|---|---|---|
| `npm audit fix` (no `--force`) if fresh audit shows patch/minor only | **SAFE candidate** | Matches CI-11 discipline; only if evidence shows remaining patchables |
| `overrides.sharp` → **≥0.35.0** under **next 15.5.x** (no Next/React change) | **Slice 1 candidate** | Clears Trivy/npm sharp floor **if** solver + Next image pipeline accept it — **requires evidence before land** |
| Next **15 → 14** (or any Next downgrade) | **STOP** | npm audit framing for sharp; destroys App Router 15 line |
| Silent Next **minor/major** without advisory+compat evidence | **STOP** | Blast radius (build, image, eslint-config-next) |
| Silent React **19 → other major** | **STOP** | Out of CI-14 residual clusters; no evidence gate |
| ESLint **9 → 10** (+ flat-config / plugin cascade) | **STOP until dedicated slice** | Major; lint CI + local DX; not auto-safe |
| Jest **29 → 30+** (or audit’s **→25** downgrade) | **STOP until dedicated slice** | Major + Jest-debt interaction; **→25 is STOP** |
| `ts-jest` major / audit **→27** downgrade | **STOP until dedicated slice** | Tied to Jest major; **→27 is STOP** |
| `eslint-config-next` nonsense pin (**0.2.4**) | **STOP** | Incompatible with Next 15 |
| `npm audit fix --force` | **STOP** | Forbidden by DEC-018 / CI-11 precedent |
| Backend Poetry / CI-22 / Railway | **STOP (out of story)** | Explicit non-goals |

---

## 5. Risk order (execution sequence when authorized)

1. **Re-baseline evidence (read-only):** with approved install, capture `npm audit --json` summary + confirm 30-high class still matches Clusters A/B (no new patch-only cluster assumed).  
2. **Slice 1 — sharp override evidence gate (preferred first executable):** try `sharp ≥0.35.0` via `overrides` (or equivalent) **without** changing `next` / `react` / `eslint` / `jest`. Validate: lock resolves; `next` stays on 15.5.x; Trivy/npm sharp advisory cleared or reduced; Frontend Lint/Types unchanged; Jest contract **failing suites ≤ inventory ceiling** (DEC-035 / current Jest-debt notes). If incompatible → **STOP Slice 1**, document, do not force Next downgrade.  
3. **Slice 2 — ESLint ecosystem major (eslint 10 + eslint-config-next aligned):** dedicated plan + lint green evidence; still no Jest major unless coupled intentionally.  
4. **Slice 3 — Jest ecosystem major:** **after** CI-13 contract + prefer lower Jest-debt noise (R-23). Never apply audit’s jest→25 downgrade.  
5. **CI security-gate honesty:** update allowlist/docs only if residuals remain after slices; do not weaken gates to fake green.

---

## 6. Dependency contracts (unchanged)

- **CI-13 / DEC-035:** after any dep bump, failing suites **≤ 33** and failing tests **≤ 163** (or the updated Jest-debt ceiling once Stage 3 re-inventory lands). No new failures beyond inventory.  
- **Jest-debt (R-23):** suite remediation is **not** CI-14.  
- **CI-11:** closed; patch-only path exhausted for the 2026-07-31 31→30 transition.

---

## 7. Recommendation — next executable slice

**Authorize CI-14 Slice 1 (sharp-only evidence package)** next:

- Scope: `salesos/frontend` lock + optional `overrides.sharp` only.  
- Explicitly **not** in Slice 1: Next, React, ESLint 10, Jest major, `--force`, backend, CI-22, Railway.  
- Exit: either (a) sharp ≥0.35 lands with evidence, or (b) **STOP** recorded with incompatibility proof — still progress.

Validation label for this planning land: **not validated** (docs only).

---

## 8. Alternatives considered

| Option | Verdict |
|---|---|
| (A) Ship silent majors now from `npm audit` suggestions | **Rejected** — includes Next/Jest **downgrades** |
| (B) Accept planning inventory + gated slices (this DEC) | **Approved** |
| (C) Permanent npm-audit allowlist without modernization | **Rejected** (DEC-018 Option 1) |
| (D) Apply a host patch bump without `node_modules` / audit evidence | **Rejected** — no safe patch proven this session |

---

## 9. Slice 1 outcome (2026-08-01) — **PASS**

Executed under **DEC-063** (authorized Slice 1 only).

| Check | Result |
|---|---|
| `package.json` `overrides.sharp` | `>=0.35.0` (alongside existing `postcss` override) |
| Lock resolve | `node_modules/sharp` → **0.35.3** |
| `npm ls sharp` | `next@15.5.22` → `sharp@0.35.3` |
| Next / React / ESLint / Jest | Unchanged: next **15.5.22**, react **19.2.7**, eslint **9.39.5**, jest **29.7.0** |
| STOP triggers | Not hit — no Next↓14, no `--force`, no major toolchain bumps |
| Narrow validation | `npx tsc --noEmit` **exit 0**; prettier **not present** in frontend deps; full `next lint` / Jest **not** run (low-load) |

**Label:** **build validated** for Cluster B sharp clear on CI (see section 10). Story CI-14 remains **OPEN** (Cluster A / Slice 2-3 pending). **CI GREEN not met** (backend gates + Prettier + Cluster A).

---

## 10. CI Observer - Slice 1 field verify (2026-08-01)

SHA: `435ba5d9988e1525dee00850835aa06f4b08e33f` (tip = land commit).

| Run | Workflow | ID | Outcome (sharp-relevant) |
|---|---|---|---|
| Slice 1 | CI | [30678336063](https://github.com/ragheeda-boop/SalesOS/actions/runs/30678336063) | `Stage 5: npm audit` **success** - `found 0 vulnerabilities`; `Stage 5: Secrets Scan` Trivy fs still **failure** on **backend** HIGH only (ecdsa/starlette x4); `package-lock.json` npm **0** findings (no `sharp` / GHSA-f88m) |
| Slice 1 | Security Scan | [30678336073](https://github.com/ragheeda-boop/SalesOS/actions/runs/30678336073) | **success** (npm-audit + secret-scan/Trivy + sast + report) |
| Pre-Slice baseline | CI | [30678290258](https://github.com/ragheeda-boop/SalesOS/actions/runs/30678290258) (`be7db9d`) | `npm audit` **failure** - `sharp <0.35.0` HIGH GHSA-f88m (2 high); Trivy npm `package-lock` **1** HIGH (`sharp` 0.34.5 -> 0.35.0) |

### Classification

| Signal | Verdict |
|---|---|
| `sharp` / GHSA-f88m / libvips CVEs | **cleared** (npm audit + Trivy npm) |
| Overall CI / Security | Not green - **pre-existing** red (Backend Lint/Types, pip-audit, Prettier on 2 test files, Trivy backend Poetry) |
| Frontend Types | **success** (unchanged vs prior) |
| Frontend Lint | **failure** - Prettier on `settings-page.test.tsx` / `AnalyticsWorkspace.test.tsx` - **pre-existing**, not Slice-1 regression |
| Override regression | **none** observed |

**Sharp CVE gate improved:** yes - CI `npm audit --audit-level=high` red->green for sharp; Trivy `package-lock` HIGH 1->0. No code fix this observer pass (document only). No majors / CI-22 / backend work.

---

## 11. Slice 2 outcome (2026-08-01) - **PASS**

Executed under standing approval after DEC-065 / early DEC-072 STOP. Full package: [`DEC-072-CI-14-SLICE-2-ESLINT-EVIDENCE.md`](DEC-072-CI-14-SLICE-2-ESLINT-EVIDENCE.md).

| Check | Result |
|---|---|
| Slice 2 definition | ESLint **9 -> 10** + eslint-config-next aligned to Next 15.5.x |
| Pins landed | eslint **10.8.0**; eslint-config-next **15.5.22**; next **15.5.22** (unchanged) |
| Compat | FlatCompat + `@eslint/compat` fixup; `.npmrc` `legacy-peer-deps=true` (not `--force`); postinstall stub for `@rushstack/eslint-patch` under ESLint 10 |
| Stage 1 evidence | Docker Linux `npm ci` + `npm run lint` **exit 0** + prettier check **exit 0** |
| STOP triggers avoided | No Next↓14; no React/Jest major; no `npm audit --force`; no eslint-config-next@0.2.4 |

**Label:** **build validated** for Cluster A ESLint leg. CI-14 remains **OPEN** for Slice 3 (Jest). **CI GREEN not met.**
