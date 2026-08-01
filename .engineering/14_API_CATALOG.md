---
EngineeringOS: v3
GeneratedAt: 2026-08-01T12:11:50Z
RepositoryCommit: c89025a
RepositoryBranch: master
Generator: OpenCode
Status: Corrected (EOS v3.1 cycle)
EvidenceLevel: Heuristic
Revalidation: Pending
---

# 14 â€” API CATALOG

> The HTTP surface. Backend registers **67** `include_router` calls in `app/boot/routers.py` (boot contract; `Select-String include_router` = 67 lines). All business routes are under `/api/v1/`.
> **B4 fix:** v3.0 invented `/api/v1/crm/*` â†’ `modules/crm`. Neither exists. The `crm` string is absent from `app/boot/routers.py` and from `app/modules/`. CRM surface = commercial/opportunity modules instead.

## 1. Routers mounted with an explicit prefix (verified in `app/boot/routers.py`)

| Router | Mounted prefix | Tags |
|---|---|---|
| identity_router | `/api/v1/identity` | Identity |
| company_router | `/api/v1/companies` | Companies |
| contact_router | `/api/v1/contacts` | Contacts |
| entity-resolution router | `/api/v1/entity-resolution` | â€” |
| graph_router | `/api/v1` (+ router-local `/graph`) | Knowledge Graph |
| graphql_router | `/graphql` | â€” |

## 2. Routers mounted at `/api/v1` (router-local paths expand inside; sampled)

notion_sync, excel_import, employee_360, employee_domain, employee_webhook, executive, dashboard, work_intelligence, decision_center, activity, event_runtime, data_fabric, feature_store, decision (Decision Engine), timeline, search, search_api, sso, communication_hub, audit, api_keys, copilot, commercial, workflow, opportunities, meetings, revenue, nba, pipeline_analytics, rag, analytics, ai, notifications, enrichment.

**Mounted with `prefix=""`:** employee_health (`include_in_schema=False`), decision_platform (Decision Platform), revenue_execution (Revenue Execution).

> **N4 note:** a naive full-string search for a prefix under-reports these because they are mounted at `/api/v1` with router-local paths. `/api/v1/crm` remains **truly absent**.

## 3. Non-REST

| Surface | Path | Notes |
|---|---|---|
| GraphQL | `/graphql` | auth-protected (`app/graphql/schema.py`) |
| Health | `/ping`, `/health/live`, `/health/detailed` | `app/main.py` + `app/health.py` |
| Well-known | `/.well-known/jwks.json` | RS256 JWKS |
| Metrics/monitoring | `/metrics`, `/monitoring` | public surfaces |

## 4. Auth model

- Bearer JWT (RS256) via identity module; browser refresh flow via FE middleware.
- Router-level `verify_token` used on sensitive surfaces (e.g., `/api/v1/capabilities`).
- CSRF token endpoint exposed for browser flows.

## 5. Endpoint drift evidence

- **ADR-033 conflict:** documented endpoint contract vs observed prefixes differ (see `27`, `28`).
- OpenAPI/docs: `scripts/generate_api_docs.sh` exists; docs artifacts untracked â€” rely on `routers.py` as source of truth.
- **Per-endpoint inventory is NOT maintained in EOS** (audit 32 Missing References): prefix-level only. Do not cite a specific path without checking `routers.py` + router file.

## 6. When this file changes

- On endpoint add/remove/move. Source of truth: `app/boot/routers.py`. Mirror `08` (flows), `29` (capabilities), `28` (ADR contracts).
