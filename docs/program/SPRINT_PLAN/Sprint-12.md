# Sprint 12 — 2027-01-04 → 2027-01-17

> **Phase:** 3 — Tenant Studio Core · **Prior:** [Sprint 11](Sprint-11.md) · **Next:** [Sprint 13](Sprint-13.md) · **Index:** [ENGINEERING_ROADMAP.md](../ENGINEERING_ROADMAP.md)

**Sprint Goal:** Custom Objects/Fields live (highest-leverage Studio module first).

| Story | Owner | Priority | Risk | Acceptance Criteria |
|---|---|---|---|---|
| STORY-10-01 (Custom Object/Field definition) | BE-Lead | P0 | Medium | **LANDED BE (Stream A):** reserved-column collision + versioned schema + `GET/POST /api/v1/studio/custom-fields` (in-memory). Crumb [`PHASE1_STORY_10_01_CUSTOM_OBJECT_FIELD_CRUMB.md`](../PHASE1_STORY_10_01_CUSTOM_OBJECT_FIELD_CRUMB.md). No new RLS. No Production GO. |
| STORY-10-02 (auto-render in existing UI) | BE2 / FE-Lead | P0 | Medium | **LANDED BE (Stream A):** Form Engine auto-render schema + `metadata.custom_fields` value bag (`GET .../form-schema`). Crumb [`PHASE1_STORY_10_02_CUSTOM_FIELD_AUTO_RENDER_CRUMB.md`](../PHASE1_STORY_10_02_CUSTOM_FIELD_AUTO_RENDER_CRUMB.md). FE page wire residual. No new RLS. No Production GO. |
| Odoo 14-day soak monitoring | BE3 | P0 | High | Daily check-in; any sync failure triaged same-day |

**Expected Demo:** Tenant admin adds a custom field via Studio, sees it live on the Company page within the same session.

**Technical Debt Created:** Custom fields support scalar types only in v1 (string/number/date/enum) — relational custom fields deferred, tracked as backlog.
