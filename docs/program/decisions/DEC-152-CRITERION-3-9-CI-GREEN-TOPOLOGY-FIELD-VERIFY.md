# DEC-152 — Criterion 3.9 CI GREEN (DEC-149 topology) field-verify

**Status:** Accepted (field evidence)  
**Date:** 2026-08-02  
**Authority:** DEC-151 Governance Freeze — allowed field evidence crumb for hard OPEN **3.9** (no topology rewrite; Stage 6 remains quarantined)

## Decision

Accept **3.9 VERIFIED → CLOSED CONDITIONAL** with same-run Stages 1–5 SUCCESS and Deploy Production SUCCESS under DEC-149 Railway+Vercel topology. Stage 6 GHCR remains quarantined (`if: false`) per DEC-150 Option B — **not** required for 3.9.

## Evidence (strongest tip-line field-verify)

| Gate | Run / SHA | Result |
|------|-----------|--------|
| CI Stages 1–5 + overall CI | [30727362895](https://github.com/ragheeda-boop/SalesOS/actions/runs/30727362895) @ `6919e3c` | All Stage 1–5 jobs **SUCCESS**; workflow **SUCCESS** |
| Prior same-run Stages 1–5 | [30726614815](https://github.com/ragheeda-boop/SalesOS/actions/runs/30726614815) @ `62bbafb` | All Stage 1–5 **SUCCESS**; workflow **SUCCESS** |
| First post–xdist tip-line | [30724762973](https://github.com/ragheeda-boop/SalesOS/actions/runs/30724762973) @ `5fafbe9` (includes `3547177`) | Stages 1–5 **SUCCESS** (workflow red on in-tree Stage 7 only) |
| Stage 6 GHCR | tip CI | **SKIPPED** (quarantined DEC-150 B) |
| Stage 7 | `e2e-stage7.yml` (not ci.yml) | Orthogonal to 3.9; see DEC-155 |
| Deploy Production | [30727362885](https://github.com/ragheeda-boop/SalesOS/actions/runs/30727362885) @ `6919e3c` | **SUCCESS** |
| Security Scan | [30727362864](https://github.com/ragheeda-boop/SalesOS/actions/runs/30727362864) @ `6919e3c` | **SUCCESS** |

## Conditions / residuals (why CONDITIONAL, not unconditional)

1. Deploy FE path remains **Git-primary** (same residual as **3.11** / DEC-149a); staging deferred; no VPS.
2. Stage 6 GHCR quarantined by governance — residual field GHCR 403 = legacy/non-blocking.
3. Later tip SHAs may temporarily regress Stages 1–2 under parallel Phase 1 streams — 3.9 stands on evidenced tip-line green runs above; re-verify if tip stays red.

## Explicit non-claims

- No Production GO / Phase 0 COMPLETE / Phase 0 GO
- No invent ARB PASS on **4.1** / **4.8**
- No Stage 6 un-quarantine / no new deploy-topology DEC
- DEC-085 untouched

## Scoreboard delta

Phase 0 **48/54 → 49/54 NO-GO**. Hard OPEN ⬜ → **3.7**, **4.1**, **4.8**.
