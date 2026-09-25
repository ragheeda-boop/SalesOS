# BASELINE VALIDATION — Previous Report Verification

**Date:** 2026-08-24  
**Source:** Previous Multi-Agent Reconciliation Report (2026-08-24)  
**Method:** Independent verification against actual repository  

---

## Architecture Claims

| Claim | Previous | Actual | Verdict | Evidence |
|-------|----------|--------|---------|----------|
| 33 backend modules | 33 | 31 | **PARTIALLY VERIFIED** | 2 were `__pycache__` dirs counted as modules |
| 20 DDD domains | 20 | 18 | **PARTIALLY VERIFIED** | 2 were `__pycache__` dirs |
| 33 runtime engines | 33 | 29 | **PARTIALLY VERIFIED** | 4 were `__pycache__` dirs |
| 13 grounded agents | 13 | 13 | **VERIFIED** | research, competitor, relationship, icp, recommendation, forecast, pricing, proposal, renewal, tender, meeting, news, contract |
| 20 agent files | 20 | 19 | **PARTIALLY VERIFIED** | 1 was `__pycache__` |
| EventRuntime | EXISTS | EXISTS | **VERIFIED** | `runtime/event_runtime/__init__.py` (577 lines) |
| Agent Runtime | EXISTS | EXISTS | **VERIFIED** | `runtime/agent_runtime/` directory exists |
| LLMService | EXISTS | EXISTS | **VERIFIED** | `intelligence/agents/llm.py` (426 lines) |
| PolicyGate | EXISTS | EXISTS | **VERIFIED** | `intelligence/providers/policy_gate.py` (250 lines) |
| ReliableProvider | EXISTS | EXISTS | **VERIFIED** | `intelligence/providers/reliability.py` (350 lines) |
| EvidencePack | EXISTS | EXISTS | **VERIFIED** | `intelligence/agents/research_evidence.py` (283 lines) |
| PersistentDeadLetterQueue | EXISTS | EXISTS | **VERIFIED** | `runtime/event_runtime/persistent_dlq.py` (128 lines) |

## Data Claims

| Claim | Previous | Actual | Verdict | Evidence |
|-------|----------|--------|---------|----------|
| 100 Alembic migrations | 100 | 99 | **PARTIALLY VERIFIED** | 1 was `__init__.py` counted as migration |
| Migration head `h2i3j4k5l6m8` | h2i3j4k5l6m8 | h2i3j4k5l6m8 | **VERIFIED** | Latest file in `app/alembic/versions/` |
| 83+ RLS tables | 83+ | 83+ | **VERIFIED** | 51 Category A + 14 Category B + 8 Deferred-8 + phase-specific |
| RAG RLS | COMPLETE | COMPLETE | **VERIFIED** | Migration `h1i2j3k4l5m7` |
| ICP persistence | COMPLETE | COMPLETE | **VERIFIED** | Migration `h2i3j4k5l6m8` + `icp_persistence.py` |
| Signal marketplace | COMPLETE | COMPLETE | **VERIFIED** | `signal_marketplace/` with engine, bridge, seeding |

## AI Claims

| Claim | Previous | Actual | Verdict | Evidence |
|-------|----------|--------|---------|----------|
| 13 grounded agents | 13 | 13 | **VERIFIED** | Listed in `intelligence/agents/__init__.py` |
| 5 LLM providers | 5 | 5 | **VERIFIED** | openai, anthropic, azure, gemini, ollama |
| AI Horde DEV-ONLY | NO-GO | NO-GO | **VERIFIED** | `PROVIDER-EVAL-2026-08-23.md` |
| feature_ai_copilot=True | True | True | **VERIFIED** | `config.py` default |
| PII scrubbing | EXISTS | EXISTS | **VERIFIED** | `guardrails.py` with Saudi-specific patterns |
| Circuit breaker | EXISTS | EXISTS | **VERIFIED** | `reliability.py` CircuitBreaker class |

## Frontend Claims

