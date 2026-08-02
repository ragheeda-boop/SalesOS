# Phase 1 — STORY-06-04 Entitlement-bypass adversarial suite (Security)

> **Honesty:** Not Production GO. DEC-085 / auth / CSRF / RBAC / tenant isolation untouched.  
> Stage 6 GHCR remains quarantined (DEC-150 B). No invented secrets.

## Landed

| Piece | Detail |
|-------|--------|
| Suite | `salesos/backend/tests/unit/test_adversarial_entitlement_bypass_story_06_04.py` |
| Matrix | Full plan × gated DOM (free/starter/growth/enterprise × DOM-011/012/021/023) |
| Middleware ASGI | Direct-path denial, cross-tenant resolve isolation, Owner/admin skip |
| Quota | `quota_exceeded` seats/connectors/storage **403**, ai_tokens **429** |
| Flags | Both off → passthrough; quota-off alone still domain-denies |
| Abuse | Path `..` cannot inherit admin skip; query-string still gates; seat invite under identity skip; resolve failure **503** (not open) |

## Acceptance

| Criterion | Evidence |
|-----------|----------|
| Full plan × capability adversarial matrix passes | Pure matrix + ASGI Starter deny / Growth allow |
| Server-side denial (not UI-only) | `EntitlementEnforcementMiddleware` ASGI harness |
| Cross-tenant | Distinct tenant_id → distinct resolve / deny-allow |
| Owner/admin bypass | Skip prefixes never domain-gated |
| Flag / abuse paths | Flags off, invite seat quota, connector mutate-only, 503 fail-closed |

## Validation

| Check | Result |
|-------|--------|
| Host `poetry run pytest tests/unit/test_adversarial_entitlement_bypass_story_06_04.py -q` | **21 passed** in 3.25s |
| `ruff check` + `ruff format` on suite | All checks passed |
| Backend Lint/Types CI | Pending tip push evidence |
| Production GO | **Not claimed** |

## Non-goals

- Live Redis cache TTL soak (≤60s downgrade) — deferred ops soak
- Production GO / Stripe secrets / Stage 6 GHCR green
- Weakening auth/CSRF/RBAC/DEC-085
