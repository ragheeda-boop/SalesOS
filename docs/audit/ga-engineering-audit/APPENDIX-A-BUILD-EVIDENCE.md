# APPENDIX A — Build & Runtime Evidence

**Audit date:** 2026-07-22  
**Host:** Windows 10, Node v22.14.0, Python 3.11.9, Docker 29.6.1  

## Commands executed

| Command | Where | Result | Notes |
|---------|-------|--------|-------|
| `npm run lint` | `salesos/frontend` | **FAIL** exit 1 | Errors: `TenantList.tsx` rules-of-hooks; `admin-queries.test.tsx` display-name; `dashboard-metrics-header.tsx` no-html-link; `SearchHeader.tsx` unescaped entities; many Tailwind color warnings |
| `npx tsc --noEmit` | `salesos/frontend` | **FAIL** exit 1 | 3 TS errors (Workflow type, StepResultEntry cast, Skeleton `style` prop) |
| `npm run build` | `salesos/frontend` | **FAIL** exit 1 | Blocked by ESLint errors during Next build |
| `npx jest … admin-queries` | `salesos/frontend` | **PASS** | 4/4 tests (suite still lint-errors in that file) |
| `python -m poetry install` | `salesos/backend` | **FAIL** | `asyncpg` needs MSVC; built against cpython-314 unexpectedly |
| `docker compose -f salesos/docker-compose.yml ps` | host | Running | backend/frontend healthy; postgres flapped; neo4j **unhealthy** |
| `GET /ping`, `/health/live`, `/health/detailed` | localhost:8000 | **200** | detailed: DB connected; cache/graph/kafka **not_configured**; version `0.1.0` |
| `GET localhost:3000/*` routes | host | Mixed | Many 200; `/copilot`,`/analytics`,`/marketplace`,`/employees`,`/knowledge`,`/signals`,`/rules`,`/activities` **404** |
| `alembic current` / `heads` | backend container | Drift | current **0033**, head **0038** |
| `pytest tests/unit` (ignore mcp) | backend container | **NOT GREEN** | 213 passed, 4 failed, 16 errors (stopped at maxfail=20) |
| `pytest tests/unit/test_mcp_server.py --collect-only` | backend container | **ERROR** | `ModuleNotFoundError: No module named 'mcp'` |
| Unauthenticated API probes | localhost:8000 | Auth required | Missing Authorization → **422** (not 401); GraphQL → **401** |
| JWKS | `/api/v1/identity/.well-known/jwks.json` | **200** | RSA key `kid=v2-rs256` |
| Latency sample | `/ping`,`/health/live`,`/health` | ~16–49ms | Earlier docker logs showed `/health` **1866ms**, `/metrics` **3520ms** |
| Browser MCP navigate | cursor-ide-browser | **FAILED** | “No browser tab available” |
| E2E Playwright | — | **Not run** | |
| Full monorepo coverage gate | — | **Not run** | |
| k6 / load | — | **Not run** | |
| `prisma migrate` | — | N/A | Stack is SQLAlchemy/Alembic, not Prisma |

## Frontend lint errors (blocking)

1. `src/features/admin/widgets/TenantList.tsx:28` — `useUpdateAdminTenant` called inside `handleToggleActive` (rules-of-hooks).
2. `src/features/admin/__tests__/admin-queries.test.tsx:41` — missing display name.
3. `src/features/dashboard/_layout/dashboard-metrics-header.tsx:42` — raw `<a>` to `/companies/new/`.
4. `src/features/search/components/SearchHeader.tsx:27` — unescaped quotes.

## TypeScript errors (blocking)

1. `src/app/(dashboard)/automation/analytics/page.tsx:278` — `Workflow` used as type.
2. `src/features/automation/widgets/workflow-builder/ExecutionTimeline.tsx:89` — unsafe cast to `StepResultEntry[]`.
3. `src/features/dashboard/_layout/dashboard-loading.tsx:13` — `style` not on `SkeletonProps`.

## Alembic gap (blocking for schema fidelity)

```
0033 -> 0034  Add missing columns to companies
0034 -> 0035  employee_signals / employee_scores
0035 -> 0036  marketplace plugin tables
0036 -> 0037  admin phase 16
0037 -> 0038  consolidate init_db + decision_center tables (HEAD)
```

Running DB stopped at **0033**.

## Unit test failures observed (partial run)

- FAILED intelligence agent grounding/LLM tests (4)
- ERROR `tests/unit/test_admin_api.py::*` AttributeError (16+ before stop)
- Collection ERROR without ignore: missing `mcp` package

## Docker services observed

Present/up: postgres, pgbouncer, neo4j, redis, zookeeper, kafka, schema-registry, backend, frontend, prometheus, alertmanager, grafana, exporters.  
**Not** in `salesos/docker-compose.yml`: Loki, OTel, Promtail (those appear in **root** `docker-compose.yml`).
