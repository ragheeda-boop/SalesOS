# Migration dress probe — WAVE-20260808-3
UTC: 2026-08-07T23:10:22Z
Target: local docker compose only
G1 compose local: PASS (salesos-* services Up)
G2 DATABASE_URL host: postgres:5432/salesos (sanitized)
G3 ENVIRONMENT: development (env.txt)
G4 RAILWAY_ENVIRONMENT: unset
alembic_version SQL: e5f9a32b0c08 (already at tip)
alembic upgrade: NOT RUN
PASS claim: NOT claimed (probe-only; tip already applied; restore-to-baseline required for full path)
Validation: light validated (identity + SQL). Full dress upgrade: not validated.
