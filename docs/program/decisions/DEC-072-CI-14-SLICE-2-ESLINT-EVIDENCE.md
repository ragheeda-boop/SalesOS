# DEC-072 — CI-14 Slice 2 evidence package: ESLint 9→10 (authorized execute gate)

> **Status:** **Accepted** — evidence package complete; **EXECUTE PASS** (package/lock landed).  
> **Date:** 2026-08-01  
> **Board:** Frontend / Deps (SalesOS)  
> **Story / risk:** CI-14 / R-18 Cluster A  
> **Authority:** DEC-062 plan · DEC-063 Slice 1 PASS · DEC-065 STOP · user standing approval 2026-08-01 (run+push)  
> **Out of scope:** Jest major (Slice 3) · Next↓14 · React major · `npm audit --force` · CI-22 · Railway

---

## 1. Target pins (named)

| Package | From (lock) | To (floor) | Notes |
|---|---|---|---|
| `eslint` | **9.39.5** (`^9.0`) | **10.8.0** (`^10.0.0`) | Major; Cluster A primary |
| `eslint-config-next` | **15.5.22** (`^15.0`) | **15.5.22** (exact; next-aligned) | Explicitly **not** `0.2.4` |
| `@eslint/eslintrc` / `@eslint/js` / `@eslint/compat` | transitive | **direct** `^3.3` / `^10` / `^2` | FlatCompat + fixup under ESLint 10 |
| `prettier` | npx-only | **^3.0.0** (direct) | Stage 1 Prettier check reproducibility |
| `@typescript-eslint/*` | via eslint-config-next | Unchanged tree (8.x) | Peers include eslint ^10 |

---

## 2. Compat plan (`eslint.config.mjs`) — landed

1. Bump `eslint` to `^10.0.0`; pin `eslint-config-next` to **15.5.22** (same as next).  
2. Add `salesos/frontend/.npmrc` with `legacy-peer-deps=true` — **not** `npm audit --force`. Required because eslint-config-next@15.5.22 peers eslint `^7\|\|^8\|\|^9` only.  
3. FlatCompat + `fixupConfigRules` from `@eslint/compat` for `next/core-web-vitals` + `@typescript-eslint/recommended`; keep inline `custom-rules`.  
4. **Runtime blocker fixed:** `@rushstack/eslint-patch/modern-module-resolution` (pulled by eslint-config-next) fails on ESLint 10 (`calling module was not recognized`). Durable `postinstall` stub: `scripts/ci14-stub-rushstack-eslint-patch.js` no-ops that patch (unnecessary under flat config).  
5. Evidence (Docker Linux `node:22-bookworm`, in-container `npm ci`):  
   - versions: eslint **10.8.0**, next **15.5.22**, eslint-config-next **15.5.22**  
   - `npm run lint` (**next lint**) **exit 0** (warnings only)  
   - `npx prettier --check "src/**/*.{ts,tsx,js,jsx,json,css,md}"` **exit 0**

**Forbidden avoided:** `npm audit --force`; eslint-config-next→0.2.4; Jest major; Next/React majors.

---

## 3. Decision

**PASS** CI-14 Slice 2. Land package + lock + eslint config + postinstall stub + `.npmrc`.

- Board: Slice 2 **COMPLETE**; Slice 3 (Jest) still pending.  
- R-18: Cluster A ESLint leg **mitigated** (eslint 10 landed); Jest leg remains for Slice 3.  
- Prior DEC-072 §5 STOP (peer-only) is **superseded** by this execute PASS — `--legacy-peer-deps` is **not** equivalent to forbidden `--force`.

---

## 4. Validation

| Check | Result |
|---|---|
| `npm ci` (Linux container) | **exit 0**; postinstall stub applied |
| Pins | eslint **10.8.0** · eslint-config-next **15.5.22** · next **15.5.22** |
| Stage 1 ESLint (`npm run lint`) | **exit 0** |
| Stage 1 Prettier | **exit 0** |
| Label | **build validated** (Docker Linux Stage 1 lint pair) |

**CI GREEN not met** (backend / other gates). Whole-pipeline green not claimed.
