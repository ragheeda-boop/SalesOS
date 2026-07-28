# Progress — Wave 16 Full GA push (2026-07-28)

**Decision:** Production GA still **NO-GO**  
**Classification:** production no-go (honest)  
**Scores (this run):** Production Readiness ~**48** / Security ~**58** (up from ~46 / ~56; still no-go)

## What this wave closed (agent-executable)

| Item | Evidence |
|------|----------|
| Live Railway API health | `GET https://salesos-production-96c0.up.railway.app/health` → `status=ok`, `database=connected`, `redis=connected` |
| CORS preflight | `OPTIONS /api/v1/auth/login` Origin `https://sales-os-muhide.vercel.app` → **200** + `ACA-Origin` echo |
| Unauth companies | `GET /api/v1/companies` → **401** `Not authenticated` |
| CSRF on register | missing CSRF → **403** |
| Vercel FE | `sales-os-muhide.vercel.app` **200**; `sales-os-jet.vercel.app` **200**; `sales-os.vercel.app` **307** |
| Muhide companies | Railway SSH probe → **141,221** companies; user `ragheed.a@muhide.com` role=`user` |
| OAuth Redis store | still present `/app/app/common/oauth_state.py`; redis connected |
| `GOOGLE_ENCRYPTION_KEY` | **SET** on Railway SalesOS (value redacted); verified `GOOGLE_ENCRYPTION_KEY_SET True` on live instance after redeploy `b1b183a3` |
| SSRF delivery pin redesign | committed `04b9ace`; focused Docker pytest **52 passed**; **live image** contains `pinned_ips must be non-empty` + delivery refuse-unpinned (SSH grep on SalesOS) |
| Git sync | `git push origin master` → `cc7111d..04b9ace` |
| Railway deploys | SUCCESS `b1b183a3` (GEK env redeploy, live); incremental `railway up` `8e55bdb0` **FAILED** (archive missing Dockerfile — builder only saw `.env.example`); retry `9a759cfc` **SKIPPED** — **not required** because SSRF code already present on live image |
| Prod Alembic status | **0046** (head in repo **0049**) — **not upgraded** this run |
| Smoke (Wave 16) | `/health` **200**; CORS preflight **200**; `/api/v1/companies` unauth **401** |

## Soak honesty

| Field | Value |
|-------|-------|
| `soak_complete_claim` | **false** |
| Cloud soak start | Railway `/health` loop started **2026-07-28T20:29:48Z** — `evidence/wave16-soak/` |
| Target | 48–72h — **not complete** |
| Prior local soak | still incomplete / high fail rate — does **not** set claim true |

## Explicitly NOT done (human / approval walls)

1. CTO + Tech Lead signatures — [SIGN_HERE.md](./SIGN_HERE.md) **UNSIGNED**
2. Production Alembic `upgrade head` (**0046 → 0049**) — **BLOCKED** pending backup + explicit approval
3. Staging VPS secrets / cloud tabletop / SSRF pentest on staging — **BLOCKED**
4. Primary WAL/PITR + offsite restore drill — **OPEN**
5. RPO acceptance — **UNSIGNED**
6. Human OAuth login smoke (password unknown to agent)
7. Optional SQL: promote `ragheed.a@muhide.com` to `admin` (CREATE/UPDATE)
8. PRC AI marketing sentence / AI honesty human sign-off
9. Hypercare Day-0 roster (starts only after signed GO)

## Exact approval command for prod migrate (do not run until backup evidence)

```text
# After pg_dump / Railway snapshot evidence recorded:
cd salesos
railway ssh -s SalesOS -- alembic current   # expect 0046
railway ssh -s SalesOS -- alembic upgrade head   # target 0049
railway ssh -s SalesOS -- alembic current   # expect 0049
curl -sS https://salesos-production-96c0.up.railway.app/health
```

Revisions pending: **0047** `google_accounts`, **0048** calendar sync token, **0049** unique provider event IDs.

## Score rationale

- **PR ~48:** live Railway+Vercel, companies present, OAuth Redis+encryption key, git+prod deploy synced; still missing soak claim, signatures, prod migrate, DR.
- **Sec ~58:** SSRF pin redesign in prod image path + unit evidence; GEK set; CSRF/401 smoke; pentest still OPEN; no forged “production-secure”.

**Do not claim Full GA from this file.**
