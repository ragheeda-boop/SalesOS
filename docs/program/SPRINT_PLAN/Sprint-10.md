# Sprint 10 — 2026-12-07 → 2026-12-20

> **Phase:** 2 — Integration Hub + Odoo GA · **Prior:** [Sprint 09](Sprint-09.md) · **Next:** [Sprint 11](Sprint-11.md) · **Index:** [ENGINEERING_ROADMAP.md](../ENGINEERING_ROADMAP.md)

**Sprint Goal:** Sync scheduling + conflict resolution; Integrations Studio UI; Odoo Company/Contact sync starts.

| Story | Owner | Priority | Risk | Acceptance Criteria |
|---|---|---|---|---|
| STORY-08-05 (SyncRun + scheduling) | BE2 | P0 | Medium | **LANDED BE (Stream A):** `sync_runs` Alembic `c4d8e21a9f07` + monthly partitions + FORCE RLS (POLICY_COUNT 70); CAP-028 `schedule_connection_sync` tick logs SyncRun. Crumb [`PHASE1_STORY_08_05_SYNC_RUN_CRUMB.md`](../PHASE1_STORY_08_05_SYNC_RUN_CRUMB.md). No Production GO. |
| STORY-08-06 (ConflictResolutionPolicy) | BE-Lead | P1 | Medium | **LANDED BE (Stream A):** OBJ-333 + FORCE RLS (POLICY_COUNT 71); feedback-loop exclusion test; Hub HTTP `/api/v1/integrations/*` for FE-08-07. Crumb [`PHASE1_STORY_08_06_CONFLICT_POLICY_HUB_HTTP_CRUMB.md`](../PHASE1_STORY_08_06_CONFLICT_POLICY_HUB_HTTP_CRUMB.md). No Production GO. |
| STORY-08-07 (Integrations Studio UI) | FE-Lead, FE2 | P0 | Medium | **LANDED FE (Stream B):** `/integrations` Studio connect/test/map/schedule/monitor/disconnect against Hub HTTP. Crumb [`PHASE1_STORY_08_07_INTEGRATIONS_STUDIO_CRUMB.md`](../PHASE1_STORY_08_07_INTEGRATIONS_STUDIO_CRUMB.md). Fake adapter test only; no Production GO. |
| FE-S08-08 (Conflict-policy Studio + Odoo honesty) | FE-Lead | P0 | Low | **LANDED FE (Stream B):** Conflict step GET/PUT tip `/conflict-policy`; Odoo connector_key honesty after STORY-09-01. Crumb [`PHASE1_FE_S08_08_CONFLICT_POLICY_STUDIO_CRUMB.md`](../PHASE1_FE_S08_08_CONFLICT_POLICY_STUDIO_CRUMB.md). No Production GO. |
| FE-S08-09 (Active mapping + tenant Integrations nav) | FE-Lead | P1 | Low | **LANDED FE (Stream B):** Map loads tip GET `/mappings/active`; tenant nav `/integrations`. Crumb [`PHASE1_FE_S08_09_ACTIVE_MAPPING_NAV_CRUMB.md`](../PHASE1_FE_S08_09_ACTIVE_MAPPING_NAV_CRUMB.md). No Production GO. |
| FE-S08-10 (Studio detail + baseline_fields polish) | FE-Lead | P1 | Low | **LANDED FE (Stream B):** connection detail from tip fields; map `baseline_fields`; monitor refresh; disconnect confirm; cmd palette. Crumb [`PHASE1_FE_S08_10_STUDIO_DETAIL_POLISH_CRUMB.md`](../PHASE1_FE_S08_10_STUDIO_DETAIL_POLISH_CRUMB.md). No Production GO. |
| FE-S08-14 (Mapping version + schedule name + connection GET) | FE-Lead | P1 | Low | **LANDED FE (Stream B):** tip mapping version + schedule name + GET connection refresh + cmd deep-links. Crumb [`PHASE1_FE_S08_14_MAPPING_SCHEDULE_CONNECTION_CRUMB.md`](../PHASE1_FE_S08_14_MAPPING_SCHEDULE_CONNECTION_CRUMB.md). No Production GO. |
| FE-S08-13 (Schedule job_type + conflict tip defaults) | FE-Lead | P1 | Low | **LANDED FE (Stream B):** tip `job_type` + conflict default load + connection active filter/`connection_config`. Crumb [`PHASE1_FE_S08_13_SCHEDULE_CONFLICT_POLISH_CRUMB.md`](../PHASE1_FE_S08_13_SCHEDULE_CONFLICT_POLISH_CRUMB.md). No Production GO. |
| FE-S08-12 (Monitor SyncRun model filter) | FE-Lead | P1 | Low | **LANDED FE (Stream B):** client model filter + tip finished_at/scheduled_job_id + `?runStatus=`/`?runModel=`. Crumb [`PHASE1_FE_S08_12_MONITOR_MODEL_FILTER_CRUMB.md`](../PHASE1_FE_S08_12_MONITOR_MODEL_FILTER_CRUMB.md). No Production GO. |
| FE-S08-11 (Studio URL deep-link polish) | FE-Lead | P1 | Low | **LANDED FE (Stream B):** `?step=`/`?connection=` sync; schedule result; monitor status filter; copy connection id. Crumb [`PHASE1_FE_S08_11_STUDIO_URL_DEEPLINK_CRUMB.md`](../PHASE1_FE_S08_11_STUDIO_URL_DEEPLINK_CRUMB.md). No Production GO. |
| STORY-09-01 (Odoo Company/Contact sync) | BE3 | P0 | Medium | **LANDED BE (Stream A):** `OdooAdapter` + `cr_number` join (matched/unlinked); in-memory RPC for CI. Crumb [`PHASE1_STORY_09_01_ODOO_COMPANY_CONTACT_SYNC_CRUMB.md`](../PHASE1_STORY_09_01_ODOO_COMPANY_CONTACT_SYNC_CRUMB.md). No new RLS. No Production GO. |

**Expected Demo:** Connect a staging Odoo sandbox through the Studio UI, see Company/Contact records materialize with Golden Record matches.

**Technical Debt Created:** "Unlinked record" badge (for match failures) is stubbed, not fully designed — completes next sprint.
