# Independent re-audit — SalesOS GA / engineering (2026-07-29)

**Clock:** 2026-07-29 (user / agent session)  
**Auditor stance:** Prior `GA_STATUS` / Wave 15–16 progress treated as **hypotheses only**; re-verified against source + live endpoints.  
**Product:** SalesOS (`salesos/`) platform intent  
**Authority framework:** [00-EXECUTIVE-SUMMARY.md](./00-EXECUTIVE-SUMMARY.md), [PRODUCTION_PLAN.md](./PRODUCTION_PLAN.md), [AI_HONESTY.md](./AI_HONESTY.md)  
**Decision:** **NO-GO** for Production GA  
**Classification:** **production no-go**  
**Validation label:** **light validated** (live HTTP + Railway SSH code/SQL + static review). Focused Docker pytest **not completed** this run (container `pytest` hung / PATH issues).

> Do **not** invent GO, browser pass, or green full suites from this note.  
> Secrets (DB/Redis/encryption key material) are **redacted** — never paste Railway variable values into docs.

---

## 1. Executive verdict

| Release | Decision |
|---------|----------|
| **Production GA** | **NO-GO** |
| External pilot | **NO-GO** |
| Internal engineering preview | Possible with conditions (data live; AI off; migrate/soak/signatures still open) |

**Why NO-GO (evidence-backed):** cloud soak **not complete** (and appears **stalled**); prod Alembic **0046** vs repo head **0049**; CTO/TL signatures **UNSIGNED**; staging SSRF pentest **OPEN**; primary WAL/PITR + offsite DR **OPEN**; health shows `graph=unavailable`, `kafka=in_memory`.

---

## 2. Scoreboard (independent)

| Dimension | Audit baseline (2026-07-22) | Wave 16 claim | **This re-audit** | Rationale |
|-----------|----------------------------:|--------------:|------------------:|-----------|
| **Production Readiness** | **38** | ~48 | **~47** | Live Railway+Vercel+data confirmed; soak stalled (~1.25h / 16 samples); schema drift; DR/signatures open; kafka/graph gaps. Slightly below Wave 16 claim. |
| **Security** | **48** | ~58 | **~57** | Live SSRF pin + OAuth Redis code path + GEK set + CSRF/401/CORS smoke; staging pentest still OPEN; KG empty-`tenant_id` residual paths; webhook service still defaults InMemory if mis-wired. |
| Testing | 52 | improved (local) | **not re-validated** this run | Prior focused suite claims exist; this run did not finish Docker pytest. |
| DevOps / Deploy | 62 | Railway live | **Railway live** | Active SUCCESS deploy `b1b183a3`; later FAILED/SKIPPED attempts; service still Online. |
| AI honesty | — | gated | **gated** | Default `feature_ai_copilot=False` in code; Railway env showed flag false (name-level); FE Decision package still STUB. |

**Verdict unchanged: Production GA = NO-GO.**

---

## 3. Live probes executed (2026-07-29)

### API / FE

| Probe | Result |
|-------|--------|
| `GET https://salesos-production-96c0.up.railway.app/health` | **200** `status=ok`, `database=connected`, `redis=connected`, `cache=connected`, `graph=unavailable`, `kafka=in_memory`, `rate_limiter=active`, `version=3.1.0` |
| `OPTIONS /api/v1/auth/login` Origin `https://sales-os-muhide.vercel.app` | **200** + `Access-Control-Allow-Origin` echo + credentials |
| `GET /api/v1/companies` (no auth) | **401** |
| `POST /api/v1/auth/register` (no CSRF) | **403** |
| `GET /api/v1/identity/csrf-token` | **200** (path under identity router; bare `/csrf-token` → 404) |
| `GET /api/v1/copilot/status` (no auth) | **401** |
| Vercel `sales-os-muhide.vercel.app` | **200** |
| Vercel `sales-os-jet.vercel.app` | **200** |
| Vercel `sales-os.vercel.app` | **307** |

### Railway ops

| Check | Result |
|-------|--------|
| `railway status` | SalesOS **Online**; deployment ID `b1b183a3…` (SUCCESS); UI also notes later Deploy failed noise |
| `railway deployment list` (top) | SUCCESS `b1b183a3` → FAILED `8e55bdb0` → SKIPPED `9a759cfc` |
| `railway ssh … alembic current` | **0046** |
| `railway ssh … alembic heads` | **0049 (head)** |
| GEK / AI flag / Redis | Name-level: `GOOGLE_ENCRYPTION_KEY` **SET**, `FEATURE_AI_COPILOT=false`, `REDIS_URL` **SET**, `ENV=production` (values **redacted**; do not commit) |

