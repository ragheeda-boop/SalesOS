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
**Decision:** **Not decided.** Full ARB + Risk Manager package: [`docs/program/decisions/DEC-DRAFT-RAILWAY-R14-PHASE0.md`](decisions/DEC-DRAFT-RAILWAY-R14-PHASE0.md). Package **recommends Option A**; interim posture if unauthorized = Option C (not B).
**Consequence:** Phase 0 exit remains **NO-GO**. S04-04 remains BLOCKED. No Railway changes authorized by this entry. Upon human accept, mint Accepted **DEC-016** (or next free ID) and mark this draft Superseded.
**Status:** **DRAFT** (not Accepted).

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
