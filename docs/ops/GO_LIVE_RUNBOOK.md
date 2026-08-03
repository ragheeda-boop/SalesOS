# Go-Live Runbook — SalesOS (Wave 13 / Sprint-26 prep)

**IDs:** PROD-W13-001 · Sprint-26 GA cutover prep  
**Status:** **DRAFT LANDED** — not executed · **not Production GO** · human sign-off **residual**  
**Authority:** [docs/audit/ga-engineering-audit/](../audit/ga-engineering-audit/) → **production no-go**  
**Product scope:** SalesOS GA candidate only (not AQLIYA multi-product GA)  
**Draft date:** 2026-08-03

> AI assists. Humans decide. Evidence governs.  
> This file is an **ops-facing runbook draft** for Sprint-26 prep. It does **not** authorize cutover, DNS flip, prod migrate, or a GA declaration.

---

## 1. Honest status (read first)

| Claim | Reality |
|-------|---------|
| Production GO | **NOT claimed** — scoreboard remains **production no-go** |
| Cutover / T-0 executed | **No** |
| CTO + Tech Lead signatures | **UNSIGNED** (residual) |
| Staging soak 48–72h | **OPEN** (see Wave 11 progress) |
| On-call roster named | **TBD** |
| This draft | **draft landed** under `docs/ops/` for program prep |

**Do not** treat “draft landed” as DoD complete. PRODUCTION_PLAN §3(ز) checkboxes stay **unchecked** until humans execute + sign.

---

## 2. Source of truth & related packs

| Doc | Role |
|-----|------|
| [PRODUCTION_PLAN.md](../audit/ga-engineering-audit/PRODUCTION_PLAN.md) § Wave 13 | Authoritative wave definition |
| [runbooks/go-live-checklist.md](../audit/ga-engineering-audit/runbooks/go-live-checklist.md) | Evidence-synced T-7→T+1 boxes + **UNSIGNED** blocks |
| [PROGRESS-WAVE14-GO-LIVE.md](../audit/ga-engineering-audit/PROGRESS-WAVE14-GO-LIVE.md) | Human-review pack (prep, not GO) |
| [SIGN_HERE.md](../audit/ga-engineering-audit/SIGN_HERE.md) | One-page signature pack — **UNSIGNED** |
| [GA_STATUS.md](../audit/ga-engineering-audit/GA_STATUS.md) | Live NO-GO scoreboard |
| [HYPERCARE_RUNBOOK.md](./HYPERCARE_RUNBOOK.md) | Wave 14 draft (post-GO only) |
| [DR_RUNBOOK.md](./DR_RUNBOOK.md) | Backup / restore / RPO-RTO |
| [DEGRADED_MODE_MATRIX.md](./DEGRADED_MODE_MATRIX.md) | Optional Kafka/Neo4j posture |
| [SLO_ALERTS.md](./SLO_ALERTS.md) | Proposed SLI/SLO — not production-proven |
| [deploy-rollback.md](../audit/ga-engineering-audit/runbooks/deploy-rollback.md) | Deploy / rollback tabletop |
| `salesos/docs/ONCALL_RUNBOOK.md` | On-call first-5-min |
| [Sprint-26.md](../program/SPRINT_PLAN/Sprint-26.md) | Terminal sprint plan (prep pointer) |
| [AI_HONESTY.md](../audit/ga-engineering-audit/AI_HONESTY.md) | Copilot / decision stub honesty |

Detailed evidence checkboxes live in the **audit checklist**. This ops runbook is the **procedure spine** operators follow once humans clear residual blockers.

---

## 3. Preconditions (must be true before any T-0)

Do **not** start T-0 while any row is open unless CTO formally accepts residual risk in writing.

| # | Precondition | Owner | Typical evidence |
|---|--------------|-------|------------------|
| 1 | PRODUCTION_PLAN P0 blockers closed or risk-accepted | TL / CTO | [GA_STATUS.md](../audit/ga-engineering-audit/GA_STATUS.md) |
| 2 | Staging soak ≥ 48–72h, zero new P0 | DevOps / QA | Wave 11 soak evidence |
| 3 | Staging RC images digests recorded | DevOps | Image digests + workflow URL |
| 4 | Staging Alembic `current == heads` | Backend | Gate log |
| 5 | Local + staging deploy/rollback tabletop | DevOps | Wave 12 progress |
| 6 | Backup/restore drill + RPO acceptance | DevOps / CTO | [DR_RUNBOOK.md](./DR_RUNBOOK.md); RPO **UNSIGNED** residual |
| 7 | Feature freeze (hotfix-only) | Product / TL | Freeze note |
| 8 | AI honesty: `feature_ai_copilot=False`; no AI-native GA marketing | Product | [AI_HONESTY.md](../audit/ga-engineering-audit/AI_HONESTY.md) |
| 9 | On-call primary + secondary named | DevOps | Roster in Hypercare runbook |
| 10 | **Human GO** — CTO + Tech Lead | CTO / TL | Signed checklist / SIGN_HERE |

**Low-load:** prod `alembic upgrade`, full FE build/test suites, and secret weakening require **explicit human approval**. Agents must not run them to “unblock” demo cutover.

---

## 4. Timeline (PROD-W13-001)

### T-7 — calendar week before

