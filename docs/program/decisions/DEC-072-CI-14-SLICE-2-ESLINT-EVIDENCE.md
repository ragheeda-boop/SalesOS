# DEC-072 — CI-14 Slice 2 evidence package: ESLint 9→10 (authorized execute gate)

> **Status:** **Accepted** — evidence package complete; **EXECUTE STOPPED** (peer blocker). No package/lock land.  
> **Date:** 2026-08-01  
> **Board:** Frontend / Deps (SalesOS / AQLIYA)  
> **Story / risk:** CI-14 / R-18 Cluster A  
> **Authority:** DEC-062 plan · DEC-063 Slice 1 PASS · DEC-065 STOP · user standing approval 2026-08-01  
> **Out of scope:** Jest major (Slice 3) · Next↓14 · React major · `npm audit --force` · CI-22 · Railway

---

## 1. Target pins (named)

| Package | From (lock) | To (floor) | Notes |
|---|---|---|---|
| `eslint` | **9.39.5** (`^9.0`) | **10.x** latest 10 | Major; Cluster A primary |
| `eslint-config-next` | **15.5.22** (`^15.0`) | **aligned to next 15.5.x** | Explicitly **not** `0.2.4` |
| `@typescript-eslint/*` | whatever eslint-config-next / tree resolves | Compatible with ESLint 10 | Cascade OK if solver-clean |

---

## 2. Compat plan (`eslint.config.mjs`)

Current config is already **flat**:

- `FlatCompat` + `next/core-web-vitals`
- `plugin:@typescript-eslint/recommended`
- Inline `custom-rules` plugin (`no-tailwind-color-classes`)

**Plan:**

1. Bump `eslint` to `^10.0.0` in `package.json`; keep `eslint-config-next` on `^15.0` (Next 15.5 line).  
2. `npm install` in `salesos/frontend` (no `--force`).  
3. If FlatCompat / typescript-eslint break: adjust peer ranges or migrate recommended extend — **do not** disable custom-rules.  
4. Evidence commands (must pass before push):
   - `npm ls eslint eslint-config-next`
   - `npm run lint` (or `npx next lint`) exit 0
   - `npx tsc --noEmit` exit 0
5. If lint cascade breaks badly (new error class explosion / FlatCompat hard fail): **STOP**, revert lock/package, document in this DEC §5, continue elsewhere.

**Forbidden:** `npm audit --force`; eslint-config-next→0.2.4; Jest major in same land; Next/React majors.

---

## 3. Decision

Accept this evidence package. **Authorize Slice 2 execute** under standing approval. Record outcome:

- **PASS** → land package+lock; update board Slice 2 COMPLETE; R-18 mitigating.  
- **STOP** → no land; append failure evidence; Slice 2 remains STOPPED.

---

## 4. Validation (pre-execute)

| Check | Result |
|---|---|
| Evidence package docs | This file |
| Package / lock (pre) | Unchanged until execute |
| Label | **not validated** until lint/tsc evidence recorded |

**CI GREEN not met.**

---

## 5. Execute outcome (2026-08-01) — STOP

**Attempt:** host 
pm install / lint probe toward eslint **10** under next **15.5.22**.

**Blocker (field evidence):** eslint-config-next@15.5.22 declares peer eslint@"^7.23.0 || ^8.0.0 || ^9.0.0" — **ESLint 10 is outside the peer range**. Solver refused without --force / --legacy-peer-deps (both **forbidden** by DEC-062 / CI-11 discipline).

**Host lint baseline:** already red on this workstation (@eslint/eslintrc missing / rushstack patch failure after partial install). CI Frontend Lint historically PASS on eslint 9 — do **not** treat host cascade as CI lint green claim either way.

**Decision:** **STOP** Slice 2 package land. Retain eslint **9.x** + eslint-config-next **15.5.x**. Next path options (separate DEC): (a) wait for Next 15.x eslint-config-next that peers eslint 10; (b) alternate Cluster A overrides for brace-expansion/minimatch under eslint 9; (c) defer Cluster A to CI-14 Slice 3+ tooling redesign.

| Check | Result |
|---|---|
| Package / lock land | **None** (STOP) |
| Label | **light validated** (peer conflict reproduced) |

**CI GREEN not met.**
