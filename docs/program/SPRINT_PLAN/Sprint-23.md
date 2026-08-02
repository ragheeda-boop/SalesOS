# Sprint 23 — 2027-06-07 → 2027-06-20

> **Phase:** 6 — Hardening, Scale, Compliance · **Prior:** [Sprint 22](Sprint-22.md) · **Next:** [Sprint 24](Sprint-24.md) · **Index:** [ENGINEERING_ROADMAP.md](../ENGINEERING_ROADMAP.md)

**Sprint Goal:** Load + chaos testing.

| Story | Owner | Priority | Risk | Acceptance Criteria |
|---|---|---|---|---|
| STORY-14-01 (load test, 50 tenants) | DevOps/SRE, BE-Lead | P0 | High | **CLOSED for BE (Stream A):** tip HTTP `/api/v1/load/*` + remediation/postmortems @ `8a369f1`/`dd59a3f`. Crumb [`PHASE1_STORY_14_01_LOAD_SLO_CRUMB.md`](../PHASE1_STORY_14_01_LOAD_SLO_CRUMB.md). Field 50-tenant / 2h soak residual = DevOps. No new RLS. Live prod kill / Production GO not claimed. |
| STORY-14-02 (chaos test) | DevOps/SRE, BE-Lead | P0 | High | **LANDED BE (Stream A):** CI fault-injection harness — connector/AI/DB drills graceful + practice postmortem each via `/api/v1/chaos/*`. Crumb [`PHASE1_STORY_14_02_CHAOS_RESILIENCE_CRUMB.md`](../PHASE1_STORY_14_02_CHAOS_RESILIENCE_CRUMB.md). No new RLS. Live kill / Production GO not claimed. |
| STORY-14-03 (DR drill) | DevOps/SRE, BE-Lead | P0 | High | **LANDED BE (Stream A):** CI/non-prod backup/restore + PITR harness — RTO≤4h / RPO≤1h measured + practice postmortem via `/api/v1/dr/*`. Crumb [`PHASE1_STORY_14_03_DR_DRILL_CRUMB.md`](../PHASE1_STORY_14_03_DR_DRILL_CRUMB.md). No new RLS. Live prod restore / Production GO not claimed. |

**Expected Demo:** Live chaos-test run: kill the primary AI provider connection mid-demo, show failover engaging within SLO.

**Technical Debt Created:** Any SLO miss becomes a tracked remediation item, reviewed before Sprint 25 gate — not silently accepted.