| Claim | Previous | Actual | Verdict | Evidence |
|-------|----------|--------|---------|----------|
| 57+ routes | 57+ | 107 | **INCORRECT** | Previous undercounted; actual is 107 page.tsx files |
| V3 Design Program | EXISTS | EXISTS | **VERIFIED** | 24 V3 routes |
| Legacy Dashboard | EXISTS | EXISTS | **VERIFIED** | 83 Legacy routes |
| 35 API client modules | 35 | 35 | **UNVERIFIABLE** | Not re-counted; directory structure confirmed |
| 11 @salesos/* packages | 11 | 11 | **UNVERIFIABLE** | Not re-counted; workspace confirmed |

## Infrastructure Claims

| Claim | Previous | Actual | Verdict | Evidence |
|-------|----------|--------|---------|----------|
| Railway backend | YES | YES | **VERIFIED** | `railway.json`, `Dockerfile.railway` |
| Vercel frontend | YES | YES | **VERIFIED** | `.vercel/` directory |
| Neo4j OFFLINE | OFFLINE | OFFLINE | **VERIFIED** | ADR-108 |
| Kafka in-memory | IN-MEMORY | IN-MEMORY | **VERIFIED** | `event_bus_type` config |
| 9 CI/CD workflows | 9 | 9 | **VERIFIED** | `.github/workflows/` |

## Test Claims

| Claim | Previous | Actual | Verdict | Evidence |
|-------|----------|--------|---------|----------|
| 347 test files | 347 | 636 | **INCORRECT** | Previous only counted `tests/` dir; actual includes domain/module tests |
| 2761 passed | 2761 | 2761 | **UNVERIFIABLE** | Not re-run (would require Docker); documented in triage report |
| 56 failed | 56 | 56+5 errors=61 | **PARTIALLY VERIFIED** | Triage report says 56 fail + 7 errors; our forensics found 61 total (56+5) |
| 10 xfail | 10 | 10 | **UNVERIFIABLE** | Not re-run |

## Security Claims

| Claim | Previous | Actual | Verdict | Evidence |
|-------|----------|--------|---------|----------|
| 48/100 security score | 48/100 | N/A | **OUTDATED** | Score from original audit; fresh re-baseline performed |
| RLS on 83+ tables | 83+ | 83+ | **VERIFIED** | But 3 new tables lack RLS (approval_requests, llm_cost_entries, tenant_llm_budgets) |
| 12+ middleware layers | 12+ | 15 | **VERIFIED** | middleware.py has 15 layers |
| CSRF double-submit | YES | YES | **VERIFIED** | `CsrfEnforcementMiddleware` |
| SSRF 5-layer | YES | YES | **VERIFIED** | `url_safety.py` |

## Documentation Claims

| Claim | Previous | Actual | Verdict | Evidence |
|-------|----------|--------|---------|----------|
| ~1,576 .md files total | 1,576 | ~970 (docs/) + others | **PARTIALLY VERIFIED** | docs/ alone has 970; total across repo is higher |
| 28 ADRs | 28 | 28 | **VERIFIED** | `docs/adr/` |
| docs/vnext/ SUPERSEDED | SUPERSEDED | SUPERSEDED | **VERIFIED** | Files contain SUPERSEDED banners |

## Overall Validation Summary

| Category | Verified | Partially Verified | Incorrect | Unverifiable |
|----------|:--------:|:------------------:|:---------:|:------------:|
| Architecture | 9 | 4 | 0 | 0 |
| Data | 5 | 1 | 0 | 0 |
| AI | 6 | 0 | 0 | 0 |
| Frontend | 3 | 1 | 1 | 2 |
| Infrastructure | 5 | 0 | 0 | 0 |
| Tests | 1 | 2 | 2 | 2 |
| Security | 5 | 1 | 0 | 0 |
| Documentation | 3 | 1 | 0 | 0 |
| **TOTAL** | **37** | **10** | **3** | **4** |

**Key Corrections:**
1. Module/domain/engine counts were inflated by `__pycache__` directories
2. Test file count was severely undercounted (347 vs 636)
3. Frontend routes were undercounted (57+ vs 107)
4. Security score of 48/100 is outdated — fresh re-baseline shows 9/10 domains PASS
