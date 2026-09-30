# 179 — Pilot next steps (2026-09-30)

**Type:** documentation only. No product code changed. No tests run for this report.
**Branch:** `fix/login-and-keys`. Written at HEAD `a3f89cdd` (same as `origin/fix/login-and-keys`).
**Status:** Production **NOT APPROVED**. G2–G16 and G8 stay closed. `feature_ai_copilot` stays `False`.

This report records what the pilot loop finished (reports 176–178, AGENTS §217–219) and what is still open, in order. Results below are the ones reported by the implementing sessions; this report re-ran none of them.

---

## 1. Done and pushed (through `a3f89cdd`)

| Commit | What changed | Evidence |
|---|---|---|
| `0f217957` | Registration no longer hangs (`RateLimitMiddleware` dispatched the app twice) | report 176 |
| `ac6d1b28` | Private JWKS key no longer copied into the main backend Docker image; production stage uses `SALESOS_JWKS_KEY_DIR=/data/jwks` | report 176 |
| `5c94f07c` | `/reviews/pending` and `/reviews/kpis` no longer 404 (static routes before `/reviews/{review_id}`) | report 176 |
| `85947d22` | Self-registration can no longer join an existing tenant; `tenant_id` in the body returns 400 | report 176 |
| `39bb564d` | Review `decided_by` comes from the JWT (query parameter ignored). `/invite` fails closed if role assignment fails; the invited user stays role `user` | report 177 |
| `df41b2df` | Railway backend and Celery Dockerfiles get the same JWKS treatment as `ac6d1b28` | report 177 |
| `7567ce1f` | Review detail page no longer sends `decided_by=manager` | report 178 |
| `d262f6a0` | Owner login needs `users.is_platform_owner` (migration `b2c3d4e5f6a8`); tenant admin alone is not enough. A self-registered user becomes tenant admin of their own tenant only | report 178 |

Proof cited by report 178: 17 backend tests on a disposable database; frontend Jest 10/10; secret scan clean apart from one fake test password. The production database `salesos` was not written. The `pilot178-*` containers were removed.

**Not verified:** the Railway images from `df41b2df` were never built or deployed. They need a writable volume mounted at `/data/jwks` before any Railway build.

---

## 2. Next steps, in order

### Code (still open)

1. **Owner `/refresh` does not re-check `is_platform_owner`.** Each owner request re-checks the flag, but a refresh does not. So after the flag is removed, the refresh token keeps minting owner tokens until it expires. Fix: re-check the flag on refresh. Prove it with a focused test that clears the flag, then asserts the refresh is rejected.
2. **Approvals UI still sends a client actor.** `salesos/frontend/src/app/v3/approvals/[id]/page.tsx:53` sends `decided_by: "current-user"`. The server ignores it. Remove the field from the client so the UI does not look like it supplies the actor. Related, not yet assessed: `v3/contracts/[id]/page.tsx:47` sends `signed_by: "current-user"`. Check whether the server derives the signer from the JWT before changing it.
3. **Phase 7 reviewer identity and the ER-path `tenant_id` still come from the client.** Not closed. Inspect the routes first, then change them. Do not auto-merge and do not auto-adjudicate G2/G4.
4. **End-to-end seller journey has not been run in a browser.** The path is: register → a tenant-admin action → invite an ordinary user → owner login is denied. Run it on a disposable stack only.

### Operator (needs the user)

5. **Nobody has `is_platform_owner` after the migration.** Until the user names the real platform-owner accounts, `/owner/login` works for nobody. Do not write production `salesos`, and do not guess which accounts to mark.

### Not a pilot code task

6. G2–G16 and G8 stay closed; production is **NOT APPROVED**; `feature_ai_copilot` stays `False`. No Railway deploy in this step. The Railway deploy needs the `/data/jwks` volume and the owner accounts from step 5 first.

---

## 3. Working-tree hygiene

These local files are untracked and stay untracked. They are not part of this commit:

- `salesos/docker-compose.windows.yml`
- `salesos/docs/architecture/`
- `salesos/docs/discovery/`
- `salesos/docs/ops/`
- `salesos/docs/roadmap/PRODUCTIZATION_ROADMAP.md`
- `scripts/` (contains `discover_*.py`)

This commit contains only this report and AGENTS.md §220.
