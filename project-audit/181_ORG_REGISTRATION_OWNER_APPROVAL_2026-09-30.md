# 181 — Organization registration waits for the platform owner

Date: 2026-09-30

## Rule

Ragheed is the platform owner. He grants permissions and must approve an organization and its manager before that manager can register. After approval, the manager registers the organization and becomes tenant admin of that tenant only. Company hierarchy and further permissions come after that, through invites.

This replaces the §221 next step that had Sultan create muhide by self-registering immediately.

## What the code does

1. Anyone can `POST /api/v1/identity/org-registration-requests` with organization name, manager name, and manager email. The handler inserts one `pending` row. It creates no tenant, no user, and no session. Rate limit: 5 requests per hour per email. A second open request for the same email returns 409.
2. A designated platform owner (`role=admin` and `users.is_platform_owner`) lists open `pending` and `approved` rows and records `approve` or `reject`. Reject requires a reason.
3. `POST /api/v1/identity/register` locks an `approved` row for that manager email. The tenant name is the approved organization name. The approval is then marked `consumed` and tied to the new tenant. The manager is created as tenant `admin` only.
4. No approval returns 403 `register.owner_approval_required`. A submitted organization name that does not match the approval returns 403 `register.organization_name_mismatch`. Joining an existing tenant by `tenant_id` is still 400.

The table `org_registration_approvals` has no `tenant_id`. It is owner-plane data (same posture as DEC-158) and is not added to `ALL_TENANT_TABLES`.

## Migration

Alembic revision `c3d4e5f6a7b9` revises `b2c3d4e5f6a8`. It was not applied to production `salesos` and was not applied to `salesos_test` in this session. `salesos_test` was already behind `b2c3d4e5f6a8`.

## Roster

The owner supplied two addresses on 2026-09-30: `ragheed@outlook.sa` (platform owner) and `sultan@muhide.com` (muhide manager). No passwords were supplied or invented. None of the seven people were created or flagged. Ragheed still needs an operator to set `is_platform_owner=true` after his account exists. The public request endpoint cannot do that.

Human sequence once accounts and a non-production database at `c3d4e5f6a7b9` exist:

1. Operator marks ragheed `is_platform_owner`.
2. Sultan submits an organization request for muhide.
3. Ragheed approves that request.
4. Sultan completes registration and is tenant admin of muhide only.
5. Sultan invites ibrahem, feras, and shaher as `user`.
6. maria and nojood reporting to shaher stay a documented line until a manager field exists. No manager column was added.

## Verification

Unit tests: `python -m pytest tests/unit/test_org_registration_gate.py tests/unit/test_register_rejects_existing_tenant.py -q` → **7 passed** in 1.06s. They cover missing approval, name mismatch, register without creating a user, tenant name taken from the approval, reject-without-reason, consume conflict, and the existing `tenant_id` rejection.

Not run: integration `test_platform_owner_marker_db.py`, e2e, frontend typecheck, browser. The register page now has a request form and a complete-registration form (password minimum 12). `/v3/admin/org-registrations` lists open requests and records approve/reject for a signed-in platform owner. Those screens were not opened in a browser.

## Gates

G2–G16 and G8 are unchanged. Production is **NOT APPROVED**. Nothing was committed in this session.