| Activity | Owner | Done when |
|----------|-------|-----------|
| Confirm P0 register vs scoreboard | TL | Written delta or “no open P0” |
| Feature freeze for non-GA work | Product | Freeze note linked |
| Re-run dependency / security scans (Wave 9) | Security | Report path |
| File backup/restore drill; flag DR gaps | DevOps | Drill report; WAL/PITR residual noted |
| Stakeholder awareness: SalesOS-only scope | CTO | Meeting / email note |
| Confirm prior GO docs SUPERSEDED | Docs | Wave 7 banners present |

### T-3 — RC on staging

| Activity | Owner | Done when |
|----------|-------|-----------|
| Deploy RC images to staging | DevOps | Digests recorded |
| Soak clock running (≥24h already preferred) | DevOps | Soak dashboard / log dir |
| Feature-flag review (`feature_ai_copilot=False`) | Backend | Env dump |
| Alembic staging head match | Backend | `alembic current` == `heads` |
| Smoke GA routes 200 on staging | FE / DevOps | Route list from Wave 4 + 13 |

### T-1 — freeze + Go/No-Go prep

| Activity | Owner | Done when |
|----------|-------|-----------|
| Code freeze (hotfix-only) | TL | Branch protection / freeze ack |
| Production backup (if data exists) | DevOps | Backup object id |
| Final Go/No-Go review vs PRODUCTION_PLAN DoD | CTO + TL | Meeting notes; current expectation **NO-GO** until residuals clear |
| Name on-call primary + secondary | DevOps | Roster filled |
| Rollback authority + tabletop ack | DevOps | Staging tabletop evidence |
| Internal comms draft ready | Product | Doc link |
| Secrets checklist complete | Security | Wave 9 checklist |

### T-0 — launch day (only after human GO)

| Step | Owner | Notes |
|------|-------|-------|
| 1. Record human GO signatures | CTO / TL | Leave UNSIGNED until real meeting |
| 2. Run `pre-deploy-gates.ps1`; then approved migrate | DevOps | **Forbidden while NO-GO** |
| 3. Deploy images (`deploy-production.yml` or approved path) | DevOps | Record Actions / change ticket |
| 4. Automated smoke green | DevOps | Workflow job |
| 5. Manual smoke: login → companies → opportunity critical path | QA / TL | Capture evidence |
| 6. Gradual traffic / DNS as planned | DevOps | Change ticket |
| 7. Intensified monitoring first 60 minutes | On-call | Dashboard link |
| 8. Rollback authority online | On-call | Channel ack |

**Any new P0 → automatic NO-GO / rollback.** Prefer forward-fix only with TL + on-call ack.

### T+1 — next calendar day

| Activity | Owner | Done when |
|----------|-------|-----------|
| Incident review (S1/S2) | On-call | IR notes |
| Continue vs rollback decision | CTO | Written |
| Start Hypercare clock formally | DevOps | [HYPERCARE_RUNBOOK.md](./HYPERCARE_RUNBOOK.md) |
| Customer / partner comms (if any) | Product | Sent |

---

## 5. Cutover command spine (reference only — not a go-ahead)

Commands below are **procedure reminders**. Do **not** execute against production while status is **production no-go** or signatures are **UNSIGNED**.

```text
# Gates (approved non-prod / staging first)
# salesos/scripts/pre-deploy-gates.ps1

# Health (host must match the approved environment)
# curl -sf https://<api-host>/health

# Alembic — only after explicit human approval for that environment
# alembic current
# alembic upgrade head   # PRODUCTION: human-approved only

# Smoke — Wave 13 paths (auth + UI); prefer existing scripts under salesos/scripts/
```

Rollback: follow [deploy-rollback.md](../audit/ga-engineering-audit/runbooks/deploy-rollback.md) and [DR_RUNBOOK.md](./DR_RUNBOOK.md).

---

## 6. War room (Sprint-26)

| Role | Responsibility | Named? |
|------|----------------|--------|
| Release Manager | Cutover sequence, freeze exceptions | TBD |
| DevOps / SRE primary | Deploy, health, rollback | TBD |
| DevOps secondary | Backup page | TBD |
| Backend TL | API / migrate / data integrity | TBD |
| Frontend TL | UI smoke / client regressions | TBD |
| Security | Auth / CSRF / tenant isolation watch | TBD |
| Product | Comms; AI honesty in launch notes | TBD |
| Program Director | Leadership sync; no forged GO | TBD |

Channels / dashboards: **UNVERIFIED** names — fill before T-1 (`#salesos-deployments`, incident channel, Grafana/Prometheus URLs).

---

## 7. Sign-off residual (humans only)

Agents **must not** fill names, dates, or Decision=GO.

Use the authoritative blanks in:

- [runbooks/go-live-checklist.md](../audit/ga-engineering-audit/runbooks/go-live-checklist.md)  
- [SIGN_HERE.md](../audit/ga-engineering-audit/SIGN_HERE.md)

Required before any Production GO claim:

- [ ] CTO — GO / NO-GO / CONDITIONAL  
- [ ] Tech Lead — same + evidence-reviewed  
- [ ] CTO — RPO acceptance if DR scope requires it  
- [ ] Optional DevOps / Security witness acks  

Until then: **production no-go**.

---

## 8. Explicit non-claims

- Draft landing under `docs/ops/` ≠ executed cutover.  
- Sprint-26 stories (RC soak, GA cutover, commercial launch, war room) remain **open** until evidence + human sign-off.  
- Prior GO docs under `docs/vnext/reports/` remain **SUPERSEDED**.  
- Validation label for this document: **not validated** (docs prep only).

---

## 9. Change log

| Date | Change |
|------|--------|
| 2026-08-03 | Initial **draft landed** for Wave 13 / Sprint-26 prep — no execution, no Production GO |
