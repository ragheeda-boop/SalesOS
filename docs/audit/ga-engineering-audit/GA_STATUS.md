# GA Status Scoreboard — AQLIYA / SalesOS

**Date:** 2026-07-28 (updated)  
**Authority:** [ga-engineering-audit](./00-EXECUTIVE-SUMMARY.md) + execution progress below  
**Decision:** **NO-GO** for Production GA  
**Classification:** production no-go

> Superseded GO claims in `docs/vnext/reports/GO_NO_GO_DECISION.md` / `GA_CHECKLIST.md` must not be used.

---

## Scoreboard (honest)

| Dimension | Audit baseline | After Waves 0–15 local + Railway evidence | Notes |
|-----------|---------------:|------------------------------------------:|-------|
| Production Readiness | **38** | ~**46** (still **no-go**) | Railway SalesOS live; muhide **141k** companies; OAuth Redis store **deployed** `339ebbab`; cutover/soak/signatures open |
| Security | **48** | ~**56** | Wave 2 + CORS on Railway; OAuth Redis store **in prod image** (SSH file + `/health` redis=connected); SSRF pentest **OPEN** |
| Testing | **52** | improved (local) | Unit focused OAuth **35 PASS**; full browser GA still open |
| DevOps / Deploy | **62** | prep+ / **Railway live** | Railway deploy `339ebbab` SUCCESS (2026-07-28); Vercel `sales-os` READY; classic staging VPS secrets still empty |
| AI honesty | — | gated | Copilot default False + API 403; FE Decision stub honesty — see AI_HONESTY.md |

**Verdict unchanged: Production GA = NO-GO.**

---

## Wave rollup

