# DEC-094 — Contract tests expansion (post STORY-03-04)

> **Status:** **Accepted** (slice 1 landed)
> **Date:** 2026-08-01
> **Story adjacency:** STORY-03-04 OpenAPI contract framework (`623077c`)
> **Validation label:** **light validated** — host `poetry run pytest tests/contract/test_openapi_contract.py -m contract` PASS

---

## Decision

Expand OpenAPI HTTP contract coverage beyond the csrf-token seed without requiring DB fixtures.

| Endpoint | Why | Change |
|---|---|---|
| `GET /ping` | Public process probe; always available in ASGI tests | `response_model=PingResponse` + contract test |
| `GET /health/live` | K8s-style liveness; no DB/cache | `response_model=HealthLiveResponse` + contract test |
| `GET /api/v1/identity/csrf-token` | Already covered (`623077c`) | Retained |

Framework helpers in `tests/contract/openapi_contract.py` unchanged.

---

## Next slice (not this land)

1. `GET /health` + `GET /health/ready` — need `get_db` / cache overrides in `contract_client`
2. Identity auth error contracts (`401` / `422`) against documented `ErrorResponse`
3. One authenticated domain list endpoint — cursor pagination shape vs OpenAPI

Do **not** claim full API surface coverage. Do **not** claim CI GREEN.

---

## Honesty

- Production GA / External pilot = **NO-GO** (unchanged)
- **CI GREEN not met**
- Auth / CSRF / RBAC not weakened
