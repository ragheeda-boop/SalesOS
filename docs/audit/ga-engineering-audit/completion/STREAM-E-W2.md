# Stream E — W2 Report (Alembic CLI hang)

**Date:** 2026-08-08  
**Board:** CP-E-01  
**Prior:** [STREAM-E-M1.md](./STREAM-E-M1.md)

## Root cause

1. `salesos/backend/app/__init__.py` re-exported `main`/`database` → any `import app.*` loaded full FastAPI (timeout ~15–20s).  
2. `app/alembic/env.py` imported `app.database` → module-level async engine create (~40s cold).

## Fixes

| File | Change |
|------|--------|
| `app/__init__.py` | Light package docstring only |
| `app/alembic/env.py` | `from app.common.models import Base` (no engine side effects) |

## Verification (local compose, non-prod)

| Command | Result |
|---------|--------|
| `alembic current` | exit 0 — `e5f9a32b0c08 (head)` |
| `check_alembic_head.py` | exit 0 — current == heads |
| `alembic upgrade` | **not run** |

**Disposition:** CLI tooling **Fixed**; full upgrade dress rehearsal still **Partial** (tip already applied; needs restore baseline).  
**Validation:** **light validated**. Production migrate: **forbidden / not claimed**.
