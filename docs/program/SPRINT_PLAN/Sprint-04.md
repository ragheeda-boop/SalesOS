# Sprint 04 — 2026-09-14 → 2026-09-27

> **Phase:** 1 — Owner Platform Core · **Prior:** [Sprint 03](Sprint-03.md) · **Next:** [Sprint 05](Sprint-05.md) · **Index:** [ENGINEERING_ROADMAP.md](../ENGINEERING_ROADMAP.md)

**Sprint Goal:** `Tenant` object extended; provisioning workflow skeleton live.

| Story | Owner | Priority | Risk | Status | Acceptance Criteria |
|---|---|---|---|---|---|
| STORY-04-01 (Tenant extension) | BE-Lead | P0 | Low | **IN PROGRESS** (A2 `64b44e9` / `f6b2e84c1a90`; FE B4 sync) | Migration applied; `plan_id`/`region`/`data_residency`/`provisioning_status`/`trial_ends_at` present |
| STORY-04-02 (provisioning workflow) | BE1 | P0 | Medium | **IN PROGRESS** (A3 skeleton + FE create wires `admin_email`) | Idempotent provisioning job creates a tenant + seeds default Studio config + assigns first admin |
| STORY-02-03 (JWT audience split, consume) | BE2 | P1 | Medium | **CLOSED** (DEC-093) | Owner-audience consumption **CLOSED** (DEC-093): Platform admin wires `decode_owner_*` via `owner_auth.py`; host pytest **14/14 PASS**. Groundwork `2379e5f`; DEC-091 OPEN superseded. |
| FE Stream B (Owner Console tenants) | FE-Lead | P1 | Low | **B1–B5 + B4 + FE-S04-06..11** ([`PHASE1_FE_STREAM_B_CRUMB.md`](../PHASE1_FE_STREAM_B_CRUMB.md)) | Admin `/admin/tenants` Owner Platform CRUD/suspend/filters; `TenantList` untouched; no Production GO |

**Expected Demo:** Provision a brand-new test tenant end-to-end via a script (no UI yet), show it isolated from Muhide's tenant in the RLS test suite.

**Technical Debt Created:** Default Studio config templates are hardcoded per plan tier (not yet Studio-editable) — acceptable, since Tenant Studio itself is Phase 3.

---

## S04-02 Status (2026-07-31)

**FIELD VERIFICATION COMPLETE.** Commit `354e13c` ("chore: Sprint 04 CI field-verification trigger") triggered the first real GitHub Actions execution on `master`: 5 workflows ran (CI, Docker Smoke Test, Security Scan, Deploy Production, Deploy Staging), **all 5 failed**, 17 failed jobs total. Full evidence-based triage of every failed job: `salesos/docs/audit/ga-engineering-audit/SPRINT_04_CI_TRIAGE.md`. **CI GREEN is not met.** None of the 17 failures originate in Sprint 04 feature code (STORY-04-01/04-02/02-03 are not yet implemented) — every failure is pre-existing CI/pipeline configuration or tooling debt, first surfaced by this being the program's first real CI run. Decision on whether Sprint 04 can proceed: see `DECISION_LOG.md` D-S4-002.
