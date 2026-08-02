# Phase 1 — STORY-06-04 residual: entitlement cache TTL / plan-downgrade soak

> **Honesty:** Not Production GO. DEC-085 / auth / CSRF / RBAC / tenant isolation untouched.
> Stage 6 GHCR quarantined (DEC-150 B). No invented secrets.

## Landed

| Piece | Detail |
|-------|--------|
| Cache | `entitlement_cache.py` — memory + optional Redis; TTL clamped **1..60s** |
| Setting | `Settings.entitlement_cache_ttl_seconds` default **60** |
| Resolve | `resolve_entitlements_for_tenant` reads/writes cache |
| Invalidate | Plan apply / pending flip / tenant plan change |
| Suite | `tests/unit/test_entitlement_cache_ttl_story_06_04.py` |

## Validation

| Check | Result |
|-------|--------|
| Host pytest TTL suite | **7 passed** (pre-push) |
| Production GO | **Not claimed** |

## Non-goals

- Live multi-hour Redis soak in prod
- Production GO / Stage 6 GHCR green
