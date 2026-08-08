# SOAK-READY — Staging Soak Readiness Status

**Run:** EAB-2026-08-06-003 · **Date:** 2026-08-07 · **Mode:** EXECUTE + VERIFY
**Canonical details:** [SOAK-READINESS.md](./SOAK-READINESS.md) · [SOAK-GATE-CHECKLIST.md](./SOAK-GATE-CHECKLIST.md) · [OPS01-ROW4-STATUS.md](./OPS01-ROW4-STATUS.md)

## Verdict: STAGING PARITY ACHIEVED → **SOAK NOT YET RUN** (K2–K6 open)

| Gate | Requirement | Status |
|------|-------------|:------:|
| K1 | Target = staging cloud, parity build | **PASS** |
| K2 | Continuous window ≥48h (prefer 72h), dated UTC | OPEN |
| K3 | Evidence dir, loop summaries, hard-fail triage | OPEN |
| K4 | No new P0 during soak | OPEN |
| K5 | Project Owner review | OPEN |
| K6 | `soak_complete_claim: true` | **false** |

## Exact soak-start commands (for the human operator once preconditions are met)

From repo root (`salesos/` present):

```bash
# 1. Confirm staging parity is still intact before starting
curl -fsS https://salesos-staging.up.railway.app/health
curl -fsS https://salesos-staging.up.railway.app/metrics | head -40

# 2. Start the 48-72h soak gate loop against staging (dated UTC window)
python salesos/scripts/wave11-soak-gate.py \
  --target https://salesos-staging.up.railway.app \
  --out evidence/ops01-staging/soak-$(date -u +%Y%m%dT%H%M%SZ)

# 3. Monitor (background)
railway logs --project responsible-comfort --environment staging \
  > evidence/ops01-staging/railway-logs-soak.txt

# 4. After window closes, Project Owner reviews summaries, then flip claim:
#    soak_complete_claim: true  (in PROGRESS-WAVE11-SOAK-CLAIM.md) + OPS-01 Row 4 -> DONE
```

## Preconditions still required before START

1. **HUMAN:** staging Google OAuth app → `SSO_GOOGLE_CLIENT_ID`/`SSO_GOOGLE_CLIENT_SECRET` on staging env.
2. **DECIDE:** accept or close staging WAL/offsite-backup gap; optional `max_connections` 100→500 and/or sanitized data seed.
3. Freeze staging (manual-only deploys; do not redeploy during the window).
