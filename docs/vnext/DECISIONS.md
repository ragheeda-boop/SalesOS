# SalesOS vNext — Architecture Decision Records Index

> Strategic decisions required for vNext. Each entry represents a decision that must be made before or during the vNext development cycle.

---

## D-001: Monorepo vs Multi-repo

| Field | Value |
|-------|-------|
| **Status** | Proposed |
| **Context** | Current codebase is a single repo with 15 domains, 31 runtimes, 57 routers, 13 frontend packages. The monolithic `api.ts` (1,240 lines) and `main.py` (773 lines) create coupling. vNext must decide whether to split. |
| **Option A: Monorepo** | **Pros**: Atomic commits, shared CI, single version, easy refactoring. **Cons**: No independent deploy, build times grow, no access control per domain. |
| **Option B: Multi-repo** | **Pros**: Independent deploy per domain, team ownership, smaller surface. **Cons**: Version coordination hell, cross-repo refactoring, CI duplication. |
| **Option C: Hybrid monorepo (recommended)** | Single repo with package-level boundaries, strict import rules, independent CI per domain. Use Nx/Turborepo for build orchestration. |
| **Recommendation** | **Option C** — keep single repo but enforce domain boundaries with tooling. Fix the monolithic files immediately (R-023, R-024). |
| **Consequences** | + Enables independent CI per domain + Enforces bounded contexts + Add build overhead (Nx) + Requires eslint-plugin-import boundaries |

---

## D-002: REST-first vs GraphQL-first API Strategy

| Field | Value |
|-------|-------|
| **Status** | Proposed |
| **Context** | Current API is REST with a separate GraphQL endpoint missing auth (R-039). vNext API surface needs to scale across 15 domains. |
| **Option A: REST-first** | Standard REST with OpenAPI docs + codegen client SDK. Proven, cacheable, wide tooling support. |
| **Option B: GraphQL-first** | Single GraphQL endpoint, client-driven queries. Solves N+1 (R-006) at protocol level. But auth harder; caching complex. |
| **Option C: REST + GraphQL coexistence** | REST for public API, GraphQL for internal frontend. Pragmatic but dual maintenance. |
| **Recommendation** | **Option A** — REST-first for vNext. Add GraphQL later when query flexibility is proven necessary. Fix GraphQL auth immediately (R-039). |
| **Consequences** | + Proven, simple + Easy client codegen + No auth complexity + N+1 must be solved at DB layer (DataLoader) + Future GraphQL is possible |

---

## D-003: API Versioning Strategy

| Field | Value |
|-------|-------|
| **Status** | Proposed |
| **Context** | Current API has zero versioning (R-026). Breaking changes deployed without migration path. 57 routers across 15 domains need a strategy. |
| **Option A: URL versioning** | `/api/v1/companies`, `/api/v2/companies`. Simple, discoverable. |
| **Option B: Header versioning** | `Accept: application/vnd.salesos.v2+json`. Cleaner URLs, harder to test. |
| **Option C: Query versioning** | `/api/companies?version=2`. Easy to implement, but clutters URLs and caching. |
| **Recommendation** | **Option A** — URL versioning (`/api/v1/...`, `/api/v2/...`). Most visible, easiest for API consumers, best tooling support. |
| **Consequences** | + Clear migration path + Easy to deprecate old versions + URL bloat (minor) + All 57 routers need v1 prefix |

---

## D-004: Event Bus Migration

| Field | Value |
|-------|-------|
| **Status** | Proposed |
| **Context** | Kafka deployed but runs in dual mode with in-memory event bus. Kafka has no healthcheck (R-008). Current in-memory bus loses events on restart. TD-002 tracks this. |
| **Option A: Keep dual mode** | In-memory for dev, Kafka for prod. Two code paths to maintain; risk of divergence. |
| **Option B: Full Kafka adoption** | Remove in-memory bus; Kafka everywhere. Requires healthcheck fix, Docker Compose stability. |
| **Option C: Lightweight message broker** | Replace both with Redis Streams or NATS. Simpler ops than Kafka, but Kafka already deployed. |
| **Recommendation** | **Option B** — Full Kafka adoption. Fix healthcheck, add Celery worker, remove in-memory bus. Phase with migration per domain. |
| **Consequences** | + Single event bus + Production-grade durability + Ops complexity + Devs need Kafka locally + Sprint 1-2 effort |