| Wave | Progress | Prep | Runtime / ops proof |
|------|----------|------|---------------------|
| 0 FE | [PROGRESS-WAVE0-FE.md](./PROGRESS-WAVE0-FE.md) | **DONE** lint/tsc/build | CI Linux standalone caveat open |
| 1 Alembic | [PROGRESS-WAVE1-3-5-PLATFORM.md](./PROGRESS-WAVE1-3-5-PLATFORM.md), [PROGRESS-WAVE12-PROD-MIGRATE-PREP.md](./PROGRESS-WAVE12-PROD-MIGRATE-PREP.md) | **DONE** local → **0040**; prod migrate **PREP DONE** | Staging/prod migrate **EXECUTION BLOCKED pending approval** |
| 2 Security | [PROGRESS-WAVE2-SEC.md](./PROGRESS-WAVE2-SEC.md), [PROGRESS-WAVE2-LOAD.md](./PROGRESS-WAVE2-LOAD.md), [PROGRESS-WAVE2-RESIDUALS.md](./PROGRESS-WAVE2-RESIDUALS.md) | **DONE** (light + local load + residual code) | Local SSRF/KG probes **PASS**; logger arity **CLOSED**; SSRF pin **hardened**; local `graph_edges` **CLOSED**; pentest **OPEN** |
| 3 Unit tests | same + [PROGRESS-CONTINUATION.md](./PROGRESS-CONTINUATION.md) | **DONE** local green-ish | Full coverage gate **OPEN** |
| 4 Runtime / FE image | [PROGRESS-WAVE4-8-9-INFRA.md](./PROGRESS-WAVE4-8-9-INFRA.md), [PROGRESS-WAVE4-FE-IMAGE.md](./PROGRESS-WAVE4-FE-IMAGE.md) | **DONE** local image smoke | `/dashboard` **200** on Docker FE `84ef1507c89e` |
| 5 Auth contracts | Wave 1/3/5 progress | **DONE** local probes | Prod metrics/auth soak **OPEN** |
| 6–7 Docs / AI | [PROGRESS-WAVE6-7-DOCS.md](./PROGRESS-WAVE6-7-DOCS.md), [PROGRESS-WAVE6-7-AI-GATE.md](./PROGRESS-WAVE6-7-AI-GATE.md), [AI_HONESTY.md](./AI_HONESTY.md) | **DONE** (docs + UI/API gate) | Human PRC AI-scope sentence **OPEN** |
| 8–9 Obs / secrets | Wave 4/8/9 progress | **DONE** config | Live scrape matrix **OPEN** |
| 10 Backup drill | [PROGRESS-WAVE10-BACKUP.md](./PROGRESS-WAVE10-BACKUP.md), [PROGRESS-WAVE10-DR-GAPS.md](./PROGRESS-WAVE10-DR-GAPS.md) | **DONE** (local) | Neo4j dump+**disposable load-verify Done**; disposable WAL archive Done; **primary** WAL/PITR + S3/MinIO **OPEN** |
| 11 Staging soak | [PROGRESS-WAVE11-SOAK.md](./PROGRESS-WAVE11-SOAK.md), [PROGRESS-WAVE11-SOAK-48H.md](./PROGRESS-WAVE11-SOAK-48H.md) | **DONE** gate + short loop + **4h local loop** (45 iters, exit 1, 16 fails); **48h local loop RUNNING** (start `2026-07-22T14:31:46Z`, PID `21856`; checkpoint `2026-07-24T13:11Z`: ~46.7h, **529** iters, **418 PASS / 111 FAIL**) — **not complete** | **`soak_complete_claim: false`** — 48–72h **NOT complete**; fail rate ~21% → Review/EXTEND; cloud staging **OPEN** |
| 12 Deploy gates / tabletop | [PROGRESS-WAVE12-GATES.md](./PROGRESS-WAVE12-GATES.md), [PROGRESS-WAVE12-TABLETOP.md](./PROGRESS-WAVE12-TABLETOP.md), [PROGRESS-WAVE12-IMAGE.md](./PROGRESS-WAVE12-IMAGE.md), [PROGRESS-WAVE12-STAGING.md](./PROGRESS-WAVE12-STAGING.md), [PROGRESS-WAVE12-STAGING-UNBLOCK.md](./PROGRESS-WAVE12-STAGING-UNBLOCK.md), [PROGRESS-WAVE12-STAGING-VIRTUAL.md](./PROGRESS-WAVE12-STAGING-VIRTUAL.md), [PROGRESS-WAVE12-PROD-MIGRATE-PREP.md](./PROGRESS-WAVE12-PROD-MIGRATE-PREP.md) | **DONE** script+docs+local tabletop+**virtual local staging tabletop**+backend image+**staging prep**+prod migrate **PREP**; cloud tabletop **BLOCKED** | Local gates **PASS**; **virtual staging DONE** (`:8001`/`:3002`); **staging cloud BLOCKED** (re-probe `2026-07-22T16:32:00Z`); prod migrate **PREP DONE / EXECUTION BLOCKED pending approval** |
| 13 Go-live / auth smoke | [PROGRESS-WAVE13-AUTH-SMOKE.md](./PROGRESS-WAVE13-AUTH-SMOKE.md), [PROGRESS-WAVE13-UI-SMOKE.md](./PROGRESS-WAVE13-UI-SMOKE.md), [PROGRESS-WAVE13-AUTH-DEMO.md](./PROGRESS-WAVE13-AUTH-DEMO.md), [PROGRESS-WAVE13-FULL-UI-CRAWL.md](./PROGRESS-WAVE13-FULL-UI-CRAWL.md), [runbooks/go-live-checklist.md](./runbooks/go-live-checklist.md), [SIGN_HERE.md](./SIGN_HERE.md) | API+UI disposable smoke **DONE** (local light); **demo `@salesos.io` UNBLOCKED**; **full UI crawl DONE** (49/49 shells PASS, 136 clicks; API residuals) | CTO/TL signatures **UNSIGNED** |
| 14 Hypercare / human review | [PROGRESS-WAVE14-GO-LIVE.md](./PROGRESS-WAVE14-GO-LIVE.md), [runbooks/hypercare-14d.md](./runbooks/hypercare-14d.md), [SIGN_HERE.md](./SIGN_HERE.md) | Forms **PREPARE** for human review | Hypercare **OPEN** (post-GO); signatures **UNSIGNED** |

---

## Remaining NO-GO blockers

1. **No 48–72h soak report** — see [PROGRESS-WAVE11-SOAK-CLAIM.md](./PROGRESS-WAVE11-SOAK-CLAIM.md); `soak_complete_claim: false`  
2. **Classic staging VPS tabletop** — secrets still empty; **Railway SalesOS is live** as cloud path ([PROGRESS-WAVE15-MUHIDE-COMPANIES-RAILWAY.md](./PROGRESS-WAVE15-MUHIDE-COMPANIES-RAILWAY.md))  
3. **No approved production Alembic upgrade** — [PROGRESS-WAVE13-CUTOVER-PREP.md](./PROGRESS-WAVE13-CUTOVER-PREP.md); **EXECUTION BLOCKED pending approval**  
4. **Security residuals** — SSRF pin redesign **code closed**; staging/Railway pentest **OPEN**; OAuth Redis store **deployed** (`339ebbab`, 2026-07-28) — human OAuth login smoke still advised  

