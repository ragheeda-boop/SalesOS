# Decision Log — SaaS Platform Program

> **Scope note:** This log is scoped to the commercial-SaaS-platform program (`docs/program/`) — the architecture and execution decisions made in designing and sequencing the Owner Platform / Tenant Workspace / Integration Hub / GTM Studio work. It is distinct from the repo-root `docs/DECISION_LOG.md`, which predates this program and covers earlier product decisions; this file does not supersede that one.
> **Format:** ADR-lite. Each entry: Decision, Date, Context, Alternatives Considered, Consequence, Status.
> **Rule:** Decisions are never edited in place once `Accepted` — a changed decision gets a new entry that marks the old one `Superseded by DEC-0XX`.

---

### DEC-001 — Reframe SalesOS as a two-plane commercial SaaS platform (Owner Platform / Tenant Workspace)

**Date:** 2026-07-30
**Context:** SalesOS's existing architecture (`CANONICAL_ARCHITECTURE.md`) was validated against a single production tenant (Muhide) and describes row-level multi-tenancy but no commercial platform layer — no billing, no self-service provisioning, no marketplace, no cross-tenant governance surface.
**Alternatives considered:** (a) Keep the single-tenant architecture and bolt on billing/provisioning as an afterthought layered directly into existing domains; (b) build a fully separate codebase for the "commercial" side.
**Decision:** Split into two planes sharing one codebase and one database engine but never sharing data or an admin surface: Side A (`DOM-020 Platform Operations`, Owner-only) and Side B (`DOM-001–019`, unchanged, now called "Tenant Workspace").
**Consequence:** Every existing DOM/CAP/OBJ ID is preserved unchanged; five new domains (`DOM-020`–`024`) are added rather than existing ones being restructured. See `SAAS_PLATFORM_ARCHITECTURE.md` §0.
**Status:** Accepted.

---

### DEC-002 — Generalize the Integration Hub now, reversing the ARB meta-review's "over-engineering" verdict

