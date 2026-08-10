# AGENTS.md — Muhide Workspace

> **Audience:** Humans and coding agents working in this repository.  
> **Last updated:** 2026-08-10 (AI Foundation F3 Complete)  
> **Authority chain:** Executable evidence → [STAR Audit](docs/audit/star-audit/) → [ga-engineering-audit](docs/audit/ga-engineering-audit/) → this file → `docs/PROJECT_BIBLE.md` (SalesOS engineering bible; product scope notes below).

---

## 11. Session Summary (2026-08-07 to 2026-08-10)

| Milestone | Status | Commit | Key Evidence |
|-----------|:------:|--------|-------------|
| M1 — P0 Closure | COMPLETE | `934e3b3` | P0-01 FIXED, P0-02 FALSE POSITIVE |
| M2 — P1 Batch | COMPLETE | `ba5a2d6` | 6/6 investigated, 3 fixes, 2 false positives, 1 schema-only |
| M3 — AI Foundation Audit | COMPLETE | read-only | 8 audit areas scored, recommendation: BUILD FOUNDATION |
| M4 — AI Foundation F1 | COMPLETE | `64f512d` | Reliability + Security, 167/167 tests pass |
| M5 — AI Foundation F2 | COMPLETE | `4e1592f` | Cost + Budget, 220/220 tests pass |
| M6 — AI Foundation F3 | COMPLETE | `4892efd` | Observability, 245/245 tests pass |

### P1 Batch details (commit `ba5a2d6`)
- P1-01: Deleted dead `routers/opportunities.py` (181 lines), cleaned `boot/routers.py`
- P1-06: Swapped Steps 3/4 (company_match before domain_match), aligned confidence to ADR-031 (1.0/0.9/0.6/0.3), `ALGORITHM_VERSION` → v1.1.1-shadow
- P1-04: Removed `_render_pdf_stub()`, replaced with `ValueError("PDF export not implemented")`
- P1-02: FALSE POSITIVE (dual flags different scopes)
- P1-03: ALREADY FIXED
- P1-05: SCHEMA ONLY (DEC-130b pattern)
- Tests: analytics + signal marketplace + feature store all passing

### AI Foundation F1 details (commit `64f512d` → `9426e36`)
- F1-1: Fixed broken cross-provider failover `await` in `factory.py`
- F1-2: Added configurable provider timeouts (30s default) via `ReliabilityConfig`
- F1-3: Added retry/backoff with error classification (3 retries, exponential backoff)
- F1-4: Wired `CircuitBreaker` to provider call path via `ReliableProvider` wrapper
- F1-5: Closed PII enforcement bypasses: RAG query path, agent prompt guard (`self._llm.client` → `self._llm`), chat_stream path
- F1-6: Enforced `DataClassRule`/max_model_tier at LLM call boundary via `PolicyGate`
- F1-7: Added provider/model allowlist policy via `ProviderModelPolicy`
- Tests: 43/43 F1 tests + 124/124 regression tests = 167/167 passing

### New files this session
- `salesos/backend/intelligence/providers/reliability.py` — `ReliableProvider`, `ReliabilityConfig`, `CircuitBreaker`, `classify_error`
- `salesos/backend/intelligence/providers/policy_gate.py` — `PolicyGate`, `PolicyGateResult`, `ProviderModelPolicy`, `DataClassRule`, `get_model_tier`
- `salesos/backend/tests/unit/test_ai_foundation_f1.py` — 43 tests

### AI Foundation F2 details (commit `4e1592f`)
- F2-1: Replaced in-memory `CostTracker` with DB-backed async API
- F2-2: Single accounting path — removed duplicate tracking from all providers
- F2-3: Pre-call budget enforcement via `SELECT FOR UPDATE`
- F2-4: Concurrency safety — transaction-level atomic budget check
- F2-5: Deterministic monthly billing period with auto-reset
- F2-6: Provider/model attribution preserved on every record
- F2-7: All LLM paths tracked: chat, chat_stream, embed
- Alembic: `f8b3d4e5f6a7` (llm_cost_entries + tenant_llm_budgets)
- Fixed: `c1d2e3f4a5b6` multi-statement RLS for asyncpg compat
- Tests: 27/27 F2 + 193/193 regression = 220/220 passing

### New files this session (F2)
- `salesos/backend/app/alembic/versions/f8b3d4e5f6a7_ai_foundation_f2_cost_tracking.py`
- `salesos/backend/tests/unit/test_ai_foundation_f2.py` — 27 tests

### AI Foundation F3 details (commit `4892efd`)
- F3-1: `AIObservability` — in-memory metrics (calls, latency, tokens, cost, policy blocks, budget rejections, CB transitions)
- F3-2: Prometheus text output wired to `GET /metrics` endpoint
- F3-3: `request_id` propagated through `ChatRequest` → `ReliableProvider` → individual providers
- F3-4: Structured logging: 6 reliability.py, 4 policy_gate.py, 1 cost_tracker.py log calls converted to `extra={}`
- F3-5: Circuit breaker state transitions now observable via `record_circuit_breaker()`
- Tests: 25/25 F3 + 220/220 regression = 245/245 passing

