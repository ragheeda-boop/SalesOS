# Dependency Matrix — v5.1.0-bootstrap-green

> **Generated:** 2026-08-06  
> **Tag:** `v5.1.0-bootstrap-green`  
> **Sources:** `salesos/backend/pyproject.toml`, `salesos/frontend/package.json`, `salesos/backend/Dockerfile`, `salesos/frontend/Dockerfile`, `salesos/docker-compose.yml`

---

## 1. Backend (Python / Poetry)

| Package | Constraint | Purpose |
|---|---|---|
| python | `^3.12` | Runtime (3.12) |
| fastapi | `>=0.136.0,<0.142.0` | Web framework |
| starlette | `>=1.3.1,<2.0` | ASGI toolkit (direct pin — pip-audit floor) |
| uvicorn | `^0.29` (standard) | ASGI server |
| sqlalchemy | `^2.0` (asyncio) | ORM + async engine |
| asyncpg | `^0.29` | PostgreSQL async driver |
| alembic | `^1.13` | DB migrations |
| pydantic | `>=2.9,<3` | Data validation (floor for FastAPI 0.14x) |
| pydantic-settings | `>=2.2,<2.5` | Env/config loading |
| python-jose | `^3.3` (cryptography) | JWT auth |
| cryptography | `>=50.0.0` | Crypto primitives (CVE-2026-69247 floor) |
| passlib | `^1.7` (bcrypt) | Password hashing |
| bcrypt | `>=4.0,<4.1` | Blowfish hashing |
| python-multipart | `>=0.0.27,<0.1.0` | File upload parsing (multipart DoS fix) |
| openpyxl | `^3.1` | Excel import |
| httpx | `^0.27` | Async HTTP client |
| aiokafka | `^0.10` | Kafka async producer/consumer |
| redis | `^5.0` | Redis client |
| neo4j | `^5.20` | Neo4j graph DB driver |
| sentry-sdk | `^2.0` (fastapi) | Error monitoring |
| python-dotenv | `^1.0` | `.env` file loading |
| openai | `^1.30` | OpenAI API client |
| opentelemetry-api | `^1.25` | OTel tracing API |
| opentelemetry-sdk | `^1.25` | OTel tracing SDK |
| opentelemetry-exporter-otlp-proto-http | `^1.25` | OTel OTLP exporter |
| celery | `^5.4` | Async task queue |
| strawberry-graphql | `>=0.315.7,<1.0.0` | GraphQL server (pip-audit floor) |
| jsonschema | `^4.22` | JSON Schema validation |
| email-validator | `>=2.0,<3` | EmailStr support for Pydantic |

### Dev Dependencies

| Package | Constraint | Purpose |
|---|---|---|
| pytest | `^8.2` | Test framework |
| pytest-asyncio | `^0.23` | Async test support |
| pytest-cov | `^5.0` | Coverage reporting |
| pytest-xdist | `^3.6` | Parallel test execution |
| httpx | `^0.27` | Test HTTP client |
| ruff | `^0.4` | Linting / formatting |
| mypy | `^1.10` | Static type checking |
| asyncpg-stubs | `^0.29` | asyncpg type stubs |

### Build System

| Tool | Version | Notes |
|---|---|---|
| poetry-core (build backend) | implicit | `build-backend = "poetry.core.masonry.api"` |

---

## 2. Frontend (npm Workspaces)

### Runtime Dependencies

| Package | Constraint | Purpose |
|---|---|---|
| next | `^15.0` | React framework (App Router) |
| react | `^19.0` | UI library |
| react-dom | `^19.0` | React DOM renderer |
| next-themes | `^0.4` | Theme switching (dark/light) |
| @tanstack/react-query | `^5.60` | Server-state / cache |
| @tanstack/react-table | `^8.20` | Table component |
| react-hook-form | `^7.54` | Form state management |
| @hookform/resolvers | `^3.9` | Form schema resolvers (Zod) |
| zod | `^3.23` | Schema validation |
| axios | `^1.7` | HTTP client |
| lucide-react | `^0.460` | Icon library |
| tailwind-merge | `^2.6` | Tailwind class dedup |
| clsx | `^2.1` | Conditional classnames |
| class-variance-authority | `^0.7` | Component variant API |
| @radix-ui/react-avatar | `^1.1` | Avatar primitive |
| @radix-ui/react-dialog | `^1.1` | Dialog/modal primitive |
| @radix-ui/react-dropdown-menu | `^2.1` | Dropdown menu primitive |
| @radix-ui/react-select | `^2.1` | Select primitive |
| @radix-ui/react-tabs | `^1.1` | Tabs primitive |
| @radix-ui/react-toast | `^1.2` | Toast notifications |
| @radix-ui/react-tooltip | `^1.1` | Tooltip primitive |
| @fontsource/ibm-plex-mono | `^5.2.7` | Monospace font |
| @fontsource/ibm-plex-sans | `^5.2.8` | Sans-serif font |
| @fontsource/ibm-plex-sans-arabic | `^5.2.9` | Arabic font |
| @fontsource/viga | `^5.2.7` | Display/heading font |

