# Hypercare Runbook — SalesOS (Wave 14 / Sprint-26 prep)

**IDs:** PROD-W14-001 · Sprint-26 post-cutover prep  
**Status:** **DRAFT LANDED** — not started · **not Production GO** · on-call names **TBD** · human sign-off **residual**  
**Authority:** [docs/audit/ga-engineering-audit/](../audit/ga-engineering-audit/) → **production no-go**  
**Product scope:** SalesOS only  
**Draft date:** 2026-08-03

> AI assists. Humans decide. Evidence governs.  
> Hypercare **does not start** until Wave 13 T-0 human GO is recorded and smoke succeeds. This file is a staffing / process draft for Sprint-26 prep only.

---

## 1. Honest status (read first)

| Claim | Reality |
|-------|---------|
| Production GO / cutover | **NOT claimed / not executed** |
| Hypercare 14-day clock | **Not started** |
| On-call primary / secondary | **TBD** (residual for DoD) |
| Mid / exit reports | **Not written** |
| This draft | **draft landed** under `docs/ops/` |

**Do not** treat “draft landed” as PRODUCTION_PLAN §3(ز) Hypercare DoD complete. Checkbox stays **unchecked** until roster is named **and** the window actually runs after GO.

---

## 2. Source of truth & related packs

| Doc | Role |
|-----|------|
| [PRODUCTION_PLAN.md](../audit/ga-engineering-audit/PRODUCTION_PLAN.md) § Wave 14 | Authoritative wave definition |
| [runbooks/hypercare-14d.md](../audit/ga-engineering-audit/runbooks/hypercare-14d.md) | Audit template (PREPARE) |
| [PROGRESS-WAVE14-HYPERCARE-PREP.md](../audit/ga-engineering-audit/PROGRESS-WAVE14-HYPERCARE-PREP.md) | Prep progress |
| [PROGRESS-WAVE14-GO-LIVE.md](../audit/ga-engineering-audit/PROGRESS-WAVE14-GO-LIVE.md) | GO pack — hypercare post-GO only |
| [GO_LIVE_RUNBOOK.md](./GO_LIVE_RUNBOOK.md) | Wave 13 ops spine |
| [SLO_ALERTS.md](./SLO_ALERTS.md) | Proposed SLIs — not production-proven |
| [DR_RUNBOOK.md](./DR_RUNBOOK.md) | Restore / disaster |
| [DEGRADED_MODE_MATRIX.md](./DEGRADED_MODE_MATRIX.md) | Optional components |
| `salesos/docs/ONCALL_RUNBOOK.md` | Severity + first-5-min |
| [Sprint-26.md](../program/SPRINT_PLAN/Sprint-26.md) | Terminal sprint (prep pointer) |

---

## 3. When the clock starts

Start D+0 only when **all** are true:

1. CTO + Tech Lead recorded **GO** (or CONDITIONAL with listed conditions still green) on the go-live checklist / SIGN_HERE.  
2. T-0 migrate → deploy → smoke completed without open P0.  
3. T+1 continue decision is **continue** (not rollback).  
4. Primary + secondary on-call ack coverage for week 1.

Until then: keep this document as **PREPARE**. Do not post “hypercare day N” status as if production were live.

---

## 4. Staffing (fill before T-1)

| Role | Name | Contact | Coverage |
|------|------|---------|----------|
| Primary on-call | _TBD_ | _TBD_ | 24×7 week 1 |
| Secondary on-call | _TBD_ | _TBD_ | Backup ≤ 15–30 min |
| Backend TL | _TBD_ | _TBD_ | Business hours + S1 |
| Frontend TL | _TBD_ | _TBD_ | Business hours + S1 |
| Security | _TBD_ | _TBD_ | Auth / isolation watch |
| Product | _TBD_ | _TBD_ | Customer / partner comms |
| Program / Release | _TBD_ | _TBD_ | Daily standup ownership |

**DoD residual:** PRODUCTION_PLAN requires Hypercare plan **with named on-call owner**. Names above remain TBD until humans assign them.

---

## 5. Rules

### First 72 hours (D+0 … D+3)