**Date:** 2026-07-30
**Context:** `ARB_REVIEW_ODOO_INTEGRATION.md` proposed a generic multi-vendor Connector Framework; `ARB_META_REVIEW.md` downgraded that to "over-engineering for a five-person team building one connector for one tenant" and recommended deferring it until a second connector was actually scoped.
**Alternatives considered:** (a) Build Odoo bespoke now, generalize only when/if a second connector is funded (the meta-review's original recommendation); (b) generalize now.
**Decision:** Build the generic `SourceConnector` framework (EPIC-08) before any Odoo-specific code, because the condition the meta-review said would flip its verdict — "revisit when a second connector is actually funded/scoped" — is now true by definition (this program's explicit mandate is "hundreds of customers, many ERPs").
**Consequence:** EPIC-08 (framework) is sequenced strictly before EPIC-09 (Odoo adapter); a second connector's certification (EPIC-11, STORY-11-10) is a hard Phase 4 exit gate, not a nice-to-have, directly closing risk R-02.
**Status:** Accepted. Supersedes the deferral recommendation in `ARB_META_REVIEW.md` §4 (that recommendation was correct for its stated scope; the scope has since changed).

---

### DEC-003 — Rename `OBJ-303 Invoice` → `PlatformBillingInvoice` is now mandatory, not merely recommended

**Date:** 2026-07-30
**Context:** The original Odoo ARB called this rename "mandatory"; the meta-review downgraded it to "Recommended," citing an existing unremarked precedent (`OBJ-006`/`OBJ-302` both named `License` across two domains).
**Alternatives considered:** (a) Leave `Invoice` ambiguous, matching the `License`/`License` precedent; (b) rename now.
**Decision:** Rename now. The precedent argument weakens materially at platform scale: `Invoice` will soon also mean "an Owner-Platform billing record queried across every tenant" — a categorically higher-traffic, higher-consequence ambiguity than the `License` precedent.
**Consequence:** A migration/aliasing period is required (explicitly not omitted this time, per the meta-review's own criticism of the original ARB for missing this) — tracked as part of EPIC-05/07 billing work.
**Status:** Accepted.

---

### DEC-004 — Entitlements are a layer over feature flags, never a replacement for them

**Date:** 2026-07-30
**Context:** SalesOS's existing feature-flag system is Grade A maturity (per-tenant override, gradual rollout) — the only Grade A infrastructure dimension in the platform.
**Alternatives considered:** (a) Build entitlements as a single unified mechanism replacing flags; (b) two independent layers.
**Decision:** Two independent layers: `Plan.entitlements` gates whole DOM/CAP visibility (commercial packaging); feature flags gate rollout within an entitled capability (technical canary/kill-switch). Never conflated.
**Consequence:** EPIC-06 (Entitlement Engine) is additive to, not a rewrite of, the existing flag infrastructure.
**Status:** Accepted.

---

### DEC-005 — Pooled multi-tenant Postgres (RLS-isolated) is the default deployment tier through GA; siloed tenancy is deferred

**Date:** 2026-07-30
**Context:** Target GA scale is "dozens of tenants," not thousands; building a dedicated-tenant infrastructure tier speculatively, before any customer requires it, is the same premature-generalization pattern the Odoo ARB debate already flagged once (DEC-002).
**Alternatives considered:** (a) Build the siloed tier now, in parallel; (b) defer until an actual signed Enterprise deal requires it.
**Decision:** Defer (b). Isolation tier is a provisioning decision (`Tenant.data_residency`/`provisioning_status`), not an architecture fork — the codebase supports it structurally, but the siloed tier itself is not built pre-GA.
**Consequence:** Named explicitly as `MASTER_EXECUTION_PLAN.md` assumption A6 and tracked in `IMPLEMENTATION_SEQUENCE.md` §4 Blocked Work — if a real deal forces it earlier, this is a tracked pull-forward decision, not silent scope creep.
**Status:** Accepted.

---

### DEC-006 — Stripe as the billing provider

**Date:** 2026-07-30
**Context:** No in-house payment processing is being considered; a third-party PCI-scope-minimizing provider is required.
**Alternatives considered:** Build custom billing logic against a lower-level payment processor; evaluate multiple providers formally.
**Decision:** Stripe, assumed as the default provider absent a stated reason to prefer another (`MASTER_EXECUTION_PLAN.md` A3).
**Consequence:** EPIC-05 is scoped specifically around Stripe's webhook/checkout/proration model. If a different provider is chosen later, EPIC-05's *tasks* re-scope; the epic's existence and sequencing position do not change.
**Status:** Accepted (provisional — flagged as an assumption, not a vendor-evaluation outcome).

---

### DEC-007 — AI Memory is scoped to conversation-level only through GA; cross-session long-term memory is deferred

**Date:** 2026-07-30
**Context:** `CAP-063 AI Memory` has never been implemented (❌ in `CANONICAL_ARCHITECTURE.md`); this is the first real implementation, and it is also the newest possible surface for a cross-tenant data leak.
**Alternatives considered:** (a) Build full cross-session long-term memory at GA; (b) conversation-level only, prove isolation, expand later.
**Decision:** (b). Ship the smallest version that can be adversarially isolation-tested before committing to the larger surface area of persistent, cross-session memory.
**Consequence:** `PROGRAM_PLAN.md` EPIC-12 explicitly flags cross-session memory as deferred, not silently dropped; it is named in the Sprint 26 GA-day backlog review.
**Status:** Accepted.

---

### DEC-008 — Security P0 remediation and tenant isolation hardening are a non-skippable, zero-partial-credit Phase 0

**Date:** 2026-07-30
**Context:** Three documented P0s (cross-tenant IDOR, webhook SSRF, CSRF bypass) exist in the current codebase; every subsequent phase adds new tenant-scoped tables that would inherit the same risk class if isolation isn't proven first.
**Alternatives considered:** (a) Fix P0s in parallel with early commercial-layer work to save calendar time; (b) treat as a strict, blocking prerequisite phase.
**Decision:** (b). `IMPLEMENTATION_SEQUENCE.md` positions 1-2 are the root of the critical path; Phase 1 does not start until Phase 0's RLS/security exit criteria are met with no partial credit.
**Consequence:** This sets the floor on the overall program timeline — compressing Phase 0 compresses nothing (it's on the critical path), while adding resources to a non-critical-path item does not shorten the program at all.
**Status:** Accepted.

---

### DEC-009 — Marketplace is first-party-only through GA; third-party submission is explicitly post-GA

**Date:** 2026-07-30
**Context:** A certification pipeline (`CAP-094`) needs to be proven against real listings before it can safely be opened to external submitters; opening it prematurely risks a low-quality or unsafe listing reaching a real tenant before the pipeline is trustworthy.
**Alternatives considered:** (a) Open third-party submissions at GA to accelerate ecosystem growth; (b) first-party only at GA, third-party post-GA once the pipeline has a track record.
**Decision:** (b).
**Consequence:** `COMMERCIAL_LAUNCH_PLAN.md`'s marketplace revenue-share model (20% platform share) is defined now, in advance of enforcement, so the number exists before any partner conversation needs it — but is not enforced in code until post-GA.
**Status:** Accepted.

---

### DEC-010 — Sprint cadence: 26 sprints (52 weeks), not compressed to match the initially-proposed `Sprint-00`…`Sprint-20` folder listing

**Date:** 2026-07-30 (this session)
**Context:** The requested `docs/program/` directory structure listed `SPRINT_PLAN/Sprint-00.md` through `Sprint-20.md` (21 sprints, 0-indexed), which conflicted with the already-completed 26-sprint (Sprint 1-26, 52-week) `ENGINEERING_ROADMAP.md`.
**Alternatives considered:** (a) Compress the program to literally fit 21 sprints (00-20), requiring either longer individual sprints or cut/merged phase scope; (b) treat Sprint-00 as a distinct non-delivery "prep" sprint ahead of 20 delivery sprints (compressing the current 26 delivery sprints to 20); (c) keep the 26-sprint plan as-is and number the files Sprint-01 through Sprint-26, treating the original listing as illustrative rather than a hard cap.
**Decision:** (c) — explicit user choice when asked.
**Consequence:** `SPRINT_PLAN/` contains `Sprint-01.md` through `Sprint-26.md`; no phase boundaries, effort estimates, or the 52-week timeline in any other document needed to change.
**Status:** Accepted.

---

### DEC-011 — Program documentation lives under `docs/program/`, reorganized from its original `salesos/` location

**Date:** 2026-07-30 (this session)
**Context:** The 10 program documents were originally written to `salesos/` (matching where `CANONICAL_ARCHITECTURE.md` and `SAAS_PLATFORM_ARCHITECTURE.md` already lived). The user specified a `docs/program/` structure instead, with `PRODUCT_RELEASE_PLAN.md` renamed to `RELEASE_PLAN.md` and three new files split out (`RISK_REGISTER.md`, `DECISION_LOG.md`, `MILESTONES.md`).
**Alternatives considered:** Leave the documents in `salesos/` and only add the three new files; duplicate content across both locations.
**Decision:** Move (not duplicate) all 10 files to `docs/program/`, rename `PRODUCT_RELEASE_PLAN.md` → `RELEASE_PLAN.md`, split `ENGINEERING_ROADMAP.md`'s per-sprint content into `SPRINT_PLAN/`, and extract the risk and milestone tables into their own canonical files (with the originating documents left pointing at them, not duplicating them going forward).
**Consequence:** `salesos/` now contains only the architecture documents (`CANONICAL_ARCHITECTURE.md`, `SAAS_PLATFORM_ARCHITECTURE.md`) and the Odoo ARB trilogy; all execution/program documents live under `docs/program/`.
**Status:** Accepted.

---

### DEC-012 — Pricing bands in `COMMERCIAL_LAUNCH_PLAN.md` are a first-draft planning assumption, not a market-validated decision

**Date:** 2026-07-30
**Context:** Starter/Growth/Enterprise price points ($499/$1,999/custom) were needed to make the Commercial Launch Plan concrete rather than full of placeholders, per the instruction that "no placeholders" was acceptable in the deliverable.
**Alternatives considered:** Leave pricing as "TBD"; run a formal pricing study before committing numbers to a document.
**Decision:** Publish concrete numbers now, explicitly flagged as a first draft for the team to pressure-test, rather than leaving the document full of unresolved placeholders.
**Consequence:** Sales enablement (`ENGINEERING_ROADMAP.md` Sprint 26) must not proceed on these exact numbers without an explicit pricing review — this decision does not constitute that review.
**Status:** Proposed (not yet validated against market data).

---

### DEC-013 — R-14 blocks Sprint 03's RLS rollout; remediation plan accepted, execution not yet authorized

**Date:** 2026-07-31
**Context:** STORY-02-01's hand-test (Sprint 02) discovered that the application's database role (`salesos`) is a Postgres superuser with BYPASSRLS, meaning RLS policies — however correctly written — provide zero actual protection. A dedicated R-14 Production Security Validation pass then confirmed this is not a local-dev artifact: identical role provisioning (`pgvector/pgvector:pg16` official-image `POSTGRES_USER` bootstrap, no demotion step anywhere) is present in CI, staging, and the self-hosted production template, verified by direct file inspection of each environment's config. The empirical core claim — a correct, `FORCE`-enabled policy with a correctly-set session variable still leaking cross-tenant rows under the `salesos` role — was independently reproduced twice more (once by the validation pass, once again directly by this log's maintainer with a freshly-created probe table), not merely re-read from a prior transcript. Separately, a locally-saved snapshot of the real Railway production `DATABASE_URL` shows the live database connecting as `postgres` — diverging from this project's own `salesos`-based templates — a discrepancy that remains genuinely unresolved because no one has connected to confirm it, deliberately, per the stated Rules of Engagement (a locally-saved credential file is not standing authorization to use it against production).
**Alternatives considered:** (a) Proceed with Sprint 03's planned "RLS rollout, complete" across all 72 tables regardless, treating the pilot's finding as a Sprint-03-scope fix to make concurrently; (b) block Sprint 03's RLS work specifically until a non-superuser application role exists and is verified effective, while allowing Sprint 03's other stories (STORY-02-02 middleware.ts, STORY-02-03 JWT audience split, STORY-03-04 contract test framework) to proceed unaffected.
**Decision:** (b). Rolling RLS out to 62 more tables on top of a connection role that unconditionally bypasses it would produce exactly what the validation report calls "a false sense of security — correct-looking policies that silently do nothing," which is worse than not having attempted RLS at all, since it would pass casual review. The remediation plan (new `salesos_app` role — `NOSUPERUSER NOBYPASSRLS NOCREATEROLE NOCREATEDB NOREPLICATION LOGIN`, non-owning; scoped grants plus `ALTER DEFAULT PRIVILEGES` so future migrations are auto-covered; a new `app_database_url` setting used only by the runtime engine, with a safe fallback; `alembic/env.py` left unchanged since migrations must keep running as the owning role) is accepted as the correct shape of fix — additive, not a replacement of the existing `salesos` role, and reversible by unsetting one env var.
**Consequence:** Sprint 03's `docs/program/SPRINT_PLAN/Sprint-03.md` STORY-02-01 ("RLS rollout, complete") does not start until (a) `salesos_app` exists and is granted correctly in the target environment, (b) the application is reconnected through it, and (c) the bypass-probe demonstrated in the validation report is re-run and returns zero cross-tenant rows. This decision **accepts the remediation plan** but does **not** authorize executing it — creating a new role and rewiring connection configuration across environments is an infrastructure change requiring an explicit go-ahead from whoever owns each environment, not something to execute automatically off the back of a risk-register entry. Also unresolved and explicitly not closed by this decision: the `salesos` vs `postgres` role discrepancy between the production templates and the apparent live Railway snapshot — resolving that requires an explicit, separately-authorized live-production check.
**Status:** Superseded by DEC-014 for the local-dev scope (execution authorized and completed same day); Blocking still stands, unchanged, for CI/staging/prod.

---

### DEC-014 — R-14 remediation executed in local dev; CI/staging/prod explicitly deferred

**Date:** 2026-07-31
**Context:** DEC-013 accepted the `salesos_app` remediation plan but explicitly withheld execution authorization pending an owner decision. Asked directly, the decision was: implement now, local dev only.
**Alternatives considered:** (a) Implement across all environments in one pass; (b) local dev only, leaving CI/staging/prod for a separately-authorized follow-up; (c) defer all execution, file the plan only.
**Decision:** (b). Implemented: `infra/docker/postgres/init/02-app-role.sql` (idempotent role + scoped grants + `ALTER DEFAULT PRIVILEGES`), `app/config.py`'s `app_database_url` (fallback-safe), `app/database.py` split into a request-serving `engine` (new role) and a bootstrap-only `owner_engine` (unchanged role) — the split was necessary, not optional: `CREATE SCHEMA IF NOT EXISTS` was verified to still require database-level CREATE privilege even when the schema already exists, so `init_db()`'s bootstrap DDL cannot run under the restricted role. `alembic/env.py` untouched.
**Consequence:** Local dev's `salesos` database now has zero application tables *by default until migrations run* — a separate, pre-existing finding surfaced while executing this decision: the running `salesos-backend-1` container had apparently been serving traffic against an empty schema for its entire 13+ hour uptime (`init_db()`'s automatic migration path silently degrades on failure by design, per its own log message, rather than crashing). Running `alembic upgrade head` manually resolved it (86 tables now present, migration chain intact to head `0052`) — this is disclosed as a distinct, pre-existing operational gap, not something this decision set out to fix, and not evidence of any flaw in the R-14 remediation itself. Post-fix, verified end-to-end: `docker compose up -d --force-recreate` (not `restart`, which does not reload `.env` — a real gotcha hit during this work) picked up the new role; `pg_stat_activity` showed both `salesos` (owner_engine) and `salesos_app` (request engine) connected simultaneously; `/health` and `/ping` returned 200; the full regression suite held at 1,957 passed / 11 pre-existing failures (zero regressions); and the exact bypass-probe from the R-14 validation report, re-run against `salesos_app` instead of `salesos`, now returns only the querying tenant's row — the identical policy that leaked both tenants under `salesos` correctly isolates under `salesos_app`. CI, staging, and the self-hosted prod template are **explicitly, deliberately not touched** by this decision — `app_database_url`'s fallback means none of them are broken by this change (they simply haven't received the fix yet), and provisioning `salesos_app` plus setting `APP_POSTGRES_PASSWORD` in each is separately-scoped follow-up work, not silently assumed done. The live Railway `salesos`-vs-`postgres` discrepancy remains completely unresolved and untouched, per DEC-013's original Rules of Engagement.
**Status:** Accepted and executed (local dev only). CI/staging/prod rollout and the Railway discrepancy remain open, tracked in R-14's Owner column.

---

### DEC-015 — R-14 rolled out to CI, staging, and the production template; Railway explicitly deferred, not guessed at

**Date:** 2026-07-31
**Context:** DEC-014 left CI, staging, and the self-hosted production template unremediated. Assigned as a follow-on "R-14 Enterprise Closure" task across every remaining environment, with an explicit rule: do not close R-14 unless every production-relevant environment is either validated or explicitly authorized-and-verified, and do not guess at Railway without authorization.
**Alternatives considered:** (a) Treat CI/staging/prod-template as low-risk-enough to skip and go straight to asking about Railway; (b) roll out and independently verify CI/staging/prod-template first (each is fully under this repo's own control, no live-system risk), then ask specifically about Railway once it was the only remaining gap; (c) edit `railway.json` speculatively to auto-provision on the next real deploy without connecting live.
**Decision:** (b) for CI/staging/prod-template. Found, while reviewing: all three already mount `infra/docker/postgres/init` as `docker-entrypoint-initdb.d` in their respective compose files (`docker-compose.prod.yml`, `infra/staging/docker-compose.staging.yml`, `infra/staging/docker-compose.staging-virtual.yml`) — meaning `02-app-role.sql` auto-provisions on any fresh volume already; the actual gap was just `APP_POSTGRES_USER`/`APP_POSTGRES_PASSWORD` missing from each environment's env file/template, plus CI's `test-backend`/`integration-backend` jobs using GitHub Actions' ephemeral (non-compose) `services:` Postgres, which needed an explicit provisioning step instead of a mount. While wiring the CI step, found and fixed a real portability bug: the script hardcoded `GRANT CONNECT ON DATABASE salesos`, which only worked by coincidence where a database literally named `salesos` existed on the same server — it failed outright against CI's `salesos_test`-only instance (`database "salesos" does not exist`). Fixed to grant on `current_database()` dynamically. Each environment was independently verified via local simulation (a throwaway container matching CI's exact image/env; `docker-compose.staging-virtual.yml`'s postgres service on a fresh volume; `docker-compose.prod.yml`'s postgres service on a fresh volume under an isolated compose project name) — same bypass-probe as DEC-014, same result: owner role leaks both tenants, `salesos_app` isolates. For Railway: (c) was explicitly rejected — asked directly, mid-task, whether to (i) leave it fully untouched, (ii) authorize a live connection, or (iii) edit `railway.json` blind; the answer was (i), leave it fully untouched. No `railway.json` edit, no live connection, no credential use.
**Consequence:** R-14 moves from "closed for local dev only" to **partially closed** — local dev, CI, staging, and the production template are all remediated and independently verified; Railway is the sole remaining open environment, by explicit choice rather than oversight. A runbook for what Railway would require (manual `psql` provisioning as part of its deploy process, since it has no init-script mount; `APP_POSTGRES_PASSWORD` set via Railway's own secrets mechanism) is documented in `OPERATIONS_MANUAL.md` §14, unexecuted. One incidental operational hazard surfaced and was corrected during this work: `docker-compose.prod.yml` has no explicit Compose project name, so running it from the same directory as the primary dev stack (also unnamed) collides with the running dev containers under the same implicit project name — running it once briefly recreated the live dev `postgres` container against `.env.production`'s values before this was caught and reverted (same data volume throughout; no data lost; confirmed via live `/health/detailed` showing `database: connected` after restoration). Subsequent verification used an explicit isolated `-p` project name to avoid recurrence; this hazard is not yet fixed at the file level (still no `name:` in `docker-compose.prod.yml`) and is called out as a follow-up risk, not silently fixed in passing, since adding one is an infrastructure-shape change outside this decision's scope.
**Status:** Accepted and executed (CI, staging, production template). Railway remains open, deferred pending explicit authorization — tracked in R-14's Owner column.

---

### DEC-020 — Analytics schema drift discovered during Sprint 05 adversarial RLS verification; schema is authoritative; reconciliation scheduled as standalone Story CI-15

**Date:** 2026-07-31
**Context:** During S04-01 (adversarial RLS suite, `salesos/backend/tests/integration/test_adversarial_rls.py`) execution, after two proven root causes were fixed (`:id::uuid` SQLAlchemy `text()` bind bug in `_create_tenants`; cross-event-loop asyncpg pool reuse under pytest-asyncio 1.4.0 function-scoped loops, fixed with a file-local engine-dispose fixture per the executive's Evidence→Fix gate), the suite reached 6/7 with `test_analytics_reports_isolation` still failing: `UndefinedColumnError: column "metrics" of relation "analytics_reports" does not exist`. Investigation proved a three-way source-of-truth drift: migration `app/alembic/versions/0014_analytics.py` creates `analytics_reports` with 9 columns; ORM `domains/analytics/infrastructure/models.py` (`ReportModel`) defines 14 columns (adds `metrics`, `dimensions`, `filters`, `visualization_type`, `created_by`); live `salesos` DB (verified via `information_schema.columns`) has exactly the 9 migrated columns. No migration ever added the 5 ORM columns.
**Alternatives considered:** (A) reconcile ORM↔DB via a dedicated Alembic migration — **approved**; (B) remove the 5 columns from `ReportModel` to match the DB — rejected (hides drift, loses the architecture truth); (C) adapt the test to the 9-column DB — rejected (tests a wrong system instead of fixing it; violates the Sprint 01+ evidence-first method).
**Decision:** Schema is authoritative. ORM and database must be reconciled through an Alembic migration. No test adaptation approved. No ORM rollback approved. Migration scheduled as a standalone Story **CI-15 — Analytics Schema Reconciliation** (explicitly NOT executed inside S04-01). S04-01 is **BLOCKED** until CI-15 completes; it then re-runs to 7/7.
**Consequence:** Program progress stays 2/19 stories complete (CI-01, CI-11). S04-01 blocked on CI-15, tracked as **R-19** (HIGH, Open, Backend owner). The 6/7 fixed test state is preserved in the working tree (uncommitted) and will be committed only once CI-15 lands and 7/7 is reached.
**Status:** Accepted.

### DEC-021 — CI-15 Phase 1 executed and closed under revised acceptance criteria; systemic drift promoted to Program Initiative (R-20, DB-05)

**Date:** 2026-07-31
**Context:** DEC-020 approved CI-15 as a standalone story (analytics-only schema reconciliation) but its original ACs ("ORM=DB 100%", "Autogenerate clean", "No drift after") proved unachievable once evidence showed **systemic ORM↔DB drift** beyond analytics (`alembic check` against head `0afbf3e6ae53`: `emails`/`meetings` id/tenant UUID vs String(36); `dead_letter_queue.id` INTEGER vs UUID; `companies` ORM-removed columns; `ix_rev_*`→`ix_*` index renames; nullable/type deltas across workflow/notifications/scheduled_jobs/feature tables). The executive APPROVED CI-15 Phase 1 with REVISED acceptance criteria: (1) migration adds ONLY the 5 analytics columns; (2) `alembic upgrade head` / `downgrade -1` / `upgrade head` PASS; (3) `analytics_reports` ORM=DB after migration; (4) adversarial suite 7/7 PASS; (5) systemic drift documented and referred to standalone work. Explicitly REFUSED during CI-15: fixes to emails/meetings/companies/dead_letter_queue, index renames, nullable drift, anything else from `alembic check`. `alembic check` is evidence-only (prove analytics drift gone, other drift remains and is registered), NOT a success criterion.
**Alternatives considered:** Executing CI-15 under the original (now disproven) ACs — rejected as factually impossible; expanding CI-15 into a full schema reconciliation program — rejected on scope-discipline grounds.
**Decision:** Executed CI-15 Phase 1: new migration `07e3ec4084fc_analytics_schema_reconciliation` (down_revision `0afbf3e6ae53`) adding `metrics` (JSON NOT NULL `[]`), `dimensions` (JSON NOT NULL `[]`), `filters` (JSON NOT NULL `{}`), `visualization_type` (String(50) NOT NULL `table`), `created_by` (String(36) NOT NULL ``) matching `ReportModel`. Validation: upgrade `0afbf3e6ae53→07e3ec4084fc` PASS (14 columns, types/defaults verified via `information_schema`); downgrade `-1` PASS (9 columns, rev `0afbf3e6ae53`); re-upgrade PASS (14 columns, rev `07e3ec4084fc`); adversarial suite `tests/integration/test_adversarial_rls.py` **7/7 PASS** (was 6/7); `alembic check` after migration: **0** `analytics_reports` drift lines while **300** drift lines remain elsewhere (35 table-level + 16 column/modify deltas + index/constraint renames) — analytics drift gone, systemic drift persists and is now governed. New risk **R-20** (Systemic ORM↔Database Drift, HIGH 4×5=20, Open, Backend Platform, discovered by CI-15, blocks future schema-governance work) registered. New Program Story **DB-05 — Repository Schema Reconciliation Program** registered (P1, multi-sprint; NOT part of CI-15). Governing principle ratified: **Local Story fixes Local Drift. Systemic Drift becomes a Program Initiative.**
**Consequence:** CI-15 COMPLETE; R-19 CLOSED; S04-01 COMPLETE at 7/7 (adversarial suite fully green). Program progress: **4/19** stories complete (CI-01, CI-11, S04-01, CI-15). Records updated: `SPRINT_05_DELIVERY_BOARD.md` (CI-15/S04-01 COMPLETE, DB-05 REGISTERED), `RISK_REGISTER.md` (R-19 Closed, R-20 added), `DECISION_LOG.md` (this entry). Committed locally (no push, per the governed cycle); Phase 2 (controlled push/CI) for CI-15/S04-01 to be scheduled per the story cycle.
**Status:** Accepted. Phase 1 result: **SUCCESS — READY FOR PHASE 2.**

### DEC-022 — CI-15 Phase 2 executed and closed: real CI verification on `4793b08`, no regression; migration-file lint delta disclosed and transferred

**Date:** 2026-07-31
**Context:** Phase 2 was authorized (approval gate) with stop rules: stop immediately on Migration failure, Backend test regression, Alembic failure, New RLS failure, or New Integration regression; no fixes during execution. Commit `4793b08` (CI-15 Phase 1 + S04-01 7/7 + R-20/DB-05 records) pushed to `master`; push triggered all 5 workflows.
**Alternatives considered:** None required — the evidence set dictated the outcome; no decision fork arose during execution.
**Decision:** Phase 2 executed as evidence collection only. Backend validation at the pushed state (local, via Docker): `alembic current`/`heads` both = `07e3ec4084fc` (single head, migration applied); adversarial suite `tests/integration/test_adversarial_rls.py` = **7/7 PASS**. Real CI run `30652813475` (commit `4793b08`): job matrix compared against baseline run `30649799993` (commit `060c946`) — **identical statuses on every job** (Frontend Lint/Types SUCCESS; Backend Lint/Types FAILURE pre-existing; Backend Unit/Integration SKIPPED as baseline; Frontend Unit FAILURE pre-existing 33-suite set; npm audit/pip-audit/Bandit/Secrets FAILURE pre-existing; Arch Compliance SUCCESS; builds/E2E SKIPPED; CI Summary FAILURE as baseline). No stop-rule condition triggered: no migration failure, no alembic failure, no RLS failure, no backend/integration test regression (the affected jobs were skipped at baseline and remained skipped — not a transition). Sole delta: the new migration file `07e3ec4084fc_analytics_schema_reconciliation.py` contributes **10 new Ruff style violations** (UP035, I001, UP007×3, E501×5) to the already-red Backend Lint gate; `test_adversarial_rls.py` refs unchanged at 29 (pre-existing). These 10 violations are style-only, outside CI-15's approved ACs, and per the no-fixes rule they are **not fixed within CI-15** — transferred to the Backend Lint remediation backlog (3,611 pre-existing violations program) / tracked with DB-05.
**Consequence:** CI-15 **CLOSED**; R-19 **CLOSED**; R-20 **OPEN (Program Risk)**; DB-05 → **BACKLOG**; S04-01 **COMPLETE**. Program progress: 4/19 stories complete/closed (CI-01, CI-11, S04-01, CI-15). Board and records updated. The 10 migration-file lint violations are a registered residual, not hidden.
**Status:** Accepted. Phase 2 result: **SUCCESS — CI-15 COMPLETE.**

### DEC-023 — CI-02 Phase 1 approved and executed (toolchain remediation); R-21 + CI-16 registered; principle ratified

**Date:** 2026-07-31
**Context:** CI-02 (pip-audit in CI) was the next highest READY P0 story per the CI triage execution order (#4/#9). Pre-task package established both root causes with current-run evidence: (1) CI workflow `security-pip-audit` never installs Poetry → `poetry: command not found` (run `30652813475`); (2) Security Scan `pip-audit` invokes `-f` without a value → `argument -f/--format: expected one argument` (run `30652813513`). Local prediction (backend container, Poetry 1.8.3 / pip-audit 2.10.1) showed that once tooling is fixed, `poetry export` succeeds (98 deps) and `pip-audit --strict` fails on REAL vulnerabilities.
**Alternatives considered:** Fixing the discovered dependencies inside CI-02 — rejected by the executive; dependency remediation is a separate class of work.
**Decision:** The executive APPROVED CI-02 Phase 1 as **CI Toolchain Remediation** (not dependency remediation), with the ratified principle: **CI Stories fix CI Infrastructure, not application dependencies.** Approved scope: (1) add `pipx install poetry` to `security-pip-audit` mirroring the existing sibling pattern; (2) fix the malformed `-f` invocation in `security-scan.yml`; (3) YAML validation; (4) local verification proving the chain old-failure → `poetry export` succeeds → `pip-audit` runs → findings produced; (5) local commit only. Explicitly refused inside CI-02: poetry.lock/pyproject.toml/dependency changes, python-multipart/strawberry-graphql fixes, severity thresholds, pip-audit policy. Approved creation: **R-21** (Backend Dependency Vulnerabilities, HIGH 4×4=16, Open, Backend, discovered by CI-02, evidence = pip-audit execution after tooling remediation, scope = dependency modernization, blocks CI-16) and standalone Story **CI-16 — Backend Dependency Security Remediation**.
**Consequence:** Phase 1 executed: `.github/workflows/ci.yml` (Install Poetry step added to `security-pip-audit`) and `.github/workflows/security-scan.yml` (removed stray `-f`). YAML parse OK. Local proof chain executed in the container: `poetry export` exit 0, 98 requirement lines; `pip-audit` JSON report produced findings — `ecdsa 0.19.2` (PYSEC-2026-1325), `starlette 0.37.2` (9 advisories), `python-multipart 0.0.9` (7 advisories), `strawberry-graphql 0.243.1` (7 advisories); `--strict` exit 1 on findings (not tooling); security-scan command no longer argument-parse errors. R-21 and CI-16 registered in RISK_REGISTER / SPRINT_05_DELIVERY_BOARD. Committed locally (no push); Phase 2 (controlled push/CI) pending executive approval.
**Status:** Accepted. Phase 1 result: **SUCCESS — READY FOR PHASE 2.**

### DEC-024 — CI-02 Corrective Phase 1A: Poetry 2.x `export`-plugin gap on the GitHub runner (environment drift); `poetry-plugin-export` added

**Date:** 2026-07-31
**Context:** CI-02 Phase 2 real-run (`30655019114`, commit `b330d52`) eliminated `poetry: command not found` but surfaced a NEW toolchain failure: `The requested command export does not exist.` Diagnosis: the GitHub runner's `pipx install poetry` installs latest **Poetry 2.x**, where `export` is no longer a built-in command — it requires the separate `poetry-plugin-export` plugin (Poetry's official forward-compatible direction). Local Phase 1 validation used the backend container's **Poetry 1.8.3** (export built-in), so it passed locally — an **environment drift** (local 1.8.3 vs runner 2.x) that only the real run could expose. Confirmed locally: `poetry-plugin-export` 1.10.0 requires Poetry ≥2.1.0, so `poetry self add poetry-plugin-export` fails on 1.8.3 (validating the drift) and resolves on the runner's 2.x.
**Alternatives considered:** (a) pin `pipx install poetry@1.8.3` to match the container — rejected by the executive (binds CI to an old version, against Poetry 2's official direction); (b) the official plugin install (`poetry self add poetry-plugin-export`) — **approved**.
**Decision:** Corrective Phase 1A approved as an extension of CI-02 (same goal: remove toolchain failure entirely before reaching vulnerability findings — NOT a new story). `security-pip-audit`'s Install Poetry step becomes: `pipx install poetry` then `poetry self add poetry-plugin-export`. Scope check: toolchain only — no dependencies, no lockfile, no application code, no threshold/policy changes. New acceptance criterion added: **Poetry 2.x installation includes poetry-plugin-export.** Commit locally; no push until review.
**Consequence:** `.github/workflows/ci.yml` updated (multi-line Install Poetry step). YAML parse OK; local `poetry export` unaffected (1.8.3, 98 lines). The plugin-install correctness for Poetry 2.x is verified on the real runner in the Phase 2 re-run. Committed locally as the CI-02 corrective; Phase 2 re-run pending executive approval.
**Status:** Accepted. Corrective Phase 1A result: **SUCCESS — READY FOR PHASE 2 RE-RUN.**

### DEC-025 — CI-02 Phase 2 re-run executed and closed: full toolchain chain proven on real GitHub Actions; all pip-audit tooling failures eliminated

**Date:** 2026-07-31
**Context:** Phase 2 re-run authorized for commit `a4e880c` (Corrective Phase 1A). Stop rules: STOP/BLOCKED on `poetry: command not found`, `export does not exist`, `poetry self add` failure, plugin-install failure, or YAML failure; SUCCESS if `pip-audit` runs, produces vulnerability findings, and fails on `--strict` with findings.
**Alternatives considered:** None — evidence dictated the outcome; no decision fork arose.
**Decision:** Pushed `a4e880c`; CI run `30655650484` and Security Scan run `30655650490` observed. CI `security-pip-audit` executed the FULL chain on the runner: Poetry 2.x installed via pipx → `poetry self add poetry-plugin-export` succeeded (no `export does not exist`) → `poetry export` succeeded → `pip-audit` ran → **`Found 24 known vulnerabilities in 4 packages`** (ecdsa 0.19.2, starlette 0.37.2, python-multipart 0.0.9, strawberry-graphql 0.243.1) → `--strict` exited 1 on the findings table. Security Scan `pip-audit` = **SUCCESS** (no argument-parse error). No stop-rule condition triggered. Job matrix otherwise identical to baseline (no regression).
**Consequence:** CI-02 **CLOSED** — all pip-audit toolchain failures eliminated; any future pip-audit failure is evidence of real vulnerabilities to be handled in **CI-16 / R-21**, not CI infrastructure. DEC-024 **RATIFIED**; R-21 remains **OPEN**; CI-16 moved to **BACKLOG**. Program progress: **5/19** complete/closed (CI-01, CI-11, S04-01, CI-15, CI-02). Board and records updated; committed locally (no push).
**Status:** Accepted. Phase 2 re-run result: **SUCCESS — CI-02 COMPLETE.**

### DEC-026 — CI-03 Phase 1 approved and executed: `GF_SECURITY_ADMIN_PASSWORD` provided to the Docker Smoke workflow env (workflow-only, no compose weakening)

**Date:** 2026-07-31
**Context:** CI-03 (triage #8) — the Docker Smoke Test workflow's `Validate Compose File` step fails: `docker compose config` against `salesos/docker-compose.yml` errors `required variable GF_SECURITY_ADMIN_PASSWORD is missing a value` (run `30655650514`). The grafana service's `${GF_SECURITY_ADMIN_PASSWORD:?Set GF_SECURITY_ADMIN_PASSWORD}` is a correct guard; the gap is the workflow env, which provides postgres/neo4j/JWT/secret vars but not the Grafana password. Reproduced the exact error locally (host docker compose v5.3.1, `--env-file` mirroring the workflow `.env`): exit 1, same message.
**Alternatives considered:** Removing/weakening the `:?` guard in the compose file — rejected by the executive (the guard is correct; CI must supply the right environment, not relax real config). Approved: add the dev-only smoke value to the workflow env.
**Decision:** Added `GF_SECURITY_ADMIN_PASSWORD: salesos_smoke_test` to `.github/workflows/docker-smoke.yml` workflow-level env (mirroring the existing `salesos_smoke_test` credentials convention). Before/After proof executed: BEFORE = exit 1 with the exact GF interpolation error; AFTER = exit 0, **0** "required variable" lines, **0** "error while interpolating" lines, only the pre-existing optional-variable blank-defaulting warnings (ALERTMANAGER/SLACK/PAGERDUTY, present before the change, non-error). Principle ratified: **لا تُخفف متطلبات ملفات Compose لإرضاء CI؛ بل اجعل CI توفر البيئة الصحيحة التي يتطلبها Compose.**
**Consequence:** `.github/workflows/docker-smoke.yml` updated (workflow only); YAML parse OK. No compose file, no grafana config, no secrets handling, no other service touched. Committed locally (no push); Phase 2 (controlled push/CI) pending executive approval.
**Status:** Accepted. Phase 1 result: **SUCCESS — READY FOR PHASE 2.**

### DEC-030 — CI-18 closed: semgrep SARIF upload fixed — entire Security Scan workflow GREEN for the first time; 253 semgrep findings surfaced as a separate item

**Date:** 2026-07-31
**Context:** Phase 2 authorized for commit `6ab1d0e` (repeatable `--severity ERROR --severity WARNING` replacing invalid comma list `--severity ERROR,WARNING`). Success criteria: semgrep executes, SARIF generated, `Upload semgrep results` PASS, no CLI parse error, no regression.
**Alternatives considered:** Dropping severity filtering (scans all severities) — rejected, changes policy; repeatable flags preserve intent exactly.
**Decision:** Pushed `6ab1d0e`. Evidence — Security Scan run `30660116232`: **all 6 jobs SUCCESS** (secret-scan, sbom, sast-scan, pip-audit, npm-audit, report). `sast-scan` steps all green: `Install semgrep`, `Run semgrep (generic SAST)`, **`Upload semgrep results` SUCCESS**; log scan: **0** `invalid value` / `Path does not exist` / `semgrep scan: option` occurrences. Semgrep actually scanned: **Findings 253 (253 blocking)**, targets scanned 2806, 595 rules — all now visible in GitHub code scanning. The `--error` exit (1 on findings) is masked as designed by `|| true` + `continue-on-error: true`.
**Consequence:** CI-18 **CLOSED** (all ACs met). SAST upload path complete for Bandit + Trivy (fs & IaC) + Semgrep. Security Scan workflow fully green (previously 2 of 6 jobs red). New registered story: **CI-19** (semgrep findings remediation — triage of the 253 blocking findings). Program progress: **9/19**. Board + DECISION_LOG updated; committed locally (no push).
**Status:** Accepted. CI-18 **COMPLETE.**

### DEC-029 — CI-05 closed: Trivy SARIF category collision resolved — both uploads green in `secret-scan`

**Date:** 2026-07-31
**Context:** Phase 2 authorized for the CI-05 Phase 1 commit (actual SHA **`f34bef2`**; the earlier "c0f2199" in the Phase 1 report was inaccurate — corrected in the close records). Change: distinct `category` per `upload-sarif` step in `secret-scan` (`trivy-fs` for fs scan, `trivy-config` for IaC config scan).
**Alternatives considered:** None — GitHub's error message itself prescribes the `category` fix; audit confirmed the Trivy pair in `secret-scan` was the only tool/category collision across all 7 `upload-sarif@v3` occurrences in the repo.
**Decision:** Pushed `f34bef2` (also carried CI-04 close records `949dbf4`). Evidence — Security Scan run `30659372944`, `secret-scan`: Set up, Checkout, forbidden-files check, Gitleaks, Trivy fs scan, **`Upload Trivy results` SUCCESS**, Trivy config scan, **`Upload Trivy config results` SUCCESS** → job conclusion **SUCCESS**. Log scan: **0** occurrences of `Aborting upload` / `only one run` / `tool/category`. IaC SARIF now visible in code scanning (previously silently lost).
**Consequence:** CI-05 **CLOSED** (all Phase 2 ACs met). No regression. Program progress: **8/19**. Remaining security-scan reds are independent items: semgrep upload (CI-18), Trivy fs findings in CI workflow (triage #3). Board + DECISION_LOG updated; committed locally (no push).
**Status:** Accepted. CI-05 **COMPLETE.**

### DEC-028 — CI-04 closed: Bandit SARIF uploads fixed in both workflows; gate now executes and surfaces a pre-existing high finding (B324)

**Date:** 2026-07-31
**Context:** Phase 2 authorized for commit `ce59efd` (install `bandit[sarif]` in `ci.yml` + `security-scan.yml`). Success criteria: `bandit-results.sarif` generated, `Upload bandit results` PASS in both workflows, no Bandit `Path does not exist`; any later failure (e.g., Semgrep) is an independent item, not CI-04.
**Alternatives considered:** Dropping SARIF upload and keeping only the JSON gate (loses code-scanning visibility) — rejected; the approved fix preserves both.
**Decision:** Pushed `ce59efd`. Evidence — CI run `30658782384` `Stage 5: Bandit SAST`: Install SUCCESS, `Run bandit` SUCCESS, **`Upload bandit results` SUCCESS**, then `Run bandit (fail on high)` FAILURE. Security Scan run `30658782394` `sast-scan`: **`Upload bandit results` SUCCESS**; `Upload semgrep results` FAILURE (`Path does not exist: semgrep-results.sarif` — separate root cause).
**Key insight — NOT a regression:** Baseline run `30655650484` shows `Run bandit (fail on high)` = **SKIPPED** (the failing upload set `JOB_STATUS_CONFIGURATION_ERROR`, halting downstream steps). The high-severity JSON gate never executed until now. CI-04 fixing the upload enabled the gate for the first time; it correctly found **1 high/high finding: B324 (hashlib) — weak MD5** in `app/modules/admin/routers/roles_permissions.py:40` (`role_id = f"role_{hashlib.md5(body.name.encode()).hexdigest()[:8]}"`). Reproduced locally (bandit 1.9.4, JSON report, 1 result, HIGH/HIGH).
**Consequence:** CI-04 **CLOSED** (all ACs met). New registered stories: **CI-17** (B324 remediation — add `usedforsecurity=False`), **CI-18** (semgrep SARIF upload). Program progress: **7/19**. Board + DECISION_LOG updated; committed locally (no push). The Stage 5 job will remain red until CI-17 lands — correct gate behavior, not CI debt.
**Status:** Accepted. CI-04 **COMPLETE.**

### DEC-027 — CI-03 Phase 2 executed and closed: Docker Smoke Test fully green on real GitHub Actions (entire job, not just the gate)

**Date:** 2026-07-31
**Context:** Phase 2 authorized for commit `83e703e` (Docker Smoke workflow env now provides `GF_SECURITY_ADMIN_PASSWORD`). Stop rules: STOP on `Validate Compose File` failure (interpolation/missing var/compose syntax/workflow parsing); any failure AFTER the validation gate is NOT CI-03 (new independent item, not to be fixed here).
**Alternatives considered:** None — evidence dictated the outcome.
**Decision:** Pushed `83e703e`; Docker Smoke Test run `30656335600` observed. Step results: Set up job SUCCESS, Checkout SUCCESS, Setup .env SUCCESS, **Validate Compose File SUCCESS (1s)** — no `required variable GF_SECURITY_ADMIN_PASSWORD is missing` message, no interpolation errors; then Build Services SUCCESS (111s), Start Services SUCCESS (79s), Run Smoke Tests SUCCESS (30s), Stop Services SUCCESS. **The entire Docker E2E Smoke Test job concluded SUCCESS** — no downstream failure to classify; the previously all-red workflow is now fully green.
**Consequence:** CI-03 **CLOSED**; DEC-026 **RATIFIED**; Docker Smoke interpolation issue **eliminated**. Program progress: **6/19** complete/closed (CI-01, CI-11, S04-01, CI-15, CI-02, CI-03). Board and records updated; committed locally (no push). The smoke job is now a genuine regression guard for the docker stack.
**Status:** Accepted. Phase 2 result: **SUCCESS — CI-03 COMPLETE.**

### DEC-019 — CI-11 closed: patch-only dependency remediation verified on real GitHub Actions; zero regressions

**Date:** 2026-07-31
**Context:** CI-11 Phase 2 (regression verification) executed on the real CI run `30649799993` for commit `060c946` (push to `master`). All four target jobs compared against the pre-CI-11 baseline: Frontend Lint PASS (unchanged), Frontend Types PASS (unchanged), Frontend Unit Tests exactly the pre-existing 33-suite/163-test failure set (byte-identical, zero new failures), npm audit FAIL with 30 high (down from 31 — reduced, and the residual is the CI-14-transferred class). No `package.json` change; only `package-lock.json` in the commit.
**Alternatives considered:** None — the outcome matched the approved success criteria exactly; no decision fork arose.
**Decision:** CI-11 is COMPLETE. Patch-only remediation is proven safe on real GitHub Actions. Residual advisories remain formally transferred to CI-14 (DEC-018). Sprint 05 continues with the next highest READY story in the Entry Package.
**Consequence:** The `npm audit` CI job stays red (30 residual, tracked to R-18/CI-14) until Frontend Dependency Modernization lands — a known, governed state, not a CI-11 defect. Program progress: 2/19 stories complete (CI-01, CI-11).
**Status:** Accepted.

### DEC-018 — CI-11 Phase 1 complete (patch-only); residual advisories require Majors → new Program Story CI-14; CI-11 AC revised

**Date:** 2026-07-31
**Context:** CI-11 (npm audit remediation) Phase 1 executed within the approved patch/minor-only scope: `npm audit fix` (no `--force`) applied 9 patch-level changes (next 15.5.20→15.5.22, postcss 8.5.17→8.5.25, ts-jest 29.4.11→29.4.12, brace-expansion 1.1.16→1.1.18 and 5.0.7→5.0.9, and next-aligned subpackages), reducing `npm audit` from 31 to 30 high with zero new test failures (Jest identical to the pre-existing 33-suite baseline), TypeScript and Lint passing. The 30 residual advisories split into two clusters, both requiring **Major/breaking** changes per npm's own analysis: (a) the `brace-expansion`/`minimatch` DoS chain through the ESLint+Jest dev toolchain (eslint→10.8.0, jest→25.0.0, ts-jest→27.0.3, eslint-config-next→0.2.4), dev-only exposure; (b) `sharp <0.35.0` libvips CVEs inherited by next's image pipeline, whose fix npm frames as next→14.2.35 (downgrade across major lines). Executive ruled out both a permanent allowlist (Option 1) and authorizing Majors now (Option 3).
**Alternatives considered:** (1) permanent accepted-risk allowlist — rejected (should never be the standing resolution for a red CI security gate); (2) extract Major remediation into an independent program story, close CI-11 against revised reality-based criteria; (3) authorize Major upgrades now — rejected (architecture-level change).
**Decision:** (2). CI-11 Phase 1 is COMPLETE (patch remediation SUCCESS; no `--force`; no Major applied; no regression). CI-11 acceptance criteria are REVISED to the following five points (superseding "`npm audit` clean OR allowlist"): (1) patch-level remediations applied where safely available; (2) no new regressions introduced; (3) residual advisories classified and documented; (4) Major-version remediation extracted into a separate program story; (5) CI verification confirms no regression from the applied patch updates (Phase 2). New story **CI-14 — Frontend Dependency Modernization** registered: Upgrade ESLint ecosystem; Upgrade Jest ecosystem; Resolve sharp/libvips chain; Validate Next.js compatibility; Update CI security gates. Independent story — not an extension of CI-11. Phase 2 of CI-11 is authorized **only** for regression verification (patch fixes introduce no CI regression), explicitly **not** for making `npm audit` green.
**Consequence:** CI-14 is a standalone story assigned to Sprint 06 (P1, Frontend Lead), with CI-13 (Jest suite baseline) as a dependency for the Jest-major leg; it may be pulled into Sprint 05 only by explicit planning decision. CI-11 closes only after Phase 2 regression verification passes. The `npm audit` CI job remains red until CI-14 lands — a known, tracked state.
**Status:** Accepted.

### DEC-017 — CI-01 closed: Deploy Production branch-guard defect resolved; failure point moved from gate to infrastructure layer

**Date:** 2026-07-31
**Context:** The Sprint 05 Entry Package's CI-01 (triage #12, CRITICAL) targeted `deploy.yml`'s pre-deploy branch guard, which hardcoded `refs/heads/main` and therefore failed unconditionally on this repo's `master` — making Deploy Production non-functional at the gate, independent of every other pipeline defect. Phase 1 (implementation-only) replaced the literal with `refs/heads/master` and updated the error message; validated YAML; committed locally as `61e08d4` (not pushed, per the stop rule). Phase 2 (controlled, separately approved) pushed `61e08d4` to `master` and observed the real run `30648063788`.
**Alternatives considered:** (a) Implement a genuine Checks-API CI-status verification now (the step is misleadingly named "Verify CI passed on this commit"); (b) minimal branch-literal fix now, deeper gate later.
**Decision:** (b). The Checks-API implementation is explicitly a separate, deeper fix per the triage itself, and would block deploys until CI-02…CI-13 make CI green — sequencing it now would be speculative. Result: `pre-deploy-check` PASSED on real GitHub Actions (7s, job `91214319548`). The downstream Deploy Blue Slot job started (SSH stage) and failed within 1s — classified as infrastructure configuration (missing SSH/VPS host secrets, triage #13), not a regression and not the branch guard. Per the executive stop-condition, monitoring stopped the moment the deploy-stage job started; the run was not awaited to completion.
**Consequence:** Deploy Production now passes its gate; the pipeline's failure point has moved from the branch guard to the infrastructure layer. The branch-guard risk is closed (R-16); the SSH/VPS infrastructure gap remains open (R-17), tracked as CI-09/CI-08. The misleading step name remains a documented backlog item.
**Status:** Accepted.

### D-S4-002 — Sprint 04 continues in parallel with CI-remediation stories; CI is not currently a working merge gate

**Date:** 2026-07-31
**Context:** Commit `354e13c` triggered the program's first-ever real GitHub Actions execution on `master`. All 5 workflows (CI, Docker Smoke Test, Security Scan, Deploy Production, Deploy Staging) failed — 17 failed jobs total, independently triaged with direct evidence from the actual run logs (`gh run view --log-failed`), not assumed or guessed. Full triage: `salesos/docs/audit/ga-engineering-audit/SPRINT_04_CI_TRIAGE.md`. None of the 17 failures originate in Sprint 04 feature code — STORY-04-01/04-02/02-03 are not yet implemented; every failure is pre-existing CI/pipeline configuration or tooling debt (a hardcoded `main`-vs-`master` branch check that makes Deploy Production unconditionally non-functional; missing Poetry installs; an unsupported Bandit SARIF format; a Trivy SARIF category collision; a missing Grafana env var blocking the Docker smoke test; GHCR 403s blocking all staging image pushes; 3,611 pre-existing Ruff violations never previously enforced; 31 real high-severity npm vulnerabilities; and the already-documented Sprint 01 Jest gap, 33/194 suites, unchanged).
**Alternatives considered:** (a) Halt all Sprint 04 feature work until CI is fully green; (b) proceed with Sprint 04's feature stories in parallel, opening dedicated CI-remediation stories rather than folding pipeline fixes into feature work; (c) ignore the CI failures as noise and continue without tracking them.
**Decision:** (b). Most of the 17 failures are small, isolated, low-risk configuration corrections (workflow YAML, env vars, tool flags — no application code) that do not require Sprint 04's actual feature work to pause; none of Sprint 04's planned local-dev/test work depends on Deploy Production or Deploy Staging succeeding. The two largest items (Ruff's 3,611 violations, the Jest suite's 33 failing suites) are real, substantial, already-scoped bodies of work that deserve their own stories rather than being rushed. (c) is rejected outright — a completely red pipeline provides zero regression protection for Sprint 04's new work, which is a real risk to accept knowingly, not silently.
**Consequence:** Sprint 04's STORY-04-01/04-02/02-03 proceed as planned. New CI-remediation stories are opened per the triage's Execution Order, starting with the Deploy Production branch-name fix (2-minute fix, currently blocks 100% of production deploys, highest priority regardless of anything else). Until the quick-fix batch (items 1–9 in the triage) lands, CI cannot be relied on to distinguish a real regression in Sprint 04's new code from pre-existing noise — reviewers should manually check which job failed and cross-reference the triage before treating any red CI run on a Sprint 04 PR as a genuine regression.
**Status:** Accepted.
