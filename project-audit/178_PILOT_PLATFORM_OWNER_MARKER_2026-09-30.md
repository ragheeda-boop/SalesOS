# 178 — Pilot decision A: explicit platform-owner marker, self-registrant tenant admin (2026-09-30)

**Branch:** `fix/login-and-keys` (base `2b85769f`) · **Scope:** SalesOS backend identity/RBAC + one review UI page · **Classification:** build validated (narrow, disposable DB). Production **NOT APPROVED**; G2–G16 / G8 unchanged.

## 1. Decision implemented

| Rule | Implementation |
|---|---|
| `/owner/login` requires an explicit marker, not tenant `admin` | New column `users.is_platform_owner` (BOOLEAN NOT NULL DEFAULT false, migration `b2c3d4e5f6a8`, down `a1b2c3d4e5f7`). `/owner/login` requires active + admin + marker. `owner_auth.get_current_owner_user_role` re-checks the marker on every owner request (403 otherwise). |
| Self-registrant = admin of own tenant only | `/register` creates a new tenant and assigns `admin` in that tenant (`create_user(..., role="admin")`). |
| Second registration cannot join an existing tenant | `/register` with `tenant_id` in the body → 400 (unchanged from `85947d22`, re-proven). |
| Invitee stays `user`, invite fails closed | `/invite` requires `user:CREATE`, default role `user`, rolls back + 500 on role failure (from `39bb564d`, re-proven). |
| No owner / billing / cross-tenant powers for self-registered admins | New `require_platform_owner_dep()` (tenant token + admin + marker) on platform-wide surfaces that were previously `require_role_dep("admin")`: `POST /tenants`, cache admin, ER run/resolve/quality/merge/unmerge, marketplace listings writes, domain marketplace, master-data writes + ingestion, Phase 7 `record_disposition`, admin_demo, benchmarks, demo, metrics, notifications admin, runtime admin. SAML config now rejects another tenant's config (403). Owner-plane routes (`require_owner_role_dep`) inherit the marker check via `owner_auth`. |

No second admin system: the marker is one boolean read by the existing role dependencies.

## 2. Proof

Disposable Postgres `pilot178-pg` (DB `salesos_pilot178`, head `b2c3d4e5f6a8`, restricted role `salesos_app`), runner `salesos-pilot-backend:local`. No `salesos` / `salesos_test` / production write.

`tests/integration/test_platform_owner_marker_db.py::test_platform_owner_requires_explicit_marker`:

| Step | Result |
|---|---|
| Self-register | 201; user is `admin` of the new tenant |
| Self-registrant `/owner/login` | 403 |
| Self-registrant `POST /tenants` | 403 |
| Self-registrant platform-owner probe | 403 |
| Owner token forged for unmarked admin → owner-only probe | 403 |
| Invite | invitee role `user`, not admin; platform probe 403 |
| SAML config for another tenant | 403 |
| Re-register with existing `tenant_id` | 400 |
| Designated owner (marker set in test DB) `/owner/login` | 200, token has no `tenant_id` |
| Designated owner: owner probe, platform probe, `POST /tenants` | pass |

- **Green:** integration + 3 updated unit files (cache, marketplace listings, domain marketplace admin gates) = **17 passed**.
- **Red 1:** HEAD `owner_auth.py` + `identity/router.py` + `identity/service.py` → fails at invite step (`user lacks permission: user.create` — self-registrant was not admin).
- **Red 2:** HEAD `owner_auth.py` only → fails at the forged-owner-token step (`{"ok":true}`), proving the per-request marker check.
- Migration upgrade/downgrade round trip verified on the disposable DB.

### Optional UI cleanup (done)

`salesos/frontend/src/app/v3/reviews/[id]/page.tsx` no longer sends `decided_by=manager` (server uses the JWT subject since `39bb564d`). New `reviews/__tests__/detail-page.test.tsx` asserts the exact decide URL without `decided_by`. In the C: mirror (no install): reviews Jest 3 suites / 10 tests pass; red (field re-added) fails; full `tsc --noEmit` exit 0; eslint exit 0; prettier clean.

## 3. Disclosures / residual risk

1. **Existing admins lose owner access until marked.** Any deployment must set `is_platform_owner=true` for the real operator(s) after migrating; the marker was set only in the disposable DB here.
2. Migration `b2c3d4e5f6a8` is required before this code runs; not applied to `salesos` or production.
3. Owner `/refresh` does not re-check the marker; every owner-protected request does (dependency), so a refreshed token for a de-marked user is still rejected on use.
4. Previously, any tenant admin could invoke global master-data, ER and ingestion writes; now platform-owner only. Tenant-admin workflows that relied on this will get 403.
5. Phase 7 review routes remain env-gated; `record_disposition` reviewer and ER `run_matching` `tenant_id` are still client-supplied (pre-existing, not changed).
6. SAML config store is in-memory (pre-existing).
7. Owner routes still need `X-Tenant-Id` because `users` has FORCE RLS (pre-existing). Owner requests add two small lookups.
8. `v3/approvals/[id]/page.tsx` still sends `decided_by: "current-user"` — out of scope.
9. No browser E2E, no Railway build/deploy.
