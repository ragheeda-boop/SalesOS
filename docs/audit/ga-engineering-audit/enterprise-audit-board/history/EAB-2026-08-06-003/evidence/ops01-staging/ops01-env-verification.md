# OPS-01 — Staging & Production Environment Verification (evidence)

**Evidence ID:** ops01-staging-env-verification
**Run:** EAB-2026-08-06-003 · **Date:** 2026-08-06 · **Mode:** VERIFY FIRST (read-only; no environment modified)
**Validation label:** machine verified (live probes + GraphQL + local SQL via tunnel + redacted hashes)

## What was verified

1. **Production** (`https://salesos-production-96c0.up.railway.app`) and **staging** (`https://salesos-staging.up.railway.app`) both return `/health` **200** with `database=connected`, `redis=connected`.
2. **DB isolation (SQL proof):** staging Postgres reached through a temporary `railway connect --tunnel-only --port 5435` + disposable `postgres:18` container:
   - staging `alembic_version=b7e2f65a3f07`, companies=0, tenants=0, audit_logs=1 → **empty, separate, older-head instance**.
   - production `alembic_version=d1a8c35e7f09`, companies=141,221, tenants=57, audit_logs=683 (rows 1–3 evidence).
   - App→DB wiring proven: SalesOS `DATABASE_URL` hash == same-environment Postgres `DATABASE_URL` hash.
3. **Code drift:** staging deploy `98bf85bf` (2026-08-01, digest `sha256:1f7f845f…`, commit `0bd73fc`) is **409 commits behind** production `bdce3450` (2026-08-05, digest `sha256:11b14ac5…`, commit `4750038c`).
4. **Config drift:** staging `DEBUG=true`; missing Google SSO vars, `FRONTEND_URL`, `FEATURE_HTTPONLY_ACCESS_COOKIE`; **`JWT_SECRET_KEY` and `SECRET_KEY` identical to production** (cross-env secret reuse).
5. **Graph inversion:** staging neo4j connected; production `neo4j-prod` **OFFLINE** (`graph=unavailable`).
6. **CI wiring:** staging not connected to GitHub Actions — `RAILWAY_STAGING_*` secrets absent, `deploy-staging.yml` soft-skips; GitHub env `staging` has 0 secrets. Production CD active (`deploy.yml` push master). `deploy-production.yml` (K8s) QUARANTINED (DEC-149).
7. **Stability:** 500-line staging log window spans ~5.38-day uptime, no restart, no ERROR/CRITICAL (only duplicate-op-id + scraper-config warnings). Production: ~23.3h uptime, warnings only.

## Security handling

- No secrets written to this evidence. Secret-bearing values appear only as `sha256` first-10-hex or are marked present/absent.
- A Redis password value leaked into a terminal transcript during hashing (command alias collision); it was NOT persisted to any file or document. Recommend rotating both Redis passwords as hygiene.

## Verdict

| Item | Result |
|------|--------|
| Production | READY WITH CONDITIONS — NOT GO (neo4j-prod offline; audit no-go unchanged) |
| Staging | NOT READY (not production-parity) |
| OPS-01 Row 4 | OPEN (soak not run; `soak_complete_claim=false`) |
| Launch | NO-GO |

## Related documents

- [ENVIRONMENT-MAP.md](../ENVIRONMENT-MAP.md)
- [STAGING-VERIFICATION.md](../STAGING-VERIFICATION.md)
- [PRODUCTION-VERIFICATION.md](../PRODUCTION-VERIFICATION.md)
- [STAGING-vs-PRODUCTION-DIFF.md](../STAGING-vs-PRODUCTION-DIFF.md)
- [SOAK-READINESS.md](../SOAK-READINESS.md)
- [OPS01-ROW4-STATUS.md](../OPS01-ROW4-STATUS.md)
