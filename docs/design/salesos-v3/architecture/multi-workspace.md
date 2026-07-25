# Multi-Workspace / Multi-Tenant

## Concepts

| Concept | Definition |
|---------|------------|
| **Tenant** | Isolation boundary for data + authz |
| **Organization** | Business entity; may map 1:1 with tenant in v1 |
| **Workspace** | User-facing container (branding, members, apps) |
| **Environment** | `dev` / `staging` / `prod` (ops); never mix data |

## Switching

- Workspace switcher in topbar (L1).
- Switching clears object cache; preserves personal prefs when safe.
- Recent workspaces list (permission-filtered).

## Permissions

- Membership roles per workspace.
- No silent cross-tenant reads.
- API always tenant-scoped (JWT + `X-Tenant-Id` rules per security program).

## Cross-tenant

- Default: **denied**.
- Explicit partner-share objects only with audit events.

## Impersonation

- Admin-only, time-boxed, **full audit trail**, banner in UI while active.
- Forbidden in production without policy sign-off.
