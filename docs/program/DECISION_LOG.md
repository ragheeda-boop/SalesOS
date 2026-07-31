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
