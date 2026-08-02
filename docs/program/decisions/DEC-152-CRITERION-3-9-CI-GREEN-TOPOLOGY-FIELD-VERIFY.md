# DEC-152 — Criterion 3.9 CI GREEN (DEC-149 topology) field-verify

**Status:** Accepted (field evidence)  
**Date:** 2026-08-02  
**Authority:** DEC-151 Governance Freeze — allowed field evidence crumb for hard OPEN **3.9** (no topology rewrite; Stage 6 remains quarantined)

## Decision

Accept **3.9 VERIFIED → CLOSED CONDITIONAL** on tip `5fafbe9` with same-run Stages 1–5 SUCCESS and same-tip Deploy Production SUCCESS under DEC-149 Railway+Vercel topology. Stage 6 GHCR remains quarantined (`if: false`) per DEC-150 Option B — **not** required for 3.9.

## Evidence (tip `5fafbe9c55c8e3017891944a3005b05dce3a99e1`)

| Gate | Run | Result |
|------|-----|--------|
| CI Stages 1–5 (same run) | [30724762973](https://github.com/ragheeda-boop/SalesOS/actions/runs/30724762973) | All Stage 1–5 jobs **SUCCESS** |
| Stage 4 Integration | same run | **SUCCESS** (includes xdist fix `3547177`) |
| Stage 6 GHCR | same run | **SKIPPED** (quarantined DEC-150 B) |
| Stage 7 E2E | same run | **FAILURE** → criterion **3.7** remains OPEN (orthogonal) |
| Deploy Production | [30724762967](https://github.com/ragheeda-boop/SalesOS/actions/runs/30724762967) | **SUCCESS** (Railway + Health Gate + Vercel FE) |
| Security Scan (separate) | [30724762982](https://github.com/ragheeda-boop/SalesOS/actions/runs/30724762982) | **SUCCESS** |

## Conditions / residuals (why CONDITIONAL, not unconditional)

1. Overall CI workflow conclusion remains **failure** solely due to Stage 7 E2E (**3.7** OPEN) — do **not** claim Stages 1–7 whole-pipeline green.
2. Deploy FE path remains **Git-primary** (same residual as **3.11** / DEC-149a); staging deferred; no VPS.
3. Stage 6 GHCR quarantined by governance — residual field GHCR 403 = legacy/non-blocking.

## Explicit non-claims

- No Production GO / Phase 0 COMPLETE / Phase 0 GO
- No invent ARB PASS on **4.1** / **4.8**
- No Stage 6 un-quarantine / no new deploy-topology DEC
- DEC-085 untouched

## Scoreboard delta

Phase 0 **48/54 → 49/54 NO-GO**. Hard OPEN ⬜ → **3.7**, **4.1**, **4.8**.
