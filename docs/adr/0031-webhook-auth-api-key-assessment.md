# ADR-0031: Webhook Authentication — API Key Assessment

## Status

Accepted (No Change Required)

## Context

During Wave A security hardening (WO-001), SEC-001 identified that the webhooks router lacked explicit JWT authentication. The fix added `Depends(verify_token)` as a router-level dependency.

As an optional follow-up, WO-001 Task 6 requires assessing whether the webhook subscription management endpoints should migrate from JWT to API key authentication.

## Current Implementation

The webhooks router at `/api/v1/webhooks` handles CRUD operations for webhook subscriptions (create, read, update, delete subscription configurations). Authentication is via:

1. `Depends(verify_token)` — validates JWT Bearer token
2. `Depends(get_current_tenant_id)` — validates `x-tenant-id` header matches token

This is consistent with all other administrative API endpoints in the application.

## Assessment

| Factor | JWT | API Key | Verdict |
|--------|-----|---------|---------|
| Use case | Admin CRUD for webhook configs | Machine-to-machine auth | JWT fits better |
| Consistency | Matches all other API endpoints | Would be unique pattern | JWT wins |
| Tenant scoping | Built-in via `get_current_tenant_id` | Would need custom middleware | JWT wins |
| Key rotation | Built-in via JWKS | Requires separate rotation infra | JWT wins |
| Audit trail | User identity in token claims | API key identity linked to key | Equal |
| Rate limiting | Per-user via token claims | Per-key via key ID | Equal |

The webhook subscription management is an administrative CRUD interface, not a high-throughput machine-to-machine endpoint. JWT provides:
- Consistent auth model with the rest of the API
- Tenant isolation through token claims
- User-level audit trail
- No additional infrastructure

A separate "incoming webhook receiver" endpoint (allowing external systems to push data to SalesOS) would benefit from API key authentication, but that is a different feature not in scope.

## Decision

**No migration** to API keys is recommended. The webhook subscription management router will continue using JWT authentication via `Depends(verify_token)`.

## Consequences

- No additional infrastructure or code changes required
- Consistent auth model across all admin endpoints
- If a future "incoming webhook receiver" feature is added, it should use API keys

## References

- WO-001 Wave A: Security Hardening
- SEC-001: Webhooks Router Authentication
- `salesos/backend/app/modules/webhooks/router.py`
- `salesos/backend/app/dependencies.py`
