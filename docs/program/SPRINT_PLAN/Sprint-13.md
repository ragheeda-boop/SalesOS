# Sprint 13 — 2027-01-18 → 2027-01-31

> **Phase:** 3 — Tenant Studio Core · **Prior:** [Sprint 12](Sprint-12.md) · **Next:** [Sprint 14](Sprint-14.md) · **Index:** [ENGINEERING_ROADMAP.md](../ENGINEERING_ROADMAP.md)

**Sprint Goal:** Workflow Builder no-code canvas.

| Story | Owner | Priority | Risk | Acceptance Criteria |
|---|---|---|---|---|
| STORY-10-03 (Workflow Builder) | BE1, FE1 | P0 | High | **LANDED BE (Stream A):** canvas→`WorkflowEngine` compiler + equivalence suite (`GET/POST /api/v1/studio/workflows`). Crumb [`PHASE1_STORY_10_03_WORKFLOW_CANVAS_COMPILER_CRUMB.md`](../PHASE1_STORY_10_03_WORKFLOW_CANVAS_COMPILER_CRUMB.md). Loops deferred. No new RLS. No Production GO. |
| FE-S10-03 (Workflow Builder Studio UI) | FE-Lead | P0 | Low | **LANDED FE (Stream B):** `/studio/workflows` against tip canvas + compile. Crumb [`PHASE1_FE_S10_03_WORKFLOW_STUDIO_CRUMB.md`](../PHASE1_FE_S10_03_WORKFLOW_STUDIO_CRUMB.md). for_each not invented. No Production GO. |

**Expected Demo:** Build a workflow entirely in the no-code canvas, show it executing identically to an equivalent hand-coded workflow (side-by-side result comparison).

**Technical Debt Created:** Canvas supports linear + branching flows; loops/iterators deferred to backlog (flagged, not hidden).
