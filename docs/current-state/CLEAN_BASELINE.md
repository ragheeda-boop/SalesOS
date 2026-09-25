# CLEAN BASELINE — 2026-08-24

**The authoritative starting point for all future work.**

---

## Verified State

| Property | Value | Evidence |
|----------|-------|----------|
| HEAD | `77bb684` | `git rev-parse HEAD` |
| Branch | `master` | `git branch --show-current` |
| Version | v5.1.0-phase4f-rc1 | `git describe --tags` |
| Python | 3.12.10 | `python --version` |
| Node.js | v24.18.0 | `node --version` |
| Migration head | `i3j4k5l6m7n8` | `app/alembic/versions/` |
| Total migrations | 100 | Verified file count |
| Backend modules | 31 | `app/modules/` |
| DDD domains | 18 | `domains/` |
| Runtime engines | 29 | `runtime/` |
| Grounded agents | 13 | `intelligence/agents/` |
| LLM providers | 5 | `intelligence/providers/` |
| Test files | 636 | Recursive count |
| Frontend routes | 107 | `page.tsx` files |
| docs/ .md files | 970 | Recursive count |
| ADRs | 28 | `docs/adr/` |
| RLS tables | 86+ | Migration evidence |
| RLS gaps | 0 | Fixed in Phase A (i3j4k5l6m7n8) |
| CI/CD workflows | 9 | `.github/workflows/` |
| Security domains PASS | 10/10 | SECURITY_REBASELINE.md (post Phase A) |
| Test failures | 10 skipped (env), 0 genuine | TEST_FAILURE_REGISTER.md (post Phase B) |
| Git stashes | 0 | Cleaned in Phase A |
| Railway config | Single (root) | salesos/railway.json archived (Phase A) |
| Dockerfile.railway | Updated with tini, poetry, scripts | Phase A |

## Authoritative Documents

| Document | Location | Purpose |
|----------|----------|---------|
| AGENTS.md | Root | Agent instructions |
| PROJECT_BIBLE.md | `docs/` | Engineering bible |
| FINAL_GO_NOGO_ASSESSMENT.md | `docs/audit/ga-engineering-audit/` | Current assessment |
| SALESOS_MASTER_CLOSURE_SEQUENCE.md | `docs/audit/ga-engineering-audit/` | Closure order |
| AI_HONESTY.md | `docs/audit/ga-engineering-audit/` | AI honesty |
| SECURITY_REBASELINE.md | `docs/current-state/` | Fresh security |
| READINESS_MATRIX.md | `docs/current-state/` | Readiness dimensions |
| MASTER_ROADMAP.md | `docs/roadmap/` | Current roadmap |
| MASTER_EXECUTION_BACKLOG.md | `docs/roadmap/` | Remaining work |
| EXECUTION_SEQUENCE.md | `docs/roadmap/` | Implementation order |
| DOCUMENT_AUTHORITY.md | `docs/current-state/` | Source-of-truth hierarchy |
| ARCHIVE_INDEX.md | `docs/archive/` | Historical archive |

| Security score | 88/100 | SECURITY_REBASELINE_2026-08-24.md |
| LLM provider qualified | NO | LLM_PROVIDER_QUALIFICATION.md |
| Pentest completed | NO | PENTEST_SCOPE.md (BLOCKED) |
| Kafka decision | DEFERRED | KAFKA_PRODUCTION_DECISION.md |
| Infrastructure readiness | PARTIAL | INFRASTRUCTURE_READINESS.md |
| Railway resolved | YES | Phase A — root railway.json = single source of truth |
| Dockerfile.railway updated | YES | Phase A — tini + poetry + scripts + PYTHONPATH |
| Staging readiness | BLOCKED | STAGING_READINESS.md — needs external access |
| LLM provider selection | BLOCKED | ADR-LLM-PROVIDER-SELECTION.md — needs management decision |
| Backup/DR validated | PARTIAL | BACKUP_DR_VALIDATION.md — automated NOT implemented |

## Readiness

| Dimension | Rating | Notes |
|-----------|:------:|-------|
| Engineering | GREEN | 0 genuine defects, all fixes applied |
| Security | GREEN | 88/100, no critical gaps |
| Infrastructure | YELLOW | Railway config conflict, OAuth not isolated |
| Product | YELLOW | No qualified LLM provider |
| Production/GA | RED | LLM provider, pentest, Railway config |
| **Overall** | **YELLOW** | Conditional on external dependencies |

## Classification

- ✅ Feature Complete (Phase 1-4)
- ✅ Engineering Complete (Phase 1-4)
- ✅ Pilot Ready (with documented limitations)
- ❌ Go-Live Ready
- ❌ Production Ready
- ❌ GA Ready

## Execution Order

1. ~~**Phase A:** Baseline cleanup (RLS fixes, config fix, doc archive, debug cleanup)~~ **DONE**
2. ~~**Phase B:** Engineering hygiene (test fixes, doc updates)~~ **DONE**
3. ~~**Phase C:** Security closure (re-audit, provider qualification, pentest)~~ **DONE** (audit + qualification; pentest BLOCKED)
4. ~~**Phase D:** Infrastructure hardening (OAuth, backups, Kafka, rollback)~~ **DONE** (inspection; fixes BLOCKED on external access)
5. **Phase E:** Validation (tests, load, security score, pentest)
6. **Phase F:** Go-Live (Wave 13, Wave 14 hypercare)
7. **Phase G:** Production GA

## Starting Point

Future agents and engineers should:

1. Read this document first
2. Read `AGENTS.md` for agent instructions
3. Read `docs/roadmap/MASTER_EXECUTION_BACKLOG.md` for remaining work
4. Read `docs/roadmap/EXECUTION_SEQUENCE.md` for implementation order
5. Read `docs/current-state/SECURITY_REBASELINE.md` for security status
6. Read `docs/current-state/TEST_FAILURE_REGISTER.md` for test status
7. Never trust documentation over code (Tier 1 is always truth)
8. Never claim GA without completing all release gates

---

**This clean baseline was established on 2026-08-24 from commit `77bb684` on branch `master`.**
