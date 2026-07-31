# Sprint 09 — 2026-11-23 → 2026-12-06

> **Phase:** 2 — Integration Hub + Odoo GA · **Prior:** [Sprint 08](Sprint-08.md) · **Next:** [Sprint 10](Sprint-10.md) · **Index:** [ENGINEERING_ROADMAP.md](../ENGINEERING_ROADMAP.md)

**Sprint Goal:** Field mapping + Anti-Corruption Layer.

**Team note:** BE3 and FE2 join the team this sprint per the roster plan.

| Story | Owner | Priority | Risk | Acceptance Criteria |
|---|---|---|---|---|
| STORY-08-03 (FieldMappingConfig + drift detection) | BE1 | P0 | Medium | Drift-detection job alerts loudly on a simulated field rename |
| STORY-08-04 (Anti-Corruption Layer) | BE-Lead | P0 | Medium | `OdooTranslator`-pattern class passes unit tests for all 6 internal responsibilities |
| BE3 onboarding | BE3 | — | — | Ramp-up, paired with BE2 on Integration Hub |

**Expected Demo:** Feed a deliberately malformed record through the ACL, show it caught by the Validator stage with a clear error, not a silent null.

**Technical Debt Created:** None.
