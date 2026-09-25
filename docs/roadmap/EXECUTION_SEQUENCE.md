# EXECUTION SEQUENCE — 2026-08-24

**Answering: What happens first? What blocks what? What can run in parallel?**

---

## Phase A — Baseline Cleanup (NOW, no external dependency)

| Step | Task | Parallel? | Blocker |
|:----:|------|:---------:|---------|
| A1 | Delete 3 debug artifacts (_fails.txt, test_login.py, test_pool.py) | YES | None |
| A2 | Archive superseded docs (docs/vnext/, false GO claims) | YES | None |
| A3 | Fix 3 RLS gaps (approval_requests, llm_cost_entries, tenant_llm_budgets) | YES | None |
| A4 | Fix SignalEngine NBA defect | YES | None |
| A5 | Fix Railway preDeployCommand drift | YES | None |
| A6 | Clean 29 git stashes (review, keep relevant) | YES | None |

**Duration:** 1-2 sessions  
**External access needed:** None  
**Product decisions needed:** None

## Phase B — Engineering Hygiene (After Phase A)

| Step | Task | Parallel? | Blocker |
|:----:|------|:---------:|---------|
| B1 | Fix 48 event loop sync wrapper tests | YES | None |
| B2 | Fix 5 frontend path tests | YES | None |
| B3 | Fix 5 soak script tests | YES | None |
| B4 | Fix 2 event loop ordering tests | YES | None |
| B5 | Update documentation with corrected counts | YES | A2 |

**Duration:** 1 session  
**External access needed:** None  
**Product decisions needed:** None

## Phase C — Security Closure (After Phase A)

| Step | Task | Parallel? | Blocker |
|:----:|------|:---------:|---------|
| C1 | Re-audit security post RLS fixes | After A3 | A3 |
| C2 | Qualify commercial LLM provider | Parallel with C1 | External key |
| C3 | Engage external pentest | After C1 | C1, pentest vendor |

**Duration:** 2-4 weeks (depends on pentest vendor)  
**External access needed:** YES (LLM provider key, pentest vendor)  
**Product decisions needed:** YES (provider selection)

## Phase D — Infrastructure Hardening (Parallel with Phase C)

| Step | Task | Parallel? | Blocker |
|:----:|------|:---------:|---------|
| D1 | Create staging Google OAuth app | YES | Google Cloud Console |
| D2 | Enable Railway managed backup | YES | Railway Owner/Admin |
| D3 | Configure production Kafka | YES | None |
| D4 | Automate Railway rollback | YES | None |

**Duration:** 1-2 sessions  
**External access needed:** YES (Google Cloud, Railway)  
**Product decisions needed:** None

## Phase E — Validation (After Phases B, C, D)

| Step | Task | Parallel? | Blocker |
|:----:|------|:---------:|---------|
| E1 | Run full test suite (verify fixes) | YES | B1-B4 |
| E2 | Load/stress testing | After D3 | D3 |
| E3 | Security re-audit score | After C1 | C1 |
| E4 | Pentest results | After C3 | C3 |

**Duration:** 1-2 weeks  
**External access needed:** YES (load test infra, pentest)  
**Product decisions needed:** None

## Phase F — Go-Live (After Phases C, D, E)

| Step | Task | Parallel? | Blocker |
|:----:|------|:---------:|---------|
| F1 | Execute Wave 13 Go-Live runbook | Sequential | C1+C3+D1+D2+E1+E3+E4 |
| F2 | Start Wave 14 Hypercare | After F1 | F1 |
| F3 | 14-day monitoring | After F2 | F2 |

**Duration:** 2 weeks  
**External access needed:** YES (deployment, monitoring)  
**Product decisions needed:** YES (go/no-go sign-off, different people for CTO+TL)

## Phase G — Production GA (After Phase F)

| Step | Task | Parallel? | Blocker |
|:----:|------|:---------:|---------|
| G1 | Verify hypercare clean | Sequential | F3 |
| G2 | Business sign-off | After G1 | G1 |
| G3 | Declare Production GA | After G2 | G2 |

**Duration:** 1 session  
**External access needed:** None  
**Product decisions needed:** YES (GA declaration)

---

## Critical Path

```
Phase A (cleanup)
  → Phase B (engineering) ─────────────────────────────┐
  → Phase C (security) ──→ Phase E (validation) ───────┤
  → Phase D (infrastructure) ──────────────────────────┤
                                                        ↓
                                              Phase F (go-live)
                                                        ↓
                                              Phase G (GA)
```

**Critical path:** Phase A → Phase C (pentest) → Phase E (validation) → Phase F → Phase G

**Estimated total:** 4-8 weeks (dominated by pentest and hypercare)

---

## What Requires External Access

| Item | Access Needed | Who |
|------|--------------|-----|
| LLM provider key | API account | DevOps |
| Staging Google OAuth | Google Cloud Console | DevOps |
| Railway backup schedule | Railway Owner/Admin | Platform |
| Pentest vendor | Security engagement | Security |
| Load test infrastructure | Cloud compute | DevOps |

## What Requires Product Decisions

| Item | Decision | Who |
|------|----------|-----|
| LLM provider selection | Which commercial provider | PO + TL |
| Go-Live sign-off | CTO + TL (must be different people) | Management |
| GA declaration | Business readiness | PO + TL |
| Stripe billing | External Stripe account | Platform |
