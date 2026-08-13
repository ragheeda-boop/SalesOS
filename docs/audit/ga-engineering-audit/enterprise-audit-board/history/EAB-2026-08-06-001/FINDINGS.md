# Findings Register ? EAB-2026-08-06-001

**Pack:** Enterprise Audit Board v2.2  
**Schema:** [06-FINDINGS-SCHEMA.md](../../06-FINDINGS-SCHEMA.md)  
**Validation:** light validated (Grep/Read) unless noted  
**Status column:** dispositioned after Waves 1?3 ? see [REMEDIATION-PROGRAM-STATUS.md](./REMEDIATION-PROGRAM-STATUS.md)

Finding IDs use run-local form `EAB-001-{severity}-{TAG}-{nn}` and cite axis tags.

---

## P0 ? Blocks Production GA / external pilot

### EAB-001-P0-SEC-01 ? `db_session_factory` never set ? middleware fail-open

```yaml
id: EAB-001-P0-SEC-01
title: "app.state.db_session_factory never wired at startup"
axis: [5, 11, 30, 33, 39]
axis_tags: [SEC, SVC, RT, BE]
severity: P0
symptom: "Entitlement, suspended-tenant, and API-key middleware skip enforcement when factory is missing"
root_cause: "Fail-open design; startup never assigns app.state.db_session_factory (only unit tests set it)"
evidence:
  - salesos/backend/app/boot/startup.py
  - salesos/backend/app/modules/admin/entitlement_middleware.py (L64-66 fail-open)
  - salesos/backend/app/modules/identity/suspended_tenant_middleware.py (L50-52)
  - salesos/backend/app/modules/api_keys/middleware.py (L34-36)
  - salesos/backend/app/boot/middleware.py (middleware registered)
  - salesos/backend/tests/unit/test_adversarial_entitlement_bypass_story_06_04.py (only assignment found)
validation_label: light validated
recommendation: "Set factory in startup from async_session; change middleware to fail-closed (503/403) if unset"
owner: backend-platform
status: fixed (Wave 1; light runtime probe Wave 2)
related_ids: [EAB-001-P0-SEC-02]
economics_band: Med
drift_metric_ids: []
```

### EAB-001-P0-SEC-02 ? Process-lifetime AsyncSession + BYPASSRLS owner fallback

```yaml
id: EAB-001-P0-SEC-02
title: "Long-lived sessions without tenant GUC; empty APP_POSTGRES_PASSWORD ? BYPASSRLS owner"
axis: [6, 11, 30, 33, 39]
axis_tags: [SEC, DM, RT, BE]
severity: P0
symptom: "Five app.state.* sessions live for process lifetime without set_config(app.tenant_id); empty app password falls back to owner URL"
root_cause: "Singleton session pattern for timeline/DC/workflow/etc.; silent owner fallback in Settings.app_database_url"
evidence:
  - salesos/backend/app/boot/startup.py (_timeline_session, _fs_repo_session, _dc_session, _opportunity_session, _workflow_session)
  - salesos/backend/app/config.py (L79-80 BYPASSRLS note; L100-106 empty password fallback)
  - salesos/backend/app/database.py (get_db DEC-085 set_config ? request path OK)
validation_label: light validated
recommendation: "Per-request or factory sessions with GUC; refuse boot if APP_POSTGRES_PASSWORD empty in non-dev; no silent BYPASSRLS for request path"
owner: backend-platform
status: fixed (Wave 1 password + Wave 2 factory sessions)
related_ids: [EAB-001-P0-SEC-01]
economics_band: High
drift_metric_ids: []
```

### EAB-001-P0-FE-01 ? Blank SSR providers + token SoT break

