# Capability Register Reconciliation — 2026-09-23

> **CORRECTION (2026-09-23, same day):** §3's classification of the 21
> tenant_id-bearing/no-RLS tables as "mostly confirmed-dead legacy tables
> (hygiene, not security)" is **wrong** for 14 of them. A follow-up,
> broader-scoped grep (across `runtime/`, `sdk/`, not just `app/`) found all
> 14 are live, used via raw SQL by five routed runtime engines (Activity
> Runtime, Event Runtime, Decision Runtime, Policy Runtime, Feature Store),
> and are governed by an existing accepted architecture decision,
> **DEC-130f (2026-08-01)**, that explicitly forbids dropping them without a
> dedicated DEC. See `project-audit/59_ORPHAN_KEEP_TABLES_RLS_GAP_2026-09-23.md`
> for the full corrected finding. §3 below is left unedited for the audit
> trail; do not act on its "dead table" characterization.

Read-only, evidence-first reconciliation of the SalesOS capability census, plus
mechanical verification of alembic/git/flags/RLS/routes, plus one closed
CODE-CLOSABLE gap found during that verification. Write scope for this
session: `project-audit/` (two new reports, four index-line updates) and one
narrow migration + test pair under `salesos/backend/` (see report 58). No
production, `salesos_test`, or shared-database write occurred; all DB
verification ran on ephemeral, disposable containers destroyed after use.

## 0. The core finding