### New files this session (F3)
- `salesos/backend/intelligence/providers/observability.py` — `AIObservability`, `ai_observability`, `format_extra`, `log_context`
- `salesos/backend/tests/unit/test_ai_foundation_f3.py` — 25 tests

---

## 10. STAR Audit Summary (2026-08-07)

| Milestone | Status | Classification | Key Evidence |
|-----------|:------:|---------------|-------------|
| STAR Audit (20 items) | COMPLETE | **conditional GO** | P0 = 0 findings, 80% resolved |
| Security P0 (6 items) | COMPLETE | All MITIGATED/VERIFIED | 13 integration tests, 5-layer SSRF, 5 regression tests |
| Architecture ADRs (6) | COMPLETE | ADR-103 to ADR-108 | Digital Twin, Agent Runtime, Revenue Brain deferred; Neo4j offline; Data Residency |
| Documentation Corrections | COMPLETE | D-02, D-03 resolved | AI-native → AI-assisted; Security 10/10 → 48/100 |
| AI Test Coverage | COMPLETE | 40 tests baseline | 4 test files in `tests/evaluation/` |

### Remaining Work (outside code scope)
| Item | Owner | Blocker |
|------|-------|---------|
| A-09 (Staging parity) | DevOps | No staging branch/CI |
| C-18 (Stripe) | Platform | External Stripe account |
| A-10 (Solo architect) | Management | Hiring |
| R-01–R-07 (Monitoring) | DevOps | Infrastructure setup |

### Documentation created (STAR Audit)
- `docs/audit/star-audit/01_THEORY_MODEL.md` through `20_FINAL_STATUS.md` (20 files)
- `docs/audit/star-audit/GOVERNANCE_CLOSURE.md`
- `docs/audit/star-audit/A09_STAGING_PARITY.md`
- `docs/adr/0103-digital-twin-deferred.md` through `0108-neo4j-keep-offline.md` (6 ADRs)
- `salesos/backend/tests/evaluation/test_ai_guardrails.py` (13 tests)
- `salesos/backend/tests/evaluation/test_ai_policies.py` (18 tests)

---

## 9. Session Summary (2026-08-06)

| Milestone | Status | Tag | Key Evidence |
|-----------|:------:|-----|-------------|
| ADR-101 Green Bootstrap | COMPLETE | v5.1.0-bootstrap-green | 14/14 services healthy, TS 0 errors |
| Sprint 0.5 Baseline Freeze | COMPLETE | - | 6 baseline docs, 10/10 smoke |
| ADR-102 Engineering Hardening | COMPLETE | v5.1.0-rc1-hardened | 21 fixes, 25 files changed |
| UX Architecture + Phase 1 | COMPLETE | v5.1.0-rc2-ux-ready | Blueprint, token fix, locale fix |

### Key changes
- ESLint: ignoreDuringBuilds removed, 6 rules warn→error
- Prettier: config created, format scripts added
- Poetry: Docker aligned to 2.4.1 (matches lock)
- JWT: RS256-only enforced, templates aligned
- CSP: Added to Next.js frontend
- Kafka: All compose files standardized to 7.7.2
- Docker: 5 images pinned from :latest
- Tailwind: Wired to @salesos/tokens preset
- Locale: Now respects browser/localStorage

### Documentation created
- docs/adr/0101-platform-bootstrap-stabilization.md
- docs/adr/0102-engineering-hardening.md
- docs/releases/v5.1.0-bootstrap-green/ (6 files)
- docs/releases/rc-1/ (2 files)
- docs/ux/UX_ARCHITECTURE.md
- docs/reports/ (session report + gaps)

---

## 1. What this workspace is

**Core principle:** AI assists. Humans decide. Evidence governs.

| Product | Role | Code reality (2026-07-22) |
|---------|------|---------------------------|
| **SalesOS** | First operational product | Primary codebase under `salesos/` |
| **AuditOS** | Separate product on shared Core (vision) | Not a shipped product tree in this repo |
| **DecisionOS** | Separate product on shared Core (vision) | Not a shipped product tree in this repo |
| **LocalContentOS** | Separate product on shared Core (vision) | Not a shipped product tree in this repo |

**Do not** treat SalesOS GA work as "multi-product GA."  
**Do not** describe the platform as AuditOS-only, SaaS-only, or a chatbot.

Canonical GA engineering source of truth:

- [docs/audit/ga-engineering-audit/00-EXECUTIVE-SUMMARY.md](docs/audit/ga-engineering-audit/00-EXECUTIVE-SUMMARY.md) — **NO-GO**
- [docs/audit/ga-engineering-audit/PRODUCTION_PLAN.md](docs/audit/ga-engineering-audit/PRODUCTION_PLAN.md) — Waves 0–14
- [docs/audit/ga-engineering-audit/AI_HONESTY.md](docs/audit/ga-engineering-audit/AI_HONESTY.md) — AI marketing honesty

