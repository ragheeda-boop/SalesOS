# Phase 1 — A4 JWT owner-audience reaffirm (DEC-093)

> **Stream:** Backend A4 — [`POST_PHASE0_PARALLEL_EXECUTION_PLAN.md`](POST_PHASE0_PARALLEL_EXECUTION_PLAN.md) §4.1  
> **Depends:** A2 tenant schema land (`f6b2e84c1a90` @ `64b44e9`)  
> **Status:** REAFFIRMED (light / CI Stage 3) — tip `0782fa4`  
> **Honesty:** Not Production GO. DEC-085 untouched.

## Scope

Confirm owner-audience consumption remains green after STORY-04-01 Tenant ORM extension:

| Check | Evidence |
|-------|----------|
| Platform admin wires `require_owner_role_dep` → `decode_owner_*` | `app/owner_auth.py` + admin routers (`dependencies=[Depends(require_owner_role_dep("admin"))]`) |
| Tenant `verify_token` remains `salesos-api` only | DEC-093 standing; `settings.jwt_audience` vs `jwt_owner_audience` |
| Unit suite | `tests/unit/test_jwt_audience_split.py` — included in CI Stage 3 Backend Unit Tests |

## Field evidence (2026-08-02)

| Item | Result |
|------|--------|
| Non-prod Alembic head | `f6b2e84c1a90` (local Docker postgres; Owner Platform cols=5; `pg_policies`=67) — [`PHASE1_A2_NONPROD_MIGRATE_NOTES.md`](PHASE1_A2_NONPROD_MIGRATE_NOTES.md) |
| Tip CI Stage 1 Backend Lint | SUCCESS @ `0782fa4` run `30728358294` |
| Tip CI Stage 2 Backend Types | SUCCESS @ `0782fa4` |
| Tip CI Stage 3 Backend Unit Tests | SUCCESS @ `0782fa4` (includes JWT audience suite) |
| Code path review | Admin tenants router still `require_owner_role_dep`; no audience redesign |

**Label:** light validated / build validated for Stage 3 path. **No Production GO.**

## Non-goals

- No audience redesign  
- No AI copilot enablement  
- No Production GO / Stages 1–7 invent

## Next

1. Keep Stage 3 green after further Owner Platform API lands (activate/list filters).  
2. D3 adversarial RLS unskipped PASS remains Validation stream (Stage 4) — orthogonal to A4.