### Account / data (read-only)

| Check | Result |
|-------|--------|
| `ragheed.a@muhide.com` | `USER_FOUND True`, `ROLE user`, **`COMPANIES_COUNT 141221`** |
| Method | Railway SSH + asyncpg `SELECT COUNT(*)` scoped by user tenant (no writes) |

### Soak honesty

| Field | Evidence |
|-------|----------|
| File | `evidence/wave16-soak/health-loop.jsonl` |
| Samples | **16** lines, all `ok=True` / HTTP 200 |
| Window | `2026-07-28T20:29:52Z` → `2026-07-28T21:45:16Z` (~**1.25h**) |
| `soak_complete_claim` | **false** |
| Status | Loop appears **stalled** (no new samples through re-audit clock); **not** 48–72h |

---

## 4. Code / security verification (spot)

| Area | Status | Evidence |
|------|--------|----------|
| Decision Center `get_decision(tenant_id)` | **Fixed in code** | `domains/decision_center/postgres_repo.py` filters metadata `tenant_id` |
| Webhook SSRF + IP pin | **Fixed in code + live image** | `url_safety.py` HTTPS/private-IP rules + `_PinnedIPBackend`; live grep `pinned_ips must be non-empty`; service refuses unpinned delivery |
| Webhook persistence | **Partial** | Router wires **Postgres** repos; `WebhookService.__init__` still defaults to **InMemory** if caller omits repos |
| CSRF bypass via bare `X-API-Key` | **Fixed in code** | `middleware.py` skips CSRF only after ApiKeyMiddleware auth |
| Forecast `demo-1` | **Fixed in non-demo path** | `commercial.py` loads tenant opportunities when not demo; demo path still hardcodes |
| `GOOGLE_ENCRYPTION_KEY` | **Fixed in code + set live** | CommHub raises if unset; no SECRET_KEY fallback |
| OAuth state Redis | **Fixed in code + live image** | `oauth_state.py` `Redis.from_url` + `setex`; in-memory **fallback** remains |
| AI flag / FE stub | **Honest** | `feature_ai_copilot=False` default; `packages/platform/decision/index.ts` STUB throws |
| Activity reply_rate | **Improved** | Thread-based SQL in `email_engine.py`; vertical still **pilot-ready with conditions** |
| KG SQL repo | **Partial residual** | Several methods still allow empty `tenant_id` → unscoped `graph_edges` / company lookups |
| Dynamic SQL | **Mostly parameterized** | `text()` + bound params common; demo audit uses validated table names |
| Docker image practices | **Improved (spot)** | Backend Dockerfile: non-root `USER`, `tini` ENTRYPOINT, Poetry install |

---

## 5. Issue table

| Issue | Severity | Verified? | Status | Evidence |
|-------|----------|-----------|--------|----------|
| 48–72h soak incomplete / stalled | P0 (GA gate) | Yes | **open** | wave16 jsonl: 16 samples / ~1.25h; `soak_complete_claim: false` |
| Prod Alembic drift 0046→0049 | P0 (ops) | Yes | **open** | SSH `alembic current`/`heads` |
| CTO/TL SIGN_HERE UNSIGNED | P0 (governance) | Yes | **open** | [SIGN_HERE.md](./SIGN_HERE.md) |
| Staging cloud tabletop + SSRF pentest | P0/P1 | Docs + no cloud creds | **open** | Wave 12 staging unblock docs |
| Primary WAL/PITR + offsite restore | P1 | Docs | **open** | [PROGRESS-WAVE10-DR-GAPS.md](./PROGRESS-WAVE10-DR-GAPS.md) |
| RPO acceptance UNSIGNED | P1 | Docs | **open** | SIGN_HERE / Wave 10 |
| Graph unavailable on prod health | P1 | Yes | **open** | live `/health` |
| Kafka `in_memory` on prod health | P1 | Yes | **open** | live `/health` |
| Incremental Railway deploys FAILED/SKIPPED | P2 | Yes | **partial** | list: FAILED archive Dockerfile; service still on SUCCESS image |
| Cross-tenant Decision IDOR | P0 (orig) | Code | **fixed** | repo requires `tenant_id` |
| Webhook SSRF | P0 (orig) | Code + live | **fixed** (pentest still open) | live pin + refuse unpinned |
| CSRF bare API-key bypass | P1 (orig) | Code | **fixed** | middleware comment PROD-W5-001 |
| SECRET_KEY reuse for Google tokens | P1 | Code + env name | **fixed** | GEK required + set |
| OAuth state in-memory only | P1 | Code + live | **fixed** (fallback remains) | Redis `setex` in image |
| FE Decision stubs marketed as GA | P1 | Code | **mitigated** | STUB + AI_HONESTY; PRC human sign-off open |
| Activity fake metrics | P1 | Code | **partial / pilot** | thread reply_rate; not Full GA |
| Unauth companies leak | P0 | Live | **fixed** | **401** |
| CORS for Vercel muhide | P1 | Live | **fixed** | preflight **200** |
| Muhide companies missing | ops | Live SQL | **OK** | **141,221** |

