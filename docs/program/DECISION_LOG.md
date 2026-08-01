# Decision Log ΓÇö SaaS Platform Program

> **Scope note:** This log is scoped to the commercial-SaaS-platform program (`docs/program/`) ΓÇö the architecture and execution decisions made in designing and sequencing the Owner Platform / Tenant Workspace / Integration Hub / GTM Studio work. It is distinct from the repo-root `docs/DECISION_LOG.md`, which predates this program and covers earlier product decisions; this file does not supersede that one.
> **Format:** ADR-lite. Each entry: Decision, Date, Context, Alternatives Considered, Consequence, Status.
> **Rule:** Decisions are never edited in place once `Accepted` ΓÇö a changed decision gets a new entry that marks the old one `Superseded by DEC-0XX`.

---

### DEC-001 ΓÇö Reframe SalesOS as a two-plane commercial SaaS platform (Owner Platform / Tenant Workspace)

**Date:** 2026-07-30
**Context:** SalesOS's existing architecture (`CANONICAL_ARCHITECTURE.md`) was validated against a single production tenant (Muhide) and describes row-level multi-tenancy but no commercial platform layer ΓÇö no billing, no self-service provisioning, no marketplace, no cross-tenant governance surface.
**Alternatives considered:** (a) Keep the single-tenant architecture and bolt on billing/provisioning as an afterthought layered directly into existing domains; (b) build a fully separate codebase for the "commercial" side.
**Decision:** Split into two planes sharing one codebase and one database engine but never sharing data or an admin surface: Side A (`DOM-020 Platform Operations`, Owner-only) and Side B (`DOM-001ΓÇô019`, unchanged, now called "Tenant Workspace").
**Consequence:** Every existing DOM/CAP/OBJ ID is preserved unchanged; five new domains (`DOM-020`ΓÇô`024`) are added rather than existing ones being restructured. See `SAAS_PLATFORM_ARCHITECTURE.md` ┬º0.
**Status:** Accepted.

---

### DEC-002 ΓÇö Generalize the Integration Hub now, reversing the ARB meta-review's "over-engineering" verdict