```yaml
id: EAB-001-P0-FE-01
title: "Providers return null until useEffect; tokens.css not in globals; residual undefined CSS vars"
axis: [3, 32, 34, 39]
axis_tags: [FE, TST, IA]
severity: P0
symptom: "First paint under Providers is null; design-token SoT incomplete; --bg-muted used but undefined"
root_cause: "Client-only ready gate; UX doc claim tokens.css?globals.css not implemented"
evidence:
  - salesos/frontend/src/app/providers.tsx (if (!ready) return null)
  - salesos/frontend/tailwind.config.ts (preset wired)
  - docs/ux/UX_ARCHITECTURE.md vs globals.css (no tokens.css import)
  - --bg-muted usage without definition in globals.css
validation_label: light validated
recommendation: "SSR-safe provider shell; import tokens into globals; eliminate undefined vars; make CI verify fail on broken UI gates when approved"
owner: frontend
status: fixed (Wave 1 SSR + Wave 2 tokens SoT; build not validated)
related_ids: []
economics_band: Med
drift_metric_ids: [DM-08]
```

### EAB-001-P0-DUP-01 ? Multiple decision engines + FastAPI route collisions

```yaml
id: EAB-001-P0-DUP-01
title: "?3 BE decision surfaces + FE STUB twin; route collisions on /decision and /decisions"
axis: [4, 26, 40, 41, 43]
axis_tags: [DUP, DTM, DRIFT, AIGOV, CAP]
severity: P0
symptom: "Platform vs Runtime collide on POST /api/v1/decision/evaluate; Center vs Runtime on /decisions/{id} and feedback schemas"
root_cause: "Parallel product evolutions without single SoT; mount order defines silent winners"
evidence:
  - salesos/backend/app/modules/decision/router.py
  - salesos/backend/domains/decision_center/router.py
  - salesos/backend/runtime/decision_runtime/router.py
  - salesos/backend/app/boot/routers.py (mount order)
  - salesos/frontend/packages/platform/decision/index.ts (STUB)
  - salesos/packages/platform/decision/ (full twin, same package name)
validation_label: light validated
recommendation: "Pick one client SoT API; deprecate/shadow others behind flags; remove FE package name collision"
owner: architecture
status: partial (Wave 2 HTTP SoT + remount; engines/twin residual; 2026-08-12 FE Center ledger + Platform explain tenant-scoped)
related_ids: [EAB-001-P1-AIGOV-01]
economics_band: Extreme
drift_metric_ids: [DM-04, DM-08]
# Stream C 2026-08-06: Runtime remounted to /api/v1/decision-runtime; SoT doc DECISION-API-SOT.md.
# Residual: three engines + FE twin package name. HTTP collisions fixed; engines not deleted.
# 2026-08-12: FE /decisions Center-only feedback; Platform explain/feedback tenant-scoped; engines retained.
```

### EAB-001-P0-OPS-01 ? DR / WAL / offsite / staging parity incomplete for GA cutover

```yaml
id: EAB-001-P0-OPS-01
title: "No production-ready offsite/WAL/PITR/staging parity for GA"
axis: [22, 29, 31, 39]
axis_tags: [OPS, REL]
severity: P0
symptom: "DR docs document open gaps; local drills ? staging soak; go-live signatures UNSIGNED"
root_cause: "Wave 10+ local evidence without signed production DR path"
evidence:
  - docs/ops/DR_RUNBOOK.md
  - docs/audit/ga-engineering-audit/PROGRESS-WAVE10-DR-GAPS.md
  - docs/audit/ga-engineering-audit/runbooks/go-live-checklist.md
  - docs/audit/ga-engineering-audit/GA_STATUS.md
validation_label: light validated
recommendation: "Offsite backup + WAL archive + staging parity + signed go-live before any cutover claim"
owner: ops
status: deferred (Wave 3 checklist; human WAL/offsite/staging/signatures)
related_ids: [EAB-001-P1-OPS-02]
economics_band: High
drift_metric_ids: []
```

---

## P1 ? High priority

### EAB-001-P1-DRIFT-01 ? Orphan MetaData islands (?18)

