# Sprint 09 — 2026-11-23 → 2026-12-06

> **Phase:** 2 — Integration Hub + Odoo GA · **Prior:** [Sprint 08](Sprint-08.md) · **Next:** [Sprint 10](Sprint-10.md) · **Index:** [ENGINEERING_ROADMAP.md](../ENGINEERING_ROADMAP.md)

**Sprint Goal:** Field mapping + Anti-Corruption Layer.

**Team note:** BE3 and FE2 join the team this sprint per the roster plan.

| Story | Owner | Priority | Risk | Acceptance Criteria |
|---|---|---|---|---|
| STORY-08-03 (FieldMappingConfig + drift detection) | BE1 | P0 | Medium | **LANDED BE (Stream A):** `field_mapping_configs` Alembic `f2b8c79d3e06` + FORCE RLS; `run_field_drift_job` loud rename alert. Crumb [`PHASE1_STORY_08_03_FIELD_MAPPING_DRIFT_CRUMB.md`](../PHASE1_STORY_08_03_FIELD_MAPPING_DRIFT_CRUMB.md). No Production GO. |
| STORY-08-04 (Anti-Corruption Layer) | BE-Lead | P0 | Medium | **LANDED BE (Stream A):** `OdooTranslator` six internal stages + loud `AclValidationError`. Crumb [`PHASE1_STORY_08_04_ANTI_CORRUPTION_CRUMB.md`](../PHASE1_STORY_08_04_ANTI_CORRUPTION_CRUMB.md). No new RLS / POLICY_COUNT. No Production GO. |
| BE3 onboarding | BE3 | — | — | Ramp-up, paired with BE2 on Integration Hub |

**Expected Demo:** Feed a deliberately malformed record through the ACL, show it caught by the Validator stage with a clear error, not a silent null.

**Technical Debt Created:** None.
