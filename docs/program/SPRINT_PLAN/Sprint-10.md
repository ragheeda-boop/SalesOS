# Sprint 10 — 2026-12-07 → 2026-12-20

> **Phase:** 2 — Integration Hub + Odoo GA · **Prior:** [Sprint 09](Sprint-09.md) · **Next:** [Sprint 11](Sprint-11.md) · **Index:** [ENGINEERING_ROADMAP.md](../ENGINEERING_ROADMAP.md)

**Sprint Goal:** Sync scheduling + conflict resolution; Integrations Studio UI; Odoo Company/Contact sync starts.

| Story | Owner | Priority | Risk | Acceptance Criteria |
|---|---|---|---|---|
| STORY-08-05 (SyncRun + scheduling) | BE2 | P0 | Medium | **LANDED BE (Stream A):** `sync_runs` Alembic `c4d8e21a9f07` + monthly partitions + FORCE RLS (POLICY_COUNT 70); CAP-028 `schedule_connection_sync` tick logs SyncRun. Crumb [`PHASE1_STORY_08_05_SYNC_RUN_CRUMB.md`](../PHASE1_STORY_08_05_SYNC_RUN_CRUMB.md). No Production GO. |
| STORY-08-06 (ConflictResolutionPolicy) | BE-Lead | P1 | Medium | **LANDED BE (Stream A):** OBJ-333 + FORCE RLS (POLICY_COUNT 71); feedback-loop exclusion test; Hub HTTP `/api/v1/integrations/*` for FE-08-07. Crumb [`PHASE1_STORY_08_06_CONFLICT_POLICY_HUB_HTTP_CRUMB.md`](../PHASE1_STORY_08_06_CONFLICT_POLICY_HUB_HTTP_CRUMB.md). No Production GO. |
| STORY-08-07 (Integrations Studio UI) | FE-Lead, FE2 | P0 | Medium | **LANDED FE (Stream B):** `/integrations` Studio connect/test/map/schedule/monitor/disconnect against Hub HTTP. Crumb [`PHASE1_STORY_08_07_INTEGRATIONS_STUDIO_CRUMB.md`](../PHASE1_STORY_08_07_INTEGRATIONS_STUDIO_CRUMB.md). Fake adapter test only; no Production GO. |
| STORY-09-01 (Odoo Company/Contact sync) | BE3 | P0 | Medium | **LANDED BE (Stream A):** `OdooAdapter` + `cr_number` join (matched/unlinked); in-memory RPC for CI. Crumb [`PHASE1_STORY_09_01_ODOO_COMPANY_CONTACT_SYNC_CRUMB.md`](../PHASE1_STORY_09_01_ODOO_COMPANY_CONTACT_SYNC_CRUMB.md). No new RLS. No Production GO. |

**Expected Demo:** Connect a staging Odoo sandbox through the Studio UI, see Company/Contact records materialize with Golden Record matches.

**Technical Debt Created:** "Unlinked record" badge (for match failures) is stubbed, not fully designed — completes next sprint.
