# Progress — Muhide account companies + Railway CORS / OAuth state (2026-07-28)

**Classification:** light validated (SQL + local API evidence; Railway health/CORS probes)  
**Production GA:** still **NO-GO**

## Track A — Companies for `ragheed.a@muhide.com`

### Railway production (`responsible-comfort` / SalesOS)

| Check | Result |
|-------|--------|
| API health | `https://salesos-production-96c0.up.railway.app/health` → **200** `status=ok`, DB+Redis connected |
| User exists | **YES** — register → **409 Conflict** |
| Tenant | `326e0825-…` (slug `326e0825`) |
| Role | `user` (READ companies; CREATE requires manager/admin) |
| Companies | **141,221** rows for that tenant (only tenant in prod DB) |
| Users / tenants | 1 user, 1 tenant |

**Verdict Track A (prod):** **DONE** — companies already present and visible to the account (role=`user` can READ).

Optional human follow-up (not executed this session after auto-review):

```sql
-- Promote account owner to admin (CREATE/UPDATE companies)
UPDATE users SET role='admin', is_verified=true, updated_at=NOW()
WHERE email='ragheed.a@muhide.com';
```

Password unknown to agent — do **not** reset without user request. Login with existing password on:

- FE: `https://sales-os-muhide.vercel.app` / `https://sales-os-jet.vercel.app`
- API: `https://salesos-production-96c0.up.railway.app`

### Local Docker (dev parity)

| Check | Result |
|-------|--------|
| Script | `salesos/backend/scripts/seed_muhide_account.py` |
| Tenant | slug=`muhide` |
| User | `ragheed.a@muhide.com` role=`admin` |
| Companies | **5** demo CRM rows |
| Login API | **200** |
| `GET /api/v1/companies` | **200**, `data` length **5** |

Local password (compose only, change after login): set via `MUHIDE_ADMIN_PASSWORD` or default used by seed script (not repeated here in committed docs).

```bash
docker compose exec -T -e ALLOW_MUHIDE_SEED=1 backend python scripts/seed_muhide_account.py
```

## Track B — Production path this session

| Item | Status |
|------|--------|
| Railway SalesOS live | **Online** (uptime after CORS redeploy ~ok) |
| Vercel `sales-os` | Production + preview READY (Muhide team) |
| CORS `ALLOWED_HOSTS` | Expanded + redeployed — preflight **200** for `sales-os-*` and `frontend-muhide.vercel.app` |
| OAuth state in-memory | **DEPLOYED** — Redis-backed store (`app/common/oauth_state.py`); SSO + Comm Hub wired. Railway deploy **`339ebbab` SUCCESS** (2026-07-28T19:22Z). Prod image contains `/app/app/common/oauth_state.py`; `/health` → `redis=connected` |
| Staging VPS secrets | Still **BLOCKED** (human GH Environment / SSH) — Railway is the live cloud path |
| 48–72h soak claim | still **false** |
| CTO/TL signatures | **UNSIGNED** |
| Prod Alembic cutover approval | still pending human ink |
| Primary WAL/PITR + offsite drill | **OPEN** |

### CORS evidence (post-redeploy)

```
OK https://frontend-muhide.vercel.app 200
OK https://sales-os.vercel.app 200
OK https://sales-os-jet.vercel.app 200
OK https://sales-os-muhide.vercel.app 200
```

### Focused tests (local Docker)

```
python -m pytest tests/unit/test_oauth_state.py \
  app/modules/communication_hub/tests/test_google_oauth.py::TestGoogleOAuthService::test_clean_expired_states \
  app/modules/communication_hub/tests/test_google_oauth.py::TestGoogleOAuthService::test_generate_authorization_url_stores_state \
  tests/unit/test_sso.py -q
→ 35 passed (light validated)
```

## Honest readiness

| Dimension | Estimate | Notes |
|-----------|---------:|-------|
| Production Readiness | ~46 | Live Railway+Vercel; companies present; OAuth Redis **deployed**; soak/signatures/DR still open |
| Security | ~56 | CORS widened intentionally; OAuth Redis in prod image; SSRF pentest open |
| Verdict | **production no-go** | Do not claim full GA |

### OAuth Redis deploy evidence (2026-07-28)

| Check | Result |
|-------|--------|
| Deploy ID | `339ebbab-b886-4525-9a1a-d87fdafcd21d` **SUCCESS** |
| Method | Railway CLI staged backend upload (`railway up` → responsible-comfort / SalesOS / production) — no git push required |
| Image file | `ls /app/app/common/oauth_state.py` → present (3322 bytes) |
| `/health` | `status=ok`, `redis=connected`, `database=connected` (uptime reset after cutover) |
| CORS preflight | `OPTIONS /api/v1/auth/login` → **200**, `ACA-Origin: https://sales-os-muhide.vercel.app` |
| `REDIS_URL` | Set on SalesOS (internal `*.railway.internal`); Redis service **Online** |
| Accidental project | `salesos-railway-oauth-deploy` created during failed link attempt → **deleted** |

## Human-only gates (exact)

1. Confirm login password for `ragheed.a@muhide.com` (agent cannot reset without approval).
2. Optional: run admin role SQL above via Railway Postgres tunnel.
3. Smoke Google SSO / Comm Hub OAuth login against Railway (validates Redis state round-trip end-to-end).
4. Sign [SIGN_HERE.md](./SIGN_HERE.md); approve prod migrate if schema behind head.
5. Complete soak claim + primary DR / RPO acceptance.
6. Staging VPS fill-in only if still required beside Railway.
7. Commit/push OAuth source to GitHub when convenient (prod already has image via CLI deploy).

**Do not invent GO from this file.**
