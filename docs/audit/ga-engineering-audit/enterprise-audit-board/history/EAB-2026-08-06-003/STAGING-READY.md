# STAGING-READY — Production-Parity Confirmation

**Run:** EAB-2026-08-06-003 · **Date:** 2026-08-07 · **Mode:** EXECUTE + VERIFY
**Canonical details:** [STAGING-vs-PRODUCTION-DIFF.md](./STAGING-vs-PRODUCTION-DIFF.md) · [STAGING-READINESS.md](./STAGING-READINESS.md) · [OPS01-ROW4-STATUS.md](./OPS01-ROW4-STATUS.md)

## Verdict: STAGING IS PRODUCTION-PARITY (code/config/secret) → SOAK-CAPABLE WITH CONDITIONS

| # | Check | Result |
|---|-------|:------:|
| 1 | Staging code == prod baseline `4750038c` | **YES** |
| 2 | `/openapi.json` byte-identical to prod (881,643 B) | **YES** |
| 3 | Alembic = repo head `e5f9a32b0c08`; RLS 71/71 | **YES** |
| 4 | `DEBUG=false` (staging `/docs` → 404, prod parity) | **YES** |
| 5 | `JWT_SECRET_KEY` / `SECRET_KEY` distinct from prod | **YES** |
| 6 | Neo4j connected (staging **and** prod — no inversion) | **YES** |
| 7 | celery-worker + celery-beat on prod commit | **YES** |
| 8 | CI wiring (`RAILWAY_STAGING_*` secrets) + workflow validated | **YES** |
| 9 | Postgres saturation cleared (active=12/100) | **YES** |
| 10 | `/health` 200 all subsystems | **YES** |

## Conditions before an UNQUALIFIED soak

- **HUMAN:** staging Google OAuth app → `SSO_GOOGLE_CLIENT_ID`/`SSO_GOOGLE_CLIENT_SECRET` (currently absent).
- **ACCEPT or CLOSE:** staging WAL/PITR + offsite-backup gap; staging `max_connections`=100 vs prod 500.
- Soak **not started** (K2–K6 open; `soak_complete_claim` false).
