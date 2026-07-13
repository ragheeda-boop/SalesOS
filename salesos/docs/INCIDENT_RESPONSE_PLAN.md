# SalesOS — Incident Response Plan

> Effective: 2026-07-13 · Version: 1.0
> Owner: Engineering Lead · Review: Quarterly

---

## 1. Severity Levels

| Level | Name | Description | Response Time | Update Frequency | Resolution Target |
|-------|------|-------------|---------------|-----------------|-------------------|
| **S1** | Critical | Platform down for all users; data loss risk; security breach | 15 minutes | Every 30 minutes | 4 hours |
| **S2** | High | Major feature unavailable; significant user impact; partial outage | 30 minutes | Every 1 hour | 8 hours |
| **S3** | Medium | Minor feature degraded; workaround available; limited impact | 2 hours | Every 4 hours | 24 hours |
| **S4** | Low | Cosmetic issue; non-blocking; minor inconvenience | 8 hours | Daily | 1 week |
| **S5** | Info | Observation, improvement suggestion, no user impact | 24 hours | Weekly | Next sprint |

### Examples

| Level | Scenario |
|-------|----------|
| S1 | PostgreSQL unreachable; authentication system down; data breach confirmed |
| S2 | Search returning errors; NBA engine down; >50% API errors |
| S3 | Slow API responses (p95 > 2s); single tenant affected; backup failure |
| S4 | UI misalignment; non-critical log errors; cosmetic RTL issues |
| S5 | Performance optimization opportunity; new monitoring suggestion |

---

## 2. Escalation Paths

### 2.1 Escalation Matrix

```
S5 (Info)       → Engineering Lead (within 24h)
S4 (Low)        → Engineering Lead (within 8h)
S3 (Medium)     → Engineering Lead (within 2h) → CTO (if unresolved in 12h)
S2 (High)       → Engineering Lead + CTO (within 30min) → CEO (if unresolved in 4h)
S1 (Critical)   → All hands (within 15min) → CEO immediately → External support if needed
```

### 2.2 On-Call Rotation

| Role | Response Time | Contact Method |
|------|---------------|----------------|
| Primary On-Call | 15 min (S1), 30 min (S2) | Phone + WhatsApp |
| Secondary On-Call | 30 min (S1), 1 hour (S2) | Phone + WhatsApp |
| Engineering Lead | 1 hour (S3+), Immediate (S1-S2) | Phone + Slack |
| CTO | 2 hours (S2+), Immediate (S1) | Phone |
| CEO | 4 hours (S2 business-critical), Immediate (S1) | Phone |

### 2.3 External Contacts

| Service | Contact | When to Engage |
|---------|---------|---------------|
| AWS Support | TBD | Infrastructure failures |
| Domain Registrar | TBD | DNS issues |
| SSL Provider (Caddy) | N/A (auto-renew) | Certificate issues |
| Security Firm | TBD | S1 security incidents |

---

## 3. Communication Templates

### 3.1 Internal Notification (S1-S2)

```
[INCIDENT - S{LEVEL}] {TITLE}

Status: Investigating / Identified / Monitoring / Resolved
Impact: {BRIEF IMPACT DESCRIPTION}
Start Time: {UTC TIMESTAMP}
Duration: {TIME SINCE START}
Next Update: {UTC TIMESTAMP}

Investigation: {BRIEF UPDATE}
Action Taken: {ACTIONS}

Incident Lead: {NAME}
Slack Channel: #incident-{ID}
```

### 3.2 External Notification (S1-S2)

```
Subject: [SalesOS Status] {SERVICE} Disruption

We are currently experiencing {DESCRIPTION} affecting {AFFECTED FEATURES}.

Impact: {USER IMPACT}
Start Time: {UTC TIMESTAMP}
Our team is actively investigating and will provide updates every {FREQUENCY}.

We apologize for the inconvenience and are working to restore service as quickly as possible.

— SalesOS Engineering Team
```

### 3.3 Resolution Notification

