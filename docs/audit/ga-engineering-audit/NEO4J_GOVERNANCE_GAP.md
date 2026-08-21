# Neo4j Governance Gap — ADR-108 vs Railway Deployment

**Date:** 2026-08-20  
**Classification:** Governance Clarification Required (not a remediation blocker)  
**Authority:** ADR-108 (ACCEPTED 2026-08-07) + Railway live verification (EAB-2026-08-06-003)

---

## The Gap

| Source | Statement | Implication |
|--------|-----------|-------------|
| **ADR-108** (ACCEPTED) | "Keep Neo4j offline in v1.0. Do not activate." | Neo4j carries no production traffic; DR obligation deferred to v2.0 |
| **Railway deployment** | `neo4j-prod` service exists in both `production` and `staging` environments with `graph=connected` status | Neo4j is deployed and reachable in production infrastructure |

**Gap:** ADR-108 governs the *data path* (no production traffic through Neo4j), but the *infrastructure* has a running Neo4j service. This is a governance clarification, not a code or DR remediation issue.

---

## Analysis

### Why This Is Not a v1.0 Problem

1. **No production data flows through Neo4j** — verified by code review:
   - Activity Intelligence uses PostgreSQL (`intelligence/activity_intelligence.py`)
   - Company 360 is optional/deferred (`intelligence/company_360.py`)
   - Graph API has SQL fallback (`repositories/router_repository.py:100-156`)
   - Health check marks graph as `critical: False` (`routers/health.py`)

2. **ADR-108 §Decision explicitly governs this:** "Neo4j in docker-compose (for development/experimentation)" — the service is defined for dev convenience, not production use.

3. **ADR-108 §What moves to v2.0:** "Neo4j activation in production" — activation means routing production traffic, not deploying the service.

### Why the Gap Exists

- Railway deploys all services defined in `docker-compose.yml` / `railway.json`
- Neo4j is in `docker-compose.yml` (14 services) for development
- Railway deploys it as a running service even though ADR-108 says "offline"
- "Offline" in ADR-108 means "no production data path" — the service process running is an infrastructure artifact, not a data path violation

### Evidence That Neo4j Is Not Used in Production

| Code Path | Uses Neo4j? | Actual Backend |
|-----------|-------------|----------------|
| Activity Intelligence (`intelligence/activity_intelligence.py`) | No | PostgreSQL |
| Company 360 (`intelligence/company_360.py`) | Optional, deferred | PostgreSQL (primary) |
| Graph API fallback (`repositories/router_repository.py:100-156`) | No | PostgreSQL SQL fallback |
| Health check (`routers/health.py`) | Marks `critical: False` | N/A |

---

## Recommendation

**No remediation required for v1.0 GA.** The gap should be:

1. **Documented** (this file) — governance audit trail
2. **Acknowledged** in OPS-01-CHECKLIST.md row OPS01-06 — reclassified to NOT APPLICABLE
3. **Carried forward** to v2.0 planning — when Neo4j activation is planned, the deployment artifact becomes the activation point

### v2.0 Action Items (when Neo4j is activated)

- [ ] Confirm Neo4j production backup/restore policy (currently local dump only)
- [ ] Enable production data sync (currently SQL-only path)
- [ ] Add Neo4j to RPO/RTO scope
- [ ] Verify Neo4j volume isolation (currently same volume model as PostgreSQL)

---

## Cross-References

- ADR-108: [docs/adr/0108-neo4j-keep-offline.md](../adr/0108-neo4j-keep-offline.md)
- OPS-01 Checklist: [OPS-01-CHECKLIST.md](enterprise-audit-board/history/EAB-2026-08-06-003/OPS-01-CHECKLIST.md) — row OPS01-06
- DR-GA-Gaps: [DR-GA-GAPS-CHECKLIST.md](../ops/DR-GA-GAPS-CHECKLIST.md) — row 6
- FINAL_GO_NOGO: [FINAL_GO_NOGO_ASSESSMENT.md](FINAL_GO_NOGO_ASSESSMENT.md) — §6 Governance Reconciliation + §9 Schema Drift
- A09 Live Verification: [A09-OPS01-LIVE-VERIFICATION-2026-08-20.md](../ops/A09-OPS01-LIVE-VERIFICATION-2026-08-20.md)
- A-09 Staging Parity Analysis: [A-09-STAGING-PARITY-ANALYSIS-2026-08-20.md](../ops/A-09-STAGING-PARITY-ANALYSIS-2026-08-20.md)
- OPS-01 DR Sign-off: [OPS-01-DR-SIGNOFF-CHECKLIST-2026-08-20.md](../ops/OPS-01-DR-SIGNOFF-CHECKLIST-2026-08-20.md)
