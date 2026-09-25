# MASTER ROADMAP — 2026-08-24

**Authority:** Rebuilt from actual repository state, not old plans.

---

## Current Baseline

- HEAD: `77bb684` on `master`
- Version: v5.1.0-phase4f-rc1
- Readiness: YELLOW (pilot-ready with conditions)

## Completed

| Area | Status | Evidence |
|------|--------|----------|
| Phase 1 Product Core | ENGINEERING COMPLETE | 278 tests, 9/9 browser QA, 4 Alembic migrations |
| Phase 2 Intelligence | ENGINEERING COMPLETE | 26 tests, deterministic, zero-LLM |
| Phase 3 AI | ENGINEERING COMPLETE | 86 tests, flag=True, HITL approval, governance |
| Phase 4 Platform | ENGINEERING COMPLETE | 17 tests, DLQ, capability registry, observability |
| Phase 4A-4F Data Layer | ENGINEERING COMPLETE | 144 tests, ICP, RAG RLS, signals, 13 agents |
| P0 Schema Drift | RESOLVED | 13 migrations applied to production |
| A-09 Staging Parity | PASS | Staging deployed with matching schema |
| OPS-01 Rows 1-3, 4, 8 | SIGNED | Backup/WAL/PITR + RPO/RTO accepted |
| Soak Option A | ACCEPTED | 854 iterations, accept-with-conditions |

## Active (In Progress)

| Item | Owner | Blocker |
|------|-------|---------|
| Baseline validation & cleanup | Agent | This phase |
| RLS gap fix (3 tables) | Engineering | None |
| Test failure resolution (60 env issues) | Engineering | None |

## Blocked

| Item | Owner | Blocker |
|------|-------|---------|
| LLM provider qualification | DevOps | No commercial provider available |
| Staging Google OAuth | DevOps | Google Cloud Console access |
| Railway managed backup | Platform | Railway Owner/Admin |
| Railway preDeployCommand drift | DevOps | Config alignment |
| External pentest | Security | Engagement not started |
| Stripe billing wiring | Platform | External Stripe account |

## Remaining (Not Started)

| Item | Priority | Phase |
|------|:--------:|-------|
| Fix 3 RLS gaps | P0 | Security closure |
| Qualify LLM provider | P0 | Security closure |
| Fix Railway config drift | P0 | Infrastructure |
| Re-audit security post-fixes | P1 | Security closure |
| External pentest | P1 | Security closure |
| Fix 60 test environment issues | P1 | Engineering hygiene |
| Automated Railway rollback | P1 | Infrastructure |
| Staging Google OAuth | P1 | Infrastructure |
| Railway managed backups | P1 | Infrastructure |
| Production Kafka config | P2 | Infrastructure |
| Load/stress testing | P2 | Validation |
| Stripe billing | P2 | Product |
| Go-Live execution (Wave 13) | P1 | Release |
| Hypercare (Wave 14) | P1 | Release |
| Production GA declaration | P2 | Release |

## Deferred

| Item | Reason |
|------|--------|
| Neo4j production | ADR-108: keep offline |
| Multi-product platform | ADR-106: SalesOS-only scope |
| Digital Twin | ADR-103: deferred |
| Revenue Brain | ADR-105: deferred |

## Superseded

| Old Plan | Replacement |
|----------|-------------|
| docs/vnext/ (entire directory) | docs/audit/ga-engineering-audit/ |
| GO_NO_GO_DECISION.md (GO claim) | FINAL_GO_NOGO_ASSESSMENT.md |
| GA_CHECKLIST.md (15/15 PASS) | FINAL_GO_NOGO_ASSESSMENT.md |

## Next Execution Phase

**Phase: Security Closure + Infrastructure Hardening**

1. Fix 3 RLS gaps (approval_requests, llm_cost_entries, tenant_llm_budgets)
2. Qualify commercial LLM provider
3. Fix Railway preDeployCommand drift
4. Re-audit security post Phase 1-4 fixes
5. Engage external pentest
6. Resolve 60 test environment issues
7. Fix 1 genuine defect (SignalEngine NBA)

## Release Gates

| Gate | Criteria | Status |
|------|----------|:------:|
| Security Gate | All RLS gaps fixed, pentest clean, score ≥70/100 | NOT MET |
| Provider Gate | Commercial LLM provider qualified | NOT MET |
| Infrastructure Gate | Railway config aligned, backups automated | NOT MET |
| Test Gate | Zero genuine defects, env issues quarantined | NOT MET |
| Go-Live Gate | Wave 13 runbook executed, signatures obtained | NOT MET |
| GA Gate | All above + hypercare complete + business sign-off | NOT MET |
