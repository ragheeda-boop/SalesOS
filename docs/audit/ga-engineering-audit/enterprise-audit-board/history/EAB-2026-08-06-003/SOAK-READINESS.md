# SOAK-READINESS — OPS-01 Row 4 (48–72h staging soak)

**Run:** EAB-2026-08-06-003 · **Update:** 2026-08-07 · **Mode:** EXECUTE + VERIFY
**Parent:** [OPS-01-ADVANCEMENT.md](./OPS-01-ADVANCEMENT.md) · [SOAK-GATE-CHECKLIST.md](./SOAK-GATE-CHECKLIST.md)

**Verdict: staging is now production-parity at code/config/secret level → SOAK-CAPABLE WITH CONDITIONS. The soak itself has NOT been run (K2–K6 still open).**

---

## Soak gate assessment (K1–K6 from SOAK-GATE-CHECKLIST.md)

| Gate | Requirement | Status | Evidence this run |
|------|-------------|--------|-------------------|
| K1 | Target = staging cloud (not laptop-only) | **PASS** | Railway staging = prod baseline `4750038c`; `/openapi.json` byte-identical; alembic `e5f9a32b0c08` (head); workers synced; Neo4j connected; secrets distinct; DEBUG=false |
| K2 | Continuous window ≥48h (prefer 72h), dated UTC | **OPEN** | No soak window started on this build |
| K3 | Evidence dir, loop summaries, hard-fail triage | **OPEN** | Health/`/metrics`/logs captured; no `wave11-soak-gate.py` run against staging yet |
| K4 | No new P0 during soak | **OPEN** | Not yet applicable |
| K5 | Project Owner review before flipping claim | **OPEN** | HUMAN |
| K6 | `soak_complete_claim: true` | **false** | Correct today |

## Soak criteria (mission checklist) — verified status

| Criterion | Status | Detail |
|-----------|:------:|--------|
| Deployment frozen during soak | PARTIAL | Staging has manual-only deploys; freeze trivially true but no enforcement runbook; worker/beat just synced |
| Restart / crash stability | PASS | `/health` 200; no ERROR/Traceback/CRITICAL in log buffer; only benign "scraper API keys missing → MOCK MODE" warnings (identical to prod) |
| Monitoring (logs) | PASS | `railway logs` works for staging; no dashboard/alerts confirmed |
| Metrics | PARTIAL | Public `/metrics` (60,470 B) verified; `/metrics/pool`,`/metrics/app` → 401 (auth required, prod parity); no dashboard |
| Health checks | PASS | `/health` 200 all subsystems; `/docs` 404 (DEBUG=false, parity); `/ready`/`/live` absent routes (prod parity) |
| External uptime monitor | **OPEN** | None configured for `https://salesos-staging.up.railway.app` |
| Rollback | PARTIAL | Railway redeploy (UI/CLI) usable; not scripted/tabletop-verified |
| Alerts | **OPEN** | No alert channel wired to staging health |
| Resource limits | PARTIAL | 1 replica; staging Postgres `max_connections=100` vs prod **500** (capacity gap) |
| Data realism | PARTIAL | Clean empty DB (0/0/1) — boot/idle paths only; no tenant/load realism until seeded |

## Preconditions to START the soak (human actions, in order)

1. **Create staging Google OAuth app** → set `SSO_GOOGLE_CLIENT_ID` + `SSO_GOOGLE_CLIENT_SECRET` on staging env (own app; never reuse prod's).
2. **Accept or close** the staging WAL/PITR + offsite-backup gap (parity with prod rows 1–3) — or explicitly document as accepted staging risk.
3. **(Recommended)** Optionally raise staging `max_connections` to 500 and/or seed **sanitized non-prod** data for load realism (separate DEC).
4. Start soak: `python salesos/scripts/wave11-soak-gate.py --target https://salesos-staging.up.railway.app` with dated UTC window; collect under `evidence/ops01-staging/`.
5. TL review → update `soak_complete_claim` and OPS-01 Row 4.

## Known remaining risks (soak-relevant)

- Staging Postgres `max_connections=100` vs prod 500 — sustained parallel load could hit the ceiling sooner on staging.
- Prod DB is **11 revisions behind its own deployed code** (`d1a8c35e7f09` vs `e5f9a32b0c08`) — soak validates staging at head, which is *ahead* of what prod's DB actually runs; **prod migration requires human approval** before launch conversations.
- Prod `neo4j-prod` has no persistent volume (ephemeral graph) — see [ROOTCAUSE-NEO4J.md](./ROOTCAUSE-NEO4J.md).
