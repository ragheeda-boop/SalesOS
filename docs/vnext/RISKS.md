# SalesOS vNext — Risk Register

> Generated from Sprint 13 audit (2026-07-14). Overall readiness: 7.5/10, 79-85% complete.

---

## Risk Matrix Legend

| Impact | Description |
|--------|-------------|
| Critical | System down, data loss, security breach |
| High | Major feature degradation, significant rework |
| Medium | Operational friction, minor degradation |
| Low | Cosmetic, nice-to-have |

| Likelihood | Description |
|------------|-------------|
| Certain | >90% will occur |
| Likely | 50-90% |
| Possible | 10-50% |
| Unlikely | <10% |

---

## 1. Current Risks (Exist Today)

| ID | Risk | Impact | Likelihood | Severity | Mitigation |
|----|------|--------|------------|----------|------------|
| R-001 | **Webhooks router — no authentication** — any unauthenticated actor can create, read, update, or delete webhooks | Critical | Certain | **Critical** | Add auth middleware to webhooks router; backport to existing sprint |
| R-002 | **Admin router — in-memory state** — all admin panel state (feature flags, config overrides) lost on process restart | High | Certain | **High** | Migrate admin state to PostgreSQL; add persistence layer |
| R-003 | **Terraform — no remote state** — state file local-only; team members overwrite each other; state loss on machine failure | High | Likely | **High** | Configure S3/Azure Blob backend with DynamoDB/ CosmosDB locking |
| R-004 | **No AI tests** — 0 backend AI tests; prompt changes, model upgrades, agent behavior cannot be verified | High | Certain | **High** | Sprint 11-12: add PromptRegistry tests, AIService tests, evaluation harness |
| R-005 | **Body consumption bug in middleware** — POST bodies consumed before route handlers; blocks all HTTP load testing | High | Certain | **High** | Fix middleware chain to not consume request body; use streaming or cache |
| R-006 | **N+1 workspace/NBA pattern** — up to 200+ DB queries per single workspace request | High | Certain | **High** | Batch load with DataLoader pattern; eager-load relationships |
| R-007 | **No backup restore verification** — backups run but restore is never tested; first disaster will reveal gaps | High | Likely | **High** | Add quarterly restore drill to runbook; automate restore test in CI |
| R-008 | **Kafka — no healthcheck in Docker Compose** — startup race condition; services connect before Kafka is ready | Medium | Likely | **Medium** | Add healthcheck (kafka-topics --bootstrap-server); depends_on with condition |
| R-009 | **Celery — no worker service in Docker Compose** — background tasks silently fail in dev/staging | Medium | Certain | **Medium** | Add celery worker service to docker-compose.yml |
| R-010 | **Agent runtime is placeholder** — cannot execute agents; agent orchestration layer is stub | Medium | Certain | **Medium** | Implement agent runtime in Sprint 11-12 |
| R-011 | **Redis deployed but ephemeral only** — rate limiting and caching use Redis (verified: `/health` → `"redis":"connected"`), but no persistence/backup/RPO obligation. Data is reconstructable. | Low | Likely | **Low** | Accept ephemeral Redis scope; exclude from RPO/RTO per ADR-108 scope decision. |
| R-012 | **OpenAI vendor lock-in** — only one AI provider; KSA data sovereignty concerns | Medium | Possible | **Medium** | Add Anthropic + local model support via provider abstraction |
| R-013 | **Data Fabric connectors return mock data** — all Data Fabric integrations return synthetic/mock data | High | Certain | **High** | Implement real connectors in Sprint 15-16 |
| R-014 | **No i18n framework** — Saudi-market product with English-only UI; Arabic/RTL claims unsupported | High | Possible | **High** | Add i18n framework (react-intl / Lingui); full Arabic pass in Sprint 19-20 |
| R-015 | **Multi-tenancy is scaffold only** — tenant isolation, data separation, tenant provisioning are not implemented | High | Certain | **High** | Implement tenant module in Sprint 17-18 |
| R-016 | **Neo4j f-string queries** — Cypher queries built with f-strings; potential NoSQL injection | Critical | Possible | **Critical** | Use parameterized queries throughout; add SAST rule banning f-strings in Neo4j |

---

## 2. Future Risks (Issues at Scale)

| ID | Risk | Impact | Likelihood | Severity | Mitigation |
|----|------|--------|------------|----------|------------|
| R-017 | **No partition strategy** — all companies in single table; 1M+ companies make full scans prohibitive | High | Possible | **High** | Implement tenant-based partitioning or time-range partitioning before 500k records |
| R-018 | **OFFSET pagination on 12+ endpoints** — 3800kB memory spill at 10k rows; deep pagination degrades rapidly | Medium | Likely | **Medium** | Migrate to keyset (cursor-based) pagination; budget 1 sprint |
| R-019 | **Wide companies table (3341-byte rows)** — TOAST overhead; SELECT * perf degrades with column count | Medium | Possible | **Medium** | Vertical split: move infrequently-accessed columns to separate tables |
| R-020 | **3072-dim vectors without HNSW index** — ANN index missing; sequential scan fallback at scale | High | Possible | **High** | Add HNSW index on vector column; monitor index build time |
| R-021 | **Single-node PostgreSQL (no HA)** — node failure = complete data unavailability until manual recovery | High | Possible | **High** | Configure streaming replication + pgpool/pgbouncer for HA |
| R-022 | **Docker Desktop ~5s overhead per request** — environment limitation skews perf measurements | Medium | Unlikely | **Low** | Document as known limitation; use native Linux for perf benchmarks |

---

## 3. Architecture Risks

