# Sprint 08 — 2026-11-09 → 2026-11-22

> **Phase:** 2 — Integration Hub + Odoo GA · **Prior:** [Sprint 07](Sprint-07.md) · **Next:** [Sprint 09](Sprint-09.md) · **Index:** [ENGINEERING_ROADMAP.md](../ENGINEERING_ROADMAP.md)

**Sprint Goal:** Entitlement Engine hardened; Integration Hub interface + connection object.

**Team note:** Security moves from part-time to full-time this sprint per the roster plan.

| Story | Owner | Priority | Risk | Acceptance Criteria |
|---|---|---|---|---|
| STORY-06-03 (quota enforcement) | BE1 | P0 | Medium | Seat/token/connector/storage quotas enforced, clear over-quota response |
| STORY-06-04 (entitlement-bypass suite) | Security | P0 | High | Full plan × capability adversarial matrix passes |
| STORY-08-01 (SourceConnector interface) | BE-Lead | P0 | Medium | Interface documented; a fake/mock adapter implements it with zero framework changes needed |
| STORY-08-02 (ExternalSystemConnection) | BE2 | P0 | High | Fernet-encrypted, tenant-scoped, passes cross-tenant regression suite |

**Expected Demo:** Show the mock adapter passing certification against the `SourceConnector` interface — proof the framework is generic *before* any Odoo-specific code exists.

**Technical Debt Created:** None.
