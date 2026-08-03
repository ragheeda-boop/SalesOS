# Hypercare — 14 Day Window (Wave 14 — PREPARE)

**ID:** PROD-W14-001  
**Status:** PREPARE ONLY — applies **after** a real Production GO (not granted as of 2026-07-22 audit)  
**Classification:** Operational prep template  
**Ops spine (Sprint-26 prep):** [HYPERCARE_RUNBOOK.md](../../../ops/HYPERCARE_RUNBOOK.md) — **draft landed** (clock not started / on-call TBD)

---

## When this starts

Only after Wave 13 T-0 human GO signatures and successful smoke.  
Until then, keep this as a staffing/process template.

---

## Staffing

| Role | Name | Contact | Coverage |
|------|------|---------|----------|
| Primary on-call | _TBD_ | _TBD_ | 24×7 week 1 |
| Secondary on-call | _TBD_ | _TBD_ | Backup 15–30 min |
| Backend TL | _TBD_ | _TBD_ | Business hours + S1 |
| Frontend TL | _TBD_ | _TBD_ | Business hours + S1 |
| Product | _TBD_ | _TBD_ | Comms |

References: `salesos/docs/ONCALL_RUNBOOK.md`, `docs/ops/DR_RUNBOOK.md`.

---

## Rules (first 72 hours)

1. **No non-fixative changes** (features, refactors, flag experiments).  
2. Hotfix require TL + on-call ack; prefer forward-fix.  
3. Any P0 security → incident channel + consider traffic cut / rollback ([deploy-rollback.md](./deploy-rollback.md)).  
4. AI flags stay **off** unless a signed exception exists ([AI_HONESTY.md](../AI_HONESTY.md)).

Days 4–14: limited changes allowed with change tickets; still bias to stability.

---

## Daily checklist (D+1 … D+14)

| Check | How | Owner |
|-------|-----|-------|
| 5xx / error budget | Prometheus / Grafana (**يحتاج تحقق** `monitoring.salesos.com`) | On-call |
| Latency p95 critical APIs | metrics | On-call |
| `/health/detailed` components | curl staging/prod API | On-call |
| Alembic drift | `alembic current` vs `heads` in prod job | DevOps |
| Backup job success | CronJob / S3 object | DevOps |
| Auth anomalies | logs / alerts | Security |
| Customer-facing tickets | support inbox | Product |

Post a short daily note in `#salesos-deployments` or incident channel (**UNVERIFIED** channel names).

---

## SLI watch (proposed — not production-proven)

From PRODUCTION_PLAN §10 — treat as **proposed** until soak baselines exist:

| SLI | Alert idea |
|-----|------------|
| Availability `/ping` or blackbox | < 99% / 15m → S1 |
| 5xx ratio | > 2% / 5m → S2; > 5% → S1 |
| p95 critical | > 2s sustained → S2 |
| Postgres down | S1 |
| Migrate drift in prod | S1 |

---

## Reporting

| Day | Deliverable |
|-----|-------------|
| D+7 | Mid-hypercare report: incidents, error budget, open risks |
| D+14 | Exit report: handoff to normal ops **or** extend hypercare |

### Exit criteria

- [ ] No open P0 without mitigation plan  
- [ ] Error budget within agreed SLO (or accepted exception)  
- [ ] On-call rota for steady state confirmed  
- [ ] Known limitations documented (Kafka/Neo4j degraded matrix if any)

---

## Incident severity quick map

Use ONCALL severity table (S1–S5). First 5 minutes: ACK → health curl → open `#incident-YYYY-MM-DD-…` → notify.

Production health examples from ONCALL (verify host):

```bash
curl -sf https://api.salesos.com/health | jq .
# K8s
kubectl get pods -n salesos -o wide
kubectl logs -n salesos deploy/backend --tail=100
```

---

## Explicit non-claims

- This file does **not** mean production is live.  
- Audit status remains **production no-go** until Waves 0–13 evidence exists and humans sign GO.