### Dev Dependencies

| Package | Constraint | Purpose |
|---|---|---|
| typescript | `^5.7` | Type checking |
| @types/node | `^22.0` | Node.js types |
| @types/react | `^19.0` | React types |
| @types/react-dom | `^19.0` | React DOM types |
| eslint | `^10.0.0` | Linting (ESLint 10) |
| eslint-config-next | `15.5.22` | Next.js ESLint config (**see §4**) |
| @eslint/compat | `^2.0.0` | ESLint v9+ compatibility |
| @eslint/eslintrc | `^3.3.0` | ESLint RC compat |
| @eslint/js | `^10.0.0` | ESLint JS package |
| prettier | `^3.0.0` | Code formatting |
| tailwindcss | `^3.4` | Utility CSS framework |
| postcss | `^8.5.10` | CSS post-processor |
| autoprefixer | `^10.4` | CSS vendor prefixes |
| jest | `^29.7` | Unit test framework |
| ts-jest | `^29.2` | TypeScript Jest transformer |
| jest-environment-jsdom | `^29.7` | JSDOM test environment |
| jest-axe | `^11.0.0` | Accessibility assertions |
| @testing-library/react | `^16.1` | React component testing |
| @testing-library/jest-dom | `^6.6` | DOM matchers |
| @testing-library/dom | `^10.4.1` | DOM testing utilities |
| @playwright/test | `^1.49` | E2E test framework |
| msw | `^2.15.0` | API mocking |
| @storybook/react | `^8.0` | Component storybook |
| ts-node | `^10.9` | TypeScript REPL / scripts |

### npm Overrides

| Package | Constraint |
|---|---|
| postcss | `$postcss` (self-reference) |
| sharp | `>=0.35.0` |

---

## 3. Infrastructure Images

| Service | Image | Tag | Pinned? |
|---|---|---|---|
| postgres | `pgvector/pgvector` | `pg16` | Semi (major) |
| pgbouncer | `edoburu/pgbouncer` | `latest` | No |
| neo4j | `neo4j` | `5-community` | Semi (major) |
| redis | `redis` | `7-alpine` | Semi (major) |
| zookeeper | `confluentinc/cp-zookeeper` | `7.7.2` | Pinned |
| kafka | `confluentinc/cp-kafka` | `7.7.2` | Pinned |
| schema-registry | `confluentinc/cp-schema-registry` | `7.7.2` | Pinned |
| kafdrop | `obsidiandynamics/kafdrop` | `latest` | No |
| prometheus | `prom/prometheus` | `latest` | No |
| grafana | `grafana/grafana` | `latest` | No |
| postgres-exporter | `prometheuscommunity/postgres-exporter` | `latest` | No |
| redis-commander | `rediscommander/redis-commander` | `latest` | No |
| redis-exporter | `oliver006/redis_exporter` | `latest` | No |
| minio | `minio/minio` | `RELEASE.2024-09-22T00-33-43Z` | Pinned |
| loki | `grafana/loki` | `3.1.1` | Pinned |
| otel-collector | `otel/opentelemetry-collector-contrib` | `0.111.0` | Pinned |
| promtail | `grafana/promtail` | `3.1.1` | Pinned |

### Docker Base Images (Build)

| Component | Base Image | Notes |
|---|---|---|
| backend (builder + production) | `python:3.12-slim` | Python 3.12 |
| frontend (build + production) | `node:22-alpine` | Node.js 22 |

---

## 4. Known Version Mismatches

### 4.1 Poetry: Lock v2.4.1 vs Docker v1.8.3

| Artifact | Poetry Version | Source |
|---|---|---|
| `poetry.lock` header | `2.4.1` | `# This file is automatically @generated by Poetry 2.4.1` |
| `backend/Dockerfile` | `1.8.3` | `pip install --no-cache-dir "poetry==1.8.3"` |

**Impact:** The lock file is generated by Poetry 2.x on the host, but Docker uses Poetry 1.8.3 for `poetry install`. This works because `poetry.lock` format is forward-compatible from 1.x to 2.x, and the `requires = ["poetry-core"]` build-system is stable. However, lock-file metadata headers may diverge, and any Poetry-2-specific features would not be available inside the Docker build.

### 4.2 ESLint 10 vs eslint-config-next peers

| Package | Version | Declared Peers |
|---|---|---|
| eslint | `^10.0.0` | — |
| eslint-config-next | `15.5.22` | `eslint ^7 \|\| ^8 \|\| ^9` |

**Impact:** `eslint-config-next@15.5.22` does not declare ESLint 10 as a compatible peer. ESLint 10 introduced breaking changes from v9.