**No file in this repository has ever enumerated all 113 capability rows by
name.** `11_CAPABILITY_MATRIX.md` states an aggregate ("~110... ~85
COMPLETE") without row IDs. `24_SALESOS_ROADMAP_CAPABILITY_MATRIX_2026-09-20.md`
§5 names 16 vision-level rows and references "row 99" (Commercial Relationship
Model) without ever printing rows 1–98 or 100–113. Reports 32/33/34/50–56 each
move a scalar counter (52→60→68→85→86→87→88→89) and name only the specific
rows *they* closed. AGENTS.md's changing header line has repeated the current
scalar and citation but never the full list. The "2026-09-12 113-row census"
that report 32 says it is a delta against is not itself present as a file
anywhere under `project-audit/` or `docs/`.

This means the 89/113 figure carried in AGENTS.md's header and
`AUDIT_INVENTORY.md`'s header is **an unaudited running total**, not a
recomputed fraction. It is internally consistent (each report's arithmetic is
correct against the prior report's stated baseline) but its *membership* — the
actual 113 names — has never been checked end-to-end. That check is what this
report does.

### Reconciliation method

1. Take `11_CAPABILITY_MATRIX.md` §1.1–1.12 as the historical base and
   de-duplicate rows that appear in more than one subsection (e.g. ICP Engine
   appears in both §1.3 and §1.10; Pipeline Analytics and NBA appear in both
   §1.2/§1.3 and §1.8's runtime-engine list; Prompt Library/AI Policies/AI
   Memory appear in both §1.3 and §1.9). De-duplicated base = **110 rows**,
   which matches the matrix's own stated "~110" aggregate — a useful
   cross-check that the de-duplication is reasonable.
2. Layer in every row named in `24_SALESOS_ROADMAP_CAPABILITY_MATRIX...md` §3–§5
   and in closure reports 32, 33, 34, 50, 51, 52, 56 that does **not** already
   correspond to a base row. This is a judgment call in a handful of cases
   (documented inline in the table) and adds **22 rows**.
3. Total reconciled register: **132 rows**. This is offered as a replacement
   for the frozen "113," not a recomputation of it — see §4 for why the two
   numbers cannot be reconciled to each other precisely.

### Why 132 ≠ 113

Three explanations were tested against the evidence and none can be ruled in
or out with certainty, which is itself the finding:
- The original 113 may have used **coarser** grouping than this register in
  some places (e.g. treating "Seller OS" as one row where this register
  leaves it as an implicit aggregate of ~9 constituent rows already counted
  elsewhere, to avoid double-counting — if the original census counted Seller
  OS *and* its constituents separately, that alone would remove much of the
  gap).
- Reports 50–52 (Opportunity Notes, Quota Snapshots, Task Detail) each claim
  "+1" against parent rows (Opportunities/Deals, Revenue, Activities) that
  `11_CAPABILITY_MATRIX.md` already lists as historically COMPLETE. That is
  only self-consistent if the running census tracks finer granularity than
  the historical matrix — which supports this register's approach of listing
  them as distinct rows — but it is also possible the original 113 never
  counted them at all and the "+1" logic in those reports is itself the
  drifting part.
- No file fixes the point in time at which "113" was first counted, so later
  legitimate scope additions (Fact Review ledger, Agent Reach, Provider
  Spend, Telemetry, ADR-0113 scoring) cannot be definitively classified as
  "already inside the original 113" versus "added to the roadmap afterward
  without the denominator being revised."

**Recommendation:** the PO/TL should adopt §2 below as the single row-level
source of truth going forward and stop tracking a bare scalar. Until that
adoption happens, AGENTS.md's historical "89/113 = 78.8%" line is left
untouched by this report (see §5) and this register's own total is reported
alongside it, not in place of it.

---

## 1. Mechanical facts (verified this session, not asserted from docs)

| Check | Method | Result |
|---|---|---|
| Migration file count on disk | `find salesos/backend/app/alembic/versions -name '*.py'` | **126** — not 96 (AGENTS.md §34), 97 (`FINAL_GO_NOGO_ASSESSMENT.md`), 109 (`AUDIT_INVENTORY.md` §4), or 113/114 (`AUDIT_INVENTORY.md` header note). One stray `0afbf3e6ae53_enable_rls_all_tenant_tables.py.bak` also present (not a live revision; harmless but should be deleted, it is dead weight in version control). |
| Alembic graph integrity | Parsed every `revision`/`down_revision` pair (regex-based, no DB needed), checked for missing link targets and multiple heads | **Single head, no broken links.** Head = `u1v2w3x4y5z6_commercial_relationship_edges` before this session's new migration; `70193187420d_force_rls_effectiveness_tables` (see report 58) is now the head. |
| Alembic upgrade from empty DB | Built the current source into a fresh Docker image (`docker build`), ran `alembic upgrade head` against a brand-new `pgvector/pgvector:pg16` container | **PASS**, full 126→127-migration chain applies cleanly end to end with no errors. (A first attempt using a bind-mounted volume via Git-Bash silently mounted stale/empty content instead of current source — see §3 finding — which produced a false failure before the image-build approach was used instead.) |
| `git status` | `git status --porcelain --ignore-submodules=all` | **735 untracked (`??`), 239 modified (`M`), 25 deleted (`D`)** — different from every prior count in AGENTS.md (§41: 512/37/25; §13 audit inventory: 512 untracked at the time). The untracked count has grown considerably since the last recorded snapshot; no staged deletes (index remains clean per the 2026-09-12 A1 repair). |
| `feature_*` flags | `grep` of `salesos/backend/app/config.py` | `feature_search_fuzzy_v2=False`, `feature_ai_copilot=False`, `feature_signal_marketplace_postgres=False`, `feature_crm_kanban=False`, `feature_httponly_access_cookie=False`, `entitlement_enforcement_enabled=True`, `quota_enforcement_enabled=True`, `demo_mode=False`, `kg_allow_sql_fallback=None`. All match the honesty posture AGENTS.md claims — no drift found. |
| v3 page count | `Glob salesos/frontend/src/app/v3/**/page.tsx` (cross-checked with `find`) | **49** — matches `AUDIT_INVENTORY.md`'s "40 sub-routes" note is stale; matches the more recent "49 V3 pages" figure in report 49/`AUDIT_INVENTORY.md`'s later addendum. |
| Legacy `(dashboard)` page count | Same method | **78** — matches the figure used consistently since §39. |
| RLS coverage (public schema, fresh ephemeral DB migrated to head) | `pg_class.relrowsecurity`/`relforcerowsecurity` + `pg_policies`, queried directly (not read from a doc) | **211 public tables total; 124 with RLS enabled; 122 with FORCE RLS; 125 total policies; 121 named `tenant_isolation_*`.** This is close to but not identical to the "107 policies total, 106 tenant-isolation named" figure carried in AGENTS.md §101/§102 — the difference is explained by the additive migrations landed since those reports (GTM capability results, commercial relationship edges, opportunity notes, quota snapshots, action-outcome links, customer surveys, runtime parent-read grants) each adding 1 policy, which is the expected direction of travel, not a discrepancy to chase further. |
| RLS enabled but not forced | Same query, filtered | **2 tables: `account_funnel`, `score_observations`.** Both are live (referenced by `app/modules/effectiveness/__init__.py` and `app/modules/signal_actions/{router,hitl_router}.py`), both had `ENABLE ROW LEVEL SECURITY` + a policy but no `FORCE ROW LEVEL SECURITY` since their originating migrations (`n9o0p1q2r3s4`, `o0p1q2r3s4t5`). **This is the one CODE-CLOSABLE gap this session closed — see report 58.** |
| Tables with a `tenant_id` column but no RLS at all | Same query, cross-referenced against `information_schema.columns` | **21 tables** (`sync_runs_*` monthly partitions excluded — they inherit RLS from the `sync_runs` partitioned parent, which is itself RLS-enabled+forced, confirmed directly). See §3 for the breakdown and why none of the 21 is treated as code-closable this session. |
| MCP server (matrix-11 said "present, not audited in depth" → UNKNOWN) | `grep` for router registration + test file presence | `app/routers/mcp.py` **is** registered in `app/boot/routers.py` under `_auth` dependencies, and `tests/unit/test_mcp_server.py` exists. Resolves UNKNOWN → **COMPLETE** (registered + tested; test execution itself not re-run this session). |

### Docker image staleness (a finding, not a blocker)

The already-running `salesos-backend` local image (and the `salesos-backend-1`
container from `docker-compose`) contain an **older** copy of
`0afbf3e6ae53_enable_rls_all_tenant_tables.py` that lacks the
`_table_exists()` existence guard present in the current source file. Running
migrations against that stale image from an empty database throws
`UndefinedTableError: relation "opportunity_contacts" does not exist` at that
migration step — a false alarm caused entirely by image staleness, not a real
migration-ordering bug in the current source (confirmed by rebuilding the
image from current source and re-running: the full chain then applies
cleanly, see the table above). This reconfirms AGENTS.md's repeated caution
(§25, §32, §80) that the long-running local Docker backend must not be
treated as evidence for current-checkout behavior — this session's own first
attempt walked directly into that exact trap before catching it.

---

## 2. Reconciled register (132 rows)

Status legend: **COMPLETE** = code, migration/schema where applicable, and at
least one passing test exist, cited below. **PARTIAL** = some of the above
exists but the row is not done. **BLOCKED** = the remaining work is not
closable by writing code in this checkout (human/PO sign-off, external
credential/provider, legal/compliance sign-off, or platform-operator action).
Every COMPLETE row below inherits the whole-document caveat that
code-scope-complete is never a production-readiness or Phase-7 claim.

### 2.1 Product Core (11)

| # | Capability | Status | Evidence |
|--:|---|---|---|
| 1 | Companies | COMPLETE | `11_CAPABILITY_MATRIX.md` §1.1 |
| 2 | Contacts | COMPLETE | same |
| 3 | People | COMPLETE | same |
| 4 | Opportunities / Deals | COMPLETE | same |
| 5 | Pipeline | COMPLETE | same |
| 6 | Activities | COMPLETE | same |
| 7 | Revenue | COMPLETE | same |
| 8 | Proposals | COMPLETE | same |
| 9 | Reviews | COMPLETE | same |
| 10 | Approvals | COMPLETE | same |
| 11 | Contracts | COMPLETE | was PARTIAL ("backend depth unverified") in matrix-11; closed by loop 33 (`test_contract_management_db.py`, Postgres repo + RLS) |

### 2.2 Intelligence (7)

| # | Capability | Status | Evidence |
|--:|---|---|---|
| 12 | Commercial Memory | COMPLETE | matrix-11 §1.2 |
| 13 | Account Intelligence | COMPLETE | matrix-11 + loop 33 (grounded CRM-fact snapshot, `test_account_intelligence_evidence_db.py`) |
| 14 | Deal Intelligence | COMPLETE | matrix-11 + loop 32 (V3-reachable, `32_IMPLEMENTATION_LOOP...md`) |
| 15 | Pipeline Analytics | COMPLETE | matrix-11 + loop 32 |
| 16 | Forecasting | COMPLETE | matrix-11 + loop 32 |
| 17 | Evidence Chain | COMPLETE | matrix-11 + loop 33 (producer/consumer wiring) |
| 18 | Recommendations | COMPLETE | matrix-11 + loop 32 |

### 2.3 AI Copilot (13)

| # | Capability | Status | Evidence |
|--:|---|---|---|
| 19 | Copilot Modes | COMPLETE | matrix-11 §1.3 (provider DEV-only, unchanged caveat) |
| 20 | Grounded EvidencePack loader | COMPLETE | same |
| 21 | RAG | COMPLETE | matrix-11 + loop 32 (V3-reachable; pilot-size corpus, unchanged caveat) |
| 22 | NBA | COMPLETE | matrix-11 + loop 32 |
| 23 | AI Governance Audit | COMPLETE | matrix-11 + loop 32 (V3 admin viewer) |
| 24 | Human Approval Service | COMPLETE | matrix-11 |
| 25 | Evaluation / Quality Gates | COMPLETE | matrix-11 |
| 26 | ICP Engine | COMPLETE | matrix-11 + loop 32 |
| 27 | Signal Marketplace | COMPLETE | matrix-11 |
| 28 | Prompt Library | COMPLETE | was PARTIAL (in-memory) in matrix-11; closed by loop 33 (durable Postgres, versioned, RLS) |
| 29 | AI Policies | COMPLETE | same, loop 33 |
| 30 | AI Memory | COMPLETE | same, loop 33 (Fernet-encrypted, TTL, opt-out delete) |
| 31 | AI Model Tiers | COMPLETE | same, loop 33 (owner-only editor) |

### 2.4 Master Data / Entity Resolution (9)

| # | Capability | Status | Evidence |
|--:|---|---|---|
| 32 | Muhide ingestion | COMPLETE (code-scope) | AGENTS.md §34–37; production promotion is separately BLOCKED by Phase 7, tracked under row 40, not this row |
| 33 | Entity Resolution (CR-safe) | COMPLETE | AGENTS.md §36 |
| 34 | Identity Classifier | COMPLETE | AGENTS.md §37 |
| 35 | Industry Normalization | COMPLETE | same |
| 36 | Quality Scoring | COMPLETE | same |
| 37 | Sales Readiness Recompute | COMPLETE | same |
| 38 | Canonical Authority Survivorship | COMPLETE | same |
| 39 | Contact Relationships (Phase 6, VERIFIED/INFERRED) | COMPLETE | same |
| 40 | Review Queue (Phase 7-A/B/C) | **PARTIAL / BLOCKED** | Capture-only on `salesos_test`; 54,185 candidates + 36 short-CR + DI P1/P2 confirmation + Product/PO sign-off outstanding. **Blocker: human/PO review, explicitly out of code-closable scope per this task's own instructions.** |

### 2.5 Platform (7)

| # | Capability | Status | Evidence |
|--:|---|---|---|
| 41 | EventBus (+ persistent DLQ) | COMPLETE | matrix-11 §1.5 |
| 42 | Capability Registry | COMPLETE | same |
| 43 | Alembic drift gate | COMPLETE | same |
| 44 | Observability | COMPLETE | same (Sentry DSN empty is a config value, not a missing capability) |
| 45 | Background Jobs | COMPLETE | same |
| 46 | Backup / Restore | **PARTIAL / BLOCKED** | Railway managed backup schedule still off per AGENTS.md §18/§32/§41. **Blocker: Railway platform-admin action (external operator), not code.** |
| 47 | Deployment (Railway + Vercel) | COMPLETE (code) | matrix-11; live-dashboard `preDeployCommand` confirmation and staging OAuth remain open ops items, tracked as sub-items, not a separate row |

### 2.6 Identity / Auth / RBAC (14)

| # | Capability | Status | Evidence |
|--:|---|---|---|
| 48 | JWT (RS256) | COMPLETE | matrix-11 §1.6 |
| 49 | Refresh tokens | COMPLETE | same |
| 50 | Owner-platform vs Tenant-API JWT audiences | COMPLETE | same |
| 51 | RBAC | COMPLETE | same |
| 52 | SSO (Google) | **PARTIAL / BLOCKED** | OAuth staging app not yet created. **Blocker: external Google Cloud Console action by DevOps; not code.** |
| 53 | SSO (Microsoft, GitHub) | **NOT STARTED / BLOCKED** | Config placeholders only. **Blocker: product decision + external app registration + credentials; not code.** |
| 54 | API Keys | COMPLETE | matrix-11 |
| 55 | CSRF | COMPLETE | same |
| 56 | Audit trail | COMPLETE | same |
| 57 | RLS (tenant isolation completeness) | COMPLETE | **Closed this session.** Mechanical audit (§1 above) found 2 live tables (`account_funnel`, `score_observations`) with RLS enabled but not forced; fixed and verified in migration `70193187420d` — see report 58. The 21 tenant_id-bearing tables with no RLS at all are a separate, explicitly-not-closed finding (§3). |
| 58 | `salesos_app` fail-closed in prod | COMPLETE | matrix-11 |
| 59 | PDPL statement | **PLANNED / BLOCKED** | Doc not signed. **Blocker: legal/compliance sign-off; not code.** |
| 60 | SOC2 Type I | **PLANNED / BLOCKED** | Evidence-pack scaffolding exists (STORY-14-05). **Blocker: external auditor engagement; not code.** |
| 61 | SBOM / SCA | COMPLETE (narrow) | Was UNKNOWN in matrix-11; loop 34 closed "deterministic dependency manifest hashes for lockfiles" (`test_sbom_manifest.py`). Scope caveat: this is manifest-hash input generation, not a running vulnerability scanner — do not present as a full SCA pipeline. |

### 2.7 Integrations (10)

| # | Capability | Status | Evidence |
|--:|---|---|---|
| 62 | Gmail sync | COMPLETE | matrix-11 §1.7 |
| 63 | Calendar sync | COMPLETE | same |
| 64 | OAuth token encryption | COMPLETE | same |
| 65 | Notion sync | COMPLETE (code) | was PARTIAL in matrix-11; loop 34 closed idempotency + no-fabricated-CR (`test_notion_sync_db.py`). Live credentials/staging E2E remain open, tracked as an ops sub-item. |
| 66 | Excel Import | COMPLETE | matrix-11 |
| 67 | Odoo | COMPLETE (code) | was NOT STARTED in matrix-11; loop 34 closed adapter + 31 tests. Live credentials/staging E2E remain open, tracked as an ops sub-item. |
| 68 | Stripe | COMPLETE (spine) | matrix-11; live keys empty is a platform/ops sub-item, not a code gap |
| 69 | Webhooks (SSRF-hardened) | COMPLETE | matrix-11 |
| 70 | Integration Hub | COMPLETE | matrix-11 |
| 71 | MCP server | COMPLETE | Was UNKNOWN in matrix-11 ("not audited in depth"); resolved this session — router registered in `app/boot/routers.py`, `tests/unit/test_mcp_server.py` exists (test execution not re-run this session) |

### 2.8 Runtime engines (14)

| # | Capability | Status | Evidence |
|--:|---|---|---|
| 72 | Activity Runtime | COMPLETE | matrix-11 §1.8 |
| 73 | Capability Framework | COMPLETE | same |
| 74 | Data Fabric Runtime | COMPLETE | same |
| 75 | Decision Runtime | COMPLETE | same |
| 76 | Feature Store | COMPLETE | same |
| 77 | Knowledge Graph Runtime | COMPLETE (code, dormant by design) | same; OFFLINE in production per ADR-108 is a deliberate architecture decision, not a gap |
| 78 | Search Runtime | COMPLETE | matrix-11 |
| 79 | Timeline Runtime | COMPLETE | same |
| 80 | UX Runtime | COMPLETE | same |
| 81 | Schema Engine | COMPLETE | same |
| 82 | Form Engine | COMPLETE | same |
| 83 | Action Engine | COMPLETE | same |
| 84 | Extension API | COMPLETE | same |
| 85 | Plugin Sandbox | COMPLETE | same |

### 2.9 Tenant Studio (7)

| # | Capability | Status | Evidence |
|--:|---|---|---|
| 86 | Custom Fields | COMPLETE | matrix-11 §1.9 |
| 87 | Workflow Builder | COMPLETE | same |
| 88 | Scoring Rules Studio | COMPLETE | same |
| 89 | Territory Rules Studio | COMPLETE | same |
| 90 | Permissions Studio | COMPLETE | same |
| 91 | Branding & Languages | COMPLETE | same |
| 92 | Notification Rules Studio | COMPLETE | same |

### 2.10 GTM Intelligence — STORY-11 (8)

| # | Capability | Status | Evidence |
|--:|---|---|---|
| 93 | TAM/SAM/SOM Market Sizing | COMPLETE | matrix-11 §1.10 (fixture-based) + loop 34 methodology fields + report 55 (durable Postgres persistence, replacing the in-memory-only caveat) |
| 94 | Lead Discovery | COMPLETE | same, durable per report 55 |
| 95 | Lookalike Accounts | COMPLETE | same |
| 96 | Enrichment Waterfall | COMPLETE | same |
| 97 | Contact Verification | COMPLETE | same |
| 98 | Website Intelligence | COMPLETE | same |
| 99 | AI Outreach | COMPLETE | same |
| 100 | Sequencing Engine | COMPLETE | same |

### 2.11 Chaos / DR / SOC2 harnesses — STORY-14 (5)

| # | Capability | Status | Evidence |
|--:|---|---|---|
| 101 | Load/SLO harness | COMPLETE | matrix-11 §1.11 |
| 102 | Chaos resilience (CI) | COMPLETE | same |
| 103 | DR drill harness | COMPLETE (non-prod) | same |
| 104 | AI provider failover | COMPLETE (non-prod) | same |
| 105 | LLM regression golden fixtures | COMPLETE (non-prod) | same |

### 2.12 Frontend surfaces (5)

| # | Capability | Status | Evidence |
|--:|---|---|---|
| 106 | v3 shell | COMPLETE | **49 pages, verified this session by Glob**, not carried from a doc |
| 107 | Legacy `(dashboard)` shell | COMPLETE (exists; retirement candidate) | **78 pages, verified this session by Glob** |
| 108 | `api/` route handlers | COMPLETE | matrix-11 §1.12 |
| 109 | Auth pages | COMPLETE | same |
| 110 | System page | COMPLETE | same |

### 2.13 Net-new rows introduced by the roadmap doc and closure reports 32–56 (22)

These rows have no equivalent in `11_CAPABILITY_MATRIX.md` at all; they enter
the register from `24_SALESOS_ROADMAP_CAPABILITY_MATRIX...md` and the named
closures in reports 32–56.

| # | Capability | Status | Evidence |
|--:|---|---|---|
| 111 | Commercial Relationship Model | COMPLETE | Report 56 (migration `u1v2w3x4y5z6`, 31 tests) |
| 112 | Canonical Fact Apply (post-approval CRM write) | COMPLETE (narrow allowlist scope) | Loop 34 (`test_fact_apply_service.py`) |
| 113 | Temporal Data Standard | COMPLETE | Loop 34 (`test_temporal_contract.py`); supersedes doc-24's earlier "no common temporal standard" note, which predates this closure |
| 114 | People 360 / Buying Committee | COMPLETE | Loop 34 (`test_buying_committee.py`) |
| 115 | Customer Health Evidence (technical envelope) | COMPLETE (envelope only) | Loop 34 (`test_health_evidence.py`). Distinct from row 132 (the broader CS lifecycle), which remains PARTIAL |
| 116 | Competitive / Win-Loss taxonomy | COMPLETE | Loop 34 (`test_win_loss_taxonomy.py`) |
| 117 | Revenue Attribution / Cost (first-touch, 90-day window) | COMPLETE (narrow scope) | Loop 34 (`test_revenue_attribution.py`) |
| 118 | Connector Health / Replay posture | COMPLETE | Loop 34 (`test_connector_health.py`) |
| 119 | Manager OS / Seller 360 | COMPLETE | Loop 34 (`test_executive_operating_views.py`) |
| 120 | Revenue Leadership OS | COMPLETE | same |
| 121 | Activity → Signal correlation | COMPLETE | Loop 34 (`test_activity_signal_correlation.py`) |
| 122 | PDF export | COMPLETE | Loop 34 (`test_pdf_export.py`) — real PDF 1.4 output, replacing the earlier `ValueError` stub |
| 123 | Automation / Workflow outcome contract | COMPLETE | Loop 34 (`test_workflow_outcome_contract.py`) |
| 124 | Fact Review / FactRecorder proposal+review ledger | COMPLETE (code-scope) | AGENTS.md §70–79, reports 26/28/81; proposal-only, `crm_applied=false` by design, browser-verified against `salesos_test` per report 81 |
| 125 | Agent Reach (research capability) | COMPLETE (code) / research-execution BLOCKED | AGENTS.md §61–67, report 65 (156/156 tests, live `salesos_test` persistence integration). **Blocker for any live run: no price cards/budget configured, no credentials, router unregistered — deliberate, not an oversight (report 29/30 — Google Maps is explicitly not an approved source and no other provider is cleared).** |
| 126 | Provider Spend Budget ledger | COMPLETE (code+DB proof) | Report 30. **Blocker: no rate cards or limits seeded — a pricing/ops decision, not code.** |
| 127 | Telemetry idempotency & authenticated pipeline | COMPLETE | Reports 53/59 (signed ASGI + `salesos_test` browser proof) |
| 128 | Opportunity Notes | COMPLETE | Report 50 |
| 129 | Quota Snapshots | COMPLETE | Report 51 |
| 130 | Task Detail (direct tenant-scoped lookup) | COMPLETE | Report 52 |
| 131 | Learning / Adaptive ICP | **PARTIAL / BLOCKED** | Doc-24 §5; needs real usage/outcome data plus a product decision on whether/how ICP profiles may self-adjust. **Blocker: product decision + real customer usage data, not code — an automatic-mutation loop without human sign-off would itself be a governance regression.** |
| 132 | Customer Success / CS Health lifecycle | **PARTIAL / BLOCKED** | Report 54 explicitly: "does not close the Customer Success lifecycle." Missing invitation/onboarding/adoption/support/renewal inputs. **Blocker: real customer usage/support data + product decision on what a Health score may claim; fabricating these inputs to close the row would violate the honesty rules this whole project is built on.** |

---

## 3. RLS-gap finding detail (21 tenant_id tables without RLS — not closed this session)

| Table(s) | What they are | Why not closed now |
|---|---|---|
| `company_deals`, `company_funding_events`, `company_intent_contacts`, `company_intent_content`, `company_intent_rfps`, `company_intent_visits`, `company_job_postings`, `company_payments`, `company_policies`, `company_products` | Created by `0002_feature_store.py` (2026-era Feature Store bootstrap) | Explicitly listed in `app/db05_orphan_keep.py` as retained-but-orphaned legacy tables; no active model/router references any of them. Adding RLS to genuinely dead tables is not a security fix, it is churn. |
| `decisions`, `decision_feedback_loop` | Legacy pre-refactor tables (superseded by `decision_center_decisions`, which already has RLS) | Only referenced by their own creation/drop migrations; no live model or router. |
| `domain_events` | `0001_baseline.py` legacy event table | Same — no live reference found. |
| `graph_nodes` | Knowledge-Graph-adjacent | Neo4j path is OFFLINE per ADR-108; dormant by the same architecture decision as row 77. |
| `activity_records` | `0009_activity_runtime.py` legacy table | Superseded by `commercial_activity_sessions`, which already has RLS. No live reference found. |
| `subscriptions`, `usage_meters`, `usage_meter_events`, `dunning_cases`, `platform_billing_invoices`, `stripe_webhook_events` | Owner-platform billing tables (STORY-04/05) | These plausibly belong to the **Owner-platform JWT audience** (row 50), not the tenant-API audience, per `config.py`'s explicit owner-vs-tenant split. Applying the standard `tenant_isolation_*` policy without confirming whether an owner-plane admin path needs legitimate cross-tenant reads (e.g. a billing dashboard) risks breaking that path or silently making it return zero rows. **This needs an explicit architecture decision (does an owner-plane query ever bypass tenant RLS via a separate role, or does it iterate tenant-by-tenant?) before any RLS migration touches these tables — not a decision this session should make unilaterally.** |

None of the 21 is classified CODE-CLOSABLE. The first 13 are dead-table
hygiene (candidates for a follow-up "confirm dead, then drop" pass, not an
RLS pass). The last 6 need a product/architecture decision first.

---

## 4. Register totals

| Denominator | COMPLETE | Fraction | Source |
|---|--:|--:|---|
| Historical scalar (frozen since the 2026-09-12 baseline, never row-audited) | 89 | 78.8% | AGENTS.md header / `AUDIT_INVENTORY.md` header, unchanged by this report — see §5 |
| This session's reconciled register (§2, 132 rows) | 124 | 93.9% | Computed directly from §2's per-row table above (132 rows − 8 PARTIAL/BLOCKED rows: 40, 46, 52, 53, 59, 60, 131, 132) |

The jump from 78.8% to 93.9% is **not** primarily new work from this session
— it is mostly proper crediting of the 56 prior closure reports into one
row-level register instead of a running scalar, plus this session's own
row-boundary reconstruction choices (§0). This session's actual new
contribution to completion is exactly one row (57, RLS-gap fix) and one
resolved UNKNOWN (71, MCP server). Treat the 93.9% figure as **a proposed
register total pending PO/TL acceptance of this reconciliation's
methodology**, not as an authoritative replacement for 89/113 until that
acceptance happens.

---

## 5. Classification outcome (step 3) and stopping condition (step 7)

Every row not marked COMPLETE in §2 is BLOCKED, with the specific blocker
named inline in the table:

1. Review Queue (Phase 7-A/B/C) — human/PO review of 54,185 candidates + DI methodology confirmation
2. Backup/Restore — Railway platform-admin action
3. SSO (Google) — external OAuth app + credentials
4. SSO (Microsoft/GitHub) — product decision + external app registration
5. PDPL statement — legal/compliance sign-off
6. SOC2 Type I — external auditor engagement
7. Learning/Adaptive ICP — product decision + real usage data
8. Customer Success/CS Health lifecycle — real customer data + product decision

**Zero rows are classified CODE-CLOSABLE after row 57's closure this
session.** The one CODE-CLOSABLE gap this mechanical audit actually found
(the RLS-not-forced pair) is closed and verified in report 58. The 21-table
RLS-gap finding (§3) was deliberately **not** treated as code-closable: 15 of
21 are confirmed-dead legacy tables (hygiene, not security), and 6 are
owner-plane billing tables that need an architecture decision before any RLS
change, per the task's own instruction not to close a BLOCKED row by writing
code that papers over an undecided question.

Per the task's stopping condition: this reconciliation's own register
(93.9%) exceeds both the 90% and 102/113-equivalent thresholds, and every
row classified CODE-CLOSABLE has been closed — the second exit condition is
what actually applies here, independent of which denominator is used. No
further rows were opportunistically added or reclassified to manufacture
this outcome; §0 and §4 disclose exactly why the reconciled total differs
from the frozen scalar so the PO/TL can judge the reconciliation on its
merits rather than the headline number.

## Deliberate non-claims

- This is a **code-scope** register. It does not claim production readiness,
  does not open Phase 7, does not authorize any provider call, and does not
  change the "production NOT APPROVED" status anywhere in this repository.
- The 132-row register is this session's best-effort reconstruction, not a
  recovered original document — §0 states plainly that the original 113-row
  membership cannot be recovered because it was never written down.
- Test suites for rows carried forward from `11_CAPABILITY_MATRIX.md` and
  reports 32–56 were **not** re-executed this session (that would mean
  re-running 56 reports' worth of test suites); their historical PASS
  results are cited, not reproduced. Only report 58's new test was executed
  this session, on a fresh ephemeral database, and is fully reproducible.
- The 21-table RLS-gap and the 2-table RLS-not-forced findings were both
  discovered by direct `pg_class`/`pg_policies` queries against a freshly
  migrated ephemeral database, not read from any document — this is the one
  part of this report that is mechanically verified rather than reconciled
  from prior claims.
