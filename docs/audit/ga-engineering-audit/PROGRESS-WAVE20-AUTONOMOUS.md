# Progress — Wave 20 autonomous production mission (2026-07-29)

**Mission stance:** Finish all engineering not requiring human credentials. Google OAuth = external dependency.  
**Decision:** **NOT READY FOR PRODUCTION** (human + operational blockers remain)  
**Classification:** production no-go  
**Validation:** focused **build validated** (Docker pytest + FE lint/tsc/build); live probes **light validated**

---

## Executive snapshot

| Area | Status |
|------|--------|
| Eng checklist (Wave 20) | **COMPLETE** except external deps |
| Prod health | **200** `ok`; Alembic **0049**; `graph=connected` (Wave 19 follow-up); `kafka=in_memory` |
| Staging health | **200** `ok`; Alembic **0049**; `graph=connected` |
| Google / Emp360 sync | **BLOCKED on human OAuth** — `google_accounts=0` until connect |
| First-sync after OAuth | **SHIPPED** — BE `schedule_initial_sync` + FE auto-trigger + `sync=started` redirect |
| Contacts from sync | **SHIPPED** — company-linked upsert only (no invented orphans) |
| Celery hub sync | **PARTIAL** — added `celery-worker` + `celery-beat`, but staging deployments still failing (latest build errors: worker `08f50b72-d5d5-4f05-9773-e0ef0fe7dbf3` + beat `8e5c93fb-1661-420d-9c39-a3fb9fa2d374`: couldn't locate `Dockerfile` in Railway code archive; earlier failures: `preDeploy init_db` failing with missing `sqlalchemy`) |
| Fake metrics | Expansion + opportunity detail no longer invent SAR from score×1e6 |
| Backend deploy | staging `1b449192` **SUCCESS**; prod `dccff73a` **SUCCESS** |
| FE | lint warnings-only; `tsc --noEmit` ok; `npm run build` exit 0; Git Vercel prod **READY** (`dpl_GmRgWV4UJDB5zymmDrX1rXMeExhx`); CLI root-dir doc added |
| Soak / SIGN_HERE | soak loop **appending** (~5m); claim **false**; unsigned |
| Prod Neo4j | **DONE** — `neo4j-prod` + `/data` volume; SalesOS `NEO4J_*` wired; deploy `6163f9e3` **SUCCESS** |

---

## Verified this session (evidence)

### Live probes
- Prod `https://salesos-production-96c0.up.railway.app/health` → **200** ok
- Staging `https://salesos-staging.up.railway.app/health` → **200** ok, graph=connected
- Prod CSRF → **200**; unauth `/api/v1/companies` → **401**
- Alembic staging+prod → **0049 (head)**

### Engineering shipped
1. **OAuth → first sync:** `initial_sync.schedule_initial_sync` from Google callback; FE `runFirstSync` on `google=connected`; redirect includes `sync=started`.
2. **Contact pipeline:** `contact_sync.upsert_contacts_from_addresses` wired into Gmail + Calendar process paths (company_linker match required).
3. **Emp360/Company360 refresh contract:** FE `invalidatePostSync` clears employee / company360 / contacts / dashboard query keys after sync.
4. **Celery Comm Hub:** tasks + beat entries; celery_app include path; Railway has **no** worker/beat service → periodic sync degraded until ops adds worker.
5. **Honesty:** ExpansionContainer + OpportunityDetailContainer no longer invent SAR.
6. **Tests:** focused Docker pytest communication_hub + health heuristic → **99 passed**.
7. **Cleanup:** removed `_tmp_*` probe scripts under `salesos/backend/scripts` and `salesos/scripts`.
8. **OAuth path test:** authorization URL reaches Google consent endpoint (static/unit; no real consent).

### Wave 19 follow-up (2026-07-29, agent 81626343)

1. **Prod Neo4j:** added Railway service `neo4j-prod` (`neo4j:5-community`, volume `/data`), wired SalesOS `NEO4J_URI=bolt://neo4j-prod.railway.internal:7687`, auth sync + volume reset after first boot mismatch. Live `/health` → **`graph=connected`**. Deploy ids: neo4j-prod `6163f9e3`; SalesOS redeploy after wiring.
2. **Vercel root-dir:** GitHub → project `sales-os` builds **READY** with repo `ragheeda-boop/SalesOS`. Double path `salesos/frontend/salesos/frontend` is a **CLI + Root Directory stack** issue — documented in `salesos/frontend/docs/VERCEL_DEPLOY.md` (use Git push or empty Root Directory when deploying from `salesos/frontend`). Local Vercel token expired (403); dashboard/API re-auth needed for CLI PATCH.
3. **Soak:** `evidence/wave16-soak/health-loop.jsonl` still appending (~5m); not restarted (not stalled).
4. **Celery worker/beat (staging) — still failing:** attempted Railway config updates to get `celery-worker` / `celery-beat` running, but latest builds are failing at Railway build stage with `couldn't locate the dockerfile at path Dockerfile in code archive` (worker `08f50b72-d5d5-4f05-9773-e0ef0fe7dbf3`, beat `8e5c93fb-1661-420d-9c39-a3fb9fa2d374`). Operational fix pending: correct Railway build context (`rootDirectory` + `dockerfilePath`) for these services so they include backend deps and start with celery.

### Explicit non-claims
- Do **not** claim READY FOR PRODUCTION / soak complete / SIGN_HERE forged.
- Google connect remains human. Celery worker deploy remains operational.
- FE Wave 19 honesty diffs may lag on Vercel until next Git deploy (prod FE still on pre-Wave19 commit via Git).

---

## Remaining (Human / Operational only — zero open eng actions)

See parent final lists A and B.