---

## D-005: Agent Runtime Architecture

| Field | Value |
|-------|-------|
| **Status** | Proposed |
| **Context** | Agent runtime is placeholder (R-010). 5 runtime stubs exist (agent, execution, scheduler, simulation, workflow) (R-028). Zero AI tests (R-004). |
| **Option A: Embedded runtime** | Agents run in same process as API. Simple, low latency, but no isolation. |
| **Option B: Sidecar runtime** | Separate agent service per tenant or per agent type. Isolated, scalable, but complex orchestration. |
| **Option C: Hybrid** | Embedded for simple agents (classification, summarization), sidecar for complex (multi-step, tool-using). |
| **Recommendation** | **Option C** — Start with embedded for AI service calls (proven pattern), build sidecar for agents in Sprint 11-12. |
| **Consequences** | + Simple start + Scales for complex agents + Two code paths + Needs careful isolation boundaries |

---

## D-006: AI Multi-Provider Strategy

| Field | Value |
|-------|-------|
| **Status** | Proposed |
| **Context** | Currently OpenAI-only (R-032). KSA data sovereignty concerns (R-012). No AI tests (R-004). |
| **Option A: Keep OpenAI-only** | Simplest, but violates KSA data residency requirements. |
| **Option B: Multi-provider abstraction** | Provider interface with OpenAI + Anthropic + local (Llama via Ollama/vLLM). Strategy pattern for model selection per tenant. |
| **Option C: Self-hosted only** | All models local via vLLM/Ollama. Full data sovereignty, but quality gap vs cloud models. |
| **Recommendation** | **Option B** — Provider abstraction. Default to OpenAI, allow Anthropic, offer local for KSA tenants. Add tests for each provider. |
| **Consequences** | + Data sovereignty compliance + Model flexibility + Provider interface maintenance + Test matrix grows 3x |

---

## D-007: i18n Framework for Arabic/RTL

| Field | Value |
|-------|-------|
| **Status** | Proposed |
| **Context** | Product targets Saudi market (R-030, R-014). UI is English-primary. No i18n framework exists. Arabic text normalization has a known bug (BUG-002). |
| **Option A: react-intl (FormatJS)** | Mature, ICU message syntax, rich-plural support, good RTL handling. |
| **Option B: react-i18next** | Most popular React i18n, lazy loading, TypeScript support, but heavier. |
| **Option C: LinguiJS** | Build-time compiled messages, smallest bundle, strong TypeScript. |
| **Recommendation** | **Option A** — `react-intl` (FormatJS). Best Arabic/RTL support, ICU message format standard, lightweight. |
| **Consequences** | + Full Arabic translation + RTL layout support + Translation management needed + Sprint 19-20 allocation |

---

## D-008: Data Fabric Architecture

| Field | Value |
|-------|-------|
| **Status** | Proposed |
| **Context** | Data Fabric is 65% complete (R-033). Connectors return mock data (R-013). Feature Store and Entity Resolution implemented but connectors missing. |
| **Option A: Direct connector per source** | Custom connector for each data source (HubSpot, Salesforce, Zoho, etc.). Maximum flexibility, maximum effort. |
| **Option B: Standard connector SDK** | Build connector SDK with interface, then implement connectors against it. Reusable, testable. |
| **Option C: Third-party integration platform** | Use Airbyte or Meltano for ELT. Faster time-to-value, but adds dependency. |
| **Recommendation** | **Option B** — Build lightweight connector SDK. Implement top-3 connectors (HubSpot, Salesforce, Zoho). Re-evaluate Airbyte in Phase 7. |
| **Consequences** | + Standardized connector model + Testable connector contracts + Top-3 connectors in Sprint 15-16 + Airbyte evaluation deferred |

