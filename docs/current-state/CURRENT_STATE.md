# CURRENT STATE — 2026-08-24

**Authoritative current state of the SalesOS repository.**

---

## System Summary

| Property | Value |
|----------|-------|
| Product | SalesOS — Enterprise Company Intelligence Platform |
| Version | v5.1.0-phase4f-rc1 |
| Commit | `77bb684` |
| Branch | master |
| Python | 3.12.10 |
| Node.js | v24.18.0 |
| Framework | FastAPI (backend) + Next.js 15 (frontend) |
| Database | PostgreSQL (pgvector:pg16) |
| Cache | Redis |
| Graph | Neo4j (OFFLINE per ADR-108) |
| Messaging | Kafka (IN-MEMORY, not production) |
| Backend deploy | Railway |
| Frontend deploy | Vercel |
| CI/CD | GitHub Actions (9 workflows) |
| Overall readiness | YELLOW (pilot-ready with conditions) |

## Codebase

| Area | Count | Notes |
|------|-------|-------|
| Backend modules | 31 | `app/modules/` |
| DDD domains | 18 | `domains/` |
| Runtime engines | 29 | `runtime/` |
| Intelligence agents | 13 active | Grounded EvidencePack pattern |
| LLM providers | 5 | OpenAI, Anthropic, Azure, Gemini, Ollama |
| Alembic migrations | 100 | Head: `i3j4k5l6m7n8` |
| API routers | 21 | Top-level `app/routers/` |
| Total test files | 636 | Recursive across backend |
| Frontend routes | 107 | `page.tsx` files |
| ADRs | 28 | `docs/adr/` |
| docs/ .md files | 970 | Recursive |

## Readiness

| Dimension | Rating | Key Blocker |
|-----------|:------:|-------------|
| Engineering | YELLOW | 0 genuine defects, 10 skipped (env-dependent), 0 env failures |
| Security | GREEN | All RLS gaps fixed (Phase A), no external pentest |
| Infrastructure | YELLOW | Kafka in-memory, no automated backups, no monitoring in prod |
| Product | YELLOW | DEV-ONLY LLM provider, minimal seeded data, no billing |
| Production/GA | **RED** | LLM provider, Railway config drift, no pentest, no go-live |

## What Is Complete

- Phase 1 Product Core (code, tests, browser QA)
- Phase 2 Intelligence (deterministic, zero-LLM)
- Phase 3 AI (copilot modes, HITL, governance, evaluation)
- Phase 4 Platform (EventBus DLQ, capability registry, migrations, observability)
- Phase 4A-4F Intelligence Data Layer (RAG RLS, ICP, signals, 13 grounded agents)
- P0 Schema Drift resolved
- A-09 Staging Parity
- OPS-01 Rows 1-3, 4, 8 signed

## What Is Not Complete

- LLM provider qualification (CRITICAL)
- Railway preDeployCommand drift fix
- External pentest
- Security re-audit (post Phase 1-4 fixes)
- ~~56 test failure resolution (60 env, 1 genuine)~~ **CLOSED** — 1 NBA fixed, 48 event loop fixed, 2 ordering fixed, 10 skipped (env-dependent)
- Staging Google OAuth
- Railway managed backup schedule
- Load/stress testing
- Stripe billing wiring
- Production Kafka configuration
- Go-Live execution (Wave 13)
- Hypercare (Wave 14)
- Production GA declaration

## Authoritative Documents

1. `AGENTS.md` — Agent instructions
2. `docs/PROJECT_BIBLE.md` — Engineering bible
3. `docs/audit/ga-engineering-audit/FINAL_GO_NOGO_ASSESSMENT.md` — Current assessment
4. `docs/audit/ga-engineering-audit/SALESOS_MASTER_CLOSURE_SEQUENCE.md` — Closure order
5. All ADRs in `docs/adr/` — Architecture decisions
6. `docs/audit/ga-engineering-audit/AI_HONESTY.md` — AI honesty
7. `docs/current-state/SECURITY_REBASELINE.md` — Fresh security
8. `docs/current-state/READINESS_MATRIX.md` — Readiness dimensions