| ID | Risk | Impact | Severity | Mitigation |
|----|------|--------|----------|------------|
| R-023 | **Monolithic api.ts (1,240 lines)** — 57 routers in one file; every new domain increases merge conflict probability | High | **High** | Split into per-domain router files; one file per bounded context |
| R-024 | **Monolithic main.py (773 lines)** — startup registration, middleware, exception handlers all coupled; any startup failure cascades | High | **High** | Modularize startup with plugin/extension pattern |
| R-025 | **Knowledge graph runtime (1,087 lines)** — single file handles graph traversal, embedding, caching, and API | High | **High** | Decompose into GraphService, EmbeddingService, CacheService |
| R-026 | **No API versioning** — breaking changes deployed without migration path; API consumers break silently | High | **High** | Adopt URL-based versioning (`/api/v2/...`); deprecation policy |
| R-027 | **No import boundaries on 13 frontend packages** — cross-package coupling; cannot independently version or test packages | High | **High** | Add eslint-plugin-import boundary rules; enforce with CI |
| R-028 | **5 runtime stubs (agent, execution, scheduler, simulation, workflow)** — scaffold code creates illusion of completeness | Medium | **Medium** | Implement or remove by Sprint 12; document known gaps |
| R-029 | **API client maintenance burden** — growing daily as new endpoints added without client generation | Medium | **Medium** | Adopt OpenAPI codegen for client SDK |

---

## 4. Business Risks

| ID | Risk | Impact | Severity | Mitigation |
|----|------|--------|----------|------------|
| R-030 | **Saudi market without Arabic i18n** — primary market cannot use product in their language | High | **High** | Block GA until i18n framework + Arabic translation pass |
| R-031 | **Multi-tenancy feature gap** — docs claim multi-tenant; actual implementation is scaffold | High | **High** | Update documentation; prioritize tenant isolation in Sprint 17-18 |
| R-032 | **OpenAI lock-in for KSA data sovereignty** — customer data may not leave KSA; OpenAI requires US processing | High | **High** | Add local model support (Llama, Mistral) via Ollama/vLLM |
| R-033 | **Data Fabric mock connectors** — Data Fabric is 65% complete (per dashboard); real value is blocked on connectors | High | **High** | Prioritize top-3 connectors (HubSpot, Salesforce, Zoho) |
| R-034 | **GA declared with maturing domains** — Settings (65%), Data Fabric (65%) are below GA bar | Medium | **Medium** | Either delay GA or clearly label beta features |

---

## 5. Technical Risks

| ID | Risk | Impact | Severity | Mitigation |
|----|------|--------|----------|------------|
| R-035 | **284 `Any` types across codebase** — type safety erosion; refactoring becomes dangerous | Medium | **Medium** | Add mypy strict mode; budget 1 sprint for Any reduction |
| R-036 | **InMemoryNotificationRepository** — notifications lost on restart; used in production | High | **High** | Implement PostgreSQL NotificationRepository |
| R-037 | **`vectors` table wrong column type** — vector data stored as incompatible type | High | **High** | Fix column type; add migration with validation |
| R-038 | **`print()` / `console.debug()` in production code** — debug output leaks in production logs | Low | **Low** | Add pre-commit hook; CI lint check for debug statements |
| R-039 | **GraphQL endpoint missing FastAPI-level auth** — GraphQL queries bypass auth middleware | Critical | **Critical** | Add auth dependency to GraphQL route; test with unauth query |
| R-040 | **MCP server has no rate limiting** — no protection against abuse | High | **High** | Add rate limiting middleware to MCP server |
| R-041 | **Decision engine (1,003 lines)** — fourth monolithic file; complex domain logic in single module | High | **High** | Decompose into DecisionService, RuleEngine, ScoringService |

---

## Mitigation Plan Summary

| Priority | Risk IDs | Sprint | Effort | Owner |
|----------|----------|--------|--------|-------|
| P0 | R-001, R-016, R-039 | Current | 3 days | Security |
| P0 | R-004 | 11-12 | 5 days | AI Team |
| P0 | R-005 | 1 | 2 days | Backend |
| P0 | R-006 | 1 | 3 days | Backend |
| P0 | R-033 | 15-16 | 10 days | Integration |
| P1 | R-002, R-003, R-036 | 1-2 | 5 days | DevOps |
| P1 | R-007 | 2 | 2 days | DevOps |
| P1 | R-008, R-009, R-011 | 1 | 3 days | DevOps |
| P1 | R-014, R-030 | 19-20 | 15 days | Frontend |
| P1 | R-015, R-031 | 17-18 | 10 days | Backend |
| P1 | R-012, R-032 | 11-12 | 5 days | AI Team |
| P1 | R-023, R-024, R-025, R-041 | 1-4 | 8 days | Architecture |
| P2 | R-017, R-018, R-019, R-020 | 21-22 | 10 days | Database |
| P2 | R-021 | 21-22 | 5 days | DevOps |
| P2 | R-026 | 3-4 | 3 days | Backend |
| P2 | R-027 | 3-4 | 3 days | Frontend |
| P2 | R-035 | 3-4 | 5 days | All teams |
| P3 | R-010, R-028 | 11-12 | 10 days | AI Team |
| P3 | R-013 | 15-16 | 15 days | Integration |
| P3 | R-038 | 1 | 1 day | All teams |
| P3 | R-040 | 1 | 1 day | Backend |

---

## Risk Distribution

```
Current:  ████████████████████ 16 risks
Future:   ██████               6 risks
Arch:     ████████             7 risks
Business: ██████               5 risks
Technical: ████████            7 risks
Total:    41 risks (2 Critical, 19 High, 15 Medium, 5 Low)
```

---

*Last updated: 2026-07-16*