5. **CTO + Tech Lead GO signatures UNSIGNED** — [SIGN_HERE.md](./SIGN_HERE.md)  
6. **AI surfaces must not be marketed as GA** — code gate DONE; PRC sign-off OPEN  
7. **Backup DR beyond local dumps** — MinIO profile added; primary WAL/PITR + offsite drill **OPEN**  
8. **RPO acceptance (24h vs WAL) UNSIGNED**  
9. **Activity Intelligence honesty** — engineering pass; still pilot-ready with conditions, not GA  

**Muhide account note (2026-07-28):** `ragheed.a@muhide.com` exists on Railway with **141,221** companies — Track A closed for data presence; GA still NO-GO.

**Verdict unchanged: Production GA = NO-GO.**

**Do not claim full GA from this scoreboard. Signatures remain UNSIGNED. Do not claim 48h soak done.**

---

## What closed prep (not GO)

- FE build green (Wave 0); FE image routes 200 (Wave 4); `/dashboard` source + **Docker image** HTTP 200  
- Local Alembic at head **`0040`** + migrate-check script; prod migrate runbook **PREP DONE** (execution not run; 0040 required on future staging/prod path)  
- Security P0 code fixes (light validated)  
- Unit suite largely green in Docker (~1542 passed)  
- Local backup/restore drill + restore-db safety + Neo4j offline dump + disposable load-verify + disposable WAL archive + WAL assess docs (Wave 10; primary PITR + S3 still open)  
- Wave 11 soak gate + short loop + **4h extended local loop DONE** + **48h local loop RUNNING** (~46.7h / 529 iters at `2026-07-24T13:11Z`; `soak_complete_claim: false`; **not** 48h complete)  
- Pre-deploy gates script (ASCII-safe) **runtime PASS** locally + local deploy/rollback tabletop (Wave 12)  
- Staging cloud **prep DONE** (no credentials): SSH+GHCR compose + `deploy-staging.yml` Environment wiring, [PROGRESS-WAVE12-STAGING-UNBLOCK.md](./PROGRESS-WAVE12-STAGING-UNBLOCK.md), [runbooks/staging-fill-in.md](./runbooks/staging-fill-in.md) — cloud tabletop still **BLOCKED**  
- **Local virtual staging tabletop DONE** (not cloud): project `salesos-staging-local`, ports `:8001`/`:3002`, evidence `evidence/wave12-staging-virtual/` — [PROGRESS-WAVE12-STAGING-VIRTUAL.md](./PROGRESS-WAVE12-STAGING-VIRTUAL.md)  
- Backend image with **jsonschema 4.26.0** baked in ([PROGRESS-WAVE12-IMAGE.md](./PROGRESS-WAVE12-IMAGE.md))  
- Local authenticated API smoke + Playwright UI smoke (Wave 13) — `/dashboard` **PASS** on rebuilt FE; `SMOKE_EMAIL`/`SMOKE_PASSWORD` env wiring on smoke scripts  
- Demo/pentest `@salesos.io` accounts **seeded locally** (`demo_tenant`; admin login **200**; auth smoke **13 PASS / 0 FAIL**) — [PROGRESS-WAVE13-AUTH-DEMO.md](./PROGRESS-WAVE13-AUTH-DEMO.md); script `salesos/backend/scripts/seed_demo_users.py`  
- Full UI crawl (Wave 13) — demo admin; **49/49** nav+deep page shells **PASS**; **136** primary clicks; evidence `evidence/wave13-full-ui-crawl/`; reusable `salesos/scripts/full-ui-crawl.ps1` — **light validated only**; API **500/404/422** + CORS residuals remain ([PROGRESS-WAVE13-FULL-UI-CRAWL.md](./PROGRESS-WAVE13-FULL-UI-CRAWL.md))  
- Wave 14 human-review pack + **UNSIGNED** CTO/TL blocks ([PROGRESS-WAVE14-GO-LIVE.md](./PROGRESS-WAVE14-GO-LIVE.md), [SIGN_HERE.md](./SIGN_HERE.md))

**Do not production deploy from this scoreboard. Signatures remain UNSIGNED. Do not claim 48h soak done.**