---

## 6. Delta vs last claimed status (Wave 16 / GA_STATUS 2026-07-28)

| Topic | Prior claim | This re-audit |
|-------|-------------|----------------|
| Verdict | NO-GO | **NO-GO** (unchanged) |
| PR / Sec scores | ~48 / ~58 | **~47 / ~57** (slightly more conservative) |
| Health / CORS / 401 | PASS | **Reconfirmed PASS** |
| Companies | 141,221; role=`user` | **141,221; role=`user`** (Wave 15 “admin” claim contradicted) |
| Alembic | 0046 vs 0049 | **Reconfirmed** |
| GEK / OAuth Redis / SSRF pin | set / live | **Reconfirmed** (code in image) |
| Soak | started; not complete | **Still incomplete; evidence stalled at ~1.25h** |
| Signatures | UNSIGNED | **UNSIGNED** |
| Pytest this run | 52 PASS (prior) | **not re-validated** |
| Deploy hygiene | SUCCESS GEK redeploy | SUCCESS still serving; later FAILED/SKIPPED noise |

Stale note: [PROGRESS-COMMHUB-ACTIVITY-HONESTY.md](./PROGRESS-COMMHUB-ACTIVITY-HONESTY.md) still says “OAuth state still in-memory” — **superseded** by Redis-backed `oauth_state.py` + live `setex` (fallback remains).

---

## 7. Ordered remaining gates to Full GA

1. Restart / complete **48–72h** Railway soak with TL review → only then set `soak_complete_claim` with evidence.  
2. Approved **prod backup** + Alembic **`upgrade head` (0046→0049)** + post-migrate health.  
3. Staging (or equivalent) **SSRF pentest** + cloud deploy/rollback tabletop.  
4. Primary **WAL/PITR** + offsite restore drill; human **RPO** acceptance.  
5. Human **CTO + Tech Lead** ink on [SIGN_HERE.md](./SIGN_HERE.md) (agents must not forge).  
6. PRC **AI honesty** sentence; keep copilot gated until evidence-validated.  
7. Close ops residuals: Neo4j/graph health, Kafka not `in_memory` for GA path, deploy archive hygiene.  
8. Optional: confirm authenticated OAuth login smoke; role elevation for `ragheed.a@muhide.com` only with explicit approval.

---

## 8. Commands run (this session)

```text
railway status
railway deployment list -s SalesOS --limit 5
# HTTP: /health, CORS OPTIONS login, GET /companies, POST /register, Vercel origins, /api/v1/copilot/status
railway ssh -s SalesOS -- alembic current    # 0046
railway ssh -s SalesOS -- alembic heads      # 0049
railway ssh -s SalesOS -- grep … url_safety.py / oauth_state.py / service.py
# read-only company count via SSH+asyncpg for ragheed.a@muhide.com
# docker compose exec pytest … — attempted; not completed (PATH/hang)
```

**Validation:** **light validated** — executable live + SSH + static. **Not** build-validated full FE suite. **Not** browser GA. **production no-go**.

---

## 9. Files updated by this re-audit

- This note: `PROGRESS-REAUDIT-2026-07-29.md`
- Scoreboard: [GA_STATUS.md](./GA_STATUS.md)

**Do not claim Full GA from this re-audit.**
