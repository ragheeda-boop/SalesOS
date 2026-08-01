# DEC-094 — Contract tests expansion (post STORY-03-04)

> **Status:** **Accepted** (slice 1 + slice 2 landed)
> **Date:** 2026-08-01
> **Story adjacency:** STORY-03-04 OpenAPI contract framework (`623077c`)
> **Validation label:** **light validated** — host `poetry run pytest tests/contract/ -m contract` → **9 passed**, 31 deselected

---

## Decision

Expand OpenAPI HTTP contract coverage beyond the csrf-token seed.

### Slice 1 (no DB) — landed @ `93a00d7`

| Endpoint | Why | Change |
|---|---|---|
| `GET /ping` | Public process probe; always available in ASGI tests | `response_model=PingResponse` + contract test |
| `GET /health/live` | K8s-style liveness; no DB/cache | `response_model=HealthLiveResponse` + contract test |
| `GET /api/v1/identity/csrf-token` | Already covered (`623077c`) | Retained |

### Slice 2 (DB fixtures) — this land

| Endpoint | Why | Change |
|---|---|---|
| `GET /health` | Full health; uses `Depends(get_db)` | `response_model=HealthResponse` + contract test |
| `GET /health/ready` | Readiness; uses `async_session` + cache | `response_model=HealthReadyResponse` + contract test |

Honest fixtures in `tests/contract/conftest.py` (`contract_db_client`):

- Override `get_db` with an AsyncMock session whose `execute` succeeds (SELECT 1 path)
- Patch `app.database.async_session` the same way for `/health/ready`
- Attach `app.state.cache` with `health() → True` so ready status is honestly `ready`

Does **not** edit `get_db()` tenant GUC (DEC-085 `set_config` preserved). Does **not** require real Postgres.

Framework helpers in `tests/contract/openapi_contract.py` unchanged.

Narrow mark: `@pytest.mark.contract` on OpenAPI HTTP tests only; `tests/contract/test_api_contracts.py` remains unmarked provider-schema unit tests (deselected by `-m contract`).

---

## Next slice (not this land)

1. Identity auth error contracts (`401` / `422`) — only after OpenAPI documents the **actual** error shapes (FastAPI `{"detail": ...}` / `HTTPValidationError`); do not force `ErrorResponse` without wiring
2. One authenticated domain list endpoint — cursor pagination shape vs OpenAPI

Do **not** claim full API surface coverage. Do **not** claim CI GREEN.

---

## Honesty

- Production GA / External pilot = **NO-GO** (unchanged)
- **CI GREEN not met**
- Auth / CSRF / RBAC not weakened
- DEC-085 `set_config` intact (no `get_db` SET LOCAL edits)
