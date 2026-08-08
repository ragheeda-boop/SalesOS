# Progress — Wave 17 GA push execution (2026-07-29)

**Clock:** 2026-07-29 (agent session after explicit user approval for full GA remediation)  
**Product:** SalesOS (`salesos/`) platform intent  
**Authority:** [00-EXECUTIVE-SUMMARY.md](./00-EXECUTIVE-SUMMARY.md), [PRODUCTION_PLAN.md](./PRODUCTION_PLAN.md), [PROGRESS-REAUDIT-2026-07-29.md](./PROGRESS-REAUDIT-2026-07-29.md)  
**Decision after this session:** still **NO-GO** for Production GA declaration  
**Classification:** **production no-go** (gates improved; human signatures + soak claim + code deploy of security diffs still open)  
**Validation:** **light validated** / partial **build validated** (FE lint+tsc+build local; focused Docker pytest)

> Do **not** invent GO. Agents must **not** forge CTO/TL signatures in [SIGN_HERE.md](./SIGN_HERE.md).  
> Secrets observed in CLI output this session must be **rotated** (Neo4j staging auth + any DB URL echoed by `railway variable list`) — values are **not** recorded here.

---

## 1. What closed this session

| Item | Status | Evidence |
|------|--------|----------|
| KG SQL require `tenant_id` | **code fixed (local)** | `runtime/knowledge_graph_runtime/repository/sql_repository.py`; populate joins companies for licenses/branches |
| API key per-key rate limit | **code fixed (local)** | `app/modules/api_keys/middleware.py` → `ApiKeyRateLimiter` @ 60 rpm |
| Webhook `None` persistence + orphan retries | **code fixed (local)** | `modules/webhooks/repository.py` + `process_retries` |
| Gmail 404 / Calendar 410 / auth tests | **tests added; 60 passed** | Docker pytest comm-hub + webhooks |
| Neo4j on Railway **staging** | **DONE** | service `neo4j` + volume; SalesOS `NEO4J_URI=bolt://neo4j.railway.internal:7687` |
| Staging `/health` graph | **connected** | live probe `graph=connected` (was `unavailable`) |
| Staging Alembic | **0049 (head)** | empty DB bootstrapped `upgrade head` → `0049` |
| Prod Alembic | **0049 (head)** | `0046→0047→0048→0049`; pre-state [evidence/wave17-prod-migrate/](./evidence/wave17-prod-migrate/) |
| 48h soak harness | **restarted** (not complete) | append loop to `evidence/wave16-soak/health-loop.jsonl` until ~2026-07-30T22:13Z UTC |
| FE lint / tsc / build | **PASS (local)** | warnings only on lint; `tsc --noEmit` exit 0; `npm run build` exit 0 |
| Health burst (staging) | **recorded** | [evidence/wave17-load/](./evidence/wave17-load/) |
| Rollback drill | **documented only** | prior SUCCESS ids noted; **not** executed on prod |

---

## 2. Still open (blocks GA claim)

1. **Soak claim** — harness restarted; `soak_complete_claim` remains **false** until ≥48h + TL review.  
2. **Security code not yet live on Railway images** — local diffs only until git deploy / `railway up` of backend with KG/webhook/API-key patches.  
3. **CTO + Tech Lead signatures UNSIGNED** — [SIGN_HERE.md](./SIGN_HERE.md).  
4. **Staging SSRF pentest / classic tabletop** — still OPEN.  
5. **Primary WAL/PITR + offsite restore** — still OPEN.  
6. **Prod Neo4j / Kafka** — prod health still `graph=unavailable`, `kafka=in_memory`.  
7. **Staging data seed / E2E OAuth→Gmail→Calendar→Dashboard** — staging DB schema at head but **0 companies**; E2E not browser-validated.  
8. **Phase 5 GA declaration docs** — **not** flipped to Production GA (would be dishonest).  
9. **Credential rotation** — staging Neo4j password and any DB URL printed by Railway CLI this session.

---

## 3. Honest scoreboard delta

| Dimension | Re-audit 2026-07-29 | After Wave 17 session | Notes |
|-----------|--------------------:|----------------------:|-------|
| Production Readiness | ~47 | **~52** (estimate) | Alembic head on prod; staging Neo4j; soak restarted; FE build reconfirmed |
| Security | ~57 | **~59** (estimate, code-only) | KG/API-key/webhook fixes local — **not** live-image verified |
| Verdict | NO-GO | **NO-GO** | unchanged until signatures + soak claim + live security deploy |

---

## 4. Commands / actions run (summary)

```text
# Code
edit sql_repository.py / service.py / api_keys/middleware.py / webhooks/*
extend test_gmail_sync.py / test_calendar_sync.py
docker compose exec backend pytest …  # 60 passed
docker KG require_tenant smoke  # PASS
frontend: npm run lint; npx tsc --noEmit; npm run build  # PASS

# Railway staging
railway add --image neo4j:5-community --service neo4j
NEO4J_* vars on SalesOS; volume /data
alembic upgrade head → 0049
soak loop restarted (48h)

# Railway production
alembic upgrade head 0046→0049
/health still ok (graph unavailable — Neo4j not added to prod)
```

**Not run:** forged signatures; README/RELEASE_GATES GA flip; production Neo4j add; full `pg_dump`; browser E2E; production rollback execution; git commit/push (unless user requests).

---

## 5. Next human decisions

1. Approve **backend deploy** of Wave 17 security diffs to staging then production.  
2. **Rotate** staging Neo4j / any leaked DB credentials.  
3. Let soak run ≥48h; TL reviews `health-loop.jsonl`.  
4. Sign [SIGN_HERE.md](./SIGN_HERE.md) only if remaining gates accepted.  
5. Optional: add Neo4j to **production** or sign degraded matrix for graph.

**Validation label:** light/build partial. **production no-go**.
