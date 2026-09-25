# BASELINE FREEZE — 2026-08-24

**Frozen at:** 2026-08-24T00:00:00Z  
**Auditor:** Phase 2 Multi-Agent Reconciliation  

---

## Git State

| Property | Value |
|----------|-------|
| HEAD | `77bb68495dcf662b4bb807c550217824ab8e0e9b` |
| Branch | `master` |
| Latest tag | `v5.1.0-phase4f-rc1` (HEAD is 2 commits ahead) |
| Remote | `origin` → `https://github.com/ragheeda-boop/SalesOS.git` |
| Working tree | Clean (3 untracked debug files) |
| Stashes | 29 |
| Local branches | 9 (master active, 2 backup, 6 feature/fix) |
| Remote branches | 42 (40 Dependabot, 1 staging, 1 master) |
| Tags | 12 |
| Contributors | 3 (Ragheed: 1084, dependabot: 35, Cursor: 2) |

## Untracked Files (to clean)

| File | Purpose | Action |
|------|---------|--------|
| `salesos/_fails.txt` | Debug artifact | DELETE |
| `salesos/backend/test_login.py` | Debug test | DELETE |
| `salesos/backend/test_pool.py` | Debug test | DELETE |

## Runtime Versions

| Tool | Version |
|------|---------|
| Python | 3.12.10 |
| Node.js | v24.18.0 |

## Codebase Counts (Verified)

| Area | Count | Notes |
|------|-------|-------|
| Backend modules (`app/modules/`) | 31 | Excluding `__pycache__` |
| DDD domains (`domains/`) | 18 | Excluding `__pycache__` |
| Runtime engines (`runtime/`) | 29 | Excluding `__pycache__` |
| Intelligence agent files | 19 | Including `__init__.py`, `base.py`, `llm.py`, `coordinator.py`, `grounded_common.py`, `research_evidence.py` + 13 agent files |
| Intelligence provider files | 14 | Including `__init__.py`, `base.py`, `protocol.py`, `factory.py`, `router.py`, `cost_tracker.py`, `reliability.py`, `policy_gate.py`, `observability.py` + 5 provider impls |
| Active grounded agents | 13 | research, competitor, relationship, icp, recommendation, forecast, pricing, proposal, renewal, tender, meeting, news, contract |
| LLM provider implementations | 5 | OpenAI, Anthropic, Azure, Gemini, Ollama |
| Alembic migrations | 99 | Head: `h2i3j4k5l6m8_phase4a_icp_profiles.py` |
| API routers (top-level) | 21 | In `app/routers/` |
| Total test files | 636 | Recursive across all of `salesos/backend/` |
| Unit test files (tests/unit/) | 184 | Directory listing |
| Frontend page.tsx routes | 107 | Recursive in `src/app/` |
| docs/ .md files | 970 | Recursive |
| ADR files | 28 | In `docs/adr/` |
| .ai/ agent docs | 17 | In `.ai/` |
| .engineering/ docs | 31 | Auto-generated |
| GitHub workflows | 9 | In `.github/workflows/` |

## Previous Report Discrepancies

| Area | Previous Claim | Actual | Delta |
|------|---------------|--------|-------|
| Backend modules | 33 | 31 | -2 (counted `__pycache__`) |
| DDD domains | 20 | 18 | -2 (counted `__pycache__`) |
| Runtime engines | 33 | 29 | -4 (counted `__pycache__`) |
| Agent files | 20 | 19 | -1 (counted `__pycache__`) |
| Provider files | 15 | 14 | -1 (counted `__pycache__`) |
| Alembic migrations | 100 | 99 | -1 (counted `__init__.py`) |
| Test files | 347 | 636 | +289 (previous only counted `tests/` dir, not domain/module tests) |
| Frontend routes | 57+ | 107 | +50 (previous undercounted) |
| docs .md files | ~935 | 970 | +35 (approximate vs exact) |

**Root cause of discrepancies:** Previous exploration agents counted directory entries including `__pycache__` subdirectories and used approximate glob patterns rather than exact file counts.

## Migration Head

```
h2i3j4k5l6m8_phase4a_icp_profiles.py
```

Chain verified: 99 migrations, single head, clean dependency chain.

## Database State (Known)

| Metric | Value |
|--------|-------|
| Total tables with RLS | 83+ |
| Tables WITHOUT RLS | tenants, sources, signal_catalog, token_blacklist, sso_connections, vectors, graph_nodes, graph_edges, approval_requests, llm_cost_entries, tenant_llm_budgets, subscriptions, stripe_webhook_events, platform_billing_invoices, usage_meter_events, usage_meters, dunning_cases |
| RLS policy pattern | `tenant_isolation_{table}` — FOR ALL, USING + WITH CHECK |
| GUC variable | `app.tenant_id` (DEC-085) |
| Dual engine | `engine` (salesos_app role) + `owner_engine` (BYPASSRLS) |

## Feature Flags (Known)

| Flag | Default | Current | Notes |
|------|---------|---------|-------|
| `feature_ai_copilot` | False | **True** | Flipped in Phase 3 |
| `feature_signal_marketplace_postgres` | False | True (local) | Used for local dev |
| `feature_crm_kanban` | False | Unknown | |
| `feature_httponly_access_cookie` | False | Unknown | |

## Deployment Configuration

| Component | Target | Config |
|-----------|--------|--------|
| Backend | Railway | `Dockerfile.railway` + `railway.json` |
| Celery Worker | Railway | `Dockerfile.railway.celery` + `railway.worker.json` |
| Celery Beat | Railway | `Dockerfile.railway.celery` + `railway.beat.json` |
| Frontend | Vercel | Next.js standalone |
| CI/CD | GitHub Actions | 9 workflows |
| Database | PostgreSQL (pgvector:pg16) | `pgvector/pgvector:pg16` in CI |
| Cache | Redis | `redis:7-alpine` in CI |

## Frozen Checkpoint

This document represents the verified state of the repository at HEAD `77bb684` on branch `master`. All subsequent Phase 2 work builds from this checkpoint.