**Mitigation:** `.npmrc` sets `legacy-peer-deps=true`. The `scripts/ci14-stub-rushstack-eslint-patch.js` postinstall hook provides a compatibility shim. The configuration works but may need auditing when Next.js releases an ESLint-10-compatible config.

### 4.3 Frontend Version Naming

| Artifact | Version | Notes |
|---|---|---|
| Root `package.json` | `5.1.0-rc1` | Pre-release designation |
| Backend `pyproject.toml` | `5.1.0` | Release-candidate version |
| Docker backend | implicit | Pinned: `poetry==1.8.3`, `python:3.12-slim` |

The frontend root version uses `5.1.0-rc1` (release candidate) while the backend uses `5.1.0` (implied release). These should be reconciled before GA.

---

## 5. Workspace Packages (`@salesos/*`)

All packages live under `salesos/frontend/packages/`.

### Packages in Root Dependencies (active)

| Package | Version | Notes |
|---|---|---|
| `@salesos/charts` | `5.1.0-rc1` | Recharts wrapper; deps: `@salesos/ui`, `recharts ^2.15` |
| `@salesos/config` | `5.0.0` | Configuration module |
| `@salesos/design-language` | `2.0.0-alpha.1` | Design language definitions (alpha) |
| `@salesos/forms` | `5.0.0` | Form components; deps: `react-hook-form`, `zod`, `@hookform/resolvers` |
| `@salesos/hooks` | `5.0.0` | Shared React hooks; deps: `axios`, `@tanstack/react-query` |
| `@salesos/icons` | `5.0.0` | Icon components; deps: `lucide-react` |
| `@salesos/renderer` | `5.0.0` | Page/widget renderer; deps: `@salesos/ui`, `@salesos/icons`, `@salesos/charts`, `@salesos/forms`, `@salesos/runtime` |
| `@salesos/runtime` | `5.0.0` | Runtime API client; deps: `axios`, `@tanstack/react-query`, `zod` |
| `@salesos/ui` | `5.0.0` | Core UI kit; deps: all Radix primitives, `lucide-react`, `tailwind-merge`, `clsx`, `cva`, `@tanstack/react-table` |
| `@salesos/workspace` | `5.0.0` | Workspace shell; deps: `@salesos/ui`, `@salesos/icons`, `@salesos/charts`, `@salesos/runtime`, `@salesos/hooks`, `@salesos/design-language`, `@salesos/renderer`, `@salesos/widget-sdk` |
| `@salesos/workspace-generator` | `5.0.0` | Workspace scaffold generator (JS only) |

### Packages NOT in Root Dependencies (auxiliary)

| Package | Version | Status | Notes |
|---|---|---|---|
| `@salesos/search` | `1.0.0` | Aux | Search module; deps: `@salesos/workspace` |
| `@salesos/tokens` | `1.0.0` | Aux | Design tokens (CSS/Tailwind/TS exports) |
| `@salesos/theme` | `0.1.0-alpha` | Scaffold | Theme package (empty) |
| `@salesos/design-system` | `1.0.0` | Aux | Design system entry; deps: `@salesos/tokens` |
| `@salesos/platform` | `0.1.0` | Scaffold | Platform kernel + contracts (AI, revenue) |
| `@salesos/widget-sdk` | `1.0.0` | Aux | Widget SDK; deps: `@salesos/ui`, `@salesos/design-language` |
| `@salesos/widgets` | `0.1.0-alpha` | Scaffold | Widget runtime scaffold (empty) |
| `@salesos/providers` | `0.1.0-alpha` | Scaffold | Context providers scaffold (empty) |
| `@salesos/charts-v3` | `0.1.0-alpha` | Scaffold | v3 charts scaffold (empty) |
| `@salesos/layouts` | `0.1.0-alpha` | Scaffold | Layout components scaffold (empty) |

---

## 6. Platform Requirements

| Requirement | Version | Source |
|---|---|---|
| Python | `3.12` | `pyproject.toml` (`python = "^3.12"`), Docker `python:3.12-slim` |
| Node.js | `22` | Docker `node:22-alpine` |
| Poetry (host) | `>=2.0` (generates lock) | `poetry.lock` header (`Poetry 2.4.1`) |
| Poetry (Docker) | `1.8.3` | `backend/Dockerfile` |
| npm (Docker) | Bundled with Node 22 | `frontend/Dockerfile` |
| Docker Compose | v3 (file format) | `docker-compose.yml` schema |
| PostgreSQL | 16 (via pgvector/pgvector:pg16) | `docker-compose.yml` |
| Neo4j | 5.x (community) | `docker-compose.yml` |
| Redis | 7.x (alpine) | `docker-compose.yml` |
| Kafka | 7.7.2 (Confluent) | `docker-compose.yml` |
| TypeScript | `^5.7` | `package.json` devDependencies |
| Next.js | `^15.0` | `package.json` dependencies |
| React | `^19.0` | `package.json` dependencies |
| Ruff target | `py312` | `pyproject.toml` |
| Mypy target | `3.12` | `pyproject.toml` |