---

## D-009: Caching Strategy Unification

| Field | Value |
|-------|-------|
| **Status** | Proposed |
| **Context** | Redis deployed in production (ephemeral only — no persistence/RPO obligation). Rate limiting uses Redis. Caching is Redis-backed. See live `/health` endpoint: `"redis":"connected"`. |
| **Option A: Redis everywhere** | Redis for cache, rate limiting, session store. Single dependency, well-understood. |
| **Option B: Multi-tier** | Redis for cache, database for persistent rate limits (PostgreSQL). More complex but no single point of failure. |
| **Option C: In-memory + Redis** | In-memory L1 cache per service, Redis L2. Lowest latency, highest complexity. |
| **Recommendation** | **Option A** — Redis everywhere. Deploy in Sprint 1. Replace in-memory rate limiting. Centralize cache configuration. |
| **Consequences** | + Single caching backend + Deploy Redis to production + Ops dependency + Cache invalidation strategy needed |

---

## D-010: Frontend State Management

| Field | Value |
|-------|-------|
| **Status** | Proposed |
| **Context** | 13 frontend packages with no import boundaries (R-027). No unified state management pattern. |
| **Option A: React Query + Context** | React Query for server state, React Context for client state. Minimal dependencies, proven pattern. |
| **Option B: React Query + Zustand** | React Query for server state, Zustand for client state. More performant than Context, simpler API. |
| **Option C: Redux Toolkit** | Single store for all state. Overkill for most cases, but strict patterns. |
| **Recommendation** | **Option B** — React Query + Zustand. Add import boundary enforcement. |
| **Consequences** | + Server/client state separation + Performant + Simple API + Add Zustand dependency + Remove unused state solutions |

---

## D-011: Widget SDK v1.1 Evolution

| Field | Value |
|-------|-------|
| **Status** | Proposed |
| **Context** | Widget SDK v1.0 is Feature Frozen per Engineering Constitution §9.4. Current patterns work, but gaps may emerge. |
| **Option A: Keep frozen** | No changes to SDK. Force all new needs through ADR process. |
| **Option B: Minor v1.1 update** | Address documented gaps with non-breaking additions. Requires ADR-003 review. |
| **Recommendation** | **Option A** — Keep v1.0 frozen for vNext Phase 0-2. Re-evaluate at Phase 3 with concrete gap evidence. |
| **Consequences** | + Stability + ADR requirement enforced + May limit some widget patterns + Gaps must be proven before changes |

---

## D-012: Plug-in Architecture vs Extension API

| Field | Value |
|-------|-------|
| **Status** | Proposed |
| **Context** | 5 runtime stubs (R-028) suggest future extensibility. No current plug-in mechanism. Data Fabric connectors need extension model. |
| **Option A: Plugin architecture** | Hot-loadable plugins with lifecycle hooks. Maximum extensibility, maximum complexity. |
| **Option B: Extension API** | Defined extension points (connectors, hooks, middleware). Simpler, well-scoped. |
| **Option C: Both** | Extension API for common cases, plugin system for advanced. |
| **Recommendation** | **Option B** — Extension API. Define connector interface, webhook handler interface, notification channel interface. Add more as needed. |
| **Consequences** | + Simple to implement + Clear extension boundaries + No runtime plugin loading + Requires versioning for extensions |

---

## D-013: Test Consolidation Strategy

| Field | Value |
|-------|-------|
| **Status** | Proposed |
| **Context** | 93% coverage (2110+ tests, 269 E2E). But zero AI tests (R-004). Data Fabric untested. Test patterns inconsistent across domains. |
| **Option A: Status quo** | Continue per-domain testing. Fill AI and Data Fabric gaps. |
| **Option B: Unified test framework** | Standardize on single test pattern (Given/When/Then). Centralize test utilities. |
| **Option C: Test pyramid audit** | Audit existing tests for quality, consolidate utilities, add missing layers. |
| **Recommendation** | **Option C** — Audit existing tests, consolidate shared utilities into test-lib package, fill AI and Data Fabric gaps. |
| **Consequences** | + Consistent test patterns + Reduced duplication + AI test coverage from zero + Audit effort (3 days) |