```
[INCIDENT RESOLVED - S{LEVEL}] {TITLE}

Resolved: {UTC TIMESTAMP}
Duration: {TOTAL DURATION}
Root Cause: {BRIEF ROOT CAUSE}

Actions Taken:
1. {ACTION 1}
2. {ACTION 2}

Post-Mortem: Scheduled for {DATE}
Follow-Up Items: {ISSUE LINKS}
```

---

## 4. Runbook Links

| Scenario | Runbook | Quick Fix |
|----------|---------|-----------|
| PostgreSQL down | `production_runbook.md` § DB Recovery | `docker compose restart postgres` |
| Neo4j connection leak | `production_runbook.md` § Neo4j | Context managers (already fixed, BUG-003) |
| High memory usage | `production_runbook.md` § Resources | `docker compose down && up -d` |
| API response time degraded | `production_runbook.md` § Performance | Check connection pool, scale workers |
| Backup failure | `production_runbook.md` § Backup | `docker compose restart backup` |
| SSL certificate expiry | `production_runbook.md` § TLS | Caddy auto-renew; manual: `caddy reload` |
| Authentication failures | `production_runbook.md` § Auth | Check JWT secret, verify token endpoint |
| Rate limiting triggered | `production_runbook.md` § Rate Limit | Check per-IP counters, adjust limits |
| Rollback deployment | `GA_LAUNCH_PLAN.md` § 2.4 | `docker compose pull` previous tag |
| Secret rotation | `production_runbook.md` § Secrets | Update `.env.production`, restart |

---

## 5. Post-Mortem Template

```markdown
# Post-Mortem: {INCIDENT TITLE}

> Date: YYYY-MM-DD
> Severity: S{LEVEL}
> Duration: {HH:MM}
> Author: {NAME}

---

## Summary

<1-2 sentence summary of what happened>

## Impact

- **Users affected**: {NUMBER or %}
- **Duration**: {START} to {END} ({DURATION})
- **Revenue impact**: {ESTIMATE or "Unknown"}
- **Data impact**: {NONE / Description}

## Timeline (UTC)

| Time | Event |
|------|-------|
| {TIME} | {EVENT} |
| {TIME} | {EVENT} |
| {TIME} | {EVENT} |

## Root Cause

<Primary root cause>

## Contributing Factors

- {Factor 1}
- {Factor 2}

## What Went Well

- {Positive 1}
- {Positive 2}

## What Went Wrong

- {Issue 1}
- {Issue 2}

## Action Items

| # | Action | Owner | Priority | Due Date | Issue |
|---|--------|-------|----------|----------|-------|
| 1 | {ACTION} | {OWNER} | P{0-3} | {DATE} | {LINK} |
| 2 | {ACTION} | {OWNER} | P{0-3} | {DATE} | {LINK} |

## Lessons Learned

<What we learned and how it changes our process>

## Detection

- **How detected**: {Monitoring alert / User report / Internal discovery}
- **Time to detect**: {DURATION}
- **Detection improvement**: {What could improve detection}

## Response

- **Time to acknowledge**: {DURATION}
- **Time to resolve**: {DURATION}
- **Response improvement**: {What could improve response}
```

---

## 6. Incident Workflow

```
Detection
    │
    ├── Automated (Prometheus alert, health check failure)
    └── Manual (user report, internal discovery)
          │
          ▼
    Triage (5 min)
    ├── Assign severity (S1-S5)
    ├── Assign incident lead
    └── Open incident channel (#incident-{ID})
          │
          ▼
    Investigation
    ├── Gather logs, metrics, traces
    ├── Identify root cause
    └── Communicate status (per update frequency)
          │
          ▼
    Mitigation
    ├── Implement fix or workaround
    ├── Verify fix in staging (if possible)
    └── Deploy fix
          │
          ▼
    Resolution
    ├── Confirm service restored
    ├── Monitor for recurrence
    └── Send resolution notification
          │
          ▼
    Post-Mortem (within 48 hours)
    ├── Complete post-mortem template
    ├── Identify action items
    └── Create GitHub Issues for follow-ups
```

---

*Last Updated: 2026-07-13 · Owner: Engineering Lead*
