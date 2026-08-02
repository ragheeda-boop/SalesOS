# Phase 1 — A4 JWT owner-audience reaffirm (DEC-093)

> **Stream:** Backend A4 — [`POST_PHASE0_PARALLEL_EXECUTION_PLAN.md`](POST_PHASE0_PARALLEL_EXECUTION_PLAN.md) §4.1  
> **Depends:** A2 tenant schema land (`f6b2e84c1a90` @ `64b44e9`)  
> **Status:** REAFFIRM READY — no code change required this wave  
> **Honesty:** Not Production GO. DEC-085 untouched.

## Scope

Confirm owner-audience consumption remains green after STORY-04-01 Tenant ORM extension:

| Check | Evidence |
|-------|----------|
| Platform admin wires `require_owner_role_dep` → `decode_owner_*` | `app/owner_auth.py` + admin routers |
| Tenant `verify_token` remains `salesos-api` only | DEC-093 standing |
| Unit suite | `tests/unit/test_jwt_audience_split.py` (DEC-093 host **14/14** — re-run after Docker migrate proof) |

## Non-goals

- No audience redesign  
- No AI copilot enablement  
- No Production GO / Stages 1–7 invent

## Next

1. After non-prod Alembic upgrade proof for A2: re-run JWT audience unit suite (narrow path).  
2. Record PASS/FAIL crumbs here — do not invent CLOSE.