---

## D-014: Configuration Management

| Field | Value |
|-------|-------|
| **Status** | Proposed |
| **Context** | Multiple `.env.*` files, hardcoded configs in code (TD-004), secrets in repo history. No unified config management. |
| **Option A: Consolidate .env** | Single .env file with documented schema. Still manual, still error-prone. |
| **Option B: Pydantic Settings + Vault** | Centralized config via Pydantic BaseSettings. Secrets from Vault. All config validated at startup. |
| **Option C: Config service** | Microservice serving config to all runtimes. Over-engineered for current scale. |
| **Recommendation** | **Option B** — Pydantic BaseSettings for all domains. Vault for secrets. Single config schema per service. |
| **Consequences** | + Validated config at startup + No scattered env reads + Vault dependency + Migration effort for all domains |

---

## D-015: Helm vs Raw K8s for Deployment

| Field | Value |
|-------|-------|
| **Status** | Proposed |
| **Context** | Current deployment via Docker Compose. 31 runtimes need orchestration at scale. No CI/CD load testing (R-014 gap). |
| **Option A: Helm charts** | Industry standard for K8s. Parameterized, reusable, ecosystem support. |
| **Option B: Kustomize** | Native K8s, no template syntax, pure YAML patches. Simpler but less powerful. |
| **Option C: Raw Docker Compose (stay)** | Simplest but doesn't scale to multi-node. |
| **Recommendation** | **Option A** — Helm charts. Start with umbrella chart for all 31 runtimes. Add per-domain sub-charts. |
| **Consequences** | + Industry standard + Reusable deploy patterns + Learning curve + Needed for multi-node scaling |

---

## D-016: Widget SDK Reconciliation (ADR-0032)

| Field | Value |
|-------|-------|
| **Status** | ✅ **Approved** — 2026-07-16 |
| **Supersedes** | ADR-003 amended (not replaced) — consolidation mandate added |
| **Context** | PRC Gate G-1 found Dual Widget SDK violation (P0). Two `createWidget()` implementations exist: Dashboard SDK (`src/features/dashboard/sdk/`) frozen v1.0 per ADR-003, and Workspace SDK (`packages/workspace/`) v5 containing a duplicate fork. Both define overlapping API surfaces, identical type sets, and near-identical testing utilities. Violates Engineering Constitution §3.4 (Frozen Interface) and §9.1 (Widget SDK mandatory). |
| **Decision** | Dashboard SDK v1.0 remains the single canonical Widget SDK. Move to `packages/widget-sdk/` as `@salesos/widget-sdk`. Workspace SDK's duplicated `createWidget()`, types, lifecycle, permissions, flags, telemetry, and testing utilities are deleted. `createWorkspaceWidget()` is retained as a thin wrapper that imports from the canonical SDK. Workspace infrastructure (`WorkspaceGrid`, `WorkspaceProvider`, workspace components) is unique and retained. |
| **Rationale** | (1) Respects ADR-003 frozen surface — this is relocation + deduplication, not an API change. (2) Dashboard SDK uses CSS variables and `@salesos/ui` — superior to inline styles. (3) Has Decision Platform integration. (4) Aligns with ARCHITECTURE_VNEXT.md `@salesos/widget-sdk` target. (5) No v1.1 — satisfies D-011. |
| **Refinements** | R1: Preserve Arabic status labels in canonical SDK. R2: Retain `mockTelemetry.ts` in workspace. R3: Retain `createEmptyWidget()` in workspace testing. R4: Explicitly document this is not a v1.1 surface change. |
| **Migration effort** | ~4 days (2.5 parallelized). 7 dashboard + ~36 workspace consumer import updates. |
| **Consequences** | + Single source of truth + DRY eliminated + Frozen surface preserved + Import path changes for all widget consumers + CI enforcement rules added |

---

*Last updated: 2026-07-16*