1. **No non-fixative changes** (features, refactors, flag experiments).  
2. Hotfix require TL + on-call ack; prefer forward-fix with change ticket.  
3. Any P0 security → incident channel + consider traffic cut / rollback.  
4. AI flags stay **off** unless a **signed** exception exists ([AI_HONESTY.md](../audit/ga-engineering-audit/AI_HONESTY.md)). Non-prod harnesses 14-06/14-07 ≠ live LLM GO.  
5. Schema: no new Alembic revisions unless emergency hotfix with dual CTO/TL ack.

### Days 4–14

Limited changes allowed with change tickets; bias to stability. Still no GA marketing claims that contradict flags/stubs.

---

## 6. Daily checklist (D+1 … D+14)

| Check | How | Owner |
|-------|-----|-------|
| 5xx / error budget | Prometheus / Grafana (**يحتاج تحقق** hosts) | On-call |
| Latency p95 critical APIs | metrics | On-call |
| `/health` / detailed components | curl approved API host | On-call |
| Alembic drift | `alembic current` vs `heads` | DevOps |
| Backup job success | Cron / object store id | DevOps |
| Auth / CSRF / tenant anomalies | logs / alerts | Security |
| Customer-facing tickets | support inbox | Product |
| Degraded optional deps (Kafka/Neo4j) | [DEGRADED_MODE_MATRIX.md](./DEGRADED_MODE_MATRIX.md) | On-call |

Post a short daily note in the approved deploy / incident channel (**UNVERIFIED** channel names — fill at T-1).

### Daily note template

```text
Hypercare D+N — YYYY-MM-DD
Env: <staging|prod>   GO ref: <link or UNSIGNED>
5xx / error budget: …
p95 critical: …
Health: …
Alembic: current=… heads=…
Backups: …
Incidents S1/S2: none | <links>
Hotfixes shipped: none | <tickets>
AI flags: feature_ai_copilot=False (expected)
Blockers / asks: …
On-call: primary=… secondary=…
```

---

## 7. SLI watch (proposed — not production-proven)

Align with [SLO_ALERTS.md](./SLO_ALERTS.md) and PRODUCTION_PLAN §10. Treat as **proposed** until soak baselines exist:

| SLI | Alert idea |
|-----|------------|
| Availability `/ping` or blackbox | < 99% / 15m → S1 |
| 5xx ratio | > 2% / 5m → S2; > 5% → S1 |
| p95 critical | > 2s sustained → S2 |
| Postgres down | S1 |
| Migrate drift in prod | S1 |
| Redis / Neo4j / Kafka | Per degraded matrix + alert rules |

---

## 8. Reporting

| Day | Deliverable | Owner |
|-----|-------------|-------|
| D+7 | Mid-hypercare report: incidents, error budget, open risks | On-call + TL |
| D+14 | Exit report: handoff to normal ops **or** extend hypercare | DevOps + CTO ack |

### Exit criteria (all required)

- [ ] No open P0 without mitigation plan  
- [ ] Error budget within agreed SLO (or accepted exception)  
- [ ] Steady-state on-call rota confirmed  
- [ ] Known limitations documented (Kafka/Neo4j degraded matrix if any)  
- [ ] AI honesty still reflected in customer-facing notes  

Exit report does **not** rewrite historical NO-GO audit scores; it only closes the hypercare window after a real GO.

---

## 9. Incident quick path

1. ACK page (ONCALL severity S1–S5).  
2. Health curl + pod/process status.  
3. Open dated incident channel.  
4. Notify primary + TL; Security if auth/tenant.  
5. Mitigate (rollback / traffic cut / hotfix) per [deploy-rollback.md](../audit/ga-engineering-audit/runbooks/deploy-rollback.md) / [DR_RUNBOOK.md](./DR_RUNBOOK.md).  
6. Write IR note before next daily hypercare note.

```bash
# Hosts must match the approved environment — examples only
# curl -sf https://<api-host>/health
# kubectl get pods -n <ns> -o wide   # if K8s path is in scope
```

---

## 10. Explicit non-claims

- Draft landing ≠ hypercare running.  
- Audit status remains **production no-go** until Waves evidence + human GO.  
- No GA cutover claim from this document.  
- Validation label: **not validated** (docs prep only).

---

## 11. Change log

| Date | Change |
|------|--------|
| 2026-08-03 | Initial **draft landed** for Wave 14 / Sprint-26 prep — clock not started, roster TBD, no Production GO |
