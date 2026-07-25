# Risk Acceptance Assessment

**Board:** Independent CTO + Release Review Board  
**Date:** 2026-07-23

---

## Risks requiring explicit acceptance

The following risks have been identified by the engineering audit, evidence review, peer review, and gap closure analysis. Each risk is presented with its current mitigation status and a recommendation from the board.

---

### R1: 48h Soak Incomplete

| Field | Detail |
|-------|--------|
| Risk | System may degrade under sustained load beyond 13.3h. Docker instability observed (~every 2-6h the stack requires recovery). |
| Evidence | `wave11-soak-48h-rerun/` — 149 iterations, 93%+ check pass rate. 22% of gate checks fail (mostly FE timeouts during Docker recovery). |
| Mitigation | Soak still running. Auto-close when 48h wall clock reached. |
| Risk if accepted now | Unknown stability beyond current duration. Docker resource pressure pattern suggests periodic restarts may be needed. |
| Recommendation | **Do not accept.** Wait for soak completion. Minimum: 24h with <5% failure rate. |

---

### R2: No Cloud Staging

| Field | Detail |
|-------|--------|
| Risk | Deploy/rollback procedures untested on production-representative infrastructure. Local Docker compose ≠ cloud VPS with real networking, SSL, DNS. |
| Evidence | `wave12-staging/probe-*.json` confirms 0 Environments, 0 secrets. `runbooks/staging-fill-in.md` documents exact procedure. |
| Mitigation | Local virtual staging tabletop DONE (proves compose works). Cloud staging blocked only by credentials, not code. |
| Risk if accepted now | First production-like deploy will happen on actual production. Rollback may fail in unexpected ways. |
| Recommendation | **Conditional acceptance for pilot.** Staging must be provisioned and tabletop completed within 72h of GO. Local tabletop provides reasonable confidence for low-risk pilot. |

---

### R3: No External Pentest

| Field | Detail |
|-------|--------|
| Risk | SSRF, IDOR, tenant isolation, RBAC, CSRF, and API auth have code-level P0 fixes but no external adversarial testing. |
| Evidence | P0 code fixes: IDOR tenant-scoped, SSRF pin-on-connect + private IP block + Alembic 0039/0040, KG SQL fallback disabled in prod config, Forecast demo gate. Local probe evidence: SSRF deny JSON, cross-tenant 403 JSON. |
| Residuals | SSRF: DNS TOCTOU race, first-IP-only pin, httpx pool private API coupling. KG: env-dependent fallback policy. |
| Mitigation | Code-level defenses tested locally. Staging pentest requires staging (R2). |
| Risk if accepted now | Undiscovered vulnerabilities may exist in the webhook delivery path, GraphQL layer, or tenant isolation boundaries. |
| Recommendation | **Accept for pilot with formal residual sign-off.** CTO + Security must sign: (a) acknowledge SSRF residuals, (b) accept pilot data scope as low-risk, (c) commit to full pentest before production GA. |

---

### R4: No Offsite Backup (S3/MinIO)

| Field | Detail |
|-------|--------|
| Risk | All backups exist only on local Docker volumes. Single-host failure = total data loss. |
| Evidence | pg_dump 22MB local. Neo4j dump local. WAL disposable drill local. `offsite-s3-restore-stub.md` documents exactly what's missing. No MinIO/S3 service in any compose file. `S3_BUCKET=""` in backup config. |
| Mitigation | Local backup drill proves dump/restore works. Offsite requires external S3 bucket or MinIO deployment. |
| Risk if accepted now | Host failure = complete data loss. No off-box copy exists. |
| Recommendation | **Conditional acceptance for pilot.** S3/MinIO backup must be configured within 7 days. Until then: manual backup copy to external storage after each significant data change. |

---

### R5: RPO Undefined

| Field | Detail |
|-------|--------|
| Risk | No formal Recovery Point Objective. If data loss occurs, no agreed-upon acceptable loss window. |
| Evidence | Options documented: 24h (simple, daily backup) vs WAL-based (~0 loss, requires `archive_mode=on`). Disposable WAL drill proven. Primary `archive_mode=off`. |
| Mitigation | CTO must choose. Both options are documented with technical paths. |
| Risk if accepted now | Ambiguity in disaster recovery expectations. |
| Recommendation | **Accept 24h RPO for pilot.** Simpler, no infra change needed. WAL-based can be implemented when offsite S3 is configured (R4). |

---

### R6: AI Marketing Scope

| Field | Detail |
|-------|--------|
| Risk | AI features (copilot, decision engine) may be marketed as production-ready despite stubs and disabled flags. |
| Evidence | `feature_ai_copilot=False` default. API returns 403. FE Decision package throws STUB. Nav/panel gated. Preview badges shown. |
| Mitigation | Code gate is fully enforced. Risk is purely in marketing/comms, not technical. |
| Risk if accepted now | Misleading launch messaging. |
| Recommendation | **Accept with PRC sign-off.** CTO + Product must review launch notes before publication. AI must not be described as "production-ready" or "GA" in any external communication. |

---

### R7: Docker/Infrastructure Stability

| Field | Detail |
|-------|--------|
| Risk | Docker daemon becomes unresponsive ~every 2-6 hours under sustained load. Requires manual restart or automatic recovery. |
| Evidence | Observed during 48h soak: stack degraded at ~2h, recovered after frontend restart. Postgres went into recovery mode after unclean shutdown. Kafka healthcheck consistently fails. |
| Mitigation | Stack recovers automatically (frontend restarts). Event bus uses `in_memory` mode (no Kafka dependency at runtime). Health checks eventually pass. |
| Risk if accepted now | Production may experience periodic ~5-15 minute unavailability windows. |
| Recommendation | **Monitor and accept.** This is a Docker Desktop / Windows host limitation, not a code defect. Production on Linux/K8s would not exhibit same behavior. Document as known pilot limitation. |

---

## Risk Acceptance Summary

| Risk | Accept Now? | Condition |
|------|------------|-----------|
| R1: Soak incomplete | **NO** | Wait for 48h completion |
| R2: No cloud staging | **YES** (conditional) | Provision within 72h |
| R3: No pentest | **YES** (conditional) | Pilot residual sign-off; full pentest before GA |
| R4: No offsite backup | **YES** (conditional) | S3 configured within 7 days |
| R5: RPO undefined | **YES** | Accept 24h for pilot |
| R6: AI marketing | **YES** | PRC sign-off on launch notes |
| R7: Docker stability | **YES** | Known dev limitation; not production-representative |

---

## Risk Acceptance Sign-Off Block

```
I, the undersigned, have reviewed the 7 risks listed above.
I accept the risks marked "YES" with the stated conditions.
I explicitly acknowledge risks marked "NO" will block Production GO until resolved.

CTO: ________________________________  Date: __________

Tech Lead: __________________________  Date: __________

Security (for R3): __________________  Date: __________
```