```yaml
id: EAB-001-P1-DRIFT-01
title: "Private MetaData() islands outside canonical Base (?18 call sites)"
axis: [6, 25, 41]
axis_tags: [DRIFT, DM]
severity: P1
symptom: "Search/KG/outbox/audit/activity/DQ/tasks/etc. construct private MetaData"
root_cause: "Historical module isolation without schema ownership program"
evidence:
  - salesos/backend/app/db05_orphan_keep.py
  - salesos/backend/app/database.py (register_orphan_keep_tables)
  - rg MetaData( under salesos/backend (?18 files)
validation_label: light validated
recommendation: "Continue DEC-130f consolidation; freeze new private MetaData; migrate KEEP inventory"
owner: backend-data
status: partial (Wave 3 freeze + KEEP pointer; residual Base islands; ceiling 6)
related_ids: []
economics_band: High
drift_metric_ids: [DM-06]
# 2026-08-12b: MetaData ceiling 17→13 (benchmark + admin COUNT stubs → table()).
# 2026-08-13: MetaData ceiling 13→6 (query/DML stubs → table()); DEC-156 proposal for residual Base merges.
```

### EAB-001-P1-OPS-02 ? Dual compose / multi-stack ambiguity

```yaml
id: EAB-001-P1-OPS-02
title: "Root vs salesos/ dual compose; ?7 compose files"
axis: [5, 31, 41]
axis_tags: [SVC, OPS, DRIFT]
severity: P1
symptom: "Two local/dev stories; Celery on root/prod not salesos/dev; event bus defaults in_memory despite Kafka"
root_cause: "Repo layout evolution without retiring root or documenting single SoT"
evidence:
  - docker-compose.yml (repo root)
  - salesos/docker-compose.yml
  - salesos/docker-compose.prod.yml
  - salesos/infra/staging/docker-compose.staging.yml
validation_label: light validated
recommendation: "Declare one authoritative compose path; deprecate or wrapper the other"
owner: ops
status: fixed (Wave 3 compose SoT honesty; merge deferred)
related_ids: [EAB-001-P0-OPS-01]
economics_band: High
drift_metric_ids: [DM-05]
```

### EAB-001-P1-SEC-03 ? Tenant ContextVar not reset after request

```yaml
id: EAB-001-P1-SEC-03
title: "TenantContextMiddleware sets ContextVar without finally reset"
axis: [30, 11]
axis_tags: [SEC, RT]
severity: P1
symptom: "set_current_tenant_id without clear; task reuse leak risk"
root_cause: "Missing request-scoped reset pattern"
evidence:
  - salesos/backend/app/common/middleware.py (TenantContextMiddleware ~L310-316)
validation_label: light validated
recommendation: "Reset ContextVar in finally; add narrow regression test when approved"
owner: backend-platform
status: fixed (Wave 2 ContextVar finally reset)
related_ids: [EAB-001-P0-SEC-02]
economics_band: Low
drift_metric_ids: []
```

### EAB-001-P1-ADR-01 ? ADR index/disk drift (101 missing; 102 unindexed; Kafka claim)

```yaml
id: EAB-001-P1-ADR-01
title: "ADR-101 indexed but missing; ADR-102 on disk unindexed; Kafka image claim mismatch"
axis: [8, 40, 41]
axis_tags: [ADR, DTM, DRIFT]
severity: P1
symptom: "docs/adr/index.md cites 0101 file absent; 0102 exists Accepted; ADR-102 text bitnami/kafka:3.6.2 vs compose confluentinc/cp-kafka:7.7.2"
root_cause: "Docs/index lag after bootstrap hardening"
evidence:
  - docs/adr/index.md
  - docs/adr/0102-engineering-hardening.md
  - salesos/docker-compose.yml (Kafka 7.7.2)
validation_label: light validated
recommendation: "Restore or retract ADR-101; index ADR-102; align ADR Kafka claim with compose"
owner: architecture
status: fixed (Wave 3 ADR-101 restore + ADR-102 index + Kafka align)
related_ids: []
economics_band: Low
drift_metric_ids: [DM-01, DM-02]
```

### EAB-001-P1-SES-01 ? No SES baseline SoT

