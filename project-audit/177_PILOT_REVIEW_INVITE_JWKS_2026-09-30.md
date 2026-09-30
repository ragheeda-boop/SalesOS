# 177 — Pilot follow-up: review actor, invite fail-closed, Railway JWKS (2026-09-30)

**Scope:** follow-up to report 176's open items. Branch `fix/login-and-keys`. Nothing touched production DB `salesos`. No Railway deploy. Gates G2–G16 and G8 unchanged. `feature_ai_copilot` unchanged. Production **NOT APPROVED**.

## 1. Commits

| Commit | Change |
|---|---|
| `39bb564d` | `decide_review` takes the actor from the JWT. `invite_user` fails closed when role assignment fails. 6 new tests. |
| `df41b2df` | `Dockerfile.railway` and `Dockerfile.railway.celery`: builder stage deletes `app/modules/identity/_keys`; production stage sets `SALESOS_JWKS_KEY_DIR=/data/jwks` (same fix as `ac6d1b28`). |

## 2. Review actor (`decided_by`)

- **Before:** `POST /reviews/{id}/decide` read `decided_by` from a query parameter, so any caller could record any name as the reviewer.
- **After:** `decided_by: str = Depends(get_current_user_id)`. The query parameter is ignored.
- **Proof:** a TestClient request with `?decided_by=spoofed-manager` stores `jwt-user-1`, the JWT subject. The route dependency is asserted to be `get_current_user_id`.
- **Frontend:** `salesos/frontend/src/app/v3/reviews/[id]/page.tsx:45` still sends `decided_by=manager`. The backend now ignores it, so it has no effect. Left unchanged; remove it in a later frontend cleanup.

## 3. Invite fail-closed

- **Before:** `/invite` caught role-assignment errors and still returned 201 with the temporary password. The user existed, but with the wrong role.
- **After:** if `update_user_role` raises, or the role on the user afterward is not the requested one, the session rolls back and the route returns 500 `Invite failed: role assignment did not complete`. The detail contains no password.
- A default `role="user"` invite makes no role call, so invited users stay ordinary users.
- The existing success response, which includes `temporary_password`, is unchanged. The password is not newly logged or stored anywhere.

## 4. Test evidence (disposable Docker container, no DB)

| Run | Result |
|---|---|
| Red: new tests against `HEAD` source (`git show HEAD:<path>`) | 4 failed, 2 passed. The 2 that passed are the default-invite and direct-call tests, which HEAD already satisfied. |
| Green: new file + `test_approval_route_identity.py` on fixed code | **9 passed** |
| Related regression (identity, register, review, approval suites) | **36 passed** |

## 5. Railway images

- Both Railway Dockerfiles build from the repo root, which has **no `.dockerignore`**. `_keys/` is git-ignored (`0367e39d`) but still sits in the local working tree, so `COPY salesos/backend/app/ app/` could bake a private signing key into the image.
- The builder stage now deletes that directory. The production stage points `SALESOS_JWKS_KEY_DIR` at `/data/jwks`, which should be a mounted volume so keys survive container recreation.
- **Not verified:** no Railway image was built, and nothing was deployed. Railway still needs a volume at `/data/jwks`, or keys are regenerated on every redeploy and all issued tokens become invalid.

## 6. Registration: first user as tenant admin — ON HOLD, not implemented

The requested behaviour was: the self-registered creator becomes `admin` of their own tenant, but not platform owner.

**Blocker:** `POST /api/v1/identity/owner/login` (`identity/router.py:445-470`) mints an Owner Platform token (`salesos-owner-platform`) for any active user with `users.role >= admin`. No separate platform-owner marker exists. Making every self-registrant `admin` would therefore let anyone on the internet obtain Owner Platform tokens. Those tokens carry cross-tenant billing and owner powers (`require_owner_role_dep("admin")`, DEC-158). That violates the stated constraint.

**Options (need a decision):**
- **(a)** Add an explicit platform-owner marker: a settings allowlist of owner user IDs or emails, or a column plus a migration. Gate `/owner/login` and `require_owner_role_dep` on that marker instead of on `role == admin`.
- **(b)** Keep role-based owner access but exclude self-registered admins, e.g. with a `self_registered` flag checked by `/owner/login`. This is weaker than (a), because any future path that grants `admin` reopens the hole.

Recommendation: (a). After it lands, the registration change is small (assign `admin` inside the new tenant) and can be proven with the three checks already specified.

**Current state (unchanged):** registration creates a new tenant, assigns role `user`, and rejects a supplied `tenant_id` with 400 (`85947d22`). The pilot therefore still has no in-app way to create a first tenant admin.

## 7. Other finding (documented, not fixed)

`/invite` accepts any `role`, including `admin`, from any caller holding `user:CREATE`. In the default matrix (`sdk/permissions.py`) only `admin` holds `user:CREATE`, so there is no escalation today. If a custom role is ever granted `user:CREATE`, its holders could create admins. Recommended guard: an inviter may not assign a role above their own.

## 8. Still open

1. Owner-marker decision, before first-user admin (§6).
2. Invite role ceiling (§7).
3. Frontend's stray `decided_by=manager` parameter (§2).
4. Railway image build and a `/data/jwks` volume (§5).
5. The E2E journey test is still not run.