**Date:** 2026-07-30
**Context:** `ARB_REVIEW_ODOO_INTEGRATION.md` proposed a generic multi-vendor Connector Framework; `ARB_META_REVIEW.md` downgraded that to "over-engineering for a five-person team building one connector for one tenant" and recommended deferring it until a second connector was actually scoped.
**Alternatives considered:** (a) Build Odoo bespoke now, generalize only when/if a second connector is funded (the meta-review's original recommendation); (b) generalize now.
**Decision:** Build the generic `SourceConnector` framework (EPIC-08) before any Odoo-specific code, because the condition the meta-review said would flip its verdict ΓÇö "revisit when a second connector is actually funded/scoped" ΓÇö is now true by definition (this program's explicit mandate is "hundreds of customers, many ERPs").
**Consequence:** EPIC-08 (framework) is sequenced strictly before EPIC-09 (Odoo adapter); a second connector's certification (EPIC-11, STORY-11-10) is a hard Phase 4 exit gate, not a nice-to-have, directly closing risk R-02.
**Status:** Accepted. Supersedes the deferral recommendation in `ARB_META_REVIEW.md` ┬º4 (that recommendation was correct for its stated scope; the scope has since changed).

---

### DEC-003 ΓÇö Rename `OBJ-303 Invoice` ΓåÆ `PlatformBillingInvoice` is now mandatory, not merely recommended

**Date:** 2026-07-30
**Context:** The original Odoo ARB called this rename "mandatory"; the meta-review downgraded it to "Recommended," citing an existing unremarked precedent (`OBJ-006`/`OBJ-302` both named `License` across two domains).
**Alternatives considered:** (a) Leave `Invoice` ambiguous, matching the `License`/`License` precedent; (b) rename now.
**Decision:** Rename now. The precedent argument weakens materially at platform scale: `Invoice` will soon also mean "an Owner-Platform billing record queried across every tenant" ΓÇö a categorically higher-traffic, higher-consequence ambiguity than the `License` precedent.
**Consequence:** A migration/aliasing period is required (explicitly not omitted this time, per the meta-review's own criticism of the original ARB for missing this) ΓÇö tracked as part of EPIC-05/07 billing work.
**Status:** Accepted.

---

### DEC-004 ΓÇö Entitlements are a layer over feature flags, never a replacement for them

**Date:** 2026-07-30
**Context:** SalesOS's existing feature-flag system is Grade A maturity (per-tenant override, gradual rollout) ΓÇö the only Grade A infrastructure dimension in the platform.
**Alternatives considered:** (a) Build entitlements as a single unified mechanism replacing flags; (b) two independent layers.
**Decision:** Two independent layers: `Plan.entitlements` gates whole DOM/CAP visibility (commercial packaging); feature flags gate rollout within an entitled capability (technical canary/kill-switch). Never conflated.
**Consequence:** EPIC-06 (Entitlement Engine) is additive to, not a rewrite of, the existing flag infrastructure.
**Status:** Accepted.

---

### DEC-005 ΓÇö Pooled multi-tenant Postgres (RLS-isolated) is the default deployment tier through GA; siloed tenancy is deferred

**Date:** 2026-07-30
**Context:** Target GA scale is "dozens of tenants," not thousands; building a dedicated-tenant infrastructure tier speculatively, before any customer requires it, is the same premature-generalization pattern the Odoo ARB debate already flagged once (DEC-002).
**Alternatives considered:** (a) Build the siloed tier now, in parallel; (b) defer until an actual signed Enterprise deal requires it.
**Decision:** Defer (b). Isolation tier is a provisioning decision (`Tenant.data_residency`/`provisioning_status`), not an architecture fork ΓÇö the codebase supports it structurally, but the siloed tier itself is not built pre-GA.
**Consequence:** Named explicitly as `MASTER_EXECUTION_PLAN.md` assumption A6 and tracked in `IMPLEMENTATION_SEQUENCE.md` ┬º4 Blocked Work ΓÇö if a real deal forces it earlier, this is a tracked pull-forward decision, not silent scope creep.
**Status:** Accepted.

---

### DEC-006 ΓÇö Stripe as the billing provider

**Date:** 2026-07-30
**Context:** No in-house payment processing is being considered; a third-party PCI-scope-minimizing provider is required.
**Alternatives considered:** Build custom billing logic against a lower-level payment processor; evaluate multiple providers formally.
**Decision:** Stripe, assumed as the default provider absent a stated reason to prefer another (`MASTER_EXECUTION_PLAN.md` A3).
**Consequence:** EPIC-05 is scoped specifically around Stripe's webhook/checkout/proration model. If a different provider is chosen later, EPIC-05's *tasks* re-scope; the epic's existence and sequencing position do not change.
**Status:** Accepted (provisional ΓÇö flagged as an assumption, not a vendor-evaluation outcome).

---

### DEC-007 ΓÇö AI Memory is scoped to conversation-level only through GA; cross-session long-term memory is deferred

**Date:** 2026-07-30
**Context:** `CAP-063 AI Memory` has never been implemented (Γ¥î in `CANONICAL_ARCHITECTURE.md`); this is the first real implementation, and it is also the newest possible surface for a cross-tenant data leak.
**Alternatives considered:** (a) Build full cross-session long-term memory at GA; (b) conversation-level only, prove isolation, expand later.
**Decision:** (b). Ship the smallest version that can be adversarially isolation-tested before committing to the larger surface area of persistent, cross-session memory.
**Consequence:** `PROGRAM_PLAN.md` EPIC-12 explicitly flags cross-session memory as deferred, not silently dropped; it is named in the Sprint 26 GA-day backlog review.
**Status:** Accepted.

---

### DEC-008 ΓÇö Security P0 remediation and tenant isolation hardening are a non-skippable, zero-partial-credit Phase 0

**Date:** 2026-07-30
**Context:** Three documented P0s (cross-tenant IDOR, webhook SSRF, CSRF bypass) exist in the current codebase; every subsequent phase adds new tenant-scoped tables that would inherit the same risk class if isolation isn't proven first.
**Alternatives considered:** (a) Fix P0s in parallel with early commercial-layer work to save calendar time; (b) treat as a strict, blocking prerequisite phase.
**Decision:** (b). `IMPLEMENTATION_SEQUENCE.md` positions 1-2 are the root of the critical path; Phase 1 does not start until Phase 0's RLS/security exit criteria are met with no partial credit.
**Consequence:** This sets the floor on the overall program timeline ΓÇö compressing Phase 0 compresses nothing (it's on the critical path), while adding resources to a non-critical-path item does not shorten the program at all.
**Status:** Accepted.

---

### DEC-009 ΓÇö Marketplace is first-party-only through GA; third-party submission is explicitly post-GA

**Date:** 2026-07-30
**Context:** A certification pipeline (`CAP-094`) needs to be proven against real listings before it can safely be opened to external submitters; opening it prematurely risks a low-quality or unsafe listing reaching a real tenant before the pipeline is trustworthy.
**Alternatives considered:** (a) Open third-party submissions at GA to accelerate ecosystem growth; (b) first-party only at GA, third-party post-GA once the pipeline has a track record.
**Decision:** (b).
**Consequence:** `COMMERCIAL_LAUNCH_PLAN.md`'s marketplace revenue-share model (20% platform share) is defined now, in advance of enforcement, so the number exists before any partner conversation needs it ΓÇö but is not enforced in code until post-GA.
**Status:** Accepted.

---

### DEC-010 ΓÇö Sprint cadence: 26 sprints (52 weeks), not compressed to match the initially-proposed `Sprint-00`ΓÇª`Sprint-20` folder listing

**Date:** 2026-07-30 (this session)
**Context:** The requested `docs/program/` directory structure listed `SPRINT_PLAN/Sprint-00.md` through `Sprint-20.md` (21 sprints, 0-indexed), which conflicted with the already-completed 26-sprint (Sprint 1-26, 52-week) `ENGINEERING_ROADMAP.md`.
**Alternatives considered:** (a) Compress the program to literally fit 21 sprints (00-20), requiring either longer individual sprints or cut/merged phase scope; (b) treat Sprint-00 as a distinct non-delivery "prep" sprint ahead of 20 delivery sprints (compressing the current 26 delivery sprints to 20); (c) keep the 26-sprint plan as-is and number the files Sprint-01 through Sprint-26, treating the original listing as illustrative rather than a hard cap.
**Decision:** (c) ΓÇö explicit user choice when asked.
**Consequence:** `SPRINT_PLAN/` contains `Sprint-01.md` through `Sprint-26.md`; no phase boundaries, effort estimates, or the 52-week timeline in any other document needed to change.
**Status:** Accepted.

---

### DEC-011 ΓÇö Program documentation lives under `docs/program/`, reorganized from its original `salesos/` location

**Date:** 2026-07-30 (this session)
**Context:** The 10 program documents were originally written to `salesos/` (matching where `CANONICAL_ARCHITECTURE.md` and `SAAS_PLATFORM_ARCHITECTURE.md` already lived). The user specified a `docs/program/` structure instead, with `PRODUCT_RELEASE_PLAN.md` renamed to `RELEASE_PLAN.md` and three new files split out (`RISK_REGISTER.md`, `DECISION_LOG.md`, `MILESTONES.md`).
**Alternatives considered:** Leave the documents in `salesos/` and only add the three new files; duplicate content across both locations.
**Decision:** Move (not duplicate) all 10 files to `docs/program/`, rename `PRODUCT_RELEASE_PLAN.md` ΓåÆ `RELEASE_PLAN.md`, split `ENGINEERING_ROADMAP.md`'s per-sprint content into `SPRINT_PLAN/`, and extract the risk and milestone tables into their own canonical files (with the originating documents left pointing at them, not duplicating them going forward).
**Consequence:** `salesos/` now contains only the architecture documents (`CANONICAL_ARCHITECTURE.md`, `SAAS_PLATFORM_ARCHITECTURE.md`) and the Odoo ARB trilogy; all execution/program documents live under `docs/program/`.
**Status:** Accepted.

---

### DEC-012 ΓÇö Pricing bands in `COMMERCIAL_LAUNCH_PLAN.md` are a first-draft planning assumption, not a market-validated decision

**Date:** 2026-07-30
**Context:** Starter/Growth/Enterprise price points ($499/$1,999/custom) were needed to make the Commercial Launch Plan concrete rather than full of placeholders, per the instruction that "no placeholders" was acceptable in the deliverable.
**Alternatives considered:** Leave pricing as "TBD"; run a formal pricing study before committing numbers to a document.
**Decision:** Publish concrete numbers now, explicitly flagged as a first draft for the team to pressure-test, rather than leaving the document full of unresolved placeholders.
**Consequence:** Sales enablement (`ENGINEERING_ROADMAP.md` Sprint 26) must not proceed on these exact numbers without an explicit pricing review ΓÇö this decision does not constitute that review.
**Status:** Proposed (not yet validated against market data).

---

### DEC-013 ΓÇö R-14 blocks Sprint 03's RLS rollout; remediation plan accepted, execution not yet authorized

**Date:** 2026-07-31
**Context:** STORY-02-01's hand-test (Sprint 02) discovered that the application's database role (`salesos`) is a Postgres superuser with BYPASSRLS, meaning RLS policies ΓÇö however correctly written ΓÇö provide zero actual protection. A dedicated R-14 Production Security Validation pass then confirmed this is not a local-dev artifact: identical role provisioning (`pgvector/pgvector:pg16` official-image `POSTGRES_USER` bootstrap, no demotion step anywhere) is present in CI, staging, and the self-hosted production template, verified by direct file inspection of each environment's config. The empirical core claim ΓÇö a correct, `FORCE`-enabled policy with a correctly-set session variable still leaking cross-tenant rows under the `salesos` role ΓÇö was independently reproduced twice more (once by the validation pass, once again directly by this log's maintainer with a freshly-created probe table), not merely re-read from a prior transcript. Separately, a locally-saved snapshot of the real Railway production `DATABASE_URL` shows the live database connecting as `postgres` ΓÇö diverging from this project's own `salesos`-based templates ΓÇö a discrepancy that remains genuinely unresolved because no one has connected to confirm it, deliberately, per the stated Rules of Engagement (a locally-saved credential file is not standing authorization to use it against production).
**Alternatives considered:** (a) Proceed with Sprint 03's planned "RLS rollout, complete" across all 72 tables regardless, treating the pilot's finding as a Sprint-03-scope fix to make concurrently; (b) block Sprint 03's RLS work specifically until a non-superuser application role exists and is verified effective, while allowing Sprint 03's other stories (STORY-02-02 middleware.ts, STORY-02-03 JWT audience split, STORY-03-04 contract test framework) to proceed unaffected.
**Decision:** (b). Rolling RLS out to 62 more tables on top of a connection role that unconditionally bypasses it would produce exactly what the validation report calls "a false sense of security ΓÇö correct-looking policies that silently do nothing," which is worse than not having attempted RLS at all, since it would pass casual review. The remediation plan (new `salesos_app` role ΓÇö `NOSUPERUSER NOBYPASSRLS NOCREATEROLE NOCREATEDB NOREPLICATION LOGIN`, non-owning; scoped grants plus `ALTER DEFAULT PRIVILEGES` so future migrations are auto-covered; a new `app_database_url` setting used only by the runtime engine, with a safe fallback; `alembic/env.py` left unchanged since migrations must keep running as the owning role) is accepted as the correct shape of fix ΓÇö additive, not a replacement of the existing `salesos` role, and reversible by unsetting one env var.
**Consequence:** Sprint 03's `docs/program/SPRINT_PLAN/Sprint-03.md` STORY-02-01 ("RLS rollout, complete") does not start until (a) `salesos_app` exists and is granted correctly in the target environment, (b) the application is reconnected through it, and (c) the bypass-probe demonstrated in the validation report is re-run and returns zero cross-tenant rows. This decision **accepts the remediation plan** but does **not** authorize executing it ΓÇö creating a new role and rewiring connection configuration across environments is an infrastructure change requiring an explicit go-ahead from whoever owns each environment, not something to execute automatically off the back of a risk-register entry. Also unresolved and explicitly not closed by this decision: the `salesos` vs `postgres` role discrepancy between the production templates and the apparent live Railway snapshot ΓÇö resolving that requires an explicit, separately-authorized live-production check.
**Status:** Superseded by DEC-014 for the local-dev scope (execution authorized and completed same day); Blocking still stands, unchanged, for CI/staging/prod.

---

### DEC-014 ΓÇö R-14 remediation executed in local dev; CI/staging/prod explicitly deferred

**Date:** 2026-07-31
**Context:** DEC-013 accepted the `salesos_app` remediation plan but explicitly withheld execution authorization pending an owner decision. Asked directly, the decision was: implement now, local dev only.
**Alternatives considered:** (a) Implement across all environments in one pass; (b) local dev only, leaving CI/staging/prod for a separately-authorized follow-up; (c) defer all execution, file the plan only.
**Decision:** (b). Implemented: `infra/docker/postgres/init/02-app-role.sql` (idempotent role + scoped grants + `ALTER DEFAULT PRIVILEGES`), `app/config.py`'s `app_database_url` (fallback-safe), `app/database.py` split into a request-serving `engine` (new role) and a bootstrap-only `owner_engine` (unchanged role) ΓÇö the split was necessary, not optional: `CREATE SCHEMA IF NOT EXISTS` was verified to still require database-level CREATE privilege even when the schema already exists, so `init_db()`'s bootstrap DDL cannot run under the restricted role. `alembic/env.py` untouched.
**Consequence:** Local dev's `salesos` database now has zero application tables *by default until migrations run* ΓÇö a separate, pre-existing finding surfaced while executing this decision: the running `salesos-backend-1` container had apparently been serving traffic against an empty schema for its entire 13+ hour uptime (`init_db()`'s automatic migration path silently degrades on failure by design, per its own log message, rather than crashing). Running `alembic upgrade head` manually resolved it (86 tables now present, migration chain intact to head `0052`) ΓÇö this is disclosed as a distinct, pre-existing operational gap, not something this decision set out to fix, and not evidence of any flaw in the R-14 remediation itself. Post-fix, verified end-to-end: `docker compose up -d --force-recreate` (not `restart`, which does not reload `.env` ΓÇö a real gotcha hit during this work) picked up the new role; `pg_stat_activity` showed both `salesos` (owner_engine) and `salesos_app` (request engine) connected simultaneously; `/health` and `/ping` returned 200; the full regression suite held at 1,957 passed / 11 pre-existing failures (zero regressions); and the exact bypass-probe from the R-14 validation report, re-run against `salesos_app` instead of `salesos`, now returns only the querying tenant's row ΓÇö the identical policy that leaked both tenants under `salesos` correctly isolates under `salesos_app`. CI, staging, and the self-hosted prod template are **explicitly, deliberately not touched** by this decision ΓÇö `app_database_url`'s fallback means none of them are broken by this change (they simply haven't received the fix yet), and provisioning `salesos_app` plus setting `APP_POSTGRES_PASSWORD` in each is separately-scoped follow-up work, not silently assumed done. The live Railway `salesos`-vs-`postgres` discrepancy remains completely unresolved and untouched, per DEC-013's original Rules of Engagement.
**Status:** Accepted and executed (local dev only). CI/staging/prod rollout and the Railway discrepancy remain open, tracked in R-14's Owner column.

---

### DEC-015 ΓÇö R-14 rolled out to CI, staging, and the production template; Railway explicitly deferred, not guessed at

**Date:** 2026-07-31
**Context:** DEC-014 left CI, staging, and the self-hosted production template unremediated. Assigned as a follow-on "R-14 Enterprise Closure" task across every remaining environment, with an explicit rule: do not close R-14 unless every production-relevant environment is either validated or explicitly authorized-and-verified, and do not guess at Railway without authorization.
**Alternatives considered:** (a) Treat CI/staging/prod-template as low-risk-enough to skip and go straight to asking about Railway; (b) roll out and independently verify CI/staging/prod-template first (each is fully under this repo's own control, no live-system risk), then ask specifically about Railway once it was the only remaining gap; (c) edit `railway.json` speculatively to auto-provision on the next real deploy without connecting live.
**Decision:** (b) for CI/staging/prod-template. Found, while reviewing: all three already mount `infra/docker/postgres/init` as `docker-entrypoint-initdb.d` in their respective compose files (`docker-compose.prod.yml`, `infra/staging/docker-compose.staging.yml`, `infra/staging/docker-compose.staging-virtual.yml`) ΓÇö meaning `02-app-role.sql` auto-provisions on any fresh volume already; the actual gap was just `APP_POSTGRES_USER`/`APP_POSTGRES_PASSWORD` missing from each environment's env file/template, plus CI's `test-backend`/`integration-backend` jobs using GitHub Actions' ephemeral (non-compose) `services:` Postgres, which needed an explicit provisioning step instead of a mount. While wiring the CI step, found and fixed a real portability bug: the script hardcoded `GRANT CONNECT ON DATABASE salesos`, which only worked by coincidence where a database literally named `salesos` existed on the same server ΓÇö it failed outright against CI's `salesos_test`-only instance (`database "salesos" does not exist`). Fixed to grant on `current_database()` dynamically. Each environment was independently verified via local simulation (a throwaway container matching CI's exact image/env; `docker-compose.staging-virtual.yml`'s postgres service on a fresh volume; `docker-compose.prod.yml`'s postgres service on a fresh volume under an isolated compose project name) ΓÇö same bypass-probe as DEC-014, same result: owner role leaks both tenants, `salesos_app` isolates. For Railway: (c) was explicitly rejected ΓÇö asked directly, mid-task, whether to (i) leave it fully untouched, (ii) authorize a live connection, or (iii) edit `railway.json` blind; the answer was (i), leave it fully untouched. No `railway.json` edit, no live connection, no credential use.
**Consequence:** R-14 moves from "closed for local dev only" to **partially closed** ΓÇö local dev, CI, staging, and the production template are all remediated and independently verified; Railway is the sole remaining open environment, by explicit choice rather than oversight. A runbook for what Railway would require (manual `psql` provisioning as part of its deploy process, since it has no init-script mount; `APP_POSTGRES_PASSWORD` set via Railway's own secrets mechanism) is documented in `OPERATIONS_MANUAL.md` ┬º14, unexecuted. One incidental operational hazard surfaced and was corrected during this work: `docker-compose.prod.yml` has no explicit Compose project name, so running it from the same directory as the primary dev stack (also unnamed) collides with the running dev containers under the same implicit project name ΓÇö running it once briefly recreated the live dev `postgres` container against `.env.production`'s values before this was caught and reverted (same data volume throughout; no data lost; confirmed via live `/health/detailed` showing `database: connected` after restoration). Subsequent verification used an explicit isolated `-p` project name to avoid recurrence; this hazard is not yet fixed at the file level (still no `name:` in `docker-compose.prod.yml`) and is called out as a follow-up risk, not silently fixed in passing, since adding one is an infrastructure-shape change outside this decision's scope.
**Status:** Accepted and executed (CI, staging, production template). Railway remains open, deferred pending explicit authorization ΓÇö tracked in R-14's Owner column.

---

### DEC-020 ΓÇö Analytics schema drift discovered during Sprint 05 adversarial RLS verification; schema is authoritative; reconciliation scheduled as standalone Story CI-15

**Date:** 2026-07-31
**Context:** During S04-01 (adversarial RLS suite, `salesos/backend/tests/integration/test_adversarial_rls.py`) execution, after two proven root causes were fixed (`:id::uuid` SQLAlchemy `text()` bind bug in `_create_tenants`; cross-event-loop asyncpg pool reuse under pytest-asyncio 1.4.0 function-scoped loops, fixed with a file-local engine-dispose fixture per the executive's EvidenceΓåÆFix gate), the suite reached 6/7 with `test_analytics_reports_isolation` still failing: `UndefinedColumnError: column "metrics" of relation "analytics_reports" does not exist`. Investigation proved a three-way source-of-truth drift: migration `app/alembic/versions/0014_analytics.py` creates `analytics_reports` with 9 columns; ORM `domains/analytics/infrastructure/models.py` (`ReportModel`) defines 14 columns (adds `metrics`, `dimensions`, `filters`, `visualization_type`, `created_by`); live `salesos` DB (verified via `information_schema.columns`) has exactly the 9 migrated columns. No migration ever added the 5 ORM columns.
**Alternatives considered:** (A) reconcile ORMΓåöDB via a dedicated Alembic migration ΓÇö **approved**; (B) remove the 5 columns from `ReportModel` to match the DB ΓÇö rejected (hides drift, loses the architecture truth); (C) adapt the test to the 9-column DB ΓÇö rejected (tests a wrong system instead of fixing it; violates the Sprint 01+ evidence-first method).
**Decision:** Schema is authoritative. ORM and database must be reconciled through an Alembic migration. No test adaptation approved. No ORM rollback approved. Migration scheduled as a standalone Story **CI-15 ΓÇö Analytics Schema Reconciliation** (explicitly NOT executed inside S04-01). S04-01 is **BLOCKED** until CI-15 completes; it then re-runs to 7/7.
**Consequence:** Program progress stays 2/19 stories complete (CI-01, CI-11). S04-01 blocked on CI-15, tracked as **R-19** (HIGH, Open, Backend owner). The 6/7 fixed test state is preserved in the working tree (uncommitted) and will be committed only once CI-15 lands and 7/7 is reached.
**Status:** Accepted.

### DEC-021 ΓÇö CI-15 Phase 1 executed and closed under revised acceptance criteria; systemic drift promoted to Program Initiative (R-20, DB-05)

**Date:** 2026-07-31
**Context:** DEC-020 approved CI-15 as a standalone story (analytics-only schema reconciliation) but its original ACs ("ORM=DB 100%", "Autogenerate clean", "No drift after") proved unachievable once evidence showed **systemic ORMΓåöDB drift** beyond analytics (`alembic check` against head `0afbf3e6ae53`: `emails`/`meetings` id/tenant UUID vs String(36); `dead_letter_queue.id` INTEGER vs UUID; `companies` ORM-removed columns; `ix_rev_*`ΓåÆ`ix_*` index renames; nullable/type deltas across workflow/notifications/scheduled_jobs/feature tables). The executive APPROVED CI-15 Phase 1 with REVISED acceptance criteria: (1) migration adds ONLY the 5 analytics columns; (2) `alembic upgrade head` / `downgrade -1` / `upgrade head` PASS; (3) `analytics_reports` ORM=DB after migration; (4) adversarial suite 7/7 PASS; (5) systemic drift documented and referred to standalone work. Explicitly REFUSED during CI-15: fixes to emails/meetings/companies/dead_letter_queue, index renames, nullable drift, anything else from `alembic check`. `alembic check` is evidence-only (prove analytics drift gone, other drift remains and is registered), NOT a success criterion.
**Alternatives considered:** Executing CI-15 under the original (now disproven) ACs ΓÇö rejected as factually impossible; expanding CI-15 into a full schema reconciliation program ΓÇö rejected on scope-discipline grounds.
**Decision:** Executed CI-15 Phase 1: new migration `07e3ec4084fc_analytics_schema_reconciliation` (down_revision `0afbf3e6ae53`) adding `metrics` (JSON NOT NULL `[]`), `dimensions` (JSON NOT NULL `[]`), `filters` (JSON NOT NULL `{}`), `visualization_type` (String(50) NOT NULL `table`), `created_by` (String(36) NOT NULL ``) matching `ReportModel`. Validation: upgrade `0afbf3e6ae53ΓåÆ07e3ec4084fc` PASS (14 columns, types/defaults verified via `information_schema`); downgrade `-1` PASS (9 columns, rev `0afbf3e6ae53`); re-upgrade PASS (14 columns, rev `07e3ec4084fc`); adversarial suite `tests/integration/test_adversarial_rls.py` **7/7 PASS** (was 6/7); `alembic check` after migration: **0** `analytics_reports` drift lines while **300** drift lines remain elsewhere (35 table-level + 16 column/modify deltas + index/constraint renames) ΓÇö analytics drift gone, systemic drift persists and is now governed. New risk **R-20** (Systemic ORMΓåöDatabase Drift, HIGH 4├ù5=20, Open, Backend Platform, discovered by CI-15, blocks future schema-governance work) registered. New Program Story **DB-05 ΓÇö Repository Schema Reconciliation Program** registered (P1, multi-sprint; NOT part of CI-15). Governing principle ratified: **Local Story fixes Local Drift. Systemic Drift becomes a Program Initiative.**
**Consequence:** CI-15 COMPLETE; R-19 CLOSED; S04-01 COMPLETE at 7/7 (adversarial suite fully green). Program progress: **4/19** stories complete (CI-01, CI-11, S04-01, CI-15). Records updated: `SPRINT_05_DELIVERY_BOARD.md` (CI-15/S04-01 COMPLETE, DB-05 REGISTERED), `RISK_REGISTER.md` (R-19 Closed, R-20 added), `DECISION_LOG.md` (this entry). Committed locally (no push, per the governed cycle); Phase 2 (controlled push/CI) for CI-15/S04-01 to be scheduled per the story cycle.
**Status:** Accepted. Phase 1 result: **SUCCESS ΓÇö READY FOR PHASE 2.**

### DEC-022 ΓÇö CI-15 Phase 2 executed and closed: real CI verification on `4793b08`, no regression; migration-file lint delta disclosed and transferred

**Date:** 2026-07-31
**Context:** Phase 2 was authorized (approval gate) with stop rules: stop immediately on Migration failure, Backend test regression, Alembic failure, New RLS failure, or New Integration regression; no fixes during execution. Commit `4793b08` (CI-15 Phase 1 + S04-01 7/7 + R-20/DB-05 records) pushed to `master`; push triggered all 5 workflows.
**Alternatives considered:** None required ΓÇö the evidence set dictated the outcome; no decision fork arose during execution.
**Decision:** Phase 2 executed as evidence collection only. Backend validation at the pushed state (local, via Docker): `alembic current`/`heads` both = `07e3ec4084fc` (single head, migration applied); adversarial suite `tests/integration/test_adversarial_rls.py` = **7/7 PASS**. Real CI run `30652813475` (commit `4793b08`): job matrix compared against baseline run `30649799993` (commit `060c946`) ΓÇö **identical statuses on every job** (Frontend Lint/Types SUCCESS; Backend Lint/Types FAILURE pre-existing; Backend Unit/Integration SKIPPED as baseline; Frontend Unit FAILURE pre-existing 33-suite set; npm audit/pip-audit/Bandit/Secrets FAILURE pre-existing; Arch Compliance SUCCESS; builds/E2E SKIPPED; CI Summary FAILURE as baseline). No stop-rule condition triggered: no migration failure, no alembic failure, no RLS failure, no backend/integration test regression (the affected jobs were skipped at baseline and remained skipped ΓÇö not a transition). Sole delta: the new migration file `07e3ec4084fc_analytics_schema_reconciliation.py` contributes **10 new Ruff style violations** (UP035, I001, UP007├ù3, E501├ù5) to the already-red Backend Lint gate; `test_adversarial_rls.py` refs unchanged at 29 (pre-existing). These 10 violations are style-only, outside CI-15's approved ACs, and per the no-fixes rule they are **not fixed within CI-15** ΓÇö transferred to the Backend Lint remediation backlog (3,611 pre-existing violations program) / tracked with DB-05.
**Consequence:** CI-15 **CLOSED**; R-19 **CLOSED**; R-20 **OPEN (Program Risk)**; DB-05 ΓåÆ **BACKLOG**; S04-01 **COMPLETE**. Program progress: 4/19 stories complete/closed (CI-01, CI-11, S04-01, CI-15). Board and records updated. The 10 migration-file lint violations are a registered residual, not hidden.
**Status:** Accepted. Phase 2 result: **SUCCESS ΓÇö CI-15 COMPLETE.**

### DEC-023 ΓÇö CI-02 Phase 1 approved and executed (toolchain remediation); R-21 + CI-16 registered; principle ratified

**Date:** 2026-07-31
**Context:** CI-02 (pip-audit in CI) was the next highest READY P0 story per the CI triage execution order (#4/#9). Pre-task package established both root causes with current-run evidence: (1) CI workflow `security-pip-audit` never installs Poetry ΓåÆ `poetry: command not found` (run `30652813475`); (2) Security Scan `pip-audit` invokes `-f` without a value ΓåÆ `argument -f/--format: expected one argument` (run `30652813513`). Local prediction (backend container, Poetry 1.8.3 / pip-audit 2.10.1) showed that once tooling is fixed, `poetry export` succeeds (98 deps) and `pip-audit --strict` fails on REAL vulnerabilities.
**Alternatives considered:** Fixing the discovered dependencies inside CI-02 ΓÇö rejected by the executive; dependency remediation is a separate class of work.
**Decision:** The executive APPROVED CI-02 Phase 1 as **CI Toolchain Remediation** (not dependency remediation), with the ratified principle: **CI Stories fix CI Infrastructure, not application dependencies.** Approved scope: (1) add `pipx install poetry` to `security-pip-audit` mirroring the existing sibling pattern; (2) fix the malformed `-f` invocation in `security-scan.yml`; (3) YAML validation; (4) local verification proving the chain old-failure ΓåÆ `poetry export` succeeds ΓåÆ `pip-audit` runs ΓåÆ findings produced; (5) local commit only. Explicitly refused inside CI-02: poetry.lock/pyproject.toml/dependency changes, python-multipart/strawberry-graphql fixes, severity thresholds, pip-audit policy. Approved creation: **R-21** (Backend Dependency Vulnerabilities, HIGH 4├ù4=16, Open, Backend, discovered by CI-02, evidence = pip-audit execution after tooling remediation, scope = dependency modernization, blocks CI-16) and standalone Story **CI-16 ΓÇö Backend Dependency Security Remediation**.
**Consequence:** Phase 1 executed: `.github/workflows/ci.yml` (Install Poetry step added to `security-pip-audit`) and `.github/workflows/security-scan.yml` (removed stray `-f`). YAML parse OK. Local proof chain executed in the container: `poetry export` exit 0, 98 requirement lines; `pip-audit` JSON report produced findings ΓÇö `ecdsa 0.19.2` (PYSEC-2026-1325), `starlette 0.37.2` (9 advisories), `python-multipart 0.0.9` (7 advisories), `strawberry-graphql 0.243.1` (7 advisories); `--strict` exit 1 on findings (not tooling); security-scan command no longer argument-parse errors. R-21 and CI-16 registered in RISK_REGISTER / SPRINT_05_DELIVERY_BOARD. Committed locally (no push); Phase 2 (controlled push/CI) pending executive approval.
**Status:** Accepted. Phase 1 result: **SUCCESS ΓÇö READY FOR PHASE 2.**

### DEC-024 ΓÇö CI-02 Corrective Phase 1A: Poetry 2.x `export`-plugin gap on the GitHub runner (environment drift); `poetry-plugin-export` added

**Date:** 2026-07-31
**Context:** CI-02 Phase 2 real-run (`30655019114`, commit `b330d52`) eliminated `poetry: command not found` but surfaced a NEW toolchain failure: `The requested command export does not exist.` Diagnosis: the GitHub runner's `pipx install poetry` installs latest **Poetry 2.x**, where `export` is no longer a built-in command ΓÇö it requires the separate `poetry-plugin-export` plugin (Poetry's official forward-compatible direction). Local Phase 1 validation used the backend container's **Poetry 1.8.3** (export built-in), so it passed locally ΓÇö an **environment drift** (local 1.8.3 vs runner 2.x) that only the real run could expose. Confirmed locally: `poetry-plugin-export` 1.10.0 requires Poetry ΓëÑ2.1.0, so `poetry self add poetry-plugin-export` fails on 1.8.3 (validating the drift) and resolves on the runner's 2.x.
**Alternatives considered:** (a) pin `pipx install poetry@1.8.3` to match the container ΓÇö rejected by the executive (binds CI to an old version, against Poetry 2's official direction); (b) the official plugin install (`poetry self add poetry-plugin-export`) ΓÇö **approved**.
**Decision:** Corrective Phase 1A approved as an extension of CI-02 (same goal: remove toolchain failure entirely before reaching vulnerability findings ΓÇö NOT a new story). `security-pip-audit`'s Install Poetry step becomes: `pipx install poetry` then `poetry self add poetry-plugin-export`. Scope check: toolchain only ΓÇö no dependencies, no lockfile, no application code, no threshold/policy changes. New acceptance criterion added: **Poetry 2.x installation includes poetry-plugin-export.** Commit locally; no push until review.
**Consequence:** `.github/workflows/ci.yml` updated (multi-line Install Poetry step). YAML parse OK; local `poetry export` unaffected (1.8.3, 98 lines). The plugin-install correctness for Poetry 2.x is verified on the real runner in the Phase 2 re-run. Committed locally as the CI-02 corrective; Phase 2 re-run pending executive approval.
**Status:** Accepted. Corrective Phase 1A result: **SUCCESS ΓÇö READY FOR PHASE 2 RE-RUN.**

### DEC-025 ΓÇö CI-02 Phase 2 re-run executed and closed: full toolchain chain proven on real GitHub Actions; all pip-audit tooling failures eliminated

**Date:** 2026-07-31
**Context:** Phase 2 re-run authorized for commit `a4e880c` (Corrective Phase 1A). Stop rules: STOP/BLOCKED on `poetry: command not found`, `export does not exist`, `poetry self add` failure, plugin-install failure, or YAML failure; SUCCESS if `pip-audit` runs, produces vulnerability findings, and fails on `--strict` with findings.
**Alternatives considered:** None ΓÇö evidence dictated the outcome; no decision fork arose.
**Decision:** Pushed `a4e880c`; CI run `30655650484` and Security Scan run `30655650490` observed. CI `security-pip-audit` executed the FULL chain on the runner: Poetry 2.x installed via pipx ΓåÆ `poetry self add poetry-plugin-export` succeeded (no `export does not exist`) ΓåÆ `poetry export` succeeded ΓåÆ `pip-audit` ran ΓåÆ **`Found 24 known vulnerabilities in 4 packages`** (ecdsa 0.19.2, starlette 0.37.2, python-multipart 0.0.9, strawberry-graphql 0.243.1) ΓåÆ `--strict` exited 1 on the findings table. Security Scan `pip-audit` = **SUCCESS** (no argument-parse error). No stop-rule condition triggered. Job matrix otherwise identical to baseline (no regression).
**Consequence:** CI-02 **CLOSED** ΓÇö all pip-audit toolchain failures eliminated; any future pip-audit failure is evidence of real vulnerabilities to be handled in **CI-16 / R-21**, not CI infrastructure. DEC-024 **RATIFIED**; R-21 remains **OPEN**; CI-16 moved to **BACKLOG**. Program progress: **5/19** complete/closed (CI-01, CI-11, S04-01, CI-15, CI-02). Board and records updated; committed locally (no push).
**Status:** Accepted. Phase 2 re-run result: **SUCCESS ΓÇö CI-02 COMPLETE.**

### DEC-037 ΓÇö compose prod name fix closed: explicit `name: salesos-prod` in production compose; implicit project collision hazard resolved

**Date:** 2026-08-01
**Context:** The delivery board row "compose prod name fix" (P2) tracked DEC-015's disclosed hazard: `docker-compose.prod.yml` had no explicit Compose project `name:`, so running it from the same directory as the unnamed dev stack collided under the same implicit project name ΓÇö briefly recreating live dev containers against `.env.production` values before revert. The fix is workflow-only at the compose file level: set an isolated production project name.
**Alternatives considered:** (a) document the hazard only and require operators to always pass `-p` manually ΓÇö rejected: error-prone; (b) add `name: salesos-prod` to the production compose file ΓÇö approved.
**Decision:** Committed and pushed `cb707be` ("fix(compose): set production project name salesos-prod") on `master`. Change: `name: salesos-prod` in `salesos/docker-compose.prod.yml` (2-line insert). Validation: **light** ΓÇö YAML `name:` field valid; `docker compose config --quiet` against production compose **fails on missing env secrets** (expected for production template without full `.env.production`); no claim of full production stack bring-up.
**Consequence:** compose prod name fix row **CLOSED**. Production compose now has an explicit project namespace, isolating it from the dev stack's implicit project name. Program progress: **16/19**. **CI GREEN not met** ΓÇö this item is compose infrastructure only, not a CI workflow gate.
**Status:** Accepted. compose prod name fix **COMPLETE**. Field-verify label: **light validated** (YAML/name only).

---

### DEC-041 ΓÇö CI-21 closed: Gitleaks false-positive neutralized (test JWT ΓÇö Bearer stub)

**Date:** 2026-08-01
**Context:** Security closed a Gitleaks false-positive on `master` commit `b03ffbf` (`b03ffbf3aec1985d540107eeab0e753a2f06ab4a`): `salesos/backend/tests/integration/test_post_middleware.py` held a jwt.io sample JWT in an Authorization header that tripped Gitleaks. Fix replaced it with `Bearer test-fake-token-not-a-jwt` (middleware only needs Bearer present); no `.gitleaksignore`, allowlist, or global Gitleaks disable.
**Alternatives considered:** (a) allowlist / ignore the path ΓÇö rejected (weakens secret scanning); (b) neutralize the fixture token in-test ΓÇö chosen by Security.
**Decision:** Register and **CLOSE** story **CI-21** on the Sprint 05 delivery board. Field-verify: Security Scan run `30671556546` on `b03ffbf` ΓÇö **entire workflow SUCCESS** (secret-scan including Gitleaks PASS; sbom, sast-scan, pip-audit, npm-audit, report all SUCCESS).
**Consequence:** CI-21 **CLOSED**. Program progress: **18/20** complete/closed. Security Scan green on this commit is **not** a claim that the main CI workflow is green ΓÇö **CI GREEN not met**.
**Status:** Accepted. CI-21 **COMPLETE**. Field-verify label: **build validated** (Security Scan workflow only).

---

### DEC-038 ΓÇö CI-20 registered: Backend Types (MyPy) remediation ΓÇö 308 errors surfaced; phased, not mechanical this sprint

**Date:** 2026-08-01
**Context:** CI-10 field-verify run `30670339985` (commit `3801151` on `master`) proved **Stage 1: Backend Lint SUCCESS** (DEC-036) while **Stage 2: Backend Types** remained red with **308 mypy errors** across the backend body ΓÇö real type debt now visible after CI-07 removed the non-existent `cli/` path (DEC-032). This is triage #1 body debt, distinct from CI-10's Ruff body debt (triage #2, now closed).
**Alternatives considered:** (a) mechanical bulk `--ignore-errors` or gate disable ΓÇö rejected (weakens the gate); (b) register as a phased program story owned by Backend Lead, scoped outside this sprint's mechanical CI closure batch ΓÇö approved.
**Decision:** Register standalone story **CI-20 ΓÇö Backend Types remediation** (P2, owner Backend Lead). Evidence anchor: CI run `30670339985`, Backend Types job, **308 mypy errors**. Scope: phased remediation of real type errors; **NOT mechanical this sprint**; blocks Backend Types gate. CI-10 close records explicitly **do not** claim CI green ΓÇö sibling jobs on the same run still fail (MyPy, pip-audit, npm audit, Frontend Unit Tests, Trivy fs, etc.).
**Consequence:** CI-20 **REGISTERED** on the delivery board. Backend Lint gate is green (CI-10); Backend Types gate remains red until CI-20 lands. No duplicate DEC for CI-10 (already DEC-036). Program progress: **16/19** closed; Registered: CI-14, CI-19, CI-20.
**Status:** Accepted. CI-20 **REGISTERED** (not started).

---

### DEC-036 ΓÇö CI-10 closed: whole-tree Ruff remediation ΓÇö 3,611 violations cleared; Backend Lint green on post-push CI run

**Date:** 2026-08-01
**Context:** CI-10 (triage #2, P2) ΓÇö after CI-07 removed the non-existent `cli/` path, Backend Lint still failed with **3,611 real Ruff violations** across the backend body (including auto-generated Alembic migration files never intended for style enforcement). Triage AC: `ruff check` exits 0; `app/alembic/versions/` excluded; `cli/` path resolved (latter satisfied by CI-07/DEC-032).
**Alternatives considered:** (a) Exclude the entire backend from Ruff and leave debt unenforced ΓÇö rejected: defeats the gate; (b) mechanical `--fix` plus targeted manual review with alembic/versions excluded ΓÇö chosen; matches triage recommendation.
**Decision:** Committed and pushed `3801151` ("CI-10: whole-tree ruff 0.4.10 pass (3,611 violations -> 0)"). Phase 1 local validation: ruff 0.4.10 clean with alembic/versions excluded. Phase 2 field verification: CI run `30670339985` on `master` ΓÇö **Stage 1: Backend Lint SUCCESS** (first green Backend Lint on real GitHub Actions). Overall CI workflow on the same run remains **failure** (MyPy, pip-audit, npm audit, Frontend Unit Tests, Trivy fs, etc.) ΓÇö **CI GREEN is not met**.
**Consequence:** CI-10 **CLOSED**. The triage #2 Ruff body debt is eliminated from the Backend Lint gate. Residual CI red jobs are pre-existing or separately tracked stories (CI-16/R-21, CI-14, Sprint 01 Jest debt, MyPy classification backlog from CI-07). Program progress: **15/19**. RISK_REGISTER unchanged ΓÇö Ruff debt was tracked on the delivery board, not as a standalone risk entry.
**Status:** Accepted. CI-10 **COMPLETE**. Field-verify label: **build validated** (Backend Lint job only); full CI workflow: **production no-go**.

---

### DEC-035 ΓÇö CI-13 closed: Jest suite baseline captured from real CI evidence ΓÇö 33/194 failing suites inventoried; dependency contract set for CI-14

**Date:** 2026-07-31
**Context:** CI-13 (triage #7, P1) ΓÇö CI `Stage 3: Frontend Unit Tests` fails with `Test Suites: 33 failed, 161 passed, 194 total` / `Tests: 163 failed, 1 skipped, 2092 passed, 2256 total`, identical to the Sprint 01 closing numbers and the Sprint 04 triage. Not a regression. CI-14 (Frontend Dependency Modernization) lists CI-13 as a dependency for its Jest-major leg ΓÇö the dependency needs a fixed-point baseline to measure before/after.
**Alternatives considered:** (a) Run the full Jest suite locally to produce the list ΓÇö unnecessary: the real CI run already produces the ground-truth inventory with command evidence; (b) treat CI-13 as the full remediation of the 33 suites ΓÇö rejected: that is the separately-scoped Sprint 01 Jest-debt story (1ΓÇô2 days), and CI-14 only needs the baseline dependency.
**Decision:** Extracted the exact failing-suite inventory and counts from real CI run `30664173050` (commit `d48cc80`, job `Stage 3: Frontend Unit Tests`, conclusion failure): **33 failing suites** (full list, including `src/components/foundation/__tests__/card.test.tsx` = `Test suite failed to run`), 163 failed / 1 skipped / 2092 passed / 2256 total. Root-cause categories recorded: (1) Card component gap (canonical `@salesos/ui` Card vs deprecated `src/components/foundation/card.tsx` duplicate); (2) stale UI-text assertions (`Expected substring: "Search failed"`, monitoring/DB-connection wiring); (3) jsdom missing browser APIs (`scrollTo`/`scrollIntoView`). Deliverable committed: `salesos/docs/audit/ga-engineering-audit/JEST_BASELINE.md`.
**Consequence:** CI-13 **CLOSED**. Dependency contract for CI-14: after any dependency bump, failing suites `<= 33` and failing tests `<= 163` ΓÇö no new failures beyond the inventoried 33 acceptable; suites that turn green during CI-14 work are removed from the baseline with a note. The remediation of the 33 suites remains the Sprint 01 Jest-debt story (not CI-14's scope). Program progress: **14/19**.
**Status:** Accepted. CI-13 **COMPLETE.**

### DEC-034 ΓÇö CI-12 closed: Trivy fs "silent failure" root-caused (SARIF suppresses the findings table) ΓÇö gate split into visible blocking table + SARIF upload leg; 11 real HIGH findings surfaced and tracked

**Date:** 2026-07-31
**Context:** CI-12 (triage #3) ΓÇö CI `security-secrets-scan` job's `Run Trivy filesystem scan` failed (exit 1) but the log showed only `[npm] Detecting vulnerabilities...` ΓåÆ `[poetry] Detecting vulnerabilities...` ΓåÆ exit, with **no vulnerability table and no error** between them. Triage classified it "silent failure", requiring local reproduction with verbose output before any fix.
**Alternatives considered:** (a) Remove `exit-code: 1` to match `security-scan.yml`'s non-blocking `secret-scan` ΓÇö rejected: weakens the CI gate (governance: never weaken without approval); (b) narrow `scan-ref` to `./salesos` to drop root scrapers ΓÇö rejected: scan-scope change is policy, needs separate approval; (c) split the step into a blocking visible table gate + a non-blocking SARIF export leg ΓÇö chosen.
**Decision:** Local reproduction on a clean `git archive` snapshot of `HEAD` with the exact CI flags (`--format sarif --severity CRITICAL,HIGH --exit-code 1`) reproduces the triage log **verbatim** (npm/poetry detecting lines ΓåÆ exit 1, no table). **Root cause:** with `--format sarif --output <file>`, Trivy writes findings only to the SARIF file; stdout carries progress lines only ΓÇö the gate correctly blocks but is opaque. The findings are REAL and match already-tracked debt exactly: `salesos/backend/poetry.lock` ΓåÆ **10 HIGH** (ecdsa CVE-2024-23342 "Minerva attack" 0.19.2, etc. ΓåÆ **CI-16 / R-21**) + `salesos/frontend/package-lock.json` ΓåÆ **1 HIGH** (sharp GHSA-f88m-g3jw-g9cj, 0.34.5 ΓåÆ 0.35.0 ΓåÆ **CI-14**). Inconsistency confirmed: `security-scan.yml` `secret-scan` has **no** `exit-code` (always passes, SARIF-only); CI `security-secrets-scan` uses `exit-code: 1` (strict gate). Secondary: secret-scanner walks large tracked root-scraper JSONs (`balady_scraper/engineering_offices_full.json` 24 MB, `najiz_scraper/data/lawyers.json` 12 MB) with high-memory warnings ΓÇö scan-scope note for later, not this story.
**Consequence:** Split the CI Trivy step (`.github/workflows/ci.yml` `security-secrets-scan`) into: (1) `Run Trivy filesystem scan (blocking gate, visible findings)` ΓÇö `format: table`, `severity: CRITICAL,HIGH`, `exit-code: 1` ΓåÆ findings now PRINT to the log; (2) `Export Trivy SARIF for code scanning` ΓÇö `format: sarif`, `output: trivy-results.sarif`, `exit-code: 0` ΓåÆ code-scanning upload preserved. Gate strictness unchanged; no security weakening. The job remains red while the 11 tracked findings exist ΓÇö now visibly and actionably. Local proof: table+exit-1 run prints the table and exits 1; sarif+exit-0 run produces the file and exits 0. CI-12 **CLOSED**; program progress **13/19**.
**Status:** Accepted. CI-12 **COMPLETE.**

### DEC-033 ΓÇö CI-06 closed: Deploy Production commit-comment 403 resolved with least-privilege job-level permissions

**Date:** 2026-07-31
**Context:** CI-06 (triage #14) ΓÇö Deploy Production (`deploy.yml`) `GitHub commit comment` step (`actions/github-script@v7` ΓåÆ `github.rest.repos.createCommitComment`) failed with `HttpError: Resource not accessible by integration (403)` because the workflow-level `permissions:` block (deploy.yml:30) granted only `contents: read`, `packages: read`, `id-token: write` ΓÇö insufficient for commit-comment creation. The comment step lives in the `notify` job (deploy.yml:276, `if: always()`), which also posts Slack/Teams notifications.
**Alternatives considered:** (a) Bump the workflow-level block to `contents: write` ΓÇö rejected: every job inherits write on contents, broader blast radius; (b) job-level `contents: write` scoped to the `notify` job only ΓÇö chosen (least privilege).
**Decision:** Added job-level `permissions: contents: write` to the `notify` job only; top-level stays `contents: read`. YAML parse OK. Pushed `20f88bc`. Evidence ΓÇö Deploy Production run `30661932918`: `Deploy Notification` **SUCCESS**; notify log shows the `createCommitComment` step executed with **0** `HttpError` / `Resource not accessible` occurrences; definitive proof via `gh api commits/20f88bc/comments` ΓåÆ commit comment actually created by **`github-actions[bot]`** at 2026-07-31T20:12:07Z ("Γ¥î Production deploy **failure** ΓÇö `20f88bcd...`"). Remaining job failures in that run are pre-existing blocked items, not regressions: Deploy Blue Slot = GHCR 403 (ΓåÆ CI-08 / R-17), Automatic Rollback = SSH/VPS secrets (ΓåÆ CI-09).
**Consequence:** CI-06 **CLOSED** ΓÇö commit-comment notification path verified working end-to-end on the real runner. No regression. Program progress: **12/19**.
**Status:** Accepted. CI-06 **COMPLETE.**

### DEC-032 ΓÇö CI-07 closed: non-existent `cli/` path removed from mypy/ruff invocations ΓÇö Backend Types/Lint now fail only on real code debt

**Date:** 2026-07-31
**Context:** CI-07 (triage #1/#2 partial) ΓÇö `.github/workflows/ci.yml` invoked `cli/` in `ruff check` (:48), `ruff format --check` (:50), and `mypy` (:92), but `cli/` does not exist in the repo ΓåÆ every CI run failed with `mypy: error: cannot read file 'cli'` (Backend Types) and `cli:1:1: E902` (Backend Lint), masking real findings.
**Alternatives considered:** None ΓÇö the path simply does not exist; removing it restores the gates to genuine results.
**Decision:** Removed `cli/` from all three invocations (workflow-only). YAML parse OK; local ruff over `app/ tests/ sdk/ modules/` = **0 E902**. Committed `b0c0069`; pushed `ba673e7..b0c0069`. Because the subsequent CI-06 push (`20f88bc`) superseded the CI-07 run via the CI concurrency group (rapid successive pushes), CI-07 verification uses CI run `30661932842`, which contains **both** changes: `Stage 2: Backend Types` and `Stage 1: Backend Lint` logs show **0** `cannot read file 'cli'` and **0** E902 occurrences (both previously present in every run). Both gates now fail only on real code debt ΓÇö mypy type errors (to be classified) and the Ruff body (3,611 ΓåÆ **CI-10**) ΓÇö which is correct gate behavior.
**Consequence:** CI-07 **CLOSED**. No regression. Program progress: **11/19** (interim; 12/19 after CI-06 close, DEC-033).
**Status:** Accepted. CI-07 **COMPLETE.**

### DEC-026 ΓÇö CI-03 Phase 1 approved and executed: `GF_SECURITY_ADMIN_PASSWORD` provided to the Docker Smoke workflow env (workflow-only, no compose weakening)

**Date:** 2026-07-31
**Context:** CI-03 (triage #8) ΓÇö the Docker Smoke Test workflow's `Validate Compose File` step fails: `docker compose config` against `salesos/docker-compose.yml` errors `required variable GF_SECURITY_ADMIN_PASSWORD is missing a value` (run `30655650514`). The grafana service's `${GF_SECURITY_ADMIN_PASSWORD:?Set GF_SECURITY_ADMIN_PASSWORD}` is a correct guard; the gap is the workflow env, which provides postgres/neo4j/JWT/secret vars but not the Grafana password. Reproduced the exact error locally (host docker compose v5.3.1, `--env-file` mirroring the workflow `.env`): exit 1, same message.
**Alternatives considered:** Removing/weakening the `:?` guard in the compose file ΓÇö rejected by the executive (the guard is correct; CI must supply the right environment, not relax real config). Approved: add the dev-only smoke value to the workflow env.
**Decision:** Added `GF_SECURITY_ADMIN_PASSWORD: salesos_smoke_test` to `.github/workflows/docker-smoke.yml` workflow-level env (mirroring the existing `salesos_smoke_test` credentials convention). Before/After proof executed: BEFORE = exit 1 with the exact GF interpolation error; AFTER = exit 0, **0** "required variable" lines, **0** "error while interpolating" lines, only the pre-existing optional-variable blank-defaulting warnings (ALERTMANAGER/SLACK/PAGERDUTY, present before the change, non-error). Principle ratified: **┘ä╪º ╪¬┘Å╪«┘ü┘ü ┘à╪¬╪╖┘ä╪¿╪º╪¬ ┘à┘ä┘ü╪º╪¬ Compose ┘ä╪Ñ╪▒╪╢╪º╪í CI╪¢ ╪¿┘ä ╪º╪¼╪╣┘ä CI ╪¬┘ê┘ü╪▒ ╪º┘ä╪¿┘è╪ª╪⌐ ╪º┘ä╪╡╪¡┘è╪¡╪⌐ ╪º┘ä╪¬┘è ┘è╪¬╪╖┘ä╪¿┘ç╪º Compose.**
**Consequence:** `.github/workflows/docker-smoke.yml` updated (workflow only); YAML parse OK. No compose file, no grafana config, no secrets handling, no other service touched. Committed locally (no push); Phase 2 (controlled push/CI) pending executive approval.
**Status:** Accepted. Phase 1 result: **SUCCESS ΓÇö READY FOR PHASE 2.**

### DEC-031 ΓÇö CI-17 closed: B324 weak MD5 remediated ΓÇö Stage 5: Bandit SAST fully green

**Date:** 2026-07-31
**Context:** Phase 2 pushed commit `b87fb22` (`usedforsecurity=False` added to the MD5 call deriving `role_id`). Success criteria: fail-on-high gate passes, Stage 5 green, no regression.
**Alternatives considered:** Replacing MD5 with SHA-256 (would change stored role IDs ΓåÆ data migration) ΓÇö rejected; `usedforsecurity=False` is exactly what B324 prescribes and is digest-preserving.
**Decision:** Evidence ΓÇö CI run `30661609555`: `Stage 5: Bandit SAST` **SUCCESS** on all steps including `Run bandit (fail on high)` (0 high/high findings) and `Upload bandit results`. Full job matrix identical to baseline with this one job flipped green ΓÇö **no regression**. Local proofs (Phase 1): digest byte-identical (`816ba59a...` both modes), 45 admin tests pass, 0 new Ruff violations.
**Consequence:** CI-17 **CLOSED**. Program progress: **10/19**. Board updated with explicit triage mapping for the remaining generic rows (CI-06=#14 permissions, CI-07=#1/#2 cli/, CI-12=#3 Trivy investigation, CI-10=#2 Ruff body). Entering autonomous continuous-execution mode per executive directive: next READY = CI-07 (cli/ path) then CI-06 (#14 permissions).
**Status:** Accepted. CI-17 **COMPLETE.**

### DEC-030 ΓÇö CI-18 closed: semgrep SARIF upload fixed ΓÇö entire Security Scan workflow GREEN for the first time; 253 semgrep findings surfaced as a separate item

**Date:** 2026-07-31
**Context:** Phase 2 authorized for commit `6ab1d0e` (repeatable `--severity ERROR --severity WARNING` replacing invalid comma list `--severity ERROR,WARNING`). Success criteria: semgrep executes, SARIF generated, `Upload semgrep results` PASS, no CLI parse error, no regression.
**Alternatives considered:** Dropping severity filtering (scans all severities) ΓÇö rejected, changes policy; repeatable flags preserve intent exactly.
**Decision:** Pushed `6ab1d0e`. Evidence ΓÇö Security Scan run `30660116232`: **all 6 jobs SUCCESS** (secret-scan, sbom, sast-scan, pip-audit, npm-audit, report). `sast-scan` steps all green: `Install semgrep`, `Run semgrep (generic SAST)`, **`Upload semgrep results` SUCCESS**; log scan: **0** `invalid value` / `Path does not exist` / `semgrep scan: option` occurrences. Semgrep actually scanned: **Findings 253 (253 blocking)**, targets scanned 2806, 595 rules ΓÇö all now visible in GitHub code scanning. The `--error` exit (1 on findings) is masked as designed by `|| true` + `continue-on-error: true`.
**Consequence:** CI-18 **CLOSED** (all ACs met). SAST upload path complete for Bandit + Trivy (fs & IaC) + Semgrep. Security Scan workflow fully green (previously 2 of 6 jobs red). New registered story: **CI-19** (semgrep findings remediation ΓÇö triage of the 253 blocking findings). Program progress: **9/19**. Board + DECISION_LOG updated; committed locally (no push).
**Status:** Accepted. CI-18 **COMPLETE.**

### DEC-029 ΓÇö CI-05 closed: Trivy SARIF category collision resolved ΓÇö both uploads green in `secret-scan`

**Date:** 2026-07-31
**Context:** Phase 2 authorized for the CI-05 Phase 1 commit (actual SHA **`f34bef2`**; the earlier "c0f2199" in the Phase 1 report was inaccurate ΓÇö corrected in the close records). Change: distinct `category` per `upload-sarif` step in `secret-scan` (`trivy-fs` for fs scan, `trivy-config` for IaC config scan).
**Alternatives considered:** None ΓÇö GitHub's error message itself prescribes the `category` fix; audit confirmed the Trivy pair in `secret-scan` was the only tool/category collision across all 7 `upload-sarif@v3` occurrences in the repo.
**Decision:** Pushed `f34bef2` (also carried CI-04 close records `949dbf4`). Evidence ΓÇö Security Scan run `30659372944`, `secret-scan`: Set up, Checkout, forbidden-files check, Gitleaks, Trivy fs scan, **`Upload Trivy results` SUCCESS**, Trivy config scan, **`Upload Trivy config results` SUCCESS** ΓåÆ job conclusion **SUCCESS**. Log scan: **0** occurrences of `Aborting upload` / `only one run` / `tool/category`. IaC SARIF now visible in code scanning (previously silently lost).
**Consequence:** CI-05 **CLOSED** (all Phase 2 ACs met). No regression. Program progress: **8/19**. Remaining security-scan reds are independent items: semgrep upload (CI-18), Trivy fs findings in CI workflow (triage #3). Board + DECISION_LOG updated; committed locally (no push).
**Status:** Accepted. CI-05 **COMPLETE.**

### DEC-028 ΓÇö CI-04 closed: Bandit SARIF uploads fixed in both workflows; gate now executes and surfaces a pre-existing high finding (B324)

**Date:** 2026-07-31
**Context:** Phase 2 authorized for commit `ce59efd` (install `bandit[sarif]` in `ci.yml` + `security-scan.yml`). Success criteria: `bandit-results.sarif` generated, `Upload bandit results` PASS in both workflows, no Bandit `Path does not exist`; any later failure (e.g., Semgrep) is an independent item, not CI-04.
**Alternatives considered:** Dropping SARIF upload and keeping only the JSON gate (loses code-scanning visibility) ΓÇö rejected; the approved fix preserves both.
**Decision:** Pushed `ce59efd`. Evidence ΓÇö CI run `30658782384` `Stage 5: Bandit SAST`: Install SUCCESS, `Run bandit` SUCCESS, **`Upload bandit results` SUCCESS**, then `Run bandit (fail on high)` FAILURE. Security Scan run `30658782394` `sast-scan`: **`Upload bandit results` SUCCESS**; `Upload semgrep results` FAILURE (`Path does not exist: semgrep-results.sarif` ΓÇö separate root cause).
**Key insight ΓÇö NOT a regression:** Baseline run `30655650484` shows `Run bandit (fail on high)` = **SKIPPED** (the failing upload set `JOB_STATUS_CONFIGURATION_ERROR`, halting downstream steps). The high-severity JSON gate never executed until now. CI-04 fixing the upload enabled the gate for the first time; it correctly found **1 high/high finding: B324 (hashlib) ΓÇö weak MD5** in `app/modules/admin/routers/roles_permissions.py:40` (`role_id = f"role_{hashlib.md5(body.name.encode()).hexdigest()[:8]}"`). Reproduced locally (bandit 1.9.4, JSON report, 1 result, HIGH/HIGH).
**Consequence:** CI-04 **CLOSED** (all ACs met). New registered stories: **CI-17** (B324 remediation ΓÇö add `usedforsecurity=False`), **CI-18** (semgrep SARIF upload). Program progress: **7/19**. Board + DECISION_LOG updated; committed locally (no push). The Stage 5 job will remain red until CI-17 lands ΓÇö correct gate behavior, not CI debt.
**Status:** Accepted. CI-04 **COMPLETE.**

### DEC-027 ΓÇö CI-03 Phase 2 executed and closed: Docker Smoke Test fully green on real GitHub Actions (entire job, not just the gate)

**Date:** 2026-07-31
**Context:** Phase 2 authorized for commit `83e703e` (Docker Smoke workflow env now provides `GF_SECURITY_ADMIN_PASSWORD`). Stop rules: STOP on `Validate Compose File` failure (interpolation/missing var/compose syntax/workflow parsing); any failure AFTER the validation gate is NOT CI-03 (new independent item, not to be fixed here).
**Alternatives considered:** None ΓÇö evidence dictated the outcome.
**Decision:** Pushed `83e703e`; Docker Smoke Test run `30656335600` observed. Step results: Set up job SUCCESS, Checkout SUCCESS, Setup .env SUCCESS, **Validate Compose File SUCCESS (1s)** ΓÇö no `required variable GF_SECURITY_ADMIN_PASSWORD is missing` message, no interpolation errors; then Build Services SUCCESS (111s), Start Services SUCCESS (79s), Run Smoke Tests SUCCESS (30s), Stop Services SUCCESS. **The entire Docker E2E Smoke Test job concluded SUCCESS** ΓÇö no downstream failure to classify; the previously all-red workflow is now fully green.
**Consequence:** CI-03 **CLOSED**; DEC-026 **RATIFIED**; Docker Smoke interpolation issue **eliminated**. Program progress: **6/19** complete/closed (CI-01, CI-11, S04-01, CI-15, CI-02, CI-03). Board and records updated; committed locally (no push). The smoke job is now a genuine regression guard for the docker stack.
**Status:** Accepted. Phase 2 result: **SUCCESS ΓÇö CI-03 COMPLETE.**

### DEC-019 ΓÇö CI-11 closed: patch-only dependency remediation verified on real GitHub Actions; zero regressions

**Date:** 2026-07-31
**Context:** CI-11 Phase 2 (regression verification) executed on the real CI run `30649799993` for commit `060c946` (push to `master`). All four target jobs compared against the pre-CI-11 baseline: Frontend Lint PASS (unchanged), Frontend Types PASS (unchanged), Frontend Unit Tests exactly the pre-existing 33-suite/163-test failure set (byte-identical, zero new failures), npm audit FAIL with 30 high (down from 31 ΓÇö reduced, and the residual is the CI-14-transferred class). No `package.json` change; only `package-lock.json` in the commit.
**Alternatives considered:** None ΓÇö the outcome matched the approved success criteria exactly; no decision fork arose.
**Decision:** CI-11 is COMPLETE. Patch-only remediation is proven safe on real GitHub Actions. Residual advisories remain formally transferred to CI-14 (DEC-018). Sprint 05 continues with the next highest READY story in the Entry Package.
**Consequence:** The `npm audit` CI job stays red (30 residual, tracked to R-18/CI-14) until Frontend Dependency Modernization lands ΓÇö a known, governed state, not a CI-11 defect. Program progress: 2/19 stories complete (CI-01, CI-11).
**Status:** Accepted.

### DEC-018 ΓÇö CI-11 Phase 1 complete (patch-only); residual advisories require Majors ΓåÆ new Program Story CI-14; CI-11 AC revised

**Date:** 2026-07-31
**Context:** CI-11 (npm audit remediation) Phase 1 executed within the approved patch/minor-only scope: `npm audit fix` (no `--force`) applied 9 patch-level changes (next 15.5.20ΓåÆ15.5.22, postcss 8.5.17ΓåÆ8.5.25, ts-jest 29.4.11ΓåÆ29.4.12, brace-expansion 1.1.16ΓåÆ1.1.18 and 5.0.7ΓåÆ5.0.9, and next-aligned subpackages), reducing `npm audit` from 31 to 30 high with zero new test failures (Jest identical to the pre-existing 33-suite baseline), TypeScript and Lint passing. The 30 residual advisories split into two clusters, both requiring **Major/breaking** changes per npm's own analysis: (a) the `brace-expansion`/`minimatch` DoS chain through the ESLint+Jest dev toolchain (eslintΓåÆ10.8.0, jestΓåÆ25.0.0, ts-jestΓåÆ27.0.3, eslint-config-nextΓåÆ0.2.4), dev-only exposure; (b) `sharp <0.35.0` libvips CVEs inherited by next's image pipeline, whose fix npm frames as nextΓåÆ14.2.35 (downgrade across major lines). Executive ruled out both a permanent allowlist (Option 1) and authorizing Majors now (Option 3).
**Alternatives considered:** (1) permanent accepted-risk allowlist ΓÇö rejected (should never be the standing resolution for a red CI security gate); (2) extract Major remediation into an independent program story, close CI-11 against revised reality-based criteria; (3) authorize Major upgrades now ΓÇö rejected (architecture-level change).
**Decision:** (2). CI-11 Phase 1 is COMPLETE (patch remediation SUCCESS; no `--force`; no Major applied; no regression). CI-11 acceptance criteria are REVISED to the following five points (superseding "`npm audit` clean OR allowlist"): (1) patch-level remediations applied where safely available; (2) no new regressions introduced; (3) residual advisories classified and documented; (4) Major-version remediation extracted into a separate program story; (5) CI verification confirms no regression from the applied patch updates (Phase 2). New story **CI-14 ΓÇö Frontend Dependency Modernization** registered: Upgrade ESLint ecosystem; Upgrade Jest ecosystem; Resolve sharp/libvips chain; Validate Next.js compatibility; Update CI security gates. Independent story ΓÇö not an extension of CI-11. Phase 2 of CI-11 is authorized **only** for regression verification (patch fixes introduce no CI regression), explicitly **not** for making `npm audit` green.
**Consequence:** CI-14 is a standalone story assigned to Sprint 06 (P1, Frontend Lead), with CI-13 (Jest suite baseline) as a dependency for the Jest-major leg; it may be pulled into Sprint 05 only by explicit planning decision. CI-11 closes only after Phase 2 regression verification passes. The `npm audit` CI job remains red until CI-14 lands ΓÇö a known, tracked state.
**Status:** Accepted.

### DEC-017 ΓÇö CI-01 closed: Deploy Production branch-guard defect resolved; failure point moved from gate to infrastructure layer

**Date:** 2026-07-31
**Context:** The Sprint 05 Entry Package's CI-01 (triage #12, CRITICAL) targeted `deploy.yml`'s pre-deploy branch guard, which hardcoded `refs/heads/main` and therefore failed unconditionally on this repo's `master` ΓÇö making Deploy Production non-functional at the gate, independent of every other pipeline defect. Phase 1 (implementation-only) replaced the literal with `refs/heads/master` and updated the error message; validated YAML; committed locally as `61e08d4` (not pushed, per the stop rule). Phase 2 (controlled, separately approved) pushed `61e08d4` to `master` and observed the real run `30648063788`.
**Alternatives considered:** (a) Implement a genuine Checks-API CI-status verification now (the step is misleadingly named "Verify CI passed on this commit"); (b) minimal branch-literal fix now, deeper gate later.
**Decision:** (b). The Checks-API implementation is explicitly a separate, deeper fix per the triage itself, and would block deploys until CI-02ΓÇªCI-13 make CI green ΓÇö sequencing it now would be speculative. Result: `pre-deploy-check` PASSED on real GitHub Actions (7s, job `91214319548`). The downstream Deploy Blue Slot job started (SSH stage) and failed within 1s ΓÇö classified as infrastructure configuration (missing SSH/VPS host secrets, triage #13), not a regression and not the branch guard. Per the executive stop-condition, monitoring stopped the moment the deploy-stage job started; the run was not awaited to completion.
**Consequence:** Deploy Production now passes its gate; the pipeline's failure point has moved from the branch guard to the infrastructure layer. The branch-guard risk is closed (R-16); the SSH/VPS infrastructure gap remains open (R-17), tracked as CI-09/CI-08. The misleading step name remains a documented backlog item.
**Status:** Accepted.

### D-S4-002 ΓÇö Sprint 04 continues in parallel with CI-remediation stories; CI is not currently a working merge gate

**Date:** 2026-07-31
**Context:** Commit `354e13c` triggered the program's first-ever real GitHub Actions execution on `master`. All 5 workflows (CI, Docker Smoke Test, Security Scan, Deploy Production, Deploy Staging) failed ΓÇö 17 failed jobs total, independently triaged with direct evidence from the actual run logs (`gh run view --log-failed`), not assumed or guessed. Full triage: `salesos/docs/audit/ga-engineering-audit/SPRINT_04_CI_TRIAGE.md`. None of the 17 failures originate in Sprint 04 feature code ΓÇö STORY-04-01/04-02/02-03 are not yet implemented; every failure is pre-existing CI/pipeline configuration or tooling debt (a hardcoded `main`-vs-`master` branch check that makes Deploy Production unconditionally non-functional; missing Poetry installs; an unsupported Bandit SARIF format; a Trivy SARIF category collision; a missing Grafana env var blocking the Docker smoke test; GHCR 403s blocking all staging image pushes; 3,611 pre-existing Ruff violations never previously enforced; 31 real high-severity npm vulnerabilities; and the already-documented Sprint 01 Jest gap, 33/194 suites, unchanged).
**Alternatives considered:** (a) Halt all Sprint 04 feature work until CI is fully green; (b) proceed with Sprint 04's feature stories in parallel, opening dedicated CI-remediation stories rather than folding pipeline fixes into feature work; (c) ignore the CI failures as noise and continue without tracking them.
**Decision:** (b). Most of the 17 failures are small, isolated, low-risk configuration corrections (workflow YAML, env vars, tool flags ΓÇö no application code) that do not require Sprint 04's actual feature work to pause; none of Sprint 04's planned local-dev/test work depends on Deploy Production or Deploy Staging succeeding. The two largest items (Ruff's 3,611 violations, the Jest suite's 33 failing suites) are real, substantial, already-scoped bodies of work that deserve their own stories rather than being rushed. (c) is rejected outright ΓÇö a completely red pipeline provides zero regression protection for Sprint 04's new work, which is a real risk to accept knowingly, not silently.
**Consequence:** Sprint 04's STORY-04-01/04-02/02-03 proceed as planned. New CI-remediation stories are opened per the triage's Execution Order, starting with the Deploy Production branch-name fix (2-minute fix, currently blocks 100% of production deploys, highest priority regardless of anything else). Until the quick-fix batch (items 1ΓÇô9 in the triage) lands, CI cannot be relied on to distinguish a real regression in Sprint 04's new code from pre-existing noise ΓÇö reviewers should manually check which job failed and cross-reference the triage before treating any red CI run on a Sprint 04 PR as a genuine regression.
**Status:** Accepted.

---

### DEC-039 — S04-05 closed: adversarial write-protection suite on master; Docker evidence **build validated** (8/8)

**Date:** 2026-08-01
**Context:** S04-05 (adversarial write-protection tests) landed as commit `8699796` (`tests/integration/test_adversarial_write_protection.py` — 8 tests mirroring the read RLS suite: 6 table write fail-closed paths, tenant_id column rejection, SELECT FOR UPDATE). Initial records close (`029a17a`) incorrectly labeled validation **not validated**. Security/QA Docker evidence: `docker compose exec backend python -m pytest tests/integration/test_adversarial_write_protection.py -v --tb=short` → **8 passed in 4.88s**.
**Alternatives considered:** (a) leave "not validated" until a future CI gate run — rejected: Docker command evidence already exists; (b) record **build validated** from the Docker run and keep **CI GREEN not met** honesty — approved.
**Decision:** Close S04-05 as COMPLETE with validation label **build validated** (Docker pytest 8/8 PASS, 4.88s). Does not claim overall CI workflow green or Phase 0 GO.
**Consequence:** Board S04-05 COMPLETE; program progress absorbs S04-05 into Complete/Closed. Related residual: S04-06 (remaining adversarial coverage) still PENDING. **CI GREEN not met.**
**Status:** Accepted. S04-05 **COMPLETE**. Field-verify label: **build validated** (Docker suite only).

---

### DEC-040 — Sprint 03 story landings recorded; Phase 0 exit remains **NO-GO**

**Date:** 2026-08-01
**Context:** Multiple Sprint 03 / adjacency stories landed on `master` while Phase 0 exit is still blocked on Railway R-14 (S04-04) and incomplete STORY-02-01 Railway AC. Landings: STORY-02-03 JWT audience groundwork `2379e5f` (DONE; consumption deferred); STORY-02-02 server-side middleware `3f4b3c8` (PARTIAL — browser/E2E redirect **not validated**); STORY-03-04 OpenAPI contract framework `623077c` (DONE; pytest execution **not validated** at records close); STORY-02-04 §17.2 relabel `932f722` (DONE, docs-only); Card primitives `9577c98` (Jest-debt related progress only — does not close CI-13 remediation).
**Alternatives considered:** (a) mark Sprint 03 / Phase 0 complete because several stories landed — rejected (Railway R-14 open; CI not green; several validations missing); (b) record honest landings + keep Phase 0 **NO-GO** — approved.
**Decision:** Update `SPRINT_PLAN/Sprint-03.md` and `EXECUTION_DAG.md` to reflect landed SHAs with honest validation labels. Phase 0 exit = **NO-GO**. Railway authorization remains the DEC-DRAFT-RAILWAY-R14-PHASE0 package (not Accepted).
**Consequence:** Sprint 03 partial progress recorded without overclaiming GO. Board progress separate (Sprint 05 delivery board). **CI GREEN not met.**
**Status:** Accepted (records only).

---

### DEC-DRAFT-RAILWAY-R14-PHASE0 — Phase 0 exit blocked on Railway R-14 human authorization (S04-04)

**Date:** 2026-08-01
**Context:** R-14 is PARTIALLY CLOSED (local/CI/staging/prod-template remediated per DEC-014/DEC-015); Railway remains the sole open environment, left untouched by explicit prior choice. Stop condition S04-04 blocks Phase 0 GO. Board story S04-04 references "DEC-016," but no Accepted DEC-016 exists yet.
**Alternatives considered (draft):** (A) authorize Railway remediation now per `OPERATIONS_MANUAL.md` §14; (B) formally accept Phase 0 exit without Railway coverage (residual risk; requires DEC-008 carve-out); (C) defer Phase 0 GO indefinitely while continuing local/CI/non-Railway work.
**Decision:** **Superseded** — human authorized **Option A**; see **DEC-016**.
**Consequence:** Historical draft retained; execution + evidence live under DEC-016.
**Status:** **Superseded** by DEC-016.

---

### DEC-016 — Authorize and execute Railway R-14 remediation (Option A); S04-04 CLOSED

**Date:** 2026-08-01
**Context:** Arabic standing approval for Option A. Railway MCP Unauthorized; Ops used Railway CLI on project `responsible-comfort`. Staging first, then production env/role only (no app image promote). Prior probe: `APP_POSTGRES_*` absent; `DATABASE_URL` present; owner role `postgres` on DB `railway`.
**Alternatives considered:** (A) §14 remediation now — accepted; (B) Phase 0 GO with Railway residual — rejected; (C) defer — superseded by A.
**Decision:** Accept Option A. Provision `salesos_app` (NOSUPERUSER NOBYPASSRLS) on Railway staging + production Postgres; set `APP_POSTGRES_USER`/`APP_POSTGRES_PASSWORD` plus `POSTGRES_HOST`/`PORT`/`DB` derived from existing plugin/`DATABASE_URL` components (app password per §14 hex — not committed); bypass-probe PASS both envs; health 200 both envs. Full record: [`docs/program/decisions/DEC-016-RAILWAY-R14-OPTION-A.md`](decisions/DEC-016-RAILWAY-R14-OPTION-A.md).
**Consequence (historical):** S04-04 CLOSED; R-14 Railway Closed; Phase 0 R-14 gate cleared. **Consequence (current, DEC-120):** security-closure consequence **revoked**; S04-04 **REOPENED**; Phase 0 R-14 **NO-GO**. Infra steps (role/env/deploy IDs/health) remain partially VERIFIED. **CI GREEN not met**. Secrets never committed.
**Status:** Accepted (authorization + partial infra). Security closure **CONTRADICTED** — see **DEC-120**.

---

### DEC-086 — Architecture Validation: Phase 0 (DEC-008 / R-14) exit = GO; production GA remains NO-GO

**Date:** 2026-08-01
**Context:** Program Manager / Architecture Validation reassessment after S04-04 CLOSED under DEC-016 Option A at docs tip `7232979` (staging+prod bypass-probe PASS; `APP_POSTGRES_*` set; health 200; no app image promote). Sources: PRODUCTION_PLAN Definition of Done (§3) + Wave gates; `SPRINT_05_DELIVERY_BOARD.md`; DEC-016; ga-engineering-audit `00-EXECUTIVE-SUMMARY.md` (production no-go). Prior DAG framed Phase 0 exit critical path as **S04-04 only** (DEC-040 / DEC-044 records note).
**Alternatives considered:** (a) claim production GO because Railway closed — **rejected** (**CI GREEN not met**; PRODUCTION_PLAN DoD incomplete; audit still production no-go); (b) keep Phase 0 exit NO-GO despite S04-04 CLOSED — **rejected** (named critical-path gate cleared; would contradict DEC-016 consequence); (c) claim **pilot-ready with conditions** for external/product pilot — **rejected** (no soak/browser/GA DoD evidence; CI-08/09 deploy gaps); (d) Phase 0 (DEC-008 RLS/R-14) **GO** + production/external pilot **NO-GO** — **approved** (historical).
**Decision (historical):** Record Phase 0 (DEC-008 tenant-isolation / R-14) exit = **GO**. Production GA = **NO-GO**. External pilot = **NO-GO**.
**Consequence (current, DEC-120):** Phase 0 R-14 **GO withdrawn** after Principal Audit Tier-1 contradicted DEC-016 security closure. Phase 0 (DEC-008 / R-14) exit = **NO-GO** until live AC re-proven. Production GA remains **NO-GO**. **CI GREEN not met.**
**Status:** Accepted historically; **Phase 0 R-14 GO superseded / withdrawn by DEC-120**.

---

### DEC-043 — CI-19 Wave 1 complete: GHA script-injection remediation (`env:` / `process.env`); CI-19 remains OPEN

**Date:** 2026-08-01
**Context:** CI-19 triage (`CI_19_SEMGREP_TRIAGE.md`) scoped Wave 1 as the only READY P0 batch: 8 GitHub Actions injection alerts (`run-shell-injection`×7 + `github-script-injection`×1) in deploy workflows and legacy `sales-os/.github/workflows/run.yml`. Engineering remediated on `master` at `d5c9b57` by moving interpolated `${{ }}` values into `env:` / `process.env` (no scanner disablement, no auth/RBAC weaken).
**Alternatives considered:** (a) close entire CI-19 on Wave 1 land — rejected (Waves 2–5 still REGISTERED: SQL honesty, SHA pins, noise excludes, residual); (b) record Wave 1 COMPLETE only and keep CI-19 IN PROGRESS — approved.
**Decision:** Accept Wave 1 as **COMPLETE** at `d5c9b57`. Update Sprint 05 board + triage Wave 1 section. Do **not** mark CI-19 CLOSED. R-24 remains Open.
**Consequence:** CI-19 stays **IN PROGRESS**. Program Complete/Closed count unchanged (**18/20**). Next waves unchanged. **CI GREEN not met.**
**Status:** Accepted. CI-19 **Wave 1 COMPLETE**; story **OPEN**.

---

### DEC-DRAFT-STORY-02-01-RLS-72 — STORY-02-01 stopped: 72-table AC vs inventory reality

**Date:** 2026-08-01
**Context:** Database Team Alpha STOPPED on STORY-02-01 with evidence (no migration shipped beyond existing 46): policies today = 46 (`ALL_TENANT_TABLES` / `0afbf3e6ae53`); AC target 72 → gap 26; ORM `tenant_id` tables = 55 (9 missing from RLS list); only `company_features` additive-safe; 8 blocked on R-09 (no CREATE TABLE); remainder is Category B join policies (Sprint 04); exact-72 inventory not pinned in code (55+14≈69).
**Alternatives considered (draft):** (A) pull Category B into STORY-02-01 now + settle canonical 72 inventory; (B) split — close STORY-02-01 at 46+`company_features` (47) with revised AC, Category B → Sprint 04, R-09 tables wait on DB-05; (C) block STORY-02-01 until R-09 CREATE TABLE migrations land for the 8 drift tables, then resume.
**Decision:** **Superseded** — human accepted **Option B**; see **DEC-044**.
**Consequence:** Historical stop record retained; execution and revised AC live under DEC-044.
**Status:** **Superseded** by DEC-044.

---

### DEC-044 — STORY-02-01 Option B accepted: revised AC closes at 47 policies

**Date:** 2026-08-01
**Context:** Human accepted Option B (“الخيار B”) from [`DEC-DRAFT-STORY-02-01-RLS-72`](decisions/DEC-DRAFT-STORY-02-01-RLS-72.md). Inventory: 46 live policies; only `company_features` additive-safe (CREATE TABLE in `0002_feature_store`); 8 ORM gaps wait on R-09/DB-05; Category B deferred to Sprint 04; literal 72 not pinned (55+14≈69).
**Alternatives considered:** (A) Category B + exact-72 inventory in STORY-02-01 — rejected; (B) close at 47 with revised AC — accepted; (C) block until eight CREATE TABLE migrations — rejected.
**Decision:** Accept Option B. STORY-02-01 closes under revised AC at **47** policies (46 + `company_features`), **not** literal 72. Category B → Sprint 04. Eight R-09 tables wait on DB-05. Phase 0 remains **NO-GO** until Railway R-14 (separate). Supersedes the draft. Full record: [`docs/program/decisions/DEC-044-STORY-02-01-RLS-OPTION-B.md`](decisions/DEC-044-STORY-02-01-RLS-OPTION-B.md).
**Consequence:** Additive migration `065d1d3a466b` + generator/`POLICY_COUNT` updates authorized. Sprint-03 STORY-02-01 → DONE under revised AC. R-25 → Closed-as-accepted-scope. R-09/DB-05 remain open. **CI GREEN not met.** Phase 0 **NO-GO**.
**Status:** Accepted. STORY-02-01 **DONE** (revised AC).

**Records note (2026-08-01, pointer only — no new architecture):** Human confirmed Option B state. Phase 0 exit **critical path = S04-04 only**; STORY-02-01 stays **CLOSED** (do not reopen). Parallel READY continues: S04-06, CI-20, CI-19 Waves 2–5, CI-16, CI-14, Jest-debt. See `EXECUTION_DAG.md` / `SPRINT_05_DELIVERY_BOARD.md` / `SPRINT_PLAN/Sprint-03.md`.

---

### DEC-045 — S04-06 closed: adversarial RLS remaining suite on master; Docker evidence **build validated** (15/15)

**Date:** 2026-08-01
**Context:** S04-06 (adversarial suite remaining) landed as commit `119df9e` (`tests/integration/test_adversarial_rls_remaining.py` — 7 tables: contacts, company_features, commercial_opportunities, opportunities, tasks, tenant_configs, webhook_subscriptions). S04-01 and S04-05 suites unchanged. Docker evidence: **15/15 PASS**. Adversarial `POLICY_COUNT` remains **47** (DEC-044). RLS inventory was **not** reopened.
**Alternatives considered:** (a) reopen RLS inventory / revise POLICY_COUNT while adding coverage — rejected (DEC-044 stands); (b) close S04-06 as COMPLETE with **build validated** Docker evidence and keep **CI GREEN not met** honesty — approved.
**Decision:** Close S04-06 as COMPLETE with validation label **build validated** (Docker pytest 15/15 PASS). Does not claim overall CI workflow green or Phase 0 GO. Does not reopen STORY-02-01 / RLS inventory.
**Consequence:** Board S04-06 COMPLETE/CLOSED; program progress **19/20**. Residual parallel READY unchanged except S04-06 removed. Phase 0 exit still **NO-GO** (S04-04 only). **CI GREEN not met.**
**Status:** Accepted. S04-06 **COMPLETE**. Field-verify label: **build validated** (Docker suite only).

---

### DEC-046 — CI-20 Phase 1 complete: admin mypy burn-down (34→0); CI-20 remains OPEN

**Date:** 2026-08-01
**Context:** CI-20 (DEC-038) tracks Backend Types remediation after CI run `30670339985` surfaced **308 mypy errors**. Phase 1 targeted module `app/modules/admin` and landed on `master` at `65296174` (`65296174d22fd4bd2881355442bb482d6f2c3dea`) — admin module **34 → 0** mypy errors per the CI list from run `30670339985`; overall expected **~308 → ~274**.
**Alternatives considered:** (a) close entire CI-20 on Phase 1 land — rejected (residual ~274 errors remain; phased story); (b) record Phase 1 COMPLETE only, keep CI-20 OPEN, R-22 mitigating — approved.
**Decision:** Accept Phase 1 as **COMPLETE** at `65296174`. Update Sprint 05 board + R-22. Do **not** mark CI-20 CLOSED. Validation label: **light validated** (host mypy); full Backend Types CI **not** re-run.
**Consequence:** CI-20 stays **IN PROGRESS / OPEN**. Program Complete/Closed count unchanged (**19/20**). R-22 remains Open (mitigating). **CI GREEN not met.**
**Status:** Accepted. CI-20 **Phase 1 COMPLETE**; story **OPEN**.

---

### DEC-047 — CI-20 Phase 2 complete: company mypy burn-down (25→0); CI-20 remains OPEN

**Date:** 2026-08-01
**Context:** CI-20 (DEC-038) tracks Backend Types remediation after CI run `30670339985` surfaced **308 mypy errors**. Phase 1 (DEC-046) cleared `app/modules/admin` (**34 → 0**; overall expected **~308 → ~274**) at `65296174`. Phase 2 targeted module `app/modules/company` and landed on `master` at `01b6a8ae` (`01b6a8aecf46e6fa3d3cc80abe270a2612593474`) — company module **25 → 0** mypy errors; overall expected **~274 → ~249**.
**Alternatives considered:** (a) close entire CI-20 on Phase 2 land — rejected (residual ~249 errors remain; phased story); (b) record Phase 2 COMPLETE only, keep CI-20 OPEN, R-22 mitigating — approved.
**Decision:** Accept Phase 2 as **COMPLETE** at `01b6a8ae`. Update Sprint 05 board + R-22. Do **not** mark CI-20 CLOSED. Validation label: **light validated** (host mypy); full Backend Types CI **not** re-run.
**Consequence:** CI-20 stays **IN PROGRESS / OPEN**. Program Complete/Closed count unchanged (**19/20**). R-22 remains Open (mitigating). **CI GREEN not met.**
**Status:** Accepted. CI-20 **Phase 2 COMPLETE**; story **OPEN**.

---

### DEC-048 — CI-20 Phase 3 complete: entity_resolution mypy burn-down (14→0); CI-20 remains OPEN

**Date:** 2026-08-01
**Context:** CI-20 (DEC-038) tracks Backend Types remediation after CI run `30670339985` surfaced **308 mypy errors**. Phase 1 (DEC-046) cleared `app/modules/admin` (**34 → 0**; overall expected **~308 → ~274**) at `65296174`. Phase 2 (DEC-047) cleared `app/modules/company` (**25 → 0**; overall expected **~274 → ~249**) at `01b6a8ae`. Phase 3 targeted module `app/modules/entity_resolution` and landed on `master` at `e5b4471` (`e5b44715c4d82c21e164805a0ebba024ab1b09cc`) — entity_resolution module **14 → 0** mypy errors; overall expected **~249 → ~235**.
**Alternatives considered:** (a) close entire CI-20 on Phase 3 land — rejected (residual ~235 errors remain; phased story); (b) record Phase 3 COMPLETE only, keep CI-20 OPEN, R-22 mitigating — approved.
**Decision:** Accept Phase 3 as **COMPLETE** at `e5b4471`. Update Sprint 05 board + R-22. Do **not** mark CI-20 CLOSED. Validation label: **light validated** (host mypy); full Backend Types CI **not** re-run.
**Consequence:** CI-20 stays **IN PROGRESS / OPEN**. Program Complete/Closed count unchanged (**19/20**). R-22 remains Open (mitigating). **CI GREEN not met.**
**Status:** Accepted. CI-20 **Phase 3 COMPLETE**; story **OPEN**.

---

### DEC-049 — CI-20 Phase 4 complete: identity mypy burn-down (16→0); CI-20 remains OPEN

**Date:** 2026-08-01
**Context:** CI-20 (DEC-038) tracks Backend Types remediation after CI run `30670339985` surfaced **308 mypy errors**. Phase 1 (DEC-046) cleared `app/modules/admin` (**34 → 0**; overall expected **~308 → ~274**) at `65296174`. Phase 2 (DEC-047) cleared `app/modules/company` (**25 → 0**; overall expected **~274 → ~249**) at `01b6a8ae`. Phase 3 (DEC-048) cleared `app/modules/entity_resolution` (**14 → 0**; overall expected **~249 → ~235**) at `e5b4471`. Phase 4 targeted module `app/modules/identity` (highest remaining hotspot vs revenue_execution 10 / sso 8) and landed on `master` at `4b3a436` (`4b3a43671aa1376f2145fbaf624fd50b8d1dc953`) — identity module **16 → 0** mypy errors; overall expected **~235 → ~219**.
**Alternatives considered:** (a) close entire CI-20 on Phase 4 land — rejected (residual ~219 errors remain; phased story); (b) record Phase 4 COMPLETE only, keep CI-20 OPEN, R-22 mitigating — approved.
**Decision:** Accept Phase 4 as **COMPLETE** at `4b3a436`. Update Sprint 05 board + R-22. Do **not** mark CI-20 CLOSED. Validation label: **light validated** (host mypy); full Backend Types CI **not** re-run.
**Consequence:** CI-20 stays **IN PROGRESS / OPEN**. Program Complete/Closed count unchanged (**19/20**). R-22 remains Open (mitigating). **CI GREEN not met.**
**Status:** Accepted. CI-20 **Phase 4 COMPLETE**; story **OPEN**.

---

### DEC-050 — CI-20 Phase 5 complete: revenue_execution mypy burn-down (10→0); CI-20 remains OPEN

**Date:** 2026-08-01
**Context:** CI-20 (DEC-038) tracks Backend Types remediation after CI run `30670339985` surfaced **308 mypy errors**. Phase 1–4 (DEC-046–049) cleared admin/company/entity_resolution/identity; overall expected **~308 → ~219**. Phase 5 targeted module `app/modules/revenue_execution` and landed on `master` at `7d8126e` (`7d8126eebefce5b26c82f4aa5747ad0c9a38086d`) — revenue_execution module **10 → 0** mypy errors (explicit `str | None` on optional defaults); overall expected **~219 → ~209**.
**Alternatives considered:** (a) close entire CI-20 on Phase 5 land — rejected (residual ~209 errors remain; phased story); (b) record Phase 5 COMPLETE only, keep CI-20 OPEN, R-22 mitigating — approved.
**Decision:** Accept Phase 5 as **COMPLETE** at `7d8126e`. Update Sprint 05 board + R-22. Do **not** mark CI-20 CLOSED. Validation label: **light validated** (host mypy); full Backend Types CI **not** re-run.
**Consequence:** CI-20 stays **IN PROGRESS / OPEN**. Program Complete/Closed count unchanged (**19/20**). R-22 remains Open (mitigating). **CI GREEN not met.**
**Status:** Accepted. CI-20 **Phase 5 COMPLETE**; story **OPEN**.

---

### DEC-051 — CI-16 Slice 1: bump `python-multipart` only (0.0.9 → 0.0.32); CI-16 remains OPEN

**Date:** 2026-08-01
**Context:** R-21 / CI-16 track four `pip-audit` packages. Narrow first slice authorized: remediate `python-multipart` only (PYSEC multipart DoS advisories; fix floor ≥0.0.27). Poetry caret `^0.0.9` had pinned the lock to `<0.0.10`. Explicitly out of slice: `strawberry-graphql`, `starlette`, `ecdsa`.
**Alternatives considered:** (a) bump all four R-21 packages in one commit — rejected (blast radius; strawberry/starlette need separate compatibility review); (b) narrow multipart-only slice, keep CI-16 OPEN — approved.
**Decision:** Accept Slice 1 as **COMPLETE** at `1e73a2f` (`1e73a2f92000be74f8d6be8ddccb2b9daeadb010`). Constraint `python-multipart = ">=0.0.27,<0.1.0"`; lock **0.0.32**. Do **not** mark CI-16 CLOSED. Validation: **light validated** (`poetry update python-multipart`; import `multipart` + `app.main` → FastAPI). No security-gate weakening.
**Consequence:** CI-16 moves **BACKLOG → IN PROGRESS**. R-21 status **Open — mitigating**. Residual packages still fail `pip-audit --strict`. Program Complete/Closed count unchanged (**19/20**). **CI GREEN not met.**
**Status:** Accepted. CI-16 **Slice 1 COMPLETE**; story **OPEN**.

---

### DEC-052 — CI-16 Slice 2 STOP: starlette bump blocked on FastAPI/pydantic cascade; CI-16 remains OPEN

**Date:** 2026-08-01
**Context:** CI-16 Slice 2 authorized a narrow `starlette` bump (do **not** bump strawberry/ecdsa; do **not** re-bump `python-multipart`) to a version that satisfies `pip-audit` while remaining compatible with the FastAPI pin in `salesos/backend/pyproject.toml`. Current lock: **fastapi 0.111.1**, **starlette 0.37.2** (via FastAPI `starlette>=0.37.2,<0.38.0`). Project pins: `fastapi = "^0.111"` (Poetry → `>=0.111,<0.112`), `pydantic = ">=2.7,<2.9"`. No further `0.37.x` releases exist after 0.37.2.
**Evidence (advisory fixed floors):** PYSEC-2026-1943 → **0.40.0**; PYSEC-2026-1941 → **0.47.2**; PYSEC-2026-161 → **1.0.1**; PYSEC-2026-2280/2281 → **1.1.0**; PYSEC-2026-248 → **1.3.0**; PYSEC-2026-249 → **1.3.1**. Clearing **all** current starlette `pip-audit` findings requires **starlette ≥ 1.3.1**.
**Compatibility wall:** FastAPI `0.111.x` admits only `starlette <0.38.0` — no patched candidate. Expanding FastAPI alone is insufficient without a dedicated cascade: e.g. `0.115.12` still caps starlette `<0.47.0`; `0.118–0.128` can reach `0.47.2` (clears 1941/1943 only) but **not** 1.3.1; `0.135+` opens `starlette>=0.46.0` (may resolve to 1.x) and from `0.136+` requires **pydantic ≥ 2.9.0**, which collides with the project `pydantic <2.9` pin. Starlette 1.x also introduces breaking ASGI/lifespan API changes.
**Alternatives considered:** (a) force-pin starlette ≥1.3.1 under FastAPI 0.111 — **impossible** (solver conflict); (b) silent FastAPI major/minor cascade + pydantic floor lift in this slice — **rejected** (blast radius; stop-rule); (c) STOP Slice 2, keep CI-16 OPEN, register dedicated FastAPI/starlette modernization follow-on — **approved**.
**Decision:** **STOP** CI-16 Slice 2. Do **not** change `poetry.lock` / FastAPI / starlette / pydantic in this commit. Record blocker; leave CI-16 **IN PROGRESS / OPEN** and R-21 **Open — mitigating** (Slice 1 multipart progress retained). Recommend a dedicated story (or CI-16 Slice 2b with explicit executive scope) for FastAPI ≥0.135 (or later) + pydantic ≥2.9 + starlette ≥1.3.1 with compatibility/regression plan.
**Consequence:** No security-gate green for starlette. Residual R-21 packages: **starlette 0.37.2**, **strawberry-graphql**, **ecdsa**. Program Complete/Closed count unchanged (**19/20**). **CI GREEN not met.** Follow-on modernization program registered as **CI-22** (see **DEC-054**) — **not** part of CI-16 slice work.
**Status:** Accepted. CI-16 **Slice 2 BLOCKED**; story **OPEN**. Pointer: **DEC-052 → CI-22**.

---

### DEC-053 — CI-20 Phase 6 complete: sso mypy burn-down (8→0); CI-20 remains OPEN

**Date:** 2026-08-01
**Context:** CI-20 (DEC-038) tracks Backend Types remediation after CI run `30670339985` surfaced **308 mypy errors**. Phase 1–5 (DEC-046–050) cleared admin/company/entity_resolution/identity/revenue_execution; overall expected **~308 → ~209**. Phase 6 targeted module `app/modules/sso` and landed on `master` at `38127af` (`38127afaff8eda91cd2774175255a21d4e21ca6b`) — sso module **8 → 0** mypy errors (CI hotspot list: `bytes | str` / `HashAlgorithm` annotations + `cast` on `ET.tostring`, `scalar_one_or_none`, `resp.json()`); overall expected **~209 → ~201**.
**Alternatives considered:** (a) close entire CI-20 on Phase 6 land — rejected (residual ~201 errors remain; phased story); (b) record Phase 6 COMPLETE only, keep CI-20 OPEN, R-22 mitigating — approved.
**Decision:** Accept Phase 6 as **COMPLETE** at `38127af`. Update Sprint 05 board + R-22. Do **not** mark CI-20 CLOSED. Validation label: **light validated** (host mypy); full Backend Types CI **not** re-run.
**Consequence:** CI-20 stays **IN PROGRESS / OPEN**. Program Complete/Closed count unchanged (**19/20**). R-22 remains Open (mitigating). **CI GREEN not met.**
**Status:** Accepted. CI-20 **Phase 6 COMPLETE**; story **OPEN**.

---

### DEC-054 — CI-22 registered: FastAPI / Starlette / Pydantic modernization (DEC-052 follow-on); not CI-16 slice work

**Date:** 2026-08-01
**Context:** CI-16 Slice 2 **STOPPED** at `8323c84` (DEC-052): starlette cannot clear `pip-audit` without FastAPI ~0.135+ and pydantic ≥2.9 cascade. Narrow CI-16 slices remain for residual packages that do not require that cascade (`strawberry-graphql`, `ecdsa`); starlette clearance is out of CI-16 slice scope.
**Alternatives considered:** (a) reopen CI-16 Slice 2 / Slice 2b inside CI-16 — rejected (blast radius; violates slice stop-rule); (b) register standalone **CI-22** modernization program with explicit scoped cascade + compatibility/regression plan — approved.
**Decision:** Register standalone story **CI-22 — FastAPI / Starlette / Pydantic modernization program** (P1, owner Backend Lead). Scope: planned cascade to clear starlette `pip-audit` floor (**starlette ≥1.3.1**), requiring FastAPI ≥~0.135 (or later) + pydantic ≥2.9, with compatibility/regression plan. **NOT** part of CI-16 slice work. Evidence anchor: DEC-052 / commit `8323c84`. No package bumps in the registration commit.
**Consequence:** CI-22 **REGISTERED** on the Sprint 05 delivery board. CI-16 remains **IN PROGRESS / OPEN** (Slice 1 retained; Slice 2 BLOCKED; strawberry/ecdsa still CI-16). R-21 updated: **DEC-052 → CI-22**. Program Complete/Closed count unchanged (**19/20**). **CI GREEN not met.**
**Status:** Accepted. CI-22 **REGISTERED** (not started).

---

### DEC-055 — CI-20 Phase 7 complete: app/routers mypy burn-down (44→0); CI-20 remains OPEN

**Date:** 2026-08-01
**Context:** CI-20 (DEC-038) tracks Backend Types remediation after CI run `30670339985` surfaced **308 mypy errors**. Phase 1–6 (DEC-046–050, DEC-053) cleared admin/company/entity_resolution/identity/revenue_execution/sso; overall expected **~308 → ~201**. Phase 7 targeted package `app/routers` (CI hotspot **44** errors across commercial/workflows/copilot/opportunities/source_of_truth/mcp/analytics) and landed on `master` at `802cde5` (`802cde5dbe23b95056ce8301ffa0e8189341895f`) — routers package **44 → 0** mypy errors (annotations, casts for `list?` shadowing from service method named `list`, OpportunityQuery page/page_size mapping, workspace `dict[str, Any]`); overall expected **~201 → ~157**.
**Alternatives considered:** (a) close entire CI-20 on Phase 7 land — rejected (residual ~157 errors remain; phased story); (b) record Phase 7 COMPLETE only, keep CI-20 OPEN, R-22 mitigating — approved.
**Decision:** Accept Phase 7 as **COMPLETE** at `802cde5`. Update Sprint 05 board + R-22. Do **not** mark CI-20 CLOSED. Validation label: **light validated** (host mypy on `app/routers`); full Backend Types CI **not** re-run.
**Consequence:** CI-20 stays **IN PROGRESS / OPEN**. Program Complete/Closed count unchanged (**19/20**). R-22 remains Open (mitigating). **CI GREEN not met.**
**Status:** Accepted. CI-20 **Phase 7 COMPLETE**; story **OPEN**.

---

### DEC-056 — CI-16 Slice 3: bump `strawberry-graphql` only (0.243.1 → 0.323.2); CI-16 remains OPEN

**Date:** 2026-08-01
**Context:** R-21 / CI-16 residual packages after Slice 1 (multipart) and Slice 2 STOP (starlette → CI-22): `strawberry-graphql 0.243.1`, `ecdsa 0.19.2`. Slice 3 authorized a narrow strawberry bump to clear pip-audit advisories without forcing FastAPI/starlette/pydantic majors. Poetry caret `^0.243` had pinned the lock to `<0.244`. Advisory clear-all floor **≥0.315.7** (PYSEC-2026-133/134/1946/2282/2283/2284). Explicitly out of slice: `ecdsa`, starlette/FastAPI/pydantic (CI-22).
**Evidence (compatibility):** strawberry core deps are `graphql-core`, `typing-extensions`, `python-dateutil`, `packaging`, `cross-web` — FastAPI/starlette/pydantic appear only as **extras**. Solver resolved **0.323.2** under `>=0.315.7,<1.0.0` with lock unchanged: **fastapi 0.111.1**, **starlette 0.37.2**, **pydantic 2.8.2**, **python-multipart 0.0.32**, **ecdsa 0.19.2**. New transitive: **cross-web 0.7.0**.
**Alternatives considered:** (a) force FastAPI/starlette cascade with strawberry — rejected (Slice 2 stop-rule; CI-22 owns that); (b) narrow strawberry-only bump, keep CI-16 OPEN — approved.
**Decision:** Accept Slice 3 as **COMPLETE** at `d3f1eef` (`d3f1eeff7f6ac0d5210e14a4f3d3f650b7cca6da`). Constraint `strawberry-graphql = ">=0.315.7,<1.0.0"`; lock **0.323.2**. Do **not** mark CI-16 CLOSED. Validation: **light validated** (`poetry update strawberry-graphql`; import `app.graphql.schema` + GraphQLRouter; `pytest tests/unit/test_graphql.py::test_graphql_schema_introspection` **1 passed**; `pip-audit` export shows **NO strawberry findings** — residual **ecdsa** + **starlette** only). No security-gate weakening.
**Consequence:** CI-16 stays **IN PROGRESS / OPEN**. R-21 **Open — mitigating**. Residual CI-16 package: **ecdsa** (often no fix / out of scope). Starlette remains on **CI-22**. Program Complete/Closed count unchanged (**19/20**). **CI GREEN not met.**
**Status:** Accepted. CI-16 **Slice 3 COMPLETE**; story **OPEN**.

---

### DEC-057 — CI-16 ecdsa disposition: accept residual risk (Option A); CI-16 CLOSED for slice scope

**Date:** 2026-08-01
**Context:** After Slice 1 (multipart @ `1e73a2f`) and Slice 3 (strawberry @ `d3f1eef`), CI-16 residuals were **ecdsa** (PYSEC-2026-1325 / CVE-2024-23342 Minerva; upstream **no planned fix**) and **starlette** (already owned by **CI-22** per DEC-052/DEC-054). Blind ecdsa bump is invalid. Full package: [`docs/program/decisions/DEC-057-CI-16-ECDSA-DISPOSITION.md`](decisions/DEC-057-CI-16-ECDSA-DISPOSITION.md).
**Usage evidence:** JWT paths use **RS256** (`app/modules/identity/jwks.py`, `jwt_algorithm` default) and **HS256** (`sdk/security.py`, webhook PyJWT). Grep: **no** `ES256`/`ES384`/`ES512` and **no** direct `import ecdsa`. `ecdsa` enters only as hard transitive of `python-jose` (lock 0.19.2) despite extras `[cryptography]`.
**Alternatives considered:** (A) accept residual risk + monitor — **approved**; (B) migrate JWT off python-jose to PyJWT/cryptography — deferred (correct hygiene, not clearly small/safe for unattended residual close; touches identity mint/verify); (C) pin/replace dependency path under jose — rejected (hard dep; fork/override risk without call-site migration).
**Decision:** Accept **Option A**. Do **not** bump ecdsa. Do **not** start CI-22. Do **not** implement Option B in this land. Prefer docs-only (no `pip-audit` ignore in this commit; named ignore for PYSEC-2026-1325 may follow under this DEC if authorized separately).
**Consequence:** CI-16 **CLOSED** for slice scope (Slices 1+3 complete; Slice 2 transferred to CI-22; ecdsa accepted residual). R-21 remains **Open — mitigating** (ecdsa accepted + monitor; starlette → CI-22). Program Complete/Closed count **20/21** style update on board (CI-16 added to closed set). **CI GREEN not met** (`pip-audit` still red on ecdsa ± starlette).
**Status:** Accepted. CI-16 **CLOSED** (accepted residual on ecdsa).

---

### DEC-058 — CI-20 Phase 8 complete: app/main.py + sdk/ mypy burn-down; CI-20 remains OPEN

**Date:** 2026-08-01
**Context:** CI-20 (DEC-038) tracks Backend Types remediation after CI run `30670339985` surfaced **308 mypy errors**. Phase 1–7 (DEC-046–050, DEC-053, DEC-055) cleared admin/company/entity_resolution/identity/revenue_execution/sso/routers; overall expected **~308 → ~157**. Phase 8 targeted CI hotspots `app/main.py` (**15**) and `sdk/` (**31**, incl. `sdk/database.py` **10**) and landed on `master` at `3e7fadb` (`3e7fadbd9ee0d6a6eb665c799c123aa36cdf9d07`) — mechanical typing only (`QueuePool` cast, `dict[str, Any]` health checks, `cast`/`assert`/annotations across sdk database/graph/security/cache/outbox/pagination/permissions/queue/vector + PEP 695 → `Generic`). Host light mypy: `app/main.py` **3 → 0**, `sdk/` **33 → 0**; CI-list clearance **15 + 31**; overall expected **~157 → ~111**.
**Alternatives considered:** (a) close entire CI-20 on Phase 8 land — rejected (residual ~111 errors remain; phased story); (b) record Phase 8 COMPLETE only, keep CI-20 OPEN, R-22 mitigating — approved.
**Decision:** Accept Phase 8 as **COMPLETE** at `3e7fadb`. Update Sprint 05 board + R-22. Do **not** mark CI-20 CLOSED. Do **not** start CI-22. Validation label: **light validated** (host mypy on `app/main.py` + `sdk/`); full Backend Types CI **not** re-run.
**Consequence:** CI-20 stays **IN PROGRESS / OPEN**. Program Complete/Closed count unchanged (**20/21**). R-22 remains Open (mitigating). **CI GREEN not met.**
**Status:** Accepted. CI-20 **Phase 8 COMPLETE**; story **OPEN**.

---

### DEC-059 — CI-20 Phase 9 complete: demo_mode mypy burn-down (11→0); CI-20 remains OPEN

**Date:** 2026-08-01
**Context:** CI-20 (DEC-038) tracks Backend Types remediation after CI run `30670339985` surfaced **308 mypy errors**. Phase 1–8 (DEC-046–050, DEC-053, DEC-055, DEC-058) cleared admin/company/entity_resolution/identity/revenue_execution/sso/routers/main+sdk; overall expected **~308 → ~111**. Phase 9 targeted module `app/modules/demo_mode` (host mypy **11** `no-any-return` on JSON getters) and landed on `master` at `821aad5` (`821aad5a5624ffc71e7657d1fb24f9b6330e9a93`) — mechanical typing only (`cast` on `json.load` / `dict.get` list returns; `dict[str, Any]` annotations). Host light mypy: demo_mode **11 → 0**; overall expected **~111 → ~100**.
**Alternatives considered:** (a) close entire CI-20 on Phase 9 land — rejected (residual ~100 errors remain; phased story); (b) record Phase 9 COMPLETE only, keep CI-20 OPEN, R-22 mitigating — approved.
**Decision:** Accept Phase 9 as **COMPLETE** at `821aad5`. Update Sprint 05 board + R-22. Do **not** mark CI-20 CLOSED. Do **not** start CI-22. Do **not** reopen CI-16. Validation label: **light validated** (host mypy on `app/modules/demo_mode`); full Backend Types CI **not** re-run.
**Consequence:** CI-20 stays **IN PROGRESS / OPEN**. Program Complete/Closed count unchanged (**20/21**). R-22 remains Open (mitigating). **CI GREEN not met.**
**Status:** Accepted. CI-20 **Phase 9 COMPLETE**; story **OPEN**.

---

### DEC-060 — CI-20 Phase 10 complete: communication_hub mypy burn-down (11→0); CI-20 remains OPEN

**Date:** 2026-08-01
**Context:** CI-20 (DEC-038) tracks Backend Types remediation after CI run `30670339985` surfaced **308 mypy errors**. Phase 1–9 (DEC-046–050, DEC-053, DEC-055, DEC-058, DEC-059) cleared admin/company/entity_resolution/identity/revenue_execution/sso/routers/main+sdk/demo_mode; overall expected **~308 → ~100** (field-verify `30677025355` **104**). Phase 10 selected largest remaining host hotspot vs boot/database/decision/SSO remnants: `app/modules/communication_hub` (**11**) and landed on `master` at `ca76f9c` (`ca76f9c7830ad1e335bd04a95537aaf1467fa9d0`) — mechanical typing only (`cast` on `resp.json()` / token / rowcount / getattr redirects; `history_id` narrow; `dict[str, Any]` / `Coroutine` annotations; rename fallback emails to clear `no-redef`). Host light mypy: communication_hub **11 → 0**; overall expected **~100 → ~89** (field baseline **104 → ~93**).
**Alternatives considered:** (a) close entire CI-20 on Phase 10 land — rejected (residual ~89 remain; phased story); (b) clear boot or database (each 7) instead — rejected (smaller than communication_hub); (c) record Phase 10 COMPLETE only, keep CI-20 OPEN, R-22 mitigating — approved.
**Decision:** Accept Phase 10 as **COMPLETE** at `ca76f9c`. Update Sprint 05 board + R-22. Do **not** mark CI-20 CLOSED. Do **not** start CI-22. Do **not** reopen CI-16 / Phase 9. Validation label: **light validated** (host mypy on `app/modules/communication_hub`). CI Observer later field-verified Backend Types on `30677381493` (`cbea4be` incl. `ca76f9c`): **93** errors / **0** communication_hub vs prior **104** / **11** — classified **pre-existing** residual; no Phase 10 hub regression; no code fix.
**Consequence:** CI-20 stays **IN PROGRESS / OPEN**. Program Complete/Closed count unchanged (**20/21**). R-22 remains Open (mitigating). **CI GREEN not met.**
**Status:** Accepted. CI-20 **Phase 10 COMPLETE**; story **OPEN**.

---

### DEC-061 — CI-20 Phase 11 complete: work_intelligence mypy burn-down (5→0); CI-20 remains OPEN

**Date:** 2026-08-01
**Context:** CI-20 (DEC-038) tracks Backend Types remediation after CI run `30670339985` surfaced **308 mypy errors**. Phase 1–10 (DEC-046–050, DEC-053, DEC-055, DEC-058–060) cleared admin/company/entity_resolution/identity/revenue_execution/sso/routers/main+sdk/demo_mode/communication_hub; overall expected **~308 → ~89** (field-verify after Phase 10: **93**). Phase 11 targeted module `app/modules/work_intelligence` (**5** errors on CI run `30677025355` / tip corroboration inventory: `float`+`object` on `ACTIVITY_WEIGHTS["hours"]`, untyped `daily_counts`) and landed on `master` at `86b4094` (`86b40948bb21491d7d4c11df0c449086b4a6d010`) — mechanical typing only (`TypedDict` for activity weights; `dict[str, int]` for `daily_counts`). Docker light mypy: `app/modules/work_intelligence` **0** errors (`--no-error-summary`, empty stdout); overall expected **~89 → ~84** (field **93 → ~88**).
**Alternatives considered:** (a) close entire CI-20 on Phase 11 land — rejected (residual ~84 remain; phased story); (b) clear `app/application` (9) or residual sso/entity_resolution hotspots instead — deferred (parallel WIP on boot/database; Phase 10 just landed hub); (c) record Phase 11 COMPLETE only, keep CI-20 OPEN, R-22 mitigating — approved.
**Decision:** Accept Phase 11 as **COMPLETE** at `86b4094`. Update Sprint 05 board + R-22. Do **not** mark CI-20 CLOSED. Do **not** start CI-22. Do **not** reopen CI-16 / Phases 1–10. Validation label: **light validated** (Docker mypy on `app/modules/work_intelligence`). CI Observer field-verified Backend Types on `30677732725` (`77aa7af` incl. `86b4094`; job `91308290962`): **88** errors / **0** work_intelligence vs prior tip `30677457937` (`deab399`): **93** / **5** WI — classified **pre-existing** residual; no Phase 11 work_intelligence regression; no WI code fix. Types SHA `86b4094` had **0** check-runs (superseded by docs tip).
**Consequence:** CI-20 stays **IN PROGRESS / OPEN**. Program Complete/Closed count unchanged (**20/21**). R-22 remains Open (mitigating). **CI GREEN not met.**
**Status:** Accepted. CI-20 **Phase 11 COMPLETE**; story **OPEN**.

---

### DEC-062 — CI-14 planning: frontend major inventory + safe vs STOP; Slice 1 = sharp evidence gate

**Date:** 2026-08-01
**Context:** CI-14 (Frontend Dependency Modernization) is REGISTERED/READY (Sprint 06, DEC-018/019; R-18; dep CI-13/DEC-035). CI-11 closed patch-only (`060c946`); residual **30 high**. Lock on `master`: next **15.5.22**, react **19.2.7**, eslint **9.39.5**, jest **29.7.0**, ts-jest **29.4.12**, sharp **0.34.5**. Host `node_modules` absent this session — no install/audit/bump executed. npm’s historical fix frames include **Next→14.2.35**, **jest→25**, **eslint-config-next→0.2.4** — downgrade/nonsense relative to current pins.
**Alternatives considered:** (a) silent majors / `npm audit --force` now — rejected; (b) invent a patch land without audit evidence — rejected; (c) accept planning inventory + gated slices, no package bumps in this land — approved.
**Decision:** Accept CI-14 **plan** as documented in [`decisions/DEC-062-CI-14-FRONTEND-DEPS-PLAN.md`](decisions/DEC-062-CI-14-FRONTEND-DEPS-PLAN.md). **STOP** without dedicated evidence: Next/React/ESLint/Jest majors, Next downgrade for sharp, audit’s jest→25 / ts-jest→27 / eslint-config-next→0.2.4, `--force`. **Next executable slice (when authorized):** Slice 1 = `sharp ≥0.35.0` override under next 15.5.x only. Do **not** start CI-22; no backend dep bumps; no Railway.
**Consequence:** CI-14 remains **OPEN / READY** (plan Accepted; execution not started). R-18 unchanged (Open). Program Complete/Closed count unchanged (**20/21**). Validation: **not validated** (docs only). **CI GREEN not met.**
**Status:** Accepted. CI-14 **PLAN COMPLETE**; Slice 1 execution recorded in **DEC-063**.

---

### DEC-063 — CI-14 Slice 1 COMPLETE: `overrides.sharp >=0.35.0` under next 15.5.x (no Next downgrade)

**Date:** 2026-08-01
**Context:** DEC-062 authorized Slice 1 as the preferred first executable for CI-14 / R-18 Cluster B (`sharp <0.35.0` / Trivy GHSA-f88m-g3jw-g9cj). npm historically frames next→14.2.35 — **STOP**. Baseline lock: sharp **0.34.5**, next **15.5.22**.
**Alternatives considered:** (a) Next↓14 for audit framing — **STOP**; (b) `npm audit fix --force` — **STOP**; (c) `overrides.sharp >=0.35.0` only + lock refresh under next 15.5.x — approved.
**Decision:** Land Slice 1: `salesos/frontend/package.json` `overrides.sharp` = `>=0.35.0`; refresh `package-lock.json`. Do not bump Next/React/ESLint/Jest. Do not start Slice 2/3, CI-22, backend deps, or Railway.
**Consequence:** Lock resolves **sharp 0.35.3** under **next 15.5.22** (`npm ls sharp`). Unchanged: react **19.2.7**, eslint **9.39.5**, jest **29.7.0**. Narrow check: `npx tsc --noEmit` exit 0; prettier not in frontend deps; full lint/Jest/npm-audit CI **not** re-run. Validation: **light validated**. CI-14 remains **OPEN** (Cluster A / Slice 2–3 pending). R-18 mitigating (sharp floor cleared in lock; toolchain cluster remains). Program Complete/Closed count unchanged (**20/21**). **CI GREEN not met.**
**Status:** Accepted. CI-14 **Slice 1 COMPLETE**; story **OPEN**.

---

### DEC-064 — CI-20 Phase 12 complete: boot/startup + database mypy burn-down (7+7→0); CI-20 remains OPEN

**Date:** 2026-08-01
**Context:** CI-20 (DEC-038) tracks Backend Types remediation after CI run `30670339985` surfaced **308 mypy errors**. Phase 1–11 (DEC-046–050, DEC-053, DEC-055, DEC-058–061) cleared admin/company/entity_resolution/identity/revenue_execution/sso/routers/main+sdk/demo_mode/communication_hub/work_intelligence; overall expected **~308 → ~84** (field-verify after Phase 11: **88**). Phase 12 targeted deferred hotspots `app/boot/startup.py` (**7**) and `app/database.py` (**7**) from the CI-104 / Phase-10 inventory and landed on `master` at `e44b7f3` (`e44b7f3d705dd0252396d84ab6ca8c19ea0d7f3a`) — mechanical typing only (`QueuePool` cast + `AsyncGenerator` return on database; `KafkaEventBus | EventRuntime` annotation; `cast(Redis)` / `cast(EventRuntime|ContextBuilder|PolicyEngine|RecommendationEngine)` on boot getattr paths). Host light mypy (`--follow-imports=silent`): both targets **0** errors; overall expected **~84 → ~70** (field **88 → ~74**). Do **not** touch `work_intelligence` or `app/application` (parallel ownership).
**Alternatives considered:** (a) close entire CI-20 on Phase 12 land — rejected (residual ~70 remain; phased story); (b) clear only one of boot/database — rejected (both feasible in one session); (c) record Phase 12 COMPLETE only, keep CI-20 OPEN, R-22 mitigating — approved.
**Decision:** Accept Phase 12 as **COMPLETE** at `e44b7f3`. Update Sprint 05 board + R-22. Do **not** mark CI-20 CLOSED. Do **not** start CI-22. Do **not** reopen CI-16 / Phases 1–11. Validation label: **light validated** (host mypy on `app/boot/startup.py` + `app/database.py`); full Backend Types CI **not** re-run.
**Consequence:** CI-20 stays **IN PROGRESS / OPEN**. Program Complete/Closed count unchanged (**20/21**). R-22 remains Open (mitigating). **CI GREEN not met.**
**Status:** Accepted. CI-20 **Phase 12 COMPLETE**; story **OPEN**.

---

### DEC-065 — CI-14 Slice 2 STOP: ESLint 9→10 is a silent major; dedicated evidence package required

**Date:** 2026-08-01
**Context:** CI-14 Slice 1 PASS at `435ba5d` (DEC-063: sharp **0.35.3** under next **15.5.22**). DEC-062 defines Slice 2 as ESLint ecosystem major (**eslint 9 → 10** + eslint-config-next aligned to Next 15.5.x) for R-18 Cluster A (`brace-expansion`/`minimatch`). Safe vs STOP matrix already labels ESLint 9→10 **STOP until dedicated slice**. Tip lock: eslint **9.39.5**, eslint-config-next **15.5.22**. Config `salesos/frontend/eslint.config.mjs` uses FlatCompat + `@typescript-eslint/recommended` + inline custom-rules — ESLint 10 is a compat cascade, not a one-line pin. Session contract forbids silent ESLint/React/Jest majors, Next↓14, and `npm audit --force`. npm’s historical Cluster A framing includes nonsense **eslint-config-next→0.2.4**.
**Alternatives considered:** (a) silent eslint 10 + eslint-config-next bump now — **rejected** (silent major; no lint-green evidence package); (b) `npm audit fix --force` / audit downgrade pins — **STOP**; (c) STOP Slice 2, docs-only, keep CI-14 OPEN with Slice 1 retained, recommend dedicated evidence package — **approved**.
**Decision:** **STOP** CI-14 Slice 2. Do **not** change `package.json` / `package-lock.json` for ESLint. Do **not** start Slice 3 / CI-22 / backend deps / Railway. Full package: [`decisions/DEC-065-CI-14-SLICE-2-ESLINT-STOP.md`](decisions/DEC-065-CI-14-SLICE-2-ESLINT-STOP.md). Companion plan §10 updated.
**Consequence:** CI-14 remains **IN PROGRESS / OPEN** (Slice 1 PASS; Slice 2 BLOCKED; Slice 3 pending). R-18 **Open — mitigating** (sharp floor retained; Cluster A unchanged). Program Complete/Closed count unchanged (**20/21**). Validation: **not validated** (docs only). **CI GREEN not met.**
**Status:** Accepted. CI-14 **Slice 2 STOPPED**; story **OPEN**. Next: authorize dedicated Slice 2 evidence package (named eslint 10 + next-aligned eslint-config-next + lint-green gate) before any lock change.

---

### DEC-066 — CI-20 Phase 13 complete: app/application mypy burn-down (9→0); CI-20 remains OPEN

**Date:** 2026-08-01
**Context:** CI-20 (DEC-038) tracks Backend Types remediation after CI run `30670339985` surfaced **308 mypy errors**. Phase 1–12 (DEC-046–050, DEC-053, DEC-055, DEC-058–061, DEC-064) cleared admin/company/entity_resolution/identity/revenue_execution/sso/routers/main+sdk/demo_mode/communication_hub/work_intelligence/boot+database; overall expected **~308 → ~70** (field after Phase 11: **88**; Phase 12 expected field **~74**). Phase 13 targeted `app/application` (**9** errors on CI-104 inventory: `decision_provider` `no-any-return` ×6, `dashboard_aggregator` `BaseException` assignment, `data_quality` `no-any-return`, `router` implicit Optional `Request`) and landed on `master` at `5edb6d6` (`5edb6d61534dc97ebde16d450507338b01167edf`) — mechanical typing only (`cast` on dict/model getters; `isinstance(..., BaseException)` narrow; `Request | None`; `cast(QualitySummary, cached)`). Host light mypy (`--follow-imports=skip` on the four files): **0** errors (exit 0); overall expected **~70 → ~61** (field **~74 → ~65**). Did **not** edit `app/boot/startup.py` or `app/database.py` (Phase 12 ownership).
**Alternatives considered:** (a) close entire CI-20 on Phase 13 land — rejected (residual ~61 remain; phased story); (b) record Phase 13 COMPLETE only, keep CI-20 OPEN, R-22 mitigating — approved.
**Decision:** Accept Phase 13 as **COMPLETE** at `5edb6d6`. Update Sprint 05 board + R-22. Do **not** mark CI-20 CLOSED. Do **not** start CI-22. Do **not** reopen CI-16 / Phases 1–12. Do **not** bump FastAPI. Validation label: **light validated** (host mypy on `app/application` targets); full Backend Types CI **not** re-run.
**Consequence:** CI-20 stays **IN PROGRESS / OPEN**. Program Complete/Closed count unchanged (**20/21**). R-22 remains Open (mitigating). **CI GREEN not met.**
**Status:** Accepted. CI-20 **Phase 13 COMPLETE**; story **OPEN**.

---

### DEC-067 — Jest Stage 3 holdout support package (docs); R-23 remains Open

**Date:** 2026-08-01
**Context:** Stage 3 field verify `30677189129` / `1c33c1b` left **11** failing suites (authoritative). Stale production-contract remediations landed at `4fdc1d8` for §8 #5/#7/#8 (Onboarding, widget.store, analytics) — **light validated** only. Remaining **8** suites are the Stage 3 holdout set; a parallel holdout agent owns those `.test.tsx` files. Program needed a governed inventory + ownership rules so CI-14 / CI-20 / CI-19 agents do not collide.
**Alternatives considered:** (a) edit holdout suites from this program session — rejected (ownership conflict); (b) wait for Stage 3 field verify before documenting — rejected (inventory already known from §8 + `4fdc1d8`); (c) docs-only holdout support package (inventory, ownership, field-verify recipe) — approved.
**Decision:** Accept [`decisions/DEC-067-JEST-STAGE3-HOLDOUT-SUPPORT.md`](decisions/DEC-067-JEST-STAGE3-HOLDOUT-SUPPORT.md). Record H1–H8 in `JEST_BASELINE.md` §9. Expected next field ceiling **≤8**. Do **not** close Jest-debt / R-23. Do **not** start CI-14 Slice 3 (Jest major). Do **not** claim Stage 3 green.
**Consequence:** Jest-debt stays **READY / PARALLEL**. R-23 **Open — mitigating**. Program Complete/Closed count unchanged (**20/21**). Validation: **not validated** (docs only). **CI GREEN not met.**
**Status:** Accepted. Stage 3 holdout **support COMPLETE** (docs); holdout **code** remains OPEN under Frontend Lead.

---

### DEC-068 — CI-20 Phase 14 complete: SSO remnant mypy burn-down (11→0); CI-20 remains OPEN

**Date:** 2026-08-01
**Context:** CI-20 (DEC-038) tracks Backend Types remediation after CI run `30670339985` surfaced **308 mypy errors**. Phase 1–13 (DEC-046–050, DEC-053, DEC-055, DEC-058–061, DEC-064, DEC-066) cleared admin/company/entity_resolution/identity/revenue_execution/sso-initial/routers/main+sdk/demo_mode/communication_hub/work_intelligence/boot+database/application; overall expected **~308 → ~61** (field after Phase 13 expected **~65**). Phase 6 cleared an earlier SSO slice (**8→0**), but CI-104 still listed **11** SSO residuals (`Mapped[str]` vs nullable tokens; `result` reuse typing `User` as `Tenant | None`; `request.client` union-attr on SAML rate-limit keys). Phase 14 targeted those remnants (did **not** redo `app/application` / Phase 13 / DEC-066; did **not** collide with DEC-067 Jest holdout docs) — mechanical typing only (`Mapped[str | None]` for nullable SSO columns; separate `tenant_result`/`user_result`; `request.client.host if request.client else "unknown"`; `cast` on encrypt/decrypt returns). Host light mypy (`--follow-imports=skip` on four SSO targets): **0** errors (exit 0); overall expected **~61 → ~50** (field **~65 → ~54**).
**Alternatives considered:** (a) close entire CI-20 on Phase 14 land — rejected (residual ~50 remain; phased story); (b) clear decision (~5) or `app/startup.py` (~4) instead — rejected (SSO 11 was largest non-application residual); (c) record Phase 14 COMPLETE only, keep CI-20 OPEN, R-22 mitigating — approved.
**Decision:** Accept Phase 14 as **COMPLETE** at 1f14337 (1f1433703bc5802ba106a7618d21e350e25513ca). Update Sprint 05 board + R-22. Do **not** mark CI-20 CLOSED. Do **not** start CI-22. Do **not** reopen CI-16 / Phases 1–13. Do **not** bump FastAPI. Validation label: **light validated** (host mypy on SSO targets). CI Observer field-verified Backend Types on `30679062993` (`1f14337`; job `91312218365`): **54** errors / **0** SSO vs prior tip `30678653664` (`1bf30d2` Phase-13 docs): **65** / **11** SSO — classified **pre-existing** residual; no Phase 14 SSO regression; no SSO code fix. Docs tip `30679120749` (`1aa1d69`; job `91312387818`) and later tip `30679150001` (`b1ec68c`; job `91312497351`) also **54** / **0** SSO.
**Consequence:** CI-20 stays **IN PROGRESS / OPEN**. Program Complete/Closed count unchanged (**20/21**). R-22 remains Open (mitigating). Field residual **54** (non-SSO). **CI GREEN not met.**
**Status:** Accepted. CI-20 **Phase 14 COMPLETE**; story **OPEN**. Field-verify recorded.

---

### DEC-069 — CI-19 Wave 3 SHA-pin COMPLETE: pin all root GHA Actions to commit SHAs; CI-19 remains OPEN

**Date:** 2026-08-01
**Context:** CI-19 triage (`CI_19_SEMGREP_TRIAGE.md`) scoped Wave 3 as supply-chain/infra hardening, led by pinning ~115 `mutable-action-tag` Action refs. Wave 1 COMPLETE (`d5c9b57` / DEC-043). Wave 2 SQL honesty rewrite was user-aborted and is **not** authorized to execute now — skipped/deferred. Program preferred Wave 3 SHA pins. Engineering pinned every `uses:` ref in `.github/workflows/{security-scan,ci,docker-smoke,deploy,deploy-staging,deploy-production}.yml` and `sales-os/.github/workflows/run.yml` to full 40-char commit SHAs (115 replacements). Floating `aquasecurity/trivy-action@master` pinned to the same `v0.29.0` commit already used in `deploy-production.yml`. Semgrep `sast-scan` severity flags and SARIF upload path **unchanged** (no gate weaken, no finding suppression).
**Alternatives considered:** (a) close entire CI-19 on SHA-pin land — rejected (Wave 2 deferred; Wave 3 residual K8s/Docker/TF + Waves 4–5 remain); (b) pin only `security-scan.yml` — rejected (same mechanical risk class across all workflows; full pin clears the 115-tag backlog in-repo); (c) record Wave 3 SHA-pin COMPLETE only, keep CI-19 OPEN, R-24 mitigating — approved.
**Decision:** Accept Wave 3 **SHA-pin slice** as **COMPLETE** at `556304d` (`556304d55f87857e23d115230c09706ee2e0e3dc`). Update Sprint 05 board + triage + R-24. Do **not** mark CI-19 CLOSED. Do **not** execute Wave 2 now. Do **not** weaken Semgrep. Next executable slice: Wave 3 residual (K8s `securityContext` / Dockerfile USER / Terraform encryption) or Wave 4 path excludes. **Honesty:** commit `556304d` also included 6 incidental FE Jest test file edits that rode along from a parallel dirty index — not part of Wave 3 scope.
**Consequence:** CI-19 stays **IN PROGRESS / OPEN**. Program Complete/Closed count unchanged (**20/21**). R-24 remains Open (mitigating). Validation: **light validated** (local inventory — 0 mutable tags in scoped workflows; field Code Scanning closure **not** yet re-verified). **CI GREEN not met.**
**Status:** Accepted. CI-19 **Wave 3 SHA-pin COMPLETE** at `556304d`; story **OPEN**.

---

### DEC-070 — CI-20 Phase 16 complete: app/startup.py mypy burn-down (4→0); CI-20 remains OPEN

**Date:** 2026-08-01
**Context:** CI-20 (DEC-038) tracks Backend Types remediation after CI run `30670339985` surfaced **308 mypy errors**. Phase 1–14 (DEC-046–050, DEC-053, DEC-055, DEC-058–061, DEC-064, DEC-066, DEC-068) cleared admin/company/entity_resolution/identity/revenue_execution/sso(+remnants)/routers/main+sdk/demo_mode/communication_hub/work_intelligence/boot+database/application; overall expected **~308 → ~50** (field after Phase 14 expected **~54**). Parallel Phase 15 work targeted other residuals; this phase cleared `app/startup.py` (**4** on CI-104: `KafkaEventBus`/`EventRuntime` assignment; `Redis | None` to `SdkCacheService`; `KafkaEventBus` to `FeatureStore`/`DecisionEngine`; `async_sessionmaker` to `PostgresFeatureStoreRepository`) — mechanical typing only (`KafkaEventBus | EventRuntime` annotation; `cast(Redis)`; `cast(EventRuntime)`; `async_session()` held as `_fs_repo_session`). Did **not** redo SSO (Phase 14 / DEC-068) or touch `app/modules/decision` (parallel ownership). Host light mypy (`--follow-imports=skip` and `silent` on `app/startup.py`): **0** errors (exit 0); overall expected **~50 → ~46** (field **~54 → ~50**).
**Alternatives considered:** (a) close entire CI-20 on Phase 16 land — rejected (residual ~46 remain; phased story); (b) clear `decision` (~5) instead — rejected (prefer `app/startup.py` to avoid parallel Phase 15 file conflicts); (c) record Phase 16 COMPLETE only, keep CI-20 OPEN, R-22 mitigating — approved.
**Decision:** Accept Phase 16 as **COMPLETE** at `26156df` (`26156dfd3a004e364cd4f414896a3e4f292b8485`). Update Sprint 05 board + R-22. Do **not** mark CI-20 CLOSED. Do **not** start CI-22. Do **not** reopen CI-16 / Phases 1–14. Do **not** bump FastAPI. Validation label: **light validated** (host mypy on `app/startup.py`); full Backend Types CI **not** re-run.
**Consequence:** CI-20 stays **IN PROGRESS / OPEN**. Program Complete/Closed count unchanged (**20/21**). R-22 remains Open (mitigating). **CI GREEN not met.**
**Status:** Accepted. CI-20 **Phase 16 COMPLETE**; story **OPEN**.

---

### DEC-071 — CI-20 Phase 15 complete: sla_monitor + redis_client mypy burn-down (2+3→0); CI-20 remains OPEN

**Date:** 2026-08-01
**Context:** CI-20 residual inventory (CI-104 / be7) still listed pp/metrics/sla_monitor.py (**2** list-item) and pp/common/redis_client.py (**3** has-type / no-any-return). Phase 16 (26156df / DEC-070) cleared pp/startup.py in parallel; Phase 15 lands the sla/redis slice at 7fed3dc — mechanical typing only (remove dual _buf init; annotate _initialized/_redis; cast on Redis GET). Host light mypy (--follow-imports=skip + pyproject): **0** errors. Overall expected **~46 → ~41** (field **~50 → ~45**) after Phase 16 baseline.
**Alternatives considered:** (a) close CI-20 — rejected; (b) fold into Phase 16 — rejected (file ownership race); (c) record Phase 15 COMPLETE, keep CI-20 OPEN — approved.
**Decision:** Accept Phase 15 as **COMPLETE** at 7fed3dc. Update Sprint 05 board + R-22. Do **not** mark CI-20 CLOSED. Do **not** bump FastAPI. Validation: **light validated**.
**Consequence:** CI-20 stays **IN PROGRESS / OPEN**. **CI GREEN not met.**
**Status:** Accepted. CI-20 **Phase 15 COMPLETE**; story **OPEN**.


---

### DEC-072 — CI-14 Slice 2 EXECUTE PASS: ESLint 10.8.0 + eslint-config-next 15.5.22 (Stage 1 lint green)

**Date:** 2026-08-01
**Context:** Standing approval authorized Slice 2 execute after DEC-065 / early peer STOP. Landed eslint **10.8.0** with eslint-config-next **15.5.22** (next **15.5.22** unchanged). Compat: .npmrc legacy-peer-deps=true (not --force); FlatCompat + @eslint/compat; postinstall stub for @rushstack/eslint-patch under ESLint 10.
**Decision:** **PASS** — land package/lock/config. Docker Linux evidence: 
pm ci + 
pm run lint exit 0 + prettier check exit 0. Full package: [decisions/DEC-072-CI-14-SLICE-2-ESLINT-EVIDENCE.md](decisions/DEC-072-CI-14-SLICE-2-ESLINT-EVIDENCE.md). Supersedes earlier DEC-072 STOP note.
**Consequence:** R-18 Cluster A ESLint leg mitigated; Slice 3 Jest still pending. Validation **build validated**. **CI GREEN not met.**
**Status:** Accepted. Slice 2 **COMPLETE**; story **OPEN** (Slice 3).

---

### DEC-073 — CI-22 FastAPI/Starlette/Pydantic plan evidence COMPLETE; no package bump

**Date:** 2026-08-01
**Context:** CI-22 REGISTERED READY (DEC-054). Session contract: prefer evidence/plan land, not silent FastAPI major.
**Decision:** Accept [decisions/DEC-073-CI-22-FASTAPI-STARLETTE-PLAN.md](decisions/DEC-073-CI-22-FASTAPI-STARLETTE-PLAN.md). C0 inventory/plan only. Do **not** bump FastAPI/Starlette/Pydantic in this land.
**Consequence:** CI-22 stays **REGISTERED / READY**. Validation **not validated** (docs). **CI GREEN not met.**
**Status:** Accepted. CI-22 **PLAN COMPLETE**; no code.

---

### DEC-074 — CI-19 Wave 3 residual COMPLETE: K8s securityContext + Dockerfile USER + TF encryption; CI-19 remains OPEN

**Date:** 2026-08-01
**Context:** After Wave 3 SHA-pin COMPLETE (`556304d` / DEC-069), triage residual was 19 Semgrep OSS alerts: 15× `allow-privilege-escalation-no-securitycontext` under `salesos/infra/k8s/`, 2× Dockerfile `missing-user` (`infra/docker/backup`, `infra/docker/monitoring/alertmanager`), 2× Terraform encryption (`aws-dynamodb-table-unencrypted`, `aws-secretsmanager-secret-unencrypted` in `main.tf`). Wave 2 SQL honesty remains skipped/deferred (not authorized).
**Alternatives considered:** (a) close entire CI-19 — rejected (Waves 4–5 remain; Wave 2 deferred); (b) force `runAsNonRoot` on postgres/neo4j/kafka/zookeeper/redis — **STOP** (architecture): official images often start as root to fix volume ownership then drop; without UID/`fsGroup` redesign this risks broken PVCs — documented STOP, remediations continue with `allowPrivilegeEscalation: false` only for data stores; (c) record Wave 3 residual COMPLETE, keep CI-19 OPEN — approved.
**Decision:** Accept Wave 3 **residual** as **COMPLETE**. App containers (backend/frontend/celery/migrate) get `allowPrivilegeEscalation: false` + `runAsNonRoot: true` + `capabilities.drop: [ALL]`. Data-store/monitoring/backup containers get `allowPrivilegeEscalation: false`. Backup image `USER postgres`; alertmanager custom image `USER alertmanager` with chowned writable dirs. DynamoDB `server_side_encryption { enabled = true }`; Secrets Manager dedicated CMK with rotation + `kms_key_id`. Do **not** mark CI-19 CLOSED. Do **not** weaken Semgrep. Do **not** execute Wave 2. Next: Wave 4 path excludes or Wave 5 residuals.
**Consequence:** CI-19 stays **IN PROGRESS / OPEN**. Program Complete/Closed count unchanged (**20/21**). R-24 remains Open (mitigating). Validation: **light validated** (local inventory vs Code Scanning alert paths #591–#609; field Code Scanning closure **not** yet re-verified). **CI GREEN not met.**
**Status:** Accepted. CI-19 **Wave 3 residual COMPLETE**; story **OPEN**.

### DEC-075 — CI-19 Wave 3 pin follow-up: bump trivy-action pin v0.29.0 → v0.36.0 (setup-trivy resolve)

**Date:** 2026-08-01
**Context:** Field verify after Wave 3 SHA-pin `556304d` (DEC-069): workflows **start and complete**, but jobs that use `aquasecurity/trivy-action@18f2510...` (v0.29.0) fail at **Set up job** with `Unable to resolve action aquasecurity/setup-trivy@v0.2.2` (tag gone; current tags include v0.2.6+). Evidence: Security Scan tip `30679471680` / pin commit `30679309711` (sbom + secret-scan setup fail) vs pre-pin parent `b1ec68c` Security Scan `30679150021` **all jobs SUCCESS**. CI tip `30679471676` / `30679589732` Secrets Scan setup fail; pre-pin CI `30679150001` Secrets Scan **Set up job SUCCESS** then failed on Trivy findings gate (pre-existing). Other CI reds (Backend Lint/Types, Frontend Lint, pip-audit) match pre-pin `30679150001` — **pre-existing**, not pin-induced.
**Alternatives considered:** (a) revert trivy to floating `@master` — rejected (undoes Wave 3 supply-chain pin); (b) bump pin to `v0.36.0` SHA `a9c7b0f06e461e9d4b4d1711f154ee024b8d7ab8` (pins `setup-trivy@3fb12ec...` / v0.2.6) — approved; (c) document-only without fix — rejected (clear pin breakage).
**Decision:** Replace all `trivy-action@18f2510... # v0.29.0` pins in `ci.yml`, `security-scan.yml`, `deploy-production.yml` with `@a9c7b0f... # v0.36.0`. Do **not** claim CI/Security GREEN. Do **not** weaken Semgrep or Trivy severity gates.
**Consequence:** CI-19 remains **IN PROGRESS / OPEN**. Expected: setup-resolve pin breakage cleared; Security Scan may return to completing jobs; CI Secrets Scan may still fail on **findings** (pre-existing). Validation after push: field run IDs (not yet). **CI GREEN not met.**
**Status:** Accepted. Pin-breakage fix landed; CI-19 **OPEN**.

### DEC-076 — CI-19 Wave 4 COMPLETE: Semgrep path excludes + secrets-doc redact; CI-19 remains OPEN

**Date:** 2026-08-01
**Context:** CI-19 triage Wave 4 scoped honest noise reduction (~30): path excludes for scrapers / root scrape JSON / abandoned `sales-os/` / demo + build scripts — **not** severity-gate weaken. Wave 1 COMPLETE (`d5c9b57`); Wave 3 COMPLETE (`556304d` / DEC-069 + `465c638` / DEC-074); DEC-075 trivy pin follow-up on tip. Wave 2 remains SKIPPED/deferred. Live Code Scanning still showed Bucket C noise (`missing-integrity` under `taqeem_scraper/`, BiDi on root/scraper JSON, demo `asyncpg-sqli`, FE/build `path-join`, root `crm_pipeline.py`) plus `detected-generic-secret` on illustrative hex/`sk-` examples in `PILOT_SECRETS_GUIDE.md`.
**Alternatives considered:** (a) drop Semgrep `--severity WARNING` or blanket `--exclude-rule` — rejected (hides real vulns / no DEC for gate weaken); (b) mass Code Scanning dismiss without path policy — rejected (not durable); (c) repo-root `.semgrepignore` with justified out-of-GA paths + redact secrets guide placeholders — approved.
**Decision:** Accept Wave 4 as **COMPLETE**. Add `.semgrepignore` excluding: `taqeem_scraper/`, `taqeem_facilities.json`, `companies.json`, `recovered_contacts.json`, `sales-os/`, `crm_pipeline.py`, `salesos/backend/demo/`, `salesos/frontend/scripts/`, `salesos/scripts/`. Redact `salesos/docs/PILOT_SECRETS_GUIDE.md` examples to `CHANGE_ME_*` (no live credential claim). Do **not** exclude `salesos/backend` app/runtime or product FE packages. Do **not** mark CI-19 CLOSED. Do **not** execute Wave 2. Do **not** weaken ERROR/WARNING severity or SARIF upload. Next: Wave 5 residual singletons.
**Consequence:** CI-19 stays **IN PROGRESS / OPEN**. Program Complete/Closed count unchanged (**20/21**). R-24 remains Open (mitigating). Validation: **light validated** (path inventory vs triage Bucket C / live alert paths; field Code Scanning closure **not** yet re-verified). **CI GREEN not met.**
**Status:** Accepted. CI-19 **Wave 4 COMPLETE**; story **OPEN**.

**Addendum (DEC-083, 2026-08-01):** Root `.semgrepignore` **replaces** Semgrep built-in defaults (`use_default_semgrepignore = not root_semgrepignore_exists`). DEC-076 Wave 4 excludes alone therefore dropped skips for `tests/`, `node_modules/`, `.venv/`, etc. → Observer-reported live open findings regression **~116 → ~130**. Fix: prepend upstream `default.semgrepignore` blob, then keep Wave 4 path excludes. Severity gates + SARIF upload **unchanged**. Does **not** claim finding-zero or CI GREEN. See **DEC-083**.

---

### DEC-077 — Jest-debt / R-23 CLOSED: Stage 3 field verify 0 failing suites

**Date:** 2026-08-01
**Context:** Sprint 01 Jest-debt (not CI-14) remediations landed via `4fdc1d8` + `5bba606` + `556304d` + Prettier Onboarding gate `11470b1`. Prior §8 field verify `30677189129` / `1c33c1b` left **11** failing suites. Holdout support DEC-067 kept R-23 Open until full Stage 3 re-verify. Authoritative §10 field evidence: GHA run `30679804383` @ `465c638` — Stage 1 Frontend Lint **SUCCESS**; Stage 3 Frontend Unit Tests job `91314523292` **SUCCESS** — **0** failing suites / **196** passed (2278 passed / 1 skipped / 2279 tests). Whole pipeline on that run still **FAILURE** (Backend Lint/Types, pip-audit, Secrets Scan) — out of Jest-debt scope.
**Alternatives considered:** (a) keep R-23 Open/Monitoring despite Stage 3 success — rejected (debt class field-cleared); (b) claim whole-pipeline CI GREEN — rejected (other gates red); (c) close Jest-debt / R-23 on §10 evidence only; do not start CI-14 Slice 3 — approved.
**Decision:** Close Sprint 01 **Jest-debt** and **R-23** as **Closed — Stage 3 field-verified**. Update board, DAG, `JEST_BASELINE.md` §7/§10. Do **not** claim CI GREEN. Do **not** auto-start CI-14 Slice 3 (Jest major).
**Consequence:** R-23 removed from open ≥15 cluster. Stage 3 no longer a Jest-debt blocker. Program Sprint 05 board fraction unchanged (**20/21**). Validation: **build validated** (GHA Stage 3 success). **CI GREEN not met.**
**Status:** Accepted. Jest-debt / R-23 **CLOSED**.

---

### DEC-078 — CI-20 Phase 17 complete: decision mypy burn-down (5→0); CI-20 remains OPEN

**Date:** 2026-08-01
**Context:** CI-20 (DEC-038) tracks Backend Types remediation after CI run `30670339985` surfaced **308 mypy errors**. Phase 1–16 (DEC-046–050, DEC-053, DEC-055, DEC-058–061, DEC-064, DEC-066, DEC-068, DEC-070, DEC-071) cleared admin/company/entity_resolution/identity/revenue_execution/sso(+remnants)/routers/main+sdk/demo_mode/communication_hub/work_intelligence/boot+database/application/startup/sla+redis; overall expected **~308 → ~41** (field after Phase 14 **54**; after Phase 15–16 expected **~45**). DEC-070 deferred `app/modules/decision` (~5 on CI-104 / be7: Literal `confidence_label`/`source`/`risk`/`trend` + `sum` over `float | None`) to parallel ownership. Phase 17 mechanical typing landed in `d5e4de2` (`d5e4de20d4c22207bb4364110bc9936a5e3c1c07`) with the DEC-071–073 docs commit — annotate `ConfidenceLabel` / `DecisionSource` / `RiskLevel` / `Literal['up','down','stable']`; narrow `time_to_execution` before `sum`; `list(result.scores)` for `get_scores`. Did **not** redo SSO / startup / application / Phase 15 files. Host light mypy (`--follow-imports=skip` on decision targets): **0** errors (exit 0). Overall expected **~41 → ~36** (field **~45 → ~41**).
**Alternatives considered:** (a) close entire CI-20 on Phase 17 land — rejected (residual ~36 remain; phased story); (b) clear entity_resolution remnants / graphql / notion_sync instead — deferred (parallel WIP; decision was largest named residual post Phase 14); (c) record Phase 17 COMPLETE only, keep CI-20 OPEN, R-22 mitigating — approved.
**Decision:** Accept Phase 17 as **COMPLETE** at `d5e4de2` (types) with this DEC recording. Update Sprint 05 board + R-22 + EXECUTION_DAG. Do **not** mark CI-20 CLOSED. Do **not** start CI-22. Do **not** reopen Phases 1–16. Do **not** bump FastAPI. Validation label: **light validated** (host mypy on `app/modules/decision`); full Backend Types CI **not** re-run.
**Consequence:** CI-20 stays **IN PROGRESS / OPEN**. Program Complete/Closed count unchanged (**20/21**). R-22 remains Open (mitigating). **CI GREEN not met.**
**Status:** Accepted. CI-20 **Phase 17 COMPLETE**; story **OPEN**.

### DEC-079 — CI-20 Phase 18 complete: entity_resolution remnant mypy burn-down (10→0); CI-20 remains OPEN

**Date:** 2026-08-01
**Context:** CI-20 residual after Phase 17 (DEC-078 decision **5→0**; expected **~36** / field **~41**) still listed `app/modules/entity_resolution` as the largest non-zero CI cluster (**10** on be7 residual inventory post Phases 12–16: DeadLetter `rowcount`/`dict(result.all())`, merge-loop `BaseModel` company_id loss, `merged_into_id` attr-defined, test `source_ids` Optional `in`). Phase 3 had cleared an earlier slice (**14→0**); these are post-CI-104 re-surfaced remnants.
**Alternatives considered:** (a) close CI-20 — rejected (graphql/notion_sync/identity/webhooks residuals remain); (b) clear graphql strawberry stubs instead — rejected (CI-visible graphql cluster is **4**, smaller than entity **10**; host `--follow-imports=skip` strawberry call-arg noise is not the CI body); (c) record Phase 18 COMPLETE only, keep CI-20 OPEN — approved.
**Decision:** Accept Phase 18 as **COMPLETE** at e9f843c (e9f843cdeeafd2b7d655678adbc1bb8f7140eeaa). Mechanical typing only: `cast`+`getattr` for `rowcount`; stage-count dict comprehension; unroll Contact/Branch/License merge selects; `setattr` for non-ORM `merged_into_id`; `cast` on conflict/golden returns; narrow Optional `source_ids` in tests. Do **not** mark CI-20 CLOSED. Do **not** bump FastAPI (CI-22). Do **not** reopen Phases 1–17. Validation: **light validated** (host mypy `app/modules/entity_resolution --follow-imports=skip` **0**). Overall expected **~36 → ~26** (field **~41 → ~31**).
**Consequence:** CI-20 stays **IN PROGRESS / OPEN**. R-22 Open — mitigating. **CI GREEN not met.**
**Status:** Accepted. CI-20 **Phase 18 COMPLETE**; story **OPEN**.

**Addendum (2026-08-01 — field regression):** CI Observer found tip `98bbb21` re-surfaced **3** entity_resolution field errors (shared merge-loop `rel` losing typed `company_id`; classic `Column` assignment on Opportunity `company_id`; direct `merged_into_id` attr-defined). Prior local fix was lost before land. Re-applied mechanical fix: distinct `contact`/`branch`/`license_row` loop vars; `setattr` for Opportunity `company_id` and source `merged_into_id`. Host mypy `app/modules/entity_resolution --follow-imports=skip` **0**. Does **not** reopen Phase 18 COMPLETE; does **not** redo Phase 19 graphql/notion. CI-20 remains OPEN.

### DEC-080 — CI-20 Phase 19 complete: notion_sync + graphql mypy burn-down (4+4→0); CI-20 remains OPEN

**Date:** 2026-08-01
**Context:** After Phase 18 (DEC-079 / `e9f843c`) cleared entity_resolution remnants (**10→0**; expected **~36 → ~26**), next CI-104 / be7 residual clusters were `app/modules/notion_sync` (**4**: `dict` value-type clash on tags; `prop.get` `no-any-return` ×3) and `app/graphql` (**4**: `OpportunityQuery` Optional→`str` for stage/company_id/owner_id; `graphql_ide` Literal). DEC-079 deferred these explicitly.
**Alternatives considered:** (a) close CI-20 — rejected (~18 remain); (b) clear webhooks/employee_360/config instead — rejected (notion+graphql were the next named residual pair post Phase 18); (c) record Phase 19 COMPLETE only, keep CI-20 OPEN — approved.
**Decision:** Accept Phase 19 as **COMPLETE** at `21362f5` (`21362f59f26596287e8eb44eb20ba519b1303b93`). Mechanical typing only (`dict[str, Any]` + `cast(str | None, …)` on Notion props; empty-string defaults for OpportunityQuery filters; `Literal[...] | None` for `graphql_ide_setting`). Do **not** mark CI-20 CLOSED. Do **not** bump FastAPI (CI-22 / DEC-073 plan-only). Do **not** reopen Phases 1–18. Validation: **light validated** (host mypy `--follow-imports=skip` on three targets **0**). Overall expected **~26 → ~18** (field **~31 → ~23**).
**Consequence:** CI-20 stays **IN PROGRESS / OPEN**. R-22 Open — mitigating. **CI GREEN not met.**
**Status:** Accepted. CI-20 **Phase 19 COMPLETE**; story **OPEN**.

### DEC-082 — CI-19 Wave 5 COMPLETE: residual singletons (xml/websocket/urllib/regexp/prototype); CI-19 remains OPEN

**Date:** 2026-08-01
**Context:** CI-19 triage Wave 5 scoped residual audit rules after Waves 1/3/4: use-defused-xml-parse, detect-insecure-websocket, dynamic-urllib-use-detected, detect-non-literal-regexp x3, prototype-pollution-loop x2 (8 Code Scanning alerts). Live open Semgrep after Wave 4 ~130. Wave 2 SQL honesty remains SKIPPED/deferred. Prefer real fixes over ignores; Semgrep ERROR/WARNING gates unchanged.
**Alternatives considered:** (a) close CI-19 on Wave 5 land — rejected (Wave 2 ~108 avoid-sqlalchemy-text + non-Wave-5 residuals remain); (b) path-exclude / nosemgrep the FE packages — rejected (in-product runtime; triage left them in-scope); (c) real code/doc remediations + keep CI-19 OPEN — approved.
**Decision:** Accept Wave 5 as COMPLETE. Remediations: Cobertura regex parse in check_diff_coverage.py (no xml.etree); pentest brief wss://; root website_li_pipeline.py to http.client; forms pattern as RegExp; search-highlight + session test without new RegExp(string); StateRuntime blocks __proto__/constructor/prototype + null-prototype nests. Architecture STOP: none. Do not mark CI-19 CLOSED. Do not execute Wave 2. Do not weaken Semgrep severity/SARIF upload.
**Consequence:** CI-19 stays IN PROGRESS / OPEN. Cleared 8 Wave 5 findings (expected). R-24 Open — mitigating. Validation: light validated (local inventory vs alert paths #567/#582/#622/#583/#586/#627/#584/#585; field Code Scanning closure not yet re-verified). CI GREEN not met.
**Status:** Accepted. CI-19 Wave 5 COMPLETE; story OPEN.

**Addendum (2026-08-01) — alert #836 httpsconnection-detected:** Wave 5 urllib→http.client cleared dynamic-urllib-use-detected but introduced Code Scanning alert #836 (HTTPSConnection + prior CERT_NONE). Field net for Wave 5 was **−5** vs claimed **−8**. Real fix: root website_li_pipeline.py now uses **httpx** with TLS verify on, hostname-only URL construction, and SSRF blocks aligned with salesos/backend/app/modules/webhooks/url_safety.py (private/loopback/link-local/reserved + metadata hostnames). No nosemgrep; Semgrep ERROR/WARNING gates unchanged. Does not close CI-19; does not claim Wave 5 finding-zero.

### DEC-081 — CI-22 Phase 1 COMPLETE: FastAPI/Starlette/Pydantic cascade (starlette ≥1.3.1); CI-22 remains OPEN

**Date:** 2026-08-01
**Context:** Standing approval authorized CI-22 execute after DEC-073 plan. Accidental early pin was reverted (2c44a79). Phase 1 cascade: astapi **0.111.1 → 0.141.1**, direct starlette **0.37.2 → 1.3.1**, pydantic **2.8.2 → 2.13.4**. C3 app fixes for FastAPI 0.14x: move Request ahead of defaulted params in dashboard + knowledge-graph path/search (reject Request | None = None / mid-signature Request = None).
**Alternatives considered:** (a) close CI-22 on Phase 1 — rejected (field pip-audit / full suite not yet green; ecdsa residual remains R-21); (b) rollback on first import failure — rejected after C3 Request fixes restored smoke; (c) record Phase 1 COMPLETE, keep CI-22 OPEN — approved.
**Decision:** Accept Phase 1 as **COMPLETE**. Evidence: host poetry lock → fastapi **0.141.1** / starlette **1.3.1** / pydantic **2.13.4**; rom app.main import app **exit 0**; pytest tests/unit/test_middleware.py **37 passed**. Do **not** mark CI-22 CLOSED. Do **not** weaken security gates. Do **not** touch Railway. Validation: **light validated** (host smoke; full CI pip-audit **not** re-verified this land).
**Consequence:** CI-22 **IN PROGRESS / OPEN**. R-21 mitigating (starlette floor met in lock; ecdsa accepted residual remains). **CI GREEN not met.**
**Status:** Accepted. CI-22 **Phase 1 COMPLETE**; story **OPEN**.

### DEC-083 — CI-19 Wave 4 follow-up: restore Semgrep built-in defaults in root `.semgrepignore`; CI-19 remains OPEN

**Date:** 2026-08-01
**Context:** CI Observer found Wave 4 regression after DEC-076 (`5c27470`): creating a repo-root `.semgrepignore` disables Semgrep's built-in default ignore set. Wave 4 path excludes landed correctly, but `tests/`, `node_modules/`, `.venv/`, `build/`, `dist/`, etc. were no longer skipped → live open Semgrep findings **~116 → ~130**. ERROR/WARNING severity flags and SARIF upload were never intended to change.
**Alternatives considered:** (a) delete root `.semgrepignore` and use only CLI `--exclude` — rejected (loses durable Wave 4 path policy); (b) weaken severity gates / blanket rule suppressions to hide the +14 — rejected; (c) prepend upstream `default.semgrepignore` patterns, then keep DEC-076 Wave 4 excludes — approved.
**Decision:** Restore Semgrep built-in defaults at the top of `.semgrepignore`, document the replace-vs-merge behavior, keep Wave 4 out-of-GA path excludes. Do **not** exclude `salesos/backend` app/runtime or product FE packages. Do **not** weaken `--severity ERROR --severity WARNING` or SARIF upload. Do **not** mark CI-19 CLOSED. Do **not** claim finding-zero GREEN.
**Consequence:** Skip intent returns to **built-ins + Wave 4 paths**. Expected: re-exclude test/vendor/venv noise that caused the ~14 finding bump; Wave 5 (DEC-082) remediations remain. Field Code Scanning recount **not** yet re-verified this land. Validation: **light validated** (ignore inventory vs upstream default blob). **CI GREEN not met.**
**Status:** Accepted. Wave 4 ignore regression **FIXED**; CI-19 **OPEN**.

---

### DEC-084 — CI-20 Phase 20 complete: webhooks + identity hosts + employee_360 mypy burn-down (3+2+3→0); CI-20 remains OPEN

**Date:** 2026-08-01
**Context:** After Phase 19 (DEC-080 / 21362f5) cleared notion_sync+graphql (**8→0**; expected **~26 → ~18**), next CI-104 / be7 residual clusters were pp/modules/webhooks (**3**: InMemory ctor annotations vs Postgres repos; socket_options object→typed), identity router remnants (**2**: 
equest.client.host union-attr on signup/invite), and pp/modules/employee_360 (**3**: signals dict|EmployeeSignals; User.is_active is True ColumnElement; untyped contracts). Also completed Phase-19 leftover graphql_ide_setting: GraphqlIde | None annotation (type alias was unused on tip).
**Alternatives considered:** (a) close CI-20 — rejected (~10 remain); (b) clear config/excel/rules_engine instead — rejected (webhooks+identity were named user candidates; employee_360 was next-largest residual); (c) record Phase 20 COMPLETE only, keep CI-20 OPEN — approved.
**Decision:** Accept Phase 20 as **COMPLETE** at c4fb067 (c4fb06787c081cc75725b84b1d6d40058c02f3fd). Mechanical typing only (Protocol ctor params; _SocketOptions+cast; client host null-narrow; _to_employee_signals; is_(True); list[EmployeePortfolioItem]; GraphqlIde annotation). Do **not** mark CI-20 CLOSED. Do **not** bump FastAPI (CI-22 separate). Do **not** reopen Phases 1–19. Validation: **light validated** (host mypy --follow-imports=skip on six targets **0**). Overall expected **~18 → ~10** (field **~23 → ~15**).
**Consequence:** CI-20 stays **IN PROGRESS / OPEN**. R-22 Open — mitigating. **CI GREEN not met.**
**Status:** Accepted. CI-20 **Phase 20 COMPLETE**; story **OPEN**.

---

### DEC-085 — S04-07 P0 fix regression: `SET LOCAL app.tenant_id = :tenant_id` is not valid Postgres; replaced with `set_config()`

**Date:** 2026-08-01
**Context:** S04-07 (`6bc261c`) parameterized `app/database.py`'s `get_db()` to fix a real SQL-injection risk (f-string-interpolated `tenant_id` into `SET LOCAL app.tenant_id = '{tenant_id}'`), landing `SET LOCAL app.tenant_id = :tenant_id` with a bound parameter. Reviewing this fix, reproduced directly against this project's own Postgres (not assumed): Postgres does **not** accept bind parameters in `SET`/`SET LOCAL`'s value position — `asyncpg.exceptions.PostgresSyntaxError: syntax error at or near "$1"` on every call where `tenant_id` is set. As shipped, this line would raise on **every** tenant-scoped request, not fix anything. Root cause of it shipping unnoticed: no test exercises the real, unmocked `get_db()` with a real tenant_id — the suites cited as validation (adversarial_rls, write_protection, middleware, "52 passed") override `get_db()` via `app.dependency_overrides`, so the actual body of this function was never executed by any passing test. **Also observed independently during this review:** this exact line was silently reverted to the broken `SET LOCAL` form three times within roughly one hour by CI-20 Phase 12's automated mypy pass over `app/database.py` (`e44b7f3`) regenerating the file from a stale base that predated the fix — a real lost-update race, not a one-off.
**Alternatives considered:** (a) leave `SET LOCAL` with the f-string interpolation it replaced (reintroduces the original SQLi — rejected); (b) validate `tenant_id` as a UUID before f-string interpolation into `SET LOCAL` (works, but fragile — depends on every future caller of `get_db()` continuing to only ever pass UUID-shaped tenant IDs, with no structural guarantee); (c) use `SELECT set_config('app.tenant_id', :tenant_id, true)` — a regular function call, which Postgres does parameterize safely, with the `true` third argument giving identical transaction-local scoping to `SET LOCAL` — **approved**, verified directly: a real bind-parameterized call succeeds, `current_setting('app.tenant_id', true)` reads back the value correctly scoped to the transaction (resets after commit/rollback), and an injection-shaped value (`x'; DROP TABLE companies; --`) is stored and read back as an inert literal string, not executed.
**Decision:** (c). `app/database.py`'s `get_db()` now calls `set_config('app.tenant_id', :tenant_id, true)` instead of `SET LOCAL app.tenant_id = :tenant_id`. **Do not revert this to `SET LOCAL` with a bind parameter — it does not work, verified empirically, not a style preference.** If `get_db()` needs further changes, keep the `set_config()` form.
**Consequence:** S04-07's SQL-injection fix is now actually functional rather than merely present in a form that would error on the vector it was meant to close. No test currently exercises this exact code path end-to-end (real `get_db()`, real tenant_id, real request) — `tests/unit/test_owner_engine_isolation.py` is the closest existing test but asserts on the connecting *role*, not on `set_config` succeeding; adding a dedicated regression test for this specific line is recommended follow-up, not done in this entry. Registered as **R-26** in `RISK_REGISTER.md`. Validation: **light validated** (direct isolated reproduction against local Postgres, both the failure and the fix; full backend test suite not re-run end-to-end in this pass because `app/application/dashboard/router.py`'s CI-22 Phase 1 `Request` positioning fix was landing concurrently and blocked pytest collection for part of this session — confirmed resolved separately, unrelated to this fix). **CI GREEN not met.**
**Status:** Accepted and applied. Not yet independently field-verified against a live CI run.

---

### DEC-088 — STORY-02-02 browser/E2E verify attempted; status remains **PARTIAL**

**Date:** 2026-08-01
**Context:** Board listed STORY-02-02 browser/E2E verify as READY after Jest-debt R-23 CLOSED. Middleware code already on master at `3f4b3c8`. Frontend/QA authorized run+push on tip around `f2c7587` / current master.
**Alternatives considered:** (a) close STORY-02-02 on unit evidence alone — rejected (AC requires server-side redirect verified in browser/E2E); (b) claim browser pass without harness execution — rejected; (c) record honest PARTIAL + light-validated units + blockers — approved.
**Decision:** Keep STORY-02-02 **PARTIAL**. Evidence: Jest `middleware-auth` + `session` **14/14 PASS** (**light validated**). Playwright smoke harness present (`playwright.smoke.config.ts` / `e2e/smoke-auth-ui.spec.ts` / `scripts/smoke-ui.ps1`) but **not run** — local FE `node_modules` incomplete (no `.bin` / broken `next`); compose FE/BE not on `:3000`/`:8000` (Docker Desktop API 500 during full up; no frontend image). Full companion: [`decisions/DEC-088-STORY-02-02-BROWSER-VERIFY.md`](decisions/DEC-088-STORY-02-02-BROWSER-VERIFY.md).
**Consequence:** No browser-pass claim. Remains: restore FE tooling or compose frontend, then unauthenticated `/dashboard` → `/login?callbackUrl` probe (+ optional authenticated `smoke-ui.ps1`). **CI GREEN not met.**
**Status:** Accepted (records). Story **PARTIAL** — not CLOSED.


### DEC-090 — CI Stage 5 pip-audit named ignore for DEC-057 ecdsa residual (PYSEC-2026-1325)

**Date:** 2026-08-01
**Context:** CI run 30681284601 @ 2c7587 Stage 5 pip-audit **FAILURE** with sole finding ecdsa 0.19.2 **PYSEC-2026-1325**. Tip e993e83 (CI-22 Phase 1 follow-up) host pip-audit: **NO starlette**; residual ecdsa only. DEC-057 Option A accepted (RS256/HS256; no ES*). Numbering: DEC-088 = STORY-02-02; DEC-089 = contract-tests expansion; this CI policy is **DEC-090**.
**Alternatives considered:** (a) leave Stage 5 red despite accepted residual — rejected (policy mismatch); (b) disable --strict / broad ignore — rejected (silent weaken); (c) Option B PyJWT now — rejected; (d) named --ignore-vuln PYSEC-2026-1325 only + keep --strict — approved.
**Decision:** Land named ignore on CI security-pip-audit only. Package: [docs/program/decisions/DEC-090-CI-PIP-AUDIT-ECDSA-NAMED-IGNORE.md](decisions/DEC-090-CI-PIP-AUDIT-ECDSA-NAMED-IGNORE.md). Update R-21 + board. Do not weaken other audits. Do not claim whole-pipeline CI GREEN.
**Consequence:** Stage 5 pip-audit expected **green**; R-21 Open — mitigating (monitor ecdsa). **CI GREEN not met.**
**Status:** Accepted.

### DEC-092 — CI-20 Phase 21 complete: residual cluster mypy burn-down (~10→0 host); CI-20 remains OPEN

**Date:** 2026-08-01
**Context:** After Phase 20 (DEC-084 / `c4fb067`) cleared webhooks+identity hosts+employee_360 (**8→0**; expected **~18 → ~10**), tip residual clusters (excluding those modules) were `rules_engine` (**2**), `excel_import` service annotation (**1**), `cache` ping `no-any-return` (**1**), `middleware`/`dependencies` `no-any-return` (**2**), `tasks` `feature_result` annotation (**1**), `contact` Company forward-ref (**1**), alembic `0034` Column typing (**1**). Related `Settings()` call-arg + excel `Request=` default already cleared on tip via CI-22 follow-up `4f035dd` (not reopened here).
**Alternatives considered:** (a) close CI-20 on host 0 — rejected (field Backend Types not yet re-verified this land); (b) remount Phase 20 webhooks/identity hosts/employee_360 — rejected (user STOP); (c) record Phase 21 COMPLETE, keep CI-20 OPEN — approved.
**Decision:** Accept Phase 21 as **COMPLETE** at 17c1eee (17c1eee69b4d1851ac6a0dbbe8385b38eb5cf2d7). Mechanical typing only (`bool(...)` / `str(...)` / annotations / `Mapped[Any]` / `list[tuple[str, Column]]`). Do **not** mark CI-20 CLOSED pending field 0. Do **not** bump FastAPI. Do **not** reopen Phases 1–20. Validation: **light validated** (host CI-equivalent `poetry run mypy app/ sdk/ modules/` **0** errors). Overall expected **~10 → ~0** (field **~15 → ~0** pending).
**Consequence:** CI-20 stays **IN PROGRESS / OPEN** until Backend Types field **0**. R-22 Open — mitigating. **CI GREEN not met.**
**Status:** Accepted. CI-20 **Phase 21 COMPLETE**; story **OPEN**.

---

### DEC-093 — JWT audience consumption CLOSED on Owner Platform admin

**Date:** 2026-08-01
**Context:** DEC-091 kept JWT audience consumption OPEN (no router used `decode_owner_*`). User authorized consumption wiring on Owner Platform surfaces without weakening tenant `salesos-api`.
**Alternatives considered:** (a) dual-accept tenant+owner on admin — rejected; (b) wait for full EPIC-04 console — rejected (Platform admin is the consumable surface); (c) patch shared `dependencies.py` only — rejected after parallel overwrite risk.
**Decision:** Close consumption. Add `app/owner_auth.py` (`verify_owner_token` → `decode_owner_access_token`); wire `app/modules/admin` to `require_owner_role_dep`. Tenant `verify_token` unchanged. Package: [decisions/DEC-093-JWT-AUDIENCE-CONSUMPTION-CLOSED.md](decisions/DEC-093-JWT-AUDIENCE-CONSUMPTION-CLOSED.md). Supersedes DEC-091 consumption-OPEN clause.
**Consequence:** Host pytest `tests/unit/test_jwt_audience_split.py` **14/14 PASS** (**light validated**). Owner login mint UX still future. **Production GO not claimed. CI GREEN not met.**
**Status:** Accepted.

---

### DEC-094 ? Contract tests expansion slice 1 (post STORY-03-04)

**Date:** 2026-08-01
**Context:** Board READY track ?Contract tests expansion? after STORY-03-04 framework land (`623077c`) covering only `GET /api/v1/identity/csrf-token`. Backend QA authorized to expand minimally and document next slice. (DEC-089 was reserved in DEC-090 notes for this track; number taken by parallel JWT work as DEC-093 ? this expansion is **DEC-094**.)
**Alternatives considered:** (a) cover `/health`+`/ready` immediately ? deferred (needs DB/cache fixtures); (b) auth-gated domain list first ? deferred; (c) type + contract public no-DB probes `/ping`+`/health/live` ? approved.
**Decision:** Land slice 1: `PingResponse` / `HealthLiveResponse` + OpenAPI HTTP contract tests for `/ping` and `/health/live` (csrf retained). Companion: [`decisions/DEC-094-CONTRACT-TESTS-EXPANSION.md`](decisions/DEC-094-CONTRACT-TESTS-EXPANSION.md).
**Consequence:** Track READY ? **IN PROGRESS**. Host `poetry run pytest tests/contract/test_openapi_contract.py -m contract` **PASS** (**light validated**). Not full API coverage. **CI GREEN not met.**
**Status:** Accepted. Slice 1 landed @ `93a00d7`; slice 2 landed (see addendum).

### DEC-094 addendum - Contract tests expansion slice 2 (/health + /health/ready)

**Date:** 2026-08-01
**Context:** Slice 1 covered no-DB probes. Next authorized slice: readiness/health with honest DB fixtures; 401/422 if time.
**Alternatives considered:** (a) require live Postgres db_session for contract mark - rejected (heavy; host may lack test DB); (b) invent ErrorResponse 401/422 OpenAPI without wiring - rejected (dishonest); (c) AsyncMock get_db / async_session + cache fixture + typed response_model - approved.
**Decision:** Land slice 2: HealthResponse / HealthReadyResponse on GET /health and GET /health/ready; contract_db_client fixture; tests in test_openapi_health_ready.py. Narrow pytest tests/contract/ -m contract. Do **not** edit get_db SET LOCAL (DEC-085). 401/422 deferred to next slice pending honest OpenAPI error docs. Companion: [decisions/DEC-094-CONTRACT-TESTS-EXPANSION.md](decisions/DEC-094-CONTRACT-TESTS-EXPANSION.md).
**Consequence:** Host poetry run pytest tests/contract/ -m contract -> **9 passed**, 31 deselected (**light validated**). Track remains **IN PROGRESS**. **CI GREEN not met.**
**Status:** Accepted. Slice 2 landed; next slice (401/422, auth list) open.

### DEC-094 addendum — Contract tests expansion slice 3 (auth list)

**Date:** 2026-08-01
**Context:** Slice 2 closed health/ready. Next authorized: one high-value authenticated list OpenAPI contract if honestly typed; 401/422 deferred.
**Alternatives considered:** (a) company GET /api/v1/companies via CursorResponse — rejected (data: list untyped items in OpenAPI); (b) invent tighter OpenAPI item schemas for CursorResponse — rejected (dishonest); (c) GET /api/v1/decisions with existing DecisionListResponse / DecisionResponse + honest verify_token + in-memory Decision Center — approved.
**Decision:** Land slice 3: contract test for authenticated GET /api/v1/decisions (cursor fields + typed items). Fixture contract_auth_client overrides verify_token only; attaches DecisionCenterService(InMemoryDecisionCenterRepository). No new response_model. Do **not** edit get_db SET LOCAL (DEC-085). 401/422 still deferred pending honest OpenAPI error docs. Companion: [decisions/DEC-094-CONTRACT-TESTS-EXPANSION.md](decisions/DEC-094-CONTRACT-TESTS-EXPANSION.md).
**Consequence:** Host poetry run pytest tests/contract/ -m contract → **11 passed**, 31 deselected (**light validated**). Code tree landed @ `bdc6fd2` (commit subject raced with parallel CI-19; content is DEC-094 auth-list contract). Track remains **IN PROGRESS**. **CI GREEN not met.**
**Status:** Accepted. Slice 3 landed; next slice (401/422) open.

### DEC-095 — STORY-02-02 browser redirect verify CLOSED

**Date:** 2026-08-01
**Context:** DEC-088 left STORY-02-02 PARTIAL (Jest 14/14; browser not run — FE install/compose blockers). Frontend/QA authorized npm install + push; tip during probe ~`5588bb7`. Middleware code already on master at `3f4b3c8`.
**Alternatives considered:** (a) keep PARTIAL after redirect PASS — rejected (AC met); (b) claim Playwright authenticated smoke without running it — rejected; (c) close on live unauthenticated redirect + public route reachability — approved.
**Decision:** Close STORY-02-02 as **DONE**. Evidence: live `next dev` on `127.0.0.1:3000` — `GET /dashboard` (no cookies) → **307** `/login?callbackUrl=%2Fdashboard`; `GET /login` + `GET /` → **200**. Validation **browser-validated** (redirect AC). Optional `smoke-ui.ps1` not run. Companion: [`decisions/DEC-095-STORY-02-02-BROWSER-VERIFY-CLOSED.md`](decisions/DEC-095-STORY-02-02-BROWSER-VERIFY-CLOSED.md). Supersedes DEC-088 PARTIAL.
**Consequence:** No middleware code change. No `app/database.py` edits. **Production GO not claimed. CI GREEN not met.**
**Status:** Accepted. Story **DONE / CLOSED**.


### DEC-096 — CI-20 Backend Types (MyPy) CLOSED — field 0

**Date:** 2026-08-01
**Context:** DEC-092 recorded Phase 21 COMPLETE at `17c1eee` (host CI-equivalent mypy **0**) but kept CI-20 OPEN pending field Backend Types **0**. Post-land field tip first failed on syntax (`pg_repositories.list_transactions` Expected `:`; fixed `5588bb7`), then DEC-093 audit-router import residuals (`a636c69`; field **1** left: `sdk/events/domain_events.py` `cls.event_type` attr-defined), then `220d91a` used `getattr(cls, "event_type")` for `EVENT_REGISTRY`.
**Alternatives considered:** (a) keep CI-20 OPEN after host 0 without field — rejected (user required field 0); (b) claim whole-pipeline CI GREEN — rejected (other gates still red); (c) close CI-20 on field Types SUCCESS / **0** errors — approved.
**Decision:** Close **CI-20**. Evidence: tip `220d91a` (`220d91aeeb4eafc07174b62e7468b98fbf1002c2`); CI run `30684023356`; Stage 2 Backend Types job `91326366120` **SUCCESS**; mypy `error:` count **0**. Tip corroboration `af4835f` run `30684308678` / job `91327119501` **SUCCESS** (also `844548e` `30684181874`/`91326794076`). Companion: [`decisions/DEC-096-CI-20-BACKEND-TYPES-CLOSED.md`](decisions/DEC-096-CI-20-BACKEND-TYPES-CLOSED.md). DEC-085 `get_db()` remains `set_config` (not `SET LOCAL`). Close **R-22**.
**Consequence:** Backend Types gate green. R-22 **Closed**. Story **CLOSED**. **Whole-pipeline CI GREEN not met.** Production GO not claimed.
**Status:** Accepted. CI-20 **CLOSED**.


### DEC-091 — CI-19 Wave 2 Slice 1 COMPLETE: SQLAlchemy Core honesty (outbox/revenue/store/audit); CI-19 remains OPEN

**Date:** 2026-08-01
**Context:** User authorized Wave 2 after Waves 1/3/4/5. Live Semgrep OSS open **85** (avoid-sqlalchemy-text **72**). Prefer Core over text(); no Semgrep suppress.
**Alternatives considered:** (a) close CI-19 — rejected (~59 text remain); (b) nosemgrep — rejected; (c) Slice 1 Core + keep OPEN — approved.
**Decision:** Accept Wave 2 Slice 1 COMPLETE. Core rewrites: outbox (8), revenue_execution service (3), store (1), audit (1). Expected clear **13**. Do not close CI-19. Do not weaken Semgrep gates.
**Consequence:** CI-19 OPEN. R-24 mitigating. Validation: light validated. CI GREEN not met.
**Status:** Accepted. Wave 2 Slice 1 COMPLETE; story OPEN.

### DEC-097 — CI-19 Wave 2 Slice 2 COMPLETE: data_quality + pgvector_migration Core honesty; CI-19 remains OPEN

**Date:** 2026-08-01
**Context:** After Wave 2 Slice 1 (`844548e` / `5fb7dc5`), densest remainder was `data_quality.py` (8) + `pgvector_migration.py` (8). Tip Lint still red (separate agent). Prefer Core / allowlisted DDL over `sqlalchemy.text`; no Semgrep suppress. DEC-085 `get_db`/`set_config` untouched. `postgres_repo` / `timeline_runtime` remain for a later slice.
**Alternatives considered:** (a) close CI-19 — rejected (~43 text remain after this slice); (b) nosemgrep / severity drop — rejected; (c) Slice 2 Core on densest pair + keep OPEN — approved.
**Decision:** Accept Wave 2 Slice 2 COMPLETE. Companion: [`decisions/DEC-097-CI-19-WAVE2-SLICE2.md`](decisions/DEC-097-CI-19-WAVE2-SLICE2.md). Expected clear **16**. Do not close CI-19. Do not weaken Semgrep gates.
**Consequence:** CI-19 OPEN. R-24 mitigating (Slice 1+2). Validation: **light validated** (AST parse). **CI GREEN not met.**
**Status:** Accepted. Wave 2 Slice 2 COMPLETE; story OPEN.


### DEC-098 - CI Stage 5 Secrets Scan (Trivy) named ignore for DEC-057 ecdsa residual (CVE-2024-23342)

**Date:** 2026-08-01
**Context:** CI run 30684813480 @ c8c1bce Stage 5 Secrets Scan **FAILURE** with sole HIGH ecdsa **CVE-2024-23342** (poetry.lock). Same accepted residual as DEC-090 pip-audit **PYSEC-2026-1325** (different ID namespace). DEC-090 left Trivy red by design; tip Lint+Types SUCCESS. DEC-085 set_config untouched. .trivyignore was gitignored; un-ignore + track after signed DEC.
**Alternatives considered:** (a) leave Secrets Scan red despite accepted residual - rejected (policy mismatch with DEC-090); (b) blanket ignore / severity drop / exit-code 0 - rejected (silent weaken); (c) Option B PyJWT now - rejected; (d) named .trivyignore CVE-2024-23342 only + keep exit-code 1 - approved.
**Decision:** Land named ignore in .trivyignore + wire trivyignores: .trivyignore on CI Secrets Scan Trivy legs; stop gitignoring .trivyignore. Package: [docs/program/decisions/DEC-098-CI-TRIVY-ECDSA-NAMED-IGNORE.md](decisions/DEC-098-CI-TRIVY-ECDSA-NAMED-IGNORE.md). Update R-21 + board. Do not weaken other findings. Do not claim whole-pipeline CI GREEN.
**Consequence:** Stage 5 Secrets Scan expected **green**; R-21 Open - mitigating (monitor ecdsa). **CI GREEN not met.**
**Status:** Accepted.

### DEC-099 — CI-19 Wave 2 Slice 3 COMPLETE: postgres_repo + timeline_runtime Core honesty; CI-19 remains OPEN

**Date:** 2026-08-01
**Context:** After Wave 2 Slice 2 (DEC-097 / 5686d4d), densest remainder was domains/search/engine/postgres_repo.py (6) + 	imeline_runtime (5). Prefer Core over sqlalchemy.text; no Semgrep suppress. DEC-085 get_db/set_config untouched; search timeout uses set_config (not SET LOCAL). DEC-098 number reserved by parallel Trivy ecdsa ignore work — this slice is DEC-099.
**Alternatives considered:** (a) close CI-19 — rejected (~32 text remain after this slice); (b) nosemgrep / severity drop — rejected; (c) Slice 3 Core + keep OPEN — approved.
**Decision:** Accept Wave 2 Slice 3 COMPLETE. Companion: [decisions/DEC-099-CI-19-WAVE2-SLICE3.md](decisions/DEC-099-CI-19-WAVE2-SLICE3.md). Expected clear **11**. Do not close CI-19. Do not weaken Semgrep gates.
**Consequence:** CI-19 OPEN. R-24 mitigating (Slice 1+2+3). Validation: **light validated** (narrow pytest **50 passed**). **CI GREEN not met.**
**Status:** Accepted. Wave 2 Slice 3 COMPLETE; story OPEN.


### DEC-104 — CI-08 / R-17 GHCR 403: prefer org Packages write (A); interim dual CI-GREEN honesty (D); no unauthorized push soften

**Date:** 2026-08-01
**Context:** Stage 6 Backend+Frontend Docker **image builds succeed** on field run `30690622307` @ `927276f` (jobs `91345633439` / `91345633450`); both fail only on **GHCR push 403**. Stage 7 skipped. Stages 1–5 green on tip path. Workflow already declares `packages: write` (ci.yml top-level + Stage 6 jobs; deploy-staging/production same pattern) and uses `GITHUB_TOKEN` — not a missing YAML permission. Triage #15/#16 same class. No alternate registry approved in PRODUCTION_PLAN / staging runbooks (all `ghcr.io/ragheeda-boop/salesos/*`).
**Alternatives considered:** (A) org/account grants GHCR Packages write for Actions — **preferred**; (B) split build-attest vs push / `continue-on-error` — **rejected without separate AC DEC** (would mask publish; Stage 7 ≠ deployable images); (C) alternate registry — **rejected** (not approved in docs); (D) park Stage 6/7 ops-blocked + redefine **CI GREEN (code path)** vs **CI GREEN (full incl. publish)** — **accepted as interim honesty**.
**Decision:** Close CI-08 only via **Option A** (human ops). Adopt **Option D** labels for reporting. Do **not** implement B/C in this land. Do **not** invent credentials or weaken security. Companion: [`decisions/DEC-104-CI-08-GHCR-OPS-OPTIONS.md`](decisions/DEC-104-CI-08-GHCR-OPS-OPTIONS.md).
**Consequence:** CI-08 remains **BLOCKED** (ops). R-17 Open — mitigating (direction set; GHCR leg awaiting field push SUCCESS). Stage 7 remains gated. Production GA / full publish GREEN **not** claimed. Validation: **docs only / not validated** (pipeline).
**Status:** Accepted (program direction). Ops execution pending.


### DEC-105 - CI-19 executive residual-close: non-alembic burn + alembic residual; story CLOSED with residual

**Date:** 2026-08-01
**Context:** Live Semgrep OSS open @ tip a02c8f1 = **19**. Wave 2 PARKED (DEC-103): app text **0**; alembic residual **11**. Non-alembic leftovers: logger x4, prototype #835, triage-doc WS FP #834, DynamoDB CMK #608, GHA workflow secret env #417. Do not churn alembic RLS. DEC-085 untouched. CI-08 GHCR out of scope (DEC-104).
**Alternatives considered:** (a) leave CI-19 OPEN indefinitely with 19 open - rejected (executive residual-close authorized once non-alembic burned); (b) nosemgrep / severity drop - rejected; (c) rewrite alembic RLS for Semgrep - rejected (DEC-103); (d) burn 8 non-alembic + CLOSE with alembic residual - approved.
**Decision:** Accept CI-19 **CLOSED with documented residual**. Companion: [decisions/DEC-105-CI-19-EXECUTIVE-RESIDUAL-CLOSE.md](decisions/DEC-105-CI-19-EXECUTIVE-RESIDUAL-CLOSE.md). Expected clear **8**; remaining accepted **11** alembic. R-24 Closed - mitigating residual. Do not claim finding-zero or whole-pipeline CI GREEN.
**Consequence:** Program Complete/Closed absorbs CI-19. Semgrep gates unchanged. **CI GREEN not met** (CI-08). **Field-verify (2026-08-01):** Security Scan `30693735860` / sast `91352893256` @ `b9062d6` **SUCCESS** - Semgrep CLI **11** blocking; CS open Semgrep **11** alembic-only; burns **8** fixed; unexpected **0**. Validation: **build validated**. Do **not** reopen CI-19.
**Status:** Accepted. CI-19 **CLOSED** with residual (field-verified).





### DEC-130c — DB-05 Slice 5c: additive CREATE for global admin trio

**Date:** 2026-08-01
**Context:** DEC-130 / DEC-130b residual `Detected added table`×3 (`admin_plans`, `admin_feature_flags`, `admin_health_snapshots`) — ORM present, live Postgres **0** rows. Criterion 7.6 stays OPEN; next land = additive CREATE (no RLS).
**Alternatives considered:** (a) metadata-only skip CREATE — rejected (tables absent); (b) ENABLE RLS — rejected (global / no `tenant_id`); (c) idempotent CREATE matching ORM — approved.
**Decision:** Accept **Slice 5c** as Cursor COMPLETE / READY FOR REVIEW. Companion: [`decisions/DEC-130c-DB-05-SLICE-5C-ADMIN-GLOBAL-CREATE.md`](decisions/DEC-130c-DB-05-SLICE-5C-ADMIN-GLOBAL-CREATE.md). Revision `e2b9d46f8a10` (down `d1a8c35e7f09`). Live Docker check @ `e2b9d46f8a10` still **FAILED** exit 255; `add_table` **3→0**. DEC-085 intact. Next: Slice **5d** index/type/nullable.
**Consequence:** Phase 0 remains **24/54**. Criterion **7.6 OPEN**. **Production GO not claimed. CI GREEN not met. Do not claim VERIFIED/CLOSED for 7.6.**
**Status:** Accepted. Criterion **7.6 OPEN** (Slice 5c COMPLETE / READY FOR REVIEW).

### DEC-130b — DB-05 Slice 5b: classify `remove_table` + register false positives

**Date:** 2026-08-01
**Context:** DEC-130 Slice 5a pinned live `alembic check` FAILED with `remove_table`×28 (many metadata false positives). Criterion 7.6 stays OPEN; next land = classify + register FPs only (no DROP).
**Alternatives considered:** (a) DROP the 28 tables — rejected; (b) mega-migration — rejected; (c) classify FP vs orphan KEEP vs true DROP DEC + register FPs — approved.
**Decision:** Accept **Slice 5b** as Cursor COMPLETE / READY FOR REVIEW. Companion: [`decisions/DEC-130b-DB-05-SLICE-5B-METADATA-CLASSIFY.md`](decisions/DEC-130b-DB-05-SLICE-5B-METADATA-CLASSIFY.md). Registered **13** FPs into `Base.metadata` (70→83); marketplace Declarative `metadata` attr → `event_metadata` (column name unchanged); `company_features` on shared Base. Live Docker check @ `d1a8c35e7f09` still **FAILED** exit 255; `remove_table` **28→15** (orphan KEEP residual). No DDL. DEC-085 intact. Next: Slice **5c** admin CREATE trio → **landed as DEC-130c** (`add_table` 3→0).
**Consequence:** Phase 0 remains **24/54**. Criterion **7.6 OPEN**. **Production GO not claimed. CI GREEN not met. Do not claim VERIFIED/CLOSED for 7.6.**
**Status:** Accepted. Criterion **7.6 OPEN** (Slice 5b COMPLETE / READY FOR REVIEW).

### DEC-130 — DB-05 criterion 7.6: live `alembic check` re-baseline + phased plan

**Date:** 2026-08-01
**Context:** Phase 0 Exit Criterion 7.6 (`alembic check` exits clean) remains OPEN after 7.1–7.5 closed. Historic CI-15 “~300 drift lines” was never re-run at tip `d1a8c35e7f09`. Full clean is multi-slice; autogenerate proposes destructive `remove_table`/`remove_column` including metadata false positives and DEC-129 KEEP-adjacent columns.
**Alternatives considered:** (a) claim 7.6 CLOSED — rejected (live check FAILED); (b) mega-migration from autogenerate — rejected (DROP risk); (c) Slice 5a live re-baseline + phased plan — approved.
**Decision:** Accept **Slice 5a** as Cursor COMPLETE / READY FOR REVIEW (plan honesty only). Companion: [`decisions/DEC-130-DB-05-CRITERION-7-6-ALEMBIC-CHECK-PHASED.md`](decisions/DEC-130-DB-05-CRITERION-7-6-ALEMBIC-CHECK-PHASED.md). Live Docker `alembic check` @ head `d1a8c35e7f09` = **FAILED** exit 255 (add_table **3** global admin; remove_table **28**; remove_index **~100**; add_index **~37**; type **4**; remove_column **2** companies KEEP-adjacent). Criterion **7.6 stays OPEN**. DEC-085 intact. No DDL this land. Next: Slice 5b metadata classify → **landed as DEC-130b** (`remove_table` 28→15).
**Consequence:** Phase 0 remains **24/54**. DB-05 residual = **7.6** only (phased). **Production GO not claimed. CI GREEN not met. Do not claim VERIFIED/CLOSED for 7.6.**
**Status:** Accepted. Criterion **7.6 OPEN** (Slice 5a COMPLETE; Slice 5b → DEC-130b).

### DEC-129 — DB-05 companies dead-column KEEP (Phase 0 criterion 7.4)

**Date:** 2026-08-01
**Context:** DEC-122 STOPPED companies DROP (`search_vector` live FTS; `parent_company_id` / feature columns still referenced). Phase 0 Exit Criterion 7.4 still OPEN (“DEC stopped”). Evidence required: `search_vector` FTS preserved + DEC decision recorded. Full `alembic check` remains criterion 7.6.
**Alternatives considered:** (a) DROP “dead” columns this land — rejected (FTS + runtime refs; prod safety unknown); (b) docs-only KEEP without ORM restore — rejected (autogenerate DROP noise); (c) KEEP + restore ORM (no DDL) — approved.
**Decision:** Accept criterion **7.4** as **Cursor COMPLETE** / **READY FOR REVIEW**. Companion: [`decisions/DEC-129-DB-05-COMPANIES-DEAD-COLUMN-KEEP.md`](decisions/DEC-129-DB-05-COMPANIES-DEAD-COLUMN-KEEP.md). Disposition = **KEEP** (no DROP migration; Alembic head unchanged `d1a8c35e7f09`). Restore live columns on `Company` ORM + unit guard. DEC-085 intact. Closed via DEC-129a after Arch+Val PASS.
**Consequence:** Phase 0 criterion **7.4** = READY FOR REVIEW (Architecture PENDING · Validation PENDING). DB-05 residual = **7.6**. **Production GO not claimed. CI GREEN not met.**
**Status:** Accepted. Criterion **CLOSED via DEC-129a**.

### DEC-129a — Orchestrator VERIFIED/CLOSED criterion 7.4 (2026-08-01)

**Context:** Architecture PASS ([architecture review 7.4](65a2e81e-066a-47e0-a991-baab13e48e95)) + Validation PASS ([Validate 7.4](14c3743a-26b8-48c9-8e5b-3d1db3d40832): Docker **4 passed**; head `d1a8c35e7f09`; no DROP; DEC-085 untouched) on land `4aacd6d` / DEC-129.
**Decision:** Execution Orchestrator records criterion **7.4 VERIFIED → CLOSED**. Phase 0 **23/54 → 24/54**. DB Schema Complete **4 → 5**. Residual DB-05 = **7.6** only (stays OPEN). Do **not** push. Do **not** claim Production GO / CI GREEN / `alembic check` clean.
**Consequence:** DB-05 residual = **7.6**. **Production GO not claimed. CI GREEN not met.**
**Status:** Accepted. Criterion **7.4 CLOSED**.

### DEC-128 — Phase 0 criterion 1.5 SAST + dependency scan READY FOR REVIEW (residual)

**Date:** 2026-08-01
**Context:** Phase 0 Exit Criterion 1.5 still checklist-Partial (“pip-audit findings remain”) after CI-02/16/17/18/19/21/22 CLOSED and DEC-057/090/098 ecdsa named ignores. Evidence required: `security-scan.yml` + `ci.yml` security jobs green. `security-scan.yml` pip-audit still used stale `PYSEC-2024-1` and did not poetry-export the lock (DEC-090 noted path mismatch).
**Alternatives considered:** (a) claim CLOSED/finding-zero from board story closes alone — rejected (checklist Partial; security-scan lock parity dishonest); (b) reopen CI-16 for ecdsa / PyJWT now — rejected (DEC-057 Option A); (c) reopen CI-19 for alembic Semgrep churn — rejected (DEC-105); (d) package READY FOR REVIEW + align security-scan pip-audit to DEC-090 — approved.
**Decision:** Accept criterion **1.5** as **Cursor COMPLETE** / **READY FOR REVIEW** with documented residual (ecdsa named ignore + CI-19 Semgrep alembic **11**). Companion: [decisions/DEC-128-CRITERION-1-5-SAST-DEPS-RESIDUAL.md](decisions/DEC-128-CRITERION-1-5-SAST-DEPS-RESIDUAL.md). Align `security-scan.yml` pip-audit to poetry export + `--ignore-vuln PYSEC-2026-1325` + `--strict`. DEC-085 intact. Do **not** mark VERIFIED/CLOSED.
**Consequence:** Phase 0 criterion **1.5** = READY FOR REVIEW (Architecture PENDING · Validation PENDING). Phase 0 remains **22/54** until Orchestrator CLOSE. Adjacent **3.5** not auto-closed. **Production GO not claimed. CI GREEN not met.**
**Status:** Accepted. Criterion **CLOSED CONDITIONAL via DEC-128a**.

### DEC-128a — Orchestrator VERIFIED/CLOSED CONDITIONAL criterion 1.5 (2026-08-01)

**Context:** Architecture PASS ([architecture review 1.5](66828f20-228e-491f-a499-50c808d04c44)) + Validation PASS_CONDITIONAL ([Validate 1.5](ff24e413-5483-4530-a507-dc64c5ed3fda): workflow honesty + named single ignore PASS; pre-land Stage 5 / Security Scan corroboration PASS via gh; post-align Security Scan pip-audit @ `fa266b5` = PENDING push field-verify; DEC-085 untouched) on land `fa266b5` / DEC-128.
**Decision:** Accept **1.5 VERIFIED → CLOSED CONDITIONAL** (same honesty pattern as 2.3 DEC-126). Residual: *post-align Security Scan pip-audit field-verify PENDING until tip containing `fa266b5` is pushed and Security Scan pip-audit SUCCESS with poetry export + 1 ignored (ecdsa)*. Do **not** push. Do **not** claim Production GO / CI GREEN / finding-zero / unconditional CLOSED.
**Consequence:** Phase 0 **22/54 → 23/54**. Security P0 Complete **4 → 5**, Open **1 → 0**. Adjacent **3.5** / **3.8** not auto-closed. **Production GO not claimed. CI GREEN not met.**
**Status:** Accepted. Criterion **1.5 CLOSED CONDITIONAL**.

### DEC-127 — CSRF X-API-Key bypass (Phase 0 criterion 1.3)

**Date:** 2026-08-01
**Context:** Phase 0 Exit Criterion 1.3 (PROD-W5-001 / STORY-01-03) still OPEN on the checklist despite Sprint 01 removal of `api_key_authenticated` CSRF bypass and unit regressions. Evidence required: regression PASS. Stale middleware docstring still claimed API-key skip. DEC-085 get_db/set_config must not regress.
**Alternatives considered:** (a) claim CLOSED from Sprint 01/02 audit notes alone — rejected (checklist ⬜; docstring dishonest; no Phase 0 HTTP contract); (b) reintroduce API-key CSRF waiver for machine clients — rejected (weakens 1.3); (c) docstring honesty + HTTP ASGI contract + package READY FOR REVIEW — approved.
**Decision:** Accept criterion **1.3** as **Cursor COMPLETE** / **READY FOR REVIEW**. Companion: [decisions/DEC-127-CSRF-X-API-KEY-BYPASS.md](decisions/DEC-127-CSRF-X-API-KEY-BYPASS.md). Narrow Docker pytest **11 passed**. DEC-085 intact. Closed via DEC-127a after Arch+Val PASS.
**Consequence:** Phase 0 criterion **1.3** = READY FOR REVIEW (Architecture PENDING · Validation PENDING). Next: Architecture Reviewer sign. **Production GO not claimed. CI GREEN not met.**
**Status:** Accepted. Criterion **CLOSED via DEC-127a**.

### DEC-127a — Orchestrator VERIFIED/CLOSED criterion 1.3 (2026-08-01)

**Context:** Architecture PASS ([architecture review 1.3](ba5c77f8-1391-41db-ac5b-8ac791576e42)) + Validation PASS ([Validate 1.3](c7257393-470f-47ec-8ca5-e60e71dbea95): Docker CSRF suite **11 passed**; DEC-085 untouched) on land `5db0756` / DEC-127.
**Decision:** Execution Orchestrator records criterion **1.3 VERIFIED → CLOSED**. Phase 0 **21/54 → 22/54**.
**Consequence:** Security P0 remaining OPEN: **1.5** only (1.1–1.4 CLOSED). **Production GO not claimed. CI GREEN not met.**
**Status:** Accepted. Criterion **1.3 CLOSED**.

### DEC-125 — Webhook SSRF URL allowlist (Phase 0 criterion 1.2)

**Date:** 2026-08-01
**Context:** Phase 0 Exit Criterion 1.2 (GA-P0-SEC-02 / PROD-W2-002 / STORY-01-02) still OPEN on the checklist despite Sprint 01 / Wave 2 url_safety.py allowlist + pinned delivery. Evidence required: regression PASS + re-verify against Integration Hub caller. DEC-085 get_db/set_config must not regress.
**Alternatives considered:** (a) claim CLOSED from prior Wave 2 notes alone — rejected (checklist open; workflow router mapped SSRF to 500; Slack Hub caller unpinned); (b) rewrite allowlist as static SaaS domain list — rejected (tenant webhooks need public-HTTPS semantics); (c) wire 400 mapping + Slack pin + HTTP/Slack regressions + package READY FOR REVIEW — approved.
**Decision:** Accept criterion **1.2** as **Cursor COMPLETE** / **READY FOR REVIEW**. Companion: [decisions/DEC-125-WEBHOOK-SSRF-URL-ALLOWLIST.md](decisions/DEC-125-WEBHOOK-SSRF-URL-ALLOWLIST.md). Narrow Docker pytest **32 passed**. DEC-085 intact. Closed via DEC-125a after Arch+Val PASS.
**Consequence:** Phase 0 criterion **1.2** = READY FOR REVIEW (Architecture PENDING · Validation PENDING). Next: Architecture Reviewer sign. Residual: staging SSRF pentest still OPEN. **Production GO not claimed. CI GREEN not met.**
**Status:** Accepted. Criterion **CLOSED via DEC-125a**.

### DEC-125a — Orchestrator VERIFIED/CLOSED criterion 1.2 (2026-08-01)

**Context:** Architecture PASS ([architecture review 1.2](35dc3738-8f72-40bc-99c8-ed844cf97397)) + Validation PASS ([Validate 1.2](b99c7a6b-5f10-47b6-bbfa-10a34fc041a2): Docker narrow SSRF suite **32 passed**, 54 deselected; DEC-085 untouched) on land `fd8699d` / DEC-125.
**Decision:** Execution Orchestrator records criterion **1.2 VERIFIED → CLOSED**. Phase 0 **20/54 → 21/54**. Residual: staging SSRF pentest remains OPEN (does not block CLOSED; Architecture accepted).
**Consequence:** Security P0 remaining OPEN: 1.3–1.5 (1.4 already CLOSED). **Production GO not claimed. CI GREEN not met.**
**Status:** Accepted. Criterion **1.2 CLOSED**.

### DEC-124a — Orchestrator VERIFIED/CLOSED criterion 1.1 (2026-08-01)

**Context:** Architecture PASS + Validation PASS (Docker 9/9) on land `31f3aee` / DEC-124.
**Decision:** Execution Orchestrator records criterion **1.1 VERIFIED → CLOSED**. Phase 0 **18/54 → 19/54** (then 20/54 with concurrent 2.3). Residual: R-14 multi-tenant caveat is tracked under 2.3 CONDITIONAL, not reopening 1.1.
**Consequence:** Security P0 remaining OPEN: 1.2 (arch in flight), 1.3–1.5. **Production GO not claimed. CI GREEN not met.**
**Status:** Accepted. Criterion **1.1 CLOSED**.

### DEC-126 — Orchestrator VERIFIED/CLOSED CONDITIONAL criterion 2.3 (2026-08-01)

**Context:** Architecture CONDITIONAL + Validation PASS_CONDITIONAL on Railway remediations A–E @ deploy `9664e9fc` / crumb `84c5163`. Evidence: `salesos_app`, `rolbypassrls=False`, POLICY_COUNT **59**, bare/wrong-tenant=0. Single live tenant → multi-tenant split not re-proven.
**Decision:** Accept **2.3 CLOSED CONDITIONAL** with residual *multi-tenant live split not re-proven*. Do **not** gate on prod alembic tip `d1a8`/67 (7.5 scope). Optional follow-up: second-tenant Slice E on staging for unconditional upgrade.
**Consequence:** Phase 0 **→ 20/54**. Blocked list drops R-14 as hard block. Residual remains documented. **Production GO not claimed. CI GREEN not met.**
**Status:** Accepted. Criterion **2.3 CLOSED CONDITIONAL**.
**Hygiene (2026-08-01):** Prod tip-align `d1a8c35e7f09` / POLICY_COUNT **67** (crumb `c842245`) is 7.5 hygiene only — does **not** reopen 2.3; does **not** upgrade to unconditional CLOSED.

### DEC-124 — Decision Center cross-tenant IDOR (Phase 0 criterion 1.1)

**Date:** 2026-08-01
**Context:** Phase 0 Exit Criterion 1.1 (GA-P0-SEC-01 / PROD-W2-001) still OPEN on the checklist despite Sprint 01 / Wave 2 app-layer fix (`get_decision` / audit / feedback require `(id, tenant_id)`). Evidence required: regression PASS + independent review. DEC-085 `get_db`/`set_config` must not regress.
**Alternatives considered:** (a) claim CLOSED from prior Wave 2 notes alone — rejected (checklist ⬜; no HTTP router proof in suite); (b) re-open and rewrite repo filters — rejected (filters already correct on dedicated `tenant_id` column); (c) add HTTP ASGI contract regression + package READY FOR REVIEW — approved.
**Decision:** Accept criterion **1.1** as **Cursor COMPLETE** / **READY FOR REVIEW**. Companion: [`decisions/DEC-124-DECISION-CENTER-CROSS-TENANT-IDOR.md`](decisions/DEC-124-DECISION-CENTER-CROSS-TENANT-IDOR.md). Narrow Docker pytest **9 passed**. DEC-085 intact. Closed via DEC-124a after Arch+Val PASS.
**Consequence:** Residual: template `tenant_id IS NULL` shared-global out of GA-P0-SEC-01 scope. **Production GO not claimed. CI GREEN not met.**
**Status:** Accepted. Criterion **CLOSED via DEC-124a**.

### DEC-123 — DB-05 Slice 4: ENABLE RLS on deferred-8 (Phase 0 criterion 7.5)

**Date:** 2026-08-01
**Context:** DEC-110 pinned eight Category A deferred tables with CREATE (DEC-113) but no RLS. Category B B1–B7 COMPLETE (DEC-119, POLICY_COUNT 59). DEC-122 closed Slice 3 indexes and STOPPED companies DROP. Phase 0 Exit Criterion 7.5 requires RLS on deferred-8.
**Alternatives considered:** (a) fold deferred-8 into ALL_TENANT_TABLES — rejected; (b) join-style Category B policies — rejected; (c) permissive OR IS NULL — rejected; (d) additive FORCE RLS via generate_policy_sql on DB05_DEFERRED_8_TENANT_TABLES — approved.
**Decision:** Accept Slice 4 as **Cursor COMPLETE** / READY FOR REVIEW. Companion: [`decisions/DEC-123-DB-05-SLICE-4-DEFERRED-8-RLS.md`](decisions/DEC-123-DB-05-SLICE-4-DEFERRED-8-RLS.md). Alembic `d1a8c35e7f09`. Live policy count **67**. Closed via DEC-123a.
**Consequence:** DB-05 residual = 7.4 · 7.6. **Production GO not claimed. CI GREEN not met.**
**Status:** Accepted. Criterion **CLOSED via DEC-123a**.

### DEC-123a — Orchestrator VERIFIED/CLOSED criterion 7.5 (2026-08-01)

**Context:** Architecture PASS + Validation PASS on tip land `578e4f2` (Docker 13/13; `tenant_isolation_%`=67; alembic `d1a8c35e7f09`).
**Decision:** Criterion **7.5 VERIFIED → CLOSED**. Phase 0 **17/54 → 18/54**.
**Consequence:** Residual DB-05 = 7.4 · 7.6. Prior residual “prod may still be on 59 until migrate” **cleared** (2026-08-01 tip-align: alembic `d1a8c35e7f09`, POLICY_COUNT **67**, crumb `c842245`) — does not reopen 7.5; does not upgrade 2.3 CONDITIONAL.
**Status:** Accepted. Criterion **7.5 CLOSED**.

### DEC-122 — DB-05 Slice 3: index rename + nullable triage (additive; companies DROP STOP)

**Date:** 2026-08-01
**Context:** DEC-111 P1 flagged index rename (`ix_rev_*`→`ix_*`), companies ORM-removed columns, and nullable/type deltas after Slice 2 UUID authority CLOSED (DEC-121). Live Docker confirmed `ix_rev_*` on opportunities/tasks, webhook short names, workflow short/long index twins, missing notification composites.
**Alternatives considered:** (a) DROP companies dead columns this land — **rejected STOP** (`search_vector` live FTS; `parent_company_id` still referenced; prod nulls unknown); (b) rename-only + additive CREATE + ORM duplicate cleanup — approved; (c) SET NOT NULL across workflow/notifications — deferred (needs prod null inventory).
**Decision:** Accept Slice 3 **CLOSED**. Companion: [`decisions/DEC-122-DB-05-SLICE-3-INDEX-NULLABLE-TRIAGE.md`](decisions/DEC-122-DB-05-SLICE-3-INDEX-NULLABLE-TRIAGE.md). Alembic `c9f4a21b6e08` (down `b7e2f65a3f07`). No ENABLE RLS on deferred-8. DEC-085 intact.
**Consequence:** DB-05 next = Slice 4+ (companies dead-column dedicated DEC; contacts index naming; governed RLS for deferred-8). **Production GO not claimed. CI GREEN not met. R-14 GO not claimed.**
**Status:** Accepted. Slice 3 **CLOSED**.

### DEC-121 — DB-05 Slice 2: emails/meetings type authority (Alembic UUID wins)

**Date:** 2026-08-01
**Context:** DEC-111 P1 flagged `emails`/`meetings` ORM `String(36)` vs Alembic `0013` `sa.UUID()` for `id`/`tenant_id`/`opportunity_id`. Slice 1 CREATE CLOSED DEC-113. Live Docker DB confirms UUID columns; `tenants`/`companies` PKs are UUID; local row counts 0. Category B B1–B7 COMPLETE (DEC-119); Railway R-14 owned by DEC-120 (out of scope).
**Alternatives considered:** (a) ALTER DDL → VARCHAR(36) to match commercial String cluster — rejected (invasive; fights platform UUID identity); (b) ORM → `UUID(as_uuid=False)` / `Mapped[str]` matching live DDL — approved; (c) `as_uuid=True` cascade into domain — rejected (blast radius); (d) analysis STOP — rejected (safe ORM-only fix).
**Decision:** Accept Slice 2 **CLOSED**. Companion: [`decisions/DEC-121-DB-05-SLICE-2-EMAILS-MEETINGS-UUID.md`](decisions/DEC-121-DB-05-SLICE-2-EMAILS-MEETINGS-UUID.md). **Authority = Alembic/live UUID.** No new Alembic revision; head remains `b7e2f65a3f07`. No ENABLE RLS on deferred-8. DEC-085 intact.
**Consequence:** DB-05 next = Slice 3 (index rename + nullable/type triage). Residual: `opportunity_id` UUID vs `commercial_opportunities.id` VARCHAR (no FK). **Production GO not claimed. CI GREEN not met.**
**Status:** Accepted. Slice 2 **CLOSED**.

### DEC-120 — DEC-016 Railway R-14 security closure CONTRADICTED; S04-04 + R-14 REOPENED

**Date:** 2026-08-01
**Context:** Independent Principal Auditor (agent `ddf9d84e`) Tier-1 evidence contradicts DEC-016 security closure: Railway prod sessions as `postgres` (BYPASSRLS); 0 RLS policies; `salesos_app` SELECT **141221** companies with no tenant; prod health image **3.1.0** (pre-`APP_POSTGRES`); env vars present but runtime not using app role. Deploy IDs match DEC-016. Staging empty-ish + 0 policies = weak PASS support. Tip CI also red (Ruff; CI-08; CI-09). Audit: [`docs/audit/PRINCIPAL_AUDIT_2026-08-01_DEC016_RAILWAY_CI.md`](../audit/PRINCIPAL_AUDIT_2026-08-01_DEC016_RAILWAY_CI.md). DEC-119 reserved for Category B B7 (parallel).
**Alternatives considered:** (a) leave DEC-016 CLOSED despite Tier-1 — rejected (dishonest); (b) reopen S04-04 / R-14 Railway + withdraw Phase 0 GO + encode remediation A–E — approved; (c) claim Production GO — rejected.
**Decision:** Accept **DEC-120**. S04-04 **REOPENED**; R-14 Railway **REOPENED**; Phase 0 (DEC-008 / R-14) = **NO-GO** (DEC-086 GO withdrawn). Dual honesty: env provision ≠ runtime RLS. Remediation READY: A (`5e7023f` wiring) → B (image promote; GHCR alt) → C (alembic) → D (`salesos_app` runtime) → E (bypass-probe + `pg_stat_activity`). **Rotate Postgres passwords** — required human/ops (do not commit secrets). Companion: [`decisions/DEC-120-DEC016-RAILWAY-R14-CONTRADICTED.md`](decisions/DEC-120-DEC016-RAILWAY-R14-CONTRADICTED.md).
**Consequence:** Phase 0 critical path blocked on S04-04 again. STORY-02-01 stays CLOSED. **Production GA = NO-GO.** Prior Phase 0 R-14 GO **withdrawn**. Validation: **docs / light validated**.
**Progress (2026-08-01):** Slice **A VERIFIED**; **B** staging tip image `98bf85bf`; **C DONE** — staging Alembic **`0049` → `b7e2f65a3f07`**, **POLICY_COUNT 59**. **D DONE** — prod deploy **`9664e9fc`** from image tip **`b62252a`**; `/health` **5.1.0-rc1**; `APP_ENGINE salesos_app` / `rolbypassrls=False`; alembic **`0051` → `c9f4a21b6e08`**, POLICY_COUNT **0 → 59**. **E DONE** — bare/wrong-tenant **0** vs owner **141221**; **PASS_WITH_SINGLE_TENANT_CAVEAT** (1 live tenant). **Prod tip RLS align DONE** — alembic **`c9f4a21b6e08` → `d1a8c35e7f09`**, POLICY_COUNT **59 → 67** (owner SSH; image still `b62252a`). This migrate crumb **does not** mark 2.3 VERIFIED/CLOSED. Password rotate still human/ops.
**Status:** Accepted. S04-04 **REOPENED** (A–E evidence landed; executive close pending).

### DEC-119 — Category B Slice B7: admin_role_permissions join RLS (`admin_role_permissions`)

**Date:** 2026-08-01
**Context:** DEC-110 pinned B7 = `admin_role_permissions` via `admin_roles` (`role_id`) with **nullable** parent `tenant_id`. B6 CLOSED DEC-118 (`a6d1e54f2e06`, POLICY_COUNT 58). Category A 47 intact (DEC-044). DEC-085 set_config must not regress. Parent FK confirmed in ORM + `0037` (String(100)=String(100)). Seeded/owner roles often omit tenant_id; Category A already fail-closes those under tenant GUC. Numbering: DEC-120 reserved this slot for parallel B7.
**Alternatives considered:** (a) defer because owner-global roles dominate — rejected (leaves child unprotected while parent is Category A; DEC-110 allowed +1); (b) add permissive `OR p.tenant_id IS NULL` so tenants see global role maps — rejected (cross-tenant leak / weakens isolation); (c) ENABLE RLS on deferred-8 admin billing in same land — rejected (DB-05 / R-09); (d) additive fail-closed join matching parent Category A + adversarial suite — approved.
**Decision:** Accept B7 **CLOSED**. Companion: [`decisions/DEC-119-CATEGORY-B7-ADMIN-ROLE-PERMISSIONS-RLS.md`](decisions/DEC-119-CATEGORY-B7-ADMIN-ROLE-PERMISSIONS-RLS.md). Alembic `b7e2f65a3f07` (down `a6d1e54f2e06`); live `POLICY_COUNT` **59**; `ALL_TENANT_TABLES` remains **47**. **Category B execution track COMPLETE (B1–B7).**
**Consequence:** DAG Category B execution CLOSED. Does **not** restore Phase 0 R-14 GO (DEC-120). Production GA **NO-GO**. **CI GREEN not met**. Validation: **build validated** (Docker `python -m pytest` **5 passed** in 16.84s).
**Status:** Accepted. Slice B7 **CLOSED**. Category B execution **COMPLETE**.

### DEC-118 — Category B Slice B6: webhook-deliveries join RLS (`webhook_deliveries`)

**Date:** 2026-08-01
**Context:** DEC-110 pinned B6 = `webhook_deliveries` via `webhook_subscriptions` (`subscription_id`). B5 CLOSED DEC-117 (`f5c0d43e1d05`, POLICY_COUNT 57). Category A 47 intact (DEC-044). DEC-085 set_config must not regress. Parent FK confirmed in ORM + `0039` (String(36)=String(36)). Deferred-8 `webhook_endpoints` is not the join parent and stays without ENABLE RLS.
**Alternatives considered:** (a) fold B6 into ALL_TENANT_TABLES / reopen STORY-02-01 — rejected; (b) join via deferred `webhook_endpoints` — rejected (wrong parent; DEC-110 inventory); (c) ENABLE RLS on `webhook_endpoints` in same land — rejected (DB-05 / R-09); (d) expand to B7 in same land — rejected (DEC-110 slices); (e) additive join-policy migration + adversarial 1-table suite — approved.
**Decision:** Accept B6 **CLOSED**. Companion: [`decisions/DEC-118-CATEGORY-B6-WEBHOOK-DELIVERIES-RLS.md`](decisions/DEC-118-CATEGORY-B6-WEBHOOK-DELIVERIES-RLS.md). Alembic `a6d1e54f2e06` (down `f5c0d43e1d05`); live `POLICY_COUNT` **58**; `ALL_TENANT_TABLES` remains **47**.
**Consequence:** DAG Category B execution advances B6 CLOSED; B7 READY. Production GA **NO-GO**. **CI GREEN not met**. Validation: **build validated** (Docker `python -m pytest` **5 passed** in 2.98s).
**Status:** Accepted. Slice B6 **CLOSED**.

### DEC-117 — Category B Slice B5: identity-token-children join RLS (`password_reset_tokens`, `refresh_token_families`)

**Date:** 2026-08-01
**Context:** DEC-110 pinned B5 = identity tokens via `users`. B4 CLOSED DEC-116 (`e4b9c32d0c04`, POLICY_COUNT 55). Category A 47 intact (DEC-044). DEC-085 set_config must not regress. Parent FKs confirmed in ORM + `0012` (UUID=UUID). Auth-path: JWT refresh sets tenant GUC; unset GUC fail-closed — no permissive bypass.
**Alternatives considered:** (a) fold B5 into ALL_TENANT_TABLES / reopen STORY-02-01 — rejected; (b) expand to B6 webhook children in same land — rejected (DEC-110 slices); (c) add permissive auth-bypass policies for token_hash lookup without tenant — rejected (weakens isolation); (d) additive join-policy migration + adversarial 2-table suite with auth-path careful checks — approved.
**Decision:** Accept B5 **CLOSED**. Companion: [`decisions/DEC-117-CATEGORY-B5-IDENTITY-TOKEN-CHILDREN-RLS.md`](decisions/DEC-117-CATEGORY-B5-IDENTITY-TOKEN-CHILDREN-RLS.md). Alembic `f5c0d43e1d05` (down `e4b9c32d0c04`); live `POLICY_COUNT` **57**; `ALL_TENANT_TABLES` remains **47**.
**Consequence:** DAG Category B execution advances B5 CLOSED; B6–B7 READY. Production GA **NO-GO**. **CI GREEN not met**. Validation: **build validated** (Docker `python -m pytest` **10 passed** in 5.47s).
**Status:** Accepted. Slice B5 **CLOSED**.

### DEC-116 — Category B Slice B4: decision-center-children join RLS (`decision_center_audits`, `decision_center_feedback`)

**Date:** 2026-08-01
**Context:** DEC-110 pinned B4 = decision-center children via `decision_center_decisions`. B3 CLOSED DEC-115 (`d3f8a21c9b03`, POLICY_COUNT 53). Category A 47 intact (DEC-044). DEC-085 set_config must not regress. Parent FKs confirmed in ORM + `0038`; UUID parent PK vs varchar child FK requires `p.id::text` cast.
**Alternatives considered:** (a) fold B4 into ALL_TENANT_TABLES / reopen STORY-02-01 — rejected; (b) expand to B5 identity children in same land — rejected (DEC-110 slices); (c) additive join-policy migration + adversarial 2-table suite with cast helper — approved.
**Decision:** Accept B4 **CLOSED**. Companion: [`decisions/DEC-116-CATEGORY-B4-DECISION-CENTER-CHILDREN-RLS.md`](decisions/DEC-116-CATEGORY-B4-DECISION-CENTER-CHILDREN-RLS.md). Alembic `e4b9c32d0c04` (down `d3f8a21c9b03`); live `POLICY_COUNT` **55**; `ALL_TENANT_TABLES` remains **47**.
**Consequence:** DAG Category B execution advances B4 CLOSED; B5–B7 READY. Production GA **NO-GO**. **CI GREEN not met**. Validation: **build validated** (Docker `python -m pytest` **9 passed** in 8.89s).
**Status:** Accepted. Slice B4 **CLOSED**.

### DEC-115 — Category B Slice B3: analytics-children join RLS (`analytics_report_executions`, `analytics_report_shares`)

**Date:** 2026-08-01
**Context:** DEC-110 pinned B3 = analytics children via `analytics_reports`. B2 CLOSED DEC-114 (`c221d15f8b02`, POLICY_COUNT 51). Category A 47 intact (DEC-044). DEC-085 set_config must not regress. Parent FKs confirmed in ORM + `0014_analytics` / `77214759646c`.
**Alternatives considered:** (a) fold B3 into ALL_TENANT_TABLES / reopen STORY-02-01 — rejected; (b) expand to B4 decision-center children in same land — rejected (DEC-110 slices); (c) additive join-policy migration + adversarial 2-table suite — approved.
**Decision:** Accept B3 **CLOSED**. Companion: [`decisions/DEC-115-CATEGORY-B3-ANALYTICS-CHILDREN-RLS.md`](decisions/DEC-115-CATEGORY-B3-ANALYTICS-CHILDREN-RLS.md). Alembic `d3f8a21c9b03` (down `c221d15f8b02`); live `POLICY_COUNT` **53**; `ALL_TENANT_TABLES` remains **47**.
**Consequence:** DAG Category B execution advances B3 CLOSED; B4–B7 READY. Production GA **NO-GO**. **CI GREEN not met**. Validation: **build validated** (Docker `python -m pytest` **7 passed** in 9.78s).
**Status:** Accepted. Slice B3 **CLOSED**.

### DEC-114 — Category B Slice B2: commercial-children join RLS (`commercial_activities`, `commercial_quote_lines`)

**Date:** 2026-08-01
**Context:** DEC-110 pinned B2 = commercial children via `commercial_activity_sessions` / `commercial_quotes`. B1 CLOSED DEC-112 (`b110c04e7a01`, POLICY_COUNT 49). Category A 47 intact (DEC-044). DEC-085 set_config must not regress. Parent FKs confirmed in ORM + `0007_commercial_domain`.
**Alternatives considered:** (a) fold B2 into ALL_TENANT_TABLES / reopen STORY-02-01 — rejected; (b) expand to B3 analytics in same land — rejected (DEC-110 slices); (c) additive join-policy migration + adversarial 2-table suite — approved.
**Decision:** Accept B2 **CLOSED**. Companion: [`decisions/DEC-114-CATEGORY-B2-COMMERCIAL-CHILDREN-RLS.md`](decisions/DEC-114-CATEGORY-B2-COMMERCIAL-CHILDREN-RLS.md). Alembic `c221d15f8b02` (down `b110c04e7a01`); live `POLICY_COUNT` **51**; `ALL_TENANT_TABLES` remains **47**.
**Consequence:** DAG Category B execution advances B2 CLOSED; B3–B7 READY. Production GA **NO-GO**. **CI GREEN not met**. Validation: **build validated** (Docker `python -m pytest` **7 passed** in 7.10s).
**Status:** Accepted. Slice B2 **CLOSED**.

### DEC-112 — Category B Slice B1: company-children join RLS (`branches`, `licenses`)

**Date:** 2026-08-01
**Context:** DEC-110 pinned Category B inventory (12 join tables) and slices B1–B7. B1 = company children `branches` + `licenses` via `companies.id`. Category A 47 intact (DEC-044). DEC-085 set_config must not regress. Concurrent DEC-113 DB-05 Slice 1 took Alembic parent `065d1d3a466b`; B1 rebased onto `b8d4f02a1c06`.
**Alternatives considered:** (a) fold B1 into ALL_TENANT_TABLES / reopen STORY-02-01 — rejected; (b) expand to B2 `commercial_activities` in same land — rejected (DEC-110 B2); (c) additive join-policy migration + adversarial 2-table suite — approved.
**Decision:** Accept B1 **CLOSED**. Companion: [`decisions/DEC-112-CATEGORY-B1-COMPANY-CHILDREN-RLS.md`](decisions/DEC-112-CATEGORY-B1-COMPANY-CHILDREN-RLS.md). Alembic `b110c04e7a01` (down `b8d4f02a1c06`); live `POLICY_COUNT` **49**; `ALL_TENANT_TABLES` remains **47**.
**Consequence:** DAG Category B execution advances B1 CLOSED; B2–B7 READY. Production GA **NO-GO**. **CI GREEN not met**. Validation: **build validated** (Docker one-off pytest **7 passed**).
**Status:** Accepted. Slice B1 **CLOSED**.

### DEC-113 - DB-05 Slice 1: additive CREATE TABLE for 8 P0 R-09 tables

**Date:** 2026-08-01
**Context:** DEC-111 Slice 0 pinned 8 Category A deferred tables with ORM+`tenant_id` but no Alembic `create_table`. Slice 1 authorized as CREATE-only (no ENABLE RLS; no production migrate; DEC-085 untouched). Concurrent Category B B1 had local WIP on parent `065d1d3a466b` (DEC-112 / `b110c04e7a01`); Slice 1 chained from committed tip head `065d1d3a466b` - B1 must rebase onto new head if still unpushed.
**Alternatives considered:** (a) wait indefinitely for B1 remote land before any CREATE - rejected (DEC-107 keep READY busy; B1 unpushed after wait); (b) ENABLE RLS in same land - rejected (DEC-110/111; Category B owns join RLS; deferred-8 RLS = later slice); (c) two additive clusters (admin x5 + webhook/scoring/revenue x3) CREATE-only - approved.
**Decision:** Accept DB-05 **Slice 1 CLOSED** for P0 CREATE. Companion: [`decisions/DEC-113-DB-05-SLICE-1-P0-CREATE.md`](decisions/DEC-113-DB-05-SLICE-1-P0-CREATE.md). Alembic: `a7c3e91f0b05` (admin_licenses, admin_invoices, admin_transactions, admin_ai_costs, admin_jobs) -> `b8d4f02a1c06` (webhook_endpoints, scoring_scorecards, revenue_analytics_snapshots). Head **`b8d4f02a1c06`**. Remaining P0 CREATE: **0**. Still no RLS on these eight.
**Consequence:** R-09 missing-CREATE gap closed for the deferred-8. R-20 remains OPEN (P1 type/index drift). Next DB-05 = Slice 2 emails/meetings type authority. Category B B1+ must not ENABLE RLS on these eight until a governed RLS handoff. Production GA **NO-GO**. **CI GREEN not met**. Validation: **light validated** (alembic heads + history; DEC-085 spot-check; no prod migrate).
**Status:** Accepted. DB-05 Slice 1 **CLOSED**; program **OPEN**.

### DEC-111 - DB-05 Slice 0: schema drift inventory kickoff (R-20 / R-09)

**Date:** 2026-08-01
**Context:** DB-05 registered by CI-15 (DEC-021/022) for systemic ORM?DB drift (R-20). DEC-044/DEC-110 pin **8** Category A deferred tables waiting on CREATE TABLE. Swarm READY (DEC-107) after CI-14/CI-22 closes. Slice 0 = inventory only ? no migrate, no Prisma, no RLS DDL, DEC-085 untouched.
**Alternatives considered:** (a) open multi-sprint rewrite / big-bang migrate now ? rejected; (b) leave DB-05 BACKLOG idle during GHCR wait ? rejected (DEC-107); (c) Slice 0 inventory + prioritized findings + next-slice plan ? approved.
**Decision:** Accept DB-05 **Slice 0 CLOSED**. Companion: [`decisions/DEC-111-DB-05-SCHEMA-DRIFT-INVENTORY.md`](decisions/DEC-111-DB-05-SCHEMA-DRIFT-INVENTORY.md). Pins: Alembic head `065d1d3a466b`; ORM 80 / create_table 89; P0 = 8 R-09 missing CREATE; P1 = emails/meetings UUID vs String(36) + companies/index/nullable clusters. Next = Slice 1 additive CREATE (still no RLS).
**Consequence:** Board DB-05 ? **IN PROGRESS**. R-20/R-09 next-action = Slice 1. Category B B1?B7 must not ENABLE RLS on deferred-8. Production GA **NO-GO**. **CI GREEN not met**. Validation: **docs / light validated**.
**Status:** Accepted. DB-05 Slice 0 **CLOSED**; program **OPEN**.

### DEC-110 — Category B RLS canonical inventory + execution slices (planning CLOSE)

**Date:** 2026-08-01
**Context:** DEC-044 deferred Category B join/parent-FK policies + canonical inventory settlement to Sprint 04. Adversarial RLS suites COMPLETE (S04-01/05/06); POLICY_COUNT **47** intact. Contracts slice 4 (DEC-106) landed. Swarm READY scan ranked Category B planning next. CI-14/CI-22 residuals owned elsewhere — no overlap. DEC-085 set_config must not regress.
**Alternatives considered:** (a) ship join-policy Alembic churn now without pinned inventory — rejected; (b) leave Category B READY indefinitely — rejected (DEC-107 keep READY tracks busy with closable planning); (c) pin inventory + slices, CLOSE planning only — approved.
**Decision:** Accept Category B **planning CLOSE**. Companion: [`decisions/DEC-110-CATEGORY-B-RLS-INVENTORY.md`](decisions/DEC-110-CATEGORY-B-RLS-INVENTORY.md). Pins: Category A live **47**; Category A deferred **8** (DB-05); Category B join **12**; historic 72 retired (evidence ≈ **67**). Execution slices B1–B7 READY; no SQL this land.
**Consequence:** DAG Category B moves planning→execution READY. STORY-02-01 **not** reopened. Production GA **NO-GO**. **CI GREEN not met**. Validation: **docs / light validated**.
**Status:** Accepted. Category B planning **CLOSED**.

### DEC-109 — CI-22 executive close: FastAPI/Starlette/Pydantic COMPLETE; starlette floor cleared

**Date:** 2026-08-01
**Context:** CI-22 Phase 1 COMPLETE (DEC-081 @ `442af64`): fastapi **0.141.1** / starlette **1.3.1** / pydantic **2.13.4**. Story stayed OPEN for field pip-audit corroboration + compatibility residuals. Field: Stage 5 pip-audit `30688863161` @ `3084e5b` job `91339902722` **SUCCESS** — `No known vulnerabilities found, 1 ignored` (ecdsa PYSEC-2026-1325 / DEC-090). Backend Unit same run **0 failed** / 2700 passed after FastAPI 0.141 RBAC override fix. Stages 1–5 green corroboration `30689682988` @ `7ba137b`. ecdsa residual owned by DEC-057 (not CI-22).
**Alternatives considered:** (a) leave CI-22 OPEN indefinitely awaiting further FastAPI majors — rejected (AC met; idle during GHCR wait); (b) reopen CI-16 for ecdsa — rejected (DEC-057 Option A); (c) executive CLOSE with documented non-CI-22 residuals — approved.
**Decision:** **CLOSE CI-22**. Companion: [`decisions/DEC-109-CI-22-EXECUTIVE-CLOSE.md`](decisions/DEC-109-CI-22-EXECUTIVE-CLOSE.md). Do **not** claim whole-pipeline CI GREEN. DEC-085 untouched.
**Consequence:** R-21 starlette leg **cleared**. Program Complete/Closed absorbs CI-22. Residual ecdsa monitored under DEC-057/090/098. **CI GREEN not met** (CI-08). Validation: **build validated** (field pip-audit + Unit + Stages 1–5).
**Status:** Accepted. CI-22 **CLOSED**.

### DEC-108 - CI-14 executive AC close: security modernization COMPLETE; Jest 30 optional backlog

**Date:** 2026-08-01
**Context:** CI-14 Slice 1 PASS (DEC-063 sharp **0.35.3**), Slice 2 PASS (DEC-072 eslint **10.8.0**), Slice 3 STOP (DEC-100: no jest 29.x patch; host npm audit **0**; silent Jest 29->30 forbidden without Stage 3 evidence). DEC-100 executive alternate: revise AC and CLOSE without Jest major. R-18 already Closed. Swarm left CI-14 PARALLEL/READY idle during CI-08 GHCR wait - preferred path is executive close (DEC-107 always-on READY), not silent Jest 30.
**Alternatives considered:** (a) silent Jest 29->30 now - rejected (DEC-100 STOP; no security driver; Stage 3 regression risk); (b) leave CI-14 OPEN indefinitely awaiting Jest 30 evidence - rejected (security AC already met; idle during ops wait); (c) revise AC: sharp + eslint 10 + audit 0 = CLOSED; Jest 30 -> optional backlog - approved.
**Decision:** Accept revised CI-14 AC. **CLOSE CI-14**. Companion: [decisions/DEC-108-CI-14-EXECUTIVE-AC-CLOSE.md](decisions/DEC-108-CI-14-EXECUTIVE-AC-CLOSE.md). Do not bump Jest. Do not claim whole-pipeline CI GREEN. DEC-085 untouched. CI-19 CLOSED residual (DEC-105) - do not reopen.
**Consequence:** Program Complete/Closed absorbs CI-14. R-18 remains Closed. Optional Jest 30 is tech-debt backlog only. **CI GREEN not met** (CI-08). Validation: **docs only / light validated**.
**Status:** Accepted. CI-14 **CLOSED**.

### DEC-107 - Swarm always-on parallel READY dispatch (no idle on GHCR/ops)

**Date:** 2026-08-01
**Context:** Engineering Swarm concurrency diagnosis showed READY-idle while CI-08/CI-09 ops leaves were BLOCKED and EXECUTION_DAG still listed independent PARALLEL tracks. No repo max_agents cap; under-utilization is behavioral. Stage 6 build proven / push 403 (DEC-104).
**Alternatives considered:** (a) pause whole swarm until GHCR Packages write - rejected; (b) change GHA concurrency/needs in this land - rejected (note-only throughput tax); (c) always-on >=2-3 PARALLEL READY agents on disjoint ownership while ops waits - approved.
**Decision:** Accept always-on parallel READY policy. Companion: [decisions/DEC-107-SWARM-ALWAYS-ON-PARALLEL-READY.md](decisions/DEC-107-SWARM-ALWAYS-ON-PARALLEL-READY.md). Retain DEC-104 dual honesty labels. Do not claim full publish CI GREEN.
**Consequence:** Orchestrators must not idle solely on CI-08/CI-09. Preferred CI-14 path during that wait = executive AC close (DEC-108), not silent Jest 30. Validation: **docs only / not validated**.
**Status:** Accepted (orchestrator policy).

### DEC-106 — Contract tests expansion slice 4 (401 / 422) COMPLETE

**Date:** 2026-08-01
**Context:** DEC-094 slices 1–3 landed (probes + health/ready + auth decisions list). Next slice was identity auth error contracts only after OpenAPI documents actual FastAPI shapes (`{"detail": string}` / `HTTPValidationError`) — not invented `ErrorResponse`. Tip OpenAPI already auto-documents **422** on `GET /api/v1/decisions`; **401** was undocumented despite router-level `verify_token` / `UnauthorizedError`.
**Alternatives considered:** (a) invent custom ErrorResponse envelope — rejected; (b) document 401 without runtime match — rejected; (c) wire honest `DetailStringError` + assert 401/422 against OpenAPI — approved.
**Decision:** Land slice 4: `DetailStringError` + `responses={401: …}` on `list_decisions`; contract tests in `tests/contract/test_openapi_auth_errors.py`. Companion: [`decisions/DEC-106-CONTRACT-TESTS-401-422.md`](decisions/DEC-106-CONTRACT-TESTS-401-422.md). Update DEC-094. Do **not** edit `get_db` (DEC-085).
**Consequence:** Host `poetry run pytest tests/contract/ -m contract` → **14 passed**, 31 deselected (**light validated**). Contract track remains **IN PROGRESS** (narrow surface). **CI GREEN not met** (CI-08).
**Status:** Accepted. DEC-094 slice 4 COMPLETE.

### DEC-103 — CI-19 Wave 2 Slice 6 COMPLETE: residual package (app clear + alembic RLS accepted); CI-19 remains OPEN

**Date:** 2026-08-01
**Context:** After Wave 2 Slice 5 (DEC-102 / 179a477), remaining in-scope app avoid-sqlalchemy-text were init_db DDL (1), benchmark (2), mcp_server (1). Alembic RLS (7) + 0020 raw/formatted (4) intentionally not churned (DEC-085 / RLS risk). Prefer exec_driver_sql / Core; no Semgrep suppress. get_db body untouched.
**Alternatives considered:** (a) close CI-19 now — rejected until CS field-verify of app text=0; (b) rewrite alembic RLS migrations for Semgrep — rejected; (c) nosemgrep — rejected; (d) Slice 6 app fixes + formal alembic residual accept — approved.
**Decision:** Accept Wave 2 Slice 6 COMPLETE and alembic residual package. Companion: [decisions/DEC-103-CI-19-WAVE2-SLICE6.md](decisions/DEC-103-CI-19-WAVE2-SLICE6.md). Expected clear **4** app alerts. Wave 2 app-honesty COMPLETE. Do not close CI-19. Do not weaken Semgrep gates. No Slice 7 unless field resurfaces non-alembic app text.
**Consequence:** CI-19 OPEN (park pending field-verify). R-24 mitigating (Slice 1–6; alembic residual accepted). Validation: **light validated** (DEC-085 guard **2 passed**). **CI GREEN not met.**
**Field-verify (2026-08-01):** Security Scan `30686789458` / sast `91334080531` @ tip `abaae85` (land `3d49ae1`) **SUCCESS**. Live CS: app `avoid-sqlalchemy-text` **0**; alembic residual **7** + `0020` **4**. Wave 2 **PARKED COMPLETE**. **No Slice 7**. Story remains OPEN (executive residual-close). Validation: **build validated** (field CS). **CI GREEN not met.**
**Status:** Accepted. Wave 2 Slice 6 COMPLETE + field-verified; story OPEN.

### DEC-102 — CI-19 Wave 2 Slice 5 COMPLETE: activity_runtime + kg + memory Core honesty; CI-19 remains OPEN

**Date:** 2026-08-01
**Context:** After Wave 2 Slice 4 (DEC-101 / 9ab3516), densest non-alembic remainder was activity_runtime (3), kg service f-string filters (2), memory postgres_store (2), plus kg sql_repository local density. Prefer Core over sqlalchemy.text; no Semgrep suppress. Alembic RLS migrations deferred (residual — churn risk). DEC-085 get_db/set_config untouched. Parallel pytest-fix agent owns activity_intelligence / company / ER / Wave2 bind-RLS tests — no overlap.
**Alternatives considered:** (a) close CI-19 — rejected (~11 text remain); (b) churn alembic RLS now — rejected; (c) nosemgrep — rejected; (d) Slice 5 Core + keep OPEN — approved.
**Decision:** Accept Wave 2 Slice 5 COMPLETE. Companion: [decisions/DEC-102-CI-19-WAVE2-SLICE5.md](decisions/DEC-102-CI-19-WAVE2-SLICE5.md). Expected clear **7**. Do not close CI-19. Do not weaken Semgrep gates.
**Consequence:** CI-19 OPEN. R-24 mitigating (Slice 1–5). Validation: **light validated** (narrow pytest **58 passed**). **CI GREEN not met.** Slice 6 / residual package next (alembic + init_db/benchmark/mcp).
**Status:** Accepted. Wave 2 Slice 5 COMPLETE; story OPEN.

### DEC-101 — CI-19 Wave 2 Slice 4 COMPLETE: search_runtime + vector/search/tasks Core honesty; CI-19 remains OPEN

**Date:** 2026-08-01
**Context:** After Wave 2 Slice 3 (DEC-099 / 1f53dce), densest remainder was search_runtime (4) then sdk/search / ector_store / 	asks / contact search. Prefer Core over sqlalchemy.text; no Semgrep suppress. DEC-085 get_db/set_config untouched; search/contact timeouts use set_config (not SET LOCAL). DEC-100 reserved by CI-14 Jest STOP — this slice is DEC-101. Parallel Backend Unit pytest-fix agent owns prior Wave 2 fallout (to_jsonb/timeline); this slice does not touch those files.
**Alternatives considered:** (a) close CI-19 — rejected (~18 text remain after this slice); (b) nosemgrep / severity drop — rejected; (c) abort for conflict with pytest-fix agent — rejected (no file overlap); (d) Slice 4 Core + keep OPEN — approved.
**Decision:** Accept Wave 2 Slice 4 COMPLETE. Companion: [decisions/DEC-101-CI-19-WAVE2-SLICE4.md](decisions/DEC-101-CI-19-WAVE2-SLICE4.md). Expected clear **14**. Do not close CI-19. Do not weaken Semgrep gates.
**Consequence:** CI-19 OPEN. R-24 mitigating (Slice 1–4). Validation: **light validated** (narrow pytest **14 passed**). **CI GREEN not met.**
**Status:** Accepted. Wave 2 Slice 4 COMPLETE; story OPEN.

### DEC-100 — CI-14 Slice 3 STOP: Jest 29→30 silent major; no patch/minor; audit already 0

**Date:** 2026-08-01
**Context:** CI-14 Slice 2 PASS at `240f9a8` (DEC-072: eslint **10.8.0**). DEC-062 defines Slice 3 as Jest ecosystem major (**29 → 30+**); forbids audit jest→25. Session prefers patch/minor when audit allows; forbids silent Jest majors without evidence. Tip lock: jest / jest-environment-jsdom **29.7.0**, ts-jest **29.4.12**, next **15.5.22**. Host `npm audit --audit-level=high` → **0** vulnerabilities. Registry latest jest **29.x** = **29.7.0** (already locked). Stage 3 field **0** (DEC-077) must not regress under jsdom 26 / Jest 30.
**Alternatives considered:** (a) silent jest 30 bump now — **rejected** (major; no Stage 3 evidence package); (b) `npm audit fix --force` / jest→25 — **STOP**; (c) STOP Slice 3, docs-only, close R-18 advisory residual on audit **0**, keep CI-14 OPEN with named next executable — **approved**.
**Decision:** **STOP** CI-14 Slice 3. Do **not** change `package.json` / `package-lock.json` for Jest. Full package: [`decisions/DEC-100-CI-14-SLICE-3-JEST-STOP.md`](decisions/DEC-100-CI-14-SLICE-3-JEST-STOP.md). Companion plan DEC-062 §12 updated. **Close R-18** (high npm advisory residual cleared by Slice 1+2).
**Consequence:** CI-14 remains **IN PROGRESS / OPEN** (Slice 1+2 PASS; Slice 3 BLOCKED). R-18 **Closed**. Next executable: dedicated Jest 30 evidence package (pins + Docker Stage 3 **0** fail) **or** executive AC close of CI-14 without Jest major. Validation: **light validated** (audit + registry). **CI GREEN not met.**
**Status:** Accepted. CI-14 **Slice 3 STOPPED**; story **OPEN**. R-18 **Closed**.