```yaml
id: EAB-001-P1-SES-01
title: "SES Compliance SoT missing under docs/"
axis: [9, 40]
axis_tags: [SES, DTM]
severity: P1
symptom: "Axis 09 has no SES baseline/changelog to compare"
root_cause: "Methodology expects SES; product never published SES pack"
evidence:
  - docs/audit/ga-engineering-audit/enterprise-audit-board/02-METHODOLOGY.md (Axis 09)
  - Glob/search: no SES baseline under docs/
validation_label: light validated
recommendation: "Publish SES baseline or formally defer Axis 09 with N/A waiver"
owner: product-architecture
status: fixed (Wave 3 SES stub + Axis 09 waiver)
related_ids: []
economics_band: Med
drift_metric_ids: [DM-08]
```

### EAB-001-P1-LINEAGE-01 ? Data lineage Vision?code breaks

```yaml
id: EAB-001-P1-LINEAGE-01
title: "Scrapers?Notion, notion_sync, ER are disconnected; data/ tree absent"
axis: [16, 17, 18, 19]
axis_tags: [LINEAGE, GR, SRCH]
severity: P1
symptom: "No single governed Notion?canonical?ER?graph?search pipeline; packages/data absent from workspace"
root_cause: "Parallel ingest worlds; EVENT_BUS_TYPE defaults in_memory"
evidence:
  - packages/scrapers/*
  - salesos/backend/app/modules/notion_sync/
  - salesos/backend/app/modules/entity_resolution/
  - salesos/docker-compose.yml EVENT_BUS_TYPE:-in_memory
validation_label: light validated
recommendation: "Document honest lineage map; wire or quarantine hops; do not claim end-to-end intelligence pipeline GA"
owner: data-platform
status: fixed (Wave 3 honesty map; pipeline breaks documented)
related_ids: []
economics_band: Extreme
drift_metric_ids: [DM-03, DM-08]
```

### EAB-001-P1-DUP-02 ? Dual search / multi-webhook / multi-prompt registry

```yaml
id: EAB-001-P1-DUP-02
title: "Duplicate search routers, webhook families, prompt registries"
axis: [13, 17, 26]
axis_tags: [DUP, SRCH, PRM]
severity: P1
symptom: "runtime/search_runtime + app/routers/search; multiple webhook surfaces; ?3 prompt registries"
root_cause: "Capability sprawl without deprecation"
evidence:
  - salesos/backend/runtime/search_runtime/router.py
  - salesos/backend/app/routers/search.py
  - salesos/backend/app/modules/webhooks/router.py
  - salesos/backend/intelligence/prompts/registry.py
  - salesos/backend/domains/ai/registry.py
validation_label: light validated
recommendation: "Capability register with SoT per surface; deprecate duplicates"
owner: architecture
status: partial (Wave 2 capability notes; code remount not required for search)
related_ids: [EAB-001-P0-DUP-01]
economics_band: High
drift_metric_ids: [DM-04]
# Stream C 2026-08-06: capability register in DECISION-API-SOT.md (doc only; no remount).
```

### EAB-001-P1-AIGOV-01 ? AI Governance structural fragmentation (honesty gates hold)

```yaml
id: EAB-001-P1-AIGOV-01
title: "Multi-engine decision transparency + OpenAI gravity; FE package name twin"
axis: [12, 13, 14, 43]
axis_tags: [AIGOV, AIA]
severity: P1
symptom: "Explain/reasoning/audit split; vendor default OpenAI; same npm name for STUB and full twin"
root_cause: "AI surfaces grew faster than single governance spine"
evidence:
  - docs/audit/ga-engineering-audit/AI_HONESTY.md
  - salesos/backend/app/config.py feature_ai_copilot=False
  - salesos/frontend/packages/platform/decision/index.ts STUB
  - salesos/packages/platform/decision/ full twin
validation_label: light validated
recommendation: "Keep flags False; rename/remove twin package; unify explainability API; HITL for consequential NBA execute"
owner: ai-governance
status: partial (Wave 2 labels + Decision SoT; multi-engine residual)
related_ids: [EAB-001-P0-DUP-01]
economics_band: High
drift_metric_ids: [DM-10]
# Stream C 2026-08-06: HTTP SoT + FE STUB/twin package labels (DECISION-API-SOT.md).
# Residual: multi-engine explainability + same package name; flag remains False.
```

