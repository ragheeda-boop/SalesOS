# DEC-065 — CI-14 Slice 2 STOP: ESLint 9→10 is a silent major (not auto-safe)

> **Status:** **Accepted** — Slice 2 **STOPPED**; CI-14 remains **OPEN**  
> **Date:** 2026-08-01  
> **Board:** Frontend / Deps (SalesOS / AQLIYA)  
> **Story / risk:** CI-14 / R-18 Cluster A (ESLint/Jest toolchain DoS — `brace-expansion` / `minimatch`)  
> **Authority:** DEC-062 plan · DEC-063 Slice 1 PASS (`435ba5d`) · CI-11 stop-rules (no `--force`; no silent majors)  
> **Out of scope this land:** package bumps · `npm install` · `npm audit --force` · Next/React/Jest majors · CI-22 · Railway · backend Poetry

---

## 1. Slice 2 definition (from DEC-062)

| Field | Value |
|---|---|
| **Name** | Slice 2 — ESLint ecosystem major |
| **Intent** | Clear Cluster A toolchain advisories via **eslint 9 → 10** + **eslint-config-next** aligned to Next 15.5.x |
| **Explicit non-goals** | Jest major (Slice 3); Next↓14; React major; `npm audit --force`; audit nonsense pins (`eslint-config-next@0.2.4`, jest→25) |

DEC-062 Safe vs STOP matrix classifies ESLint **9 → 10** (+ flat-config / plugin cascade) as **STOP until dedicated slice** — major; lint CI + local DX; **not auto-safe**.

---

## 2. Why this session STOPs (no package land)

Executing Slice 2 as an unattended bump would be a **silent ESLint major**, which violates:

1. **DEC-062 stop-rule** — ESLint major requires dedicated plan + lint-green evidence before land.  
2. **Session contract** — no Next↓14, no React/ESLint/Jest silent majors, no `npm audit --force`.  
3. **Architecture blast radius (evidence from tree, no install):**
   - Lock: `eslint` **9.39.5**, `eslint-config-next` **15.5.22** (tracks next **15.5.22**).  
   - Config already flat: `salesos/frontend/eslint.config.mjs` uses `FlatCompat` + `next/core-web-vitals` + `plugin:@typescript-eslint/recommended` + **inline custom-rules** plugin.  
   - ESLint 10 + plugin/`eslint-config-next` alignment is a **compat cascade**, not a one-line pin change.  
4. **npm audit framing risk** — historical Cluster A “fix” includes **eslint-config-next→0.2.4** (nonsense vs Next 15) — must not be applied even if audit suggests it.

**No safe non-major executable for Slice 2 is authorized or evidenced in this session.** Slice 1 (sharp) remains PASS at `435ba5d`.

---

## 3. Decision

**STOP** CI-14 Slice 2 execution.

- Do **not** bump `eslint`, `eslint-config-next`, `@typescript-eslint/*`, or related lint plugins.  
- Do **not** refresh `package-lock.json` for Cluster A in this land.  
- Do **not** start Slice 3 (Jest major).  
- Do **not** start CI-22 / backend deps / Railway.  
- Leave CI-14 **IN PROGRESS / OPEN**; R-18 **Open — mitigating** (Slice 1 sharp floor retained).

---

## 4. Next recommendation (human / executive gate)

Authorize a **dedicated Slice 2 evidence package** (docs + approval) before any lock change, with all of:

| Gate | Requirement |
|---|---|
| Target pins | `eslint` **10.x** floor named; `eslint-config-next` **aligned to next 15.5.x** (explicitly **not** `0.2.4`) |
| Compat plan | FlatCompat / `@typescript-eslint` / custom-rules in `eslint.config.mjs` — migrate or prove compatible |
| Evidence commands | `npm ls eslint eslint-config-next`; Frontend Lint CI (or approved local `next lint`) green; Types unchanged; Jest contract ≤ inventory ceiling (no new failures) |
| Coupling | **No** Jest major in the same land unless intentionally authorized as a combined slice |
| Forbidden | `--force`; Next↓14; React major; audit downgrade pins |

**Optional alternate (only if fresh `npm audit` evidence shows it):** a separately named slice for **transitive overrides** of `brace-expansion`/`minimatch` under eslint **9** — **not** the current Slice 2 definition; would need its own DEC before execution.

Until that package is Accepted, Slice 2 remains **BLOCKED / STOPPED**.

---

## 5. Validation

| Check | Result |
|---|---|
| Package / lock changes | **None** |
| Slice 1 sharp override | Unchanged (still `>=0.35.0` / lock **0.35.3** @ `435ba5d`) |
| Label | **not validated** (docs-only STOP) |

**CI GREEN not met.** npm-audit remains red on Cluster A until a governed Slice 2 (or alternate) lands.
