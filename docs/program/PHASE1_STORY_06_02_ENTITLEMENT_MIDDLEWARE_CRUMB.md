# Phase 1 — STORY-06-02 Entitlement middleware (Stream A)

> **Honesty:** Not Production GO. DEC-085 / auth / CSRF / RBAC untouched. BE-only.  
> Feature flags remain a separate layer.

## Landed

| Piece | Detail |
|-------|--------|
| Gates | Path → DOM registry (≥3 combos): `DOM-011` rag/ai, `DOM-012` copilot, `DOM-023` signals, `DOM-021` integrations |
| Resolve | Tenant/Subscription `plan_id` → `admin_plans.entitlements` (tier default fallback) |
| Middleware | `EntitlementEnforcementMiddleware` — 403 when domain disabled |
| Skip | Owner/admin/auth/health/identity (same family as suspend guard) |
| Flag | `Settings.entitlement_enforcement_enabled` (default **True**, not a secret) |
| Stack | Inner of `TenantContextMiddleware` (ContextVar tenant already set) |

## Acceptance matrix (light)

| Path family | DOM | Starter | Growth |
|-------------|-----|---------|--------|
| `/api/v1/rag`, `/api/v1/ai` | DOM-011 | deny | allow |
| `/api/v1/copilot` | DOM-012 | deny | allow |
| `/api/v1/signals` | DOM-023 | deny | allow |
| `/api/v1/integrations` | DOM-021 | allow (quota 1) | allow |