### EAB-001-P1-DOC-01 ? Dual Product/Project Bible + superseded GO docs hazard

```yaml
id: EAB-001-P1-DOC-01
title: "PRODUCT_BIBLE vs PROJECT_BIBLE conflict; superseded GO docs still citeable"
axis: [1, 10, 41]
axis_tags: [AG, PB, DRIFT]
severity: P1
symptom: "Bible maturity / AI-native language can outrun audit NO-GO; vNext GO artifacts still on disk"
root_cause: "Naming collision + incomplete quarantine enforcement"
evidence:
  - PRODUCT_BIBLE.md / docs/PROJECT_BIBLE.md
  - docs/vnext/reports/GO_NO_GO_DECISION.md (SUPERSEDED)
  - docs/vnext/reports/gates/G04_AI_VALIDATION.md (SUPERSEDED)
  - AGENTS.md (audit wins)
validation_label: light validated
recommendation: "Banner + link quarantine; bible claims must defer to ga-engineering-audit for GO"
owner: docs-governance
status: fixed (Wave 3 bible banners; GO quarantine)
related_ids: []
economics_band: Low
drift_metric_ids: [DM-07, DM-09]
```

---

## P2 ? Material debt

### EAB-001-P2-FIT-01 ? Fitness catalog not automated

```yaml
id: EAB-001-P2-FIT-01
title: "FF-01?FF-14 catalog exists; 0% automated in CI"
axis: [28, 41]
axis_tags: [FIT, DRIFT]
severity: P2
symptom: "Axis 28 and G-06 remain near zero"
root_cause: "Pack v2.2 defines fitness; no CI wiring yet (needs approval for L3)"
evidence:
  - docs/audit/ga-engineering-audit/enterprise-audit-board/05-FITNESS-CATALOG.md
validation_label: light validated
recommendation: "Automate FF-07, FF-09, FF-10, FF-12 as first CI subset when approved"
owner: platform-eng
status: deferred (Wave 3 plan only; CI needs approval)
related_ids: []
economics_band: Med
drift_metric_ids: []
```

### EAB-001-P2-SEC-04 ? CSRF bypass when SALESOS_TESTING=true

```yaml
id: EAB-001-P2-SEC-04
title: "CSRF enforcement skipped under SALESOS_TESTING=true"
axis: [30]
axis_tags: [SEC]
severity: P2
symptom: "Test env flag disables CSRF"
root_cause: "Test convenience without production assert"
evidence:
  - salesos/backend/app/common/middleware.py (CsrfEnforcementMiddleware)
validation_label: light validated
recommendation: "Ensure production templates never set SALESOS_TESTING"
owner: backend-platform
status: deferred mitigated (Wave 2 compose pin + prod WARN; bypass kept for tests)
related_ids: []
economics_band: Low
drift_metric_ids: []
```

---

## Counts

| Severity | Count (this run) | After Waves 1?3 |
|----------|-----------------:|-----------------|
| P0 | **5** | 3 Fixed � 1 Partial � 1 Deferred |
| P1 | **9** | 6 Fixed � 3 Partial |
| P2 | **2** | 2 Deferred/mitigated |
| **Total** | **16** | **0 Open undispositioned** |

**Security residual P0s (G-09):** SEC-01/02 code-fixed; OPS/FE/DUP no longer fail-open factory class. Production **NO-GO** until OPS-01 human blockers + re-board.

Program status: [REMEDIATION-PROGRAM-STATUS.md](./REMEDIATION-PROGRAM-STATUS.md)

---

*Findings ? EAB-2026-08-06-001 ? light validated ? no commit / no heavy suites*