Prior GO claims in `docs/vnext/reports/GO_NO_GO_DECISION.md` and `GA_CHECKLIST.md` are **SUPERSEDED**.

---

## 2. Repository map (agents)

| Path | Use |
|------|-----|
| `salesos/` | Product monorepo (FastAPI backend + Next.js frontend + infra) |
| `salesos/backend/` | API, domains, runtime, Alembic |
| `salesos/frontend/` | Next.js app + `@salesos/*` packages |
| `docs/` | Audits, ADRs, ops, vNext plans |
| `data/` | Notion/identity import pipelines — **not** SalesOS runtime GA path by default |
| `engineering-os/` | Governance submodule (if present) |
| Root scrapers / `sales-os/` | Legacy / adjacent — prefer `salesos/` |

---

## 3. Low-load protocol (mandatory)

Do **not** run heavy commands unless the user **explicitly approves**:

- `npm run build` / `npm run lint` / full `npm test` suites
- `npx prisma generate` / `migrate` (Prisma is **not** SalesOS core — Alembic is)
- `npm install` / `pnpm install` / `yarn install`
- Full `pytest` suites outside a narrow, approved path
- Production DB migrate / restore / deploy

Prefer:

- Read-only exploration (Grep/Read)
- Minimal patches following existing patterns
- Docker-based backend work when host Poetry/Python is broken (Windows host Poetry/asyncpg known fail per audit)

---

## 4. Security & governance — never weaken without approval

- Auth, CSRF, RBAC, tenant isolation, audit logging, evidence gates
- Do not disable security middleware “to unblock demos”
- Do not commit secrets (`.env`, credentials, kubeconfigs)
- Do not claim browser pass, production-ready, or tests passed without command evidence

---

## 5. Validation honesty labels

Use these labels; never invent a stronger claim:

| Label | Meaning |
|-------|---------|
| **not validated** | Not run / no evidence |
| **light validated** | Spot checks only |
| **build validated** | Install/lint/typecheck/build/test commands run with recorded outcome |
| **pilot-ready with conditions** | Narrow use after listed P0s closed |
| **production no-go** | Must not ship GA |

Current audit classification (2026-07-22): **production no-go** (Production Readiness 38, Security 48).

---

## 6. AI honesty

- Default: `feature_ai_copilot=False` (`salesos/backend/app/config.py`)
- FE Decision package is a **STUB** — see `AI_HONESTY.md`
- Do not market stubs as production AI
- Prefer Decision Center APIs over stub `@salesos` decision engine

---

## 7. Conflict resolution for agents

1. If docs disagree → prefer **executable evidence** + ga-engineering-audit + `docs/reports/REMAINING_GAPS.md` for known gaps.  
2. If `PROJECT_BIBLE.md` maturity scores conflict with audit → **audit wins** for GO/NO-GO.  
3. Parallel code agents may own `TenantList` / security endpoints — **do not conflict**; leave those files alone unless assigned.  
4. Only commit when the user explicitly asks.  
5. **Swarm dispatch (DEC-107):** While waiting on CI field / ops (GHCR, VPS), keep ≥2–3 PARALLEL READY agents busy on independent ownership — never pause the swarm solely because CI-08/CI-09 are BLOCKED. See `docs/program/decisions/DEC-107-SWARM-ALWAYS-ON-PARALLEL-READY.md`.

---

## 8. Preferred local paths (when approved)

```text
# Backend (Docker)
cd salesos
docker compose exec backend alembic current
docker compose exec backend alembic upgrade head   # non-prod only, after approval

# Frontend (from salesos/frontend) — requires explicit approval
npm run lint
npx tsc --noEmit
npm run build
npm run format:fix

# Scrapers (moved Phase 03)
packages/scrapers/{balady,najiz,rega,taqeem}/

# Data pipelines (moved Phase 04 — gitignored)
packages/data/scripts/clean_all.py

# Restructure decision logs
migration-log/phase-*.md
```

Windows host Poetry is **not** the production path.

---

## 9. CI/Dependabot location fix (2026-07-30)

- GitHub Actions workflows were at `salesos/.github/workflows/` — **undiscoverable** by GitHub
- **Fix:** Moved all workflows → `.github/workflows/` (repo root) + path fixes:
  - `cd backend` → `cd salesos/backend`, `cd frontend` → `cd salesos/frontend`
  - Docker context/file paths, cache keys, artifact paths, hashFiles refs
  - Gitleaks `continue-on-error: true` removed (blocking now)
- Dependabot file moved from `salesos/.github/dependabot.yml` → `.github/dependabot.yml` with `directory:` paths fixed (`/frontend` → `/salesos/frontend`)
- Credential files `cookies.txt`, `login.json`, `railway-status.json` added to `.gitignore` (both root + salesos)

---

*Agents: keep patches minimal, report files changed + commands run + validation status honestly.*

## Imported Claude Cowork project instructions
