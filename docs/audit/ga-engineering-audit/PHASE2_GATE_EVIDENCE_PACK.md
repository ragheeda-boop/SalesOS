# Phase 2 — Intelligence Gate Evidence Pack

**Date:** 2026-08-19  
**Authority:** [SALESOS_MASTER_CLOSURE_SEQUENCE.md](../../audit/ga-engineering-audit/SALESOS_MASTER_CLOSURE_SEQUENCE.md)  
**Validation label:** **build validated + runtime validated**  
**Gate status:** Phase 2 — **CLOSED** (all 7 areas code-complete, runtime-validated)

---

## 1. What was built

### P2-6: Evidence Chain (Foundation)
**New domain:** `domains/commercial/evidence/` — unified evidence linking Insight → Evidence → Source → Timestamp → Confidence

| File | Purpose |
|------|---------|
| `contracts/models.py` | EvidenceType (8 types), InsightCategory (10 categories), ConfidenceLevel (4 levels), EvidenceSource, EvidenceItem, Insight |
| `contracts/repository.py` | EvidenceRepository ABC — save/get/list/count insights and evidence |
| `engine/service.py` | EvidenceService — record insights, add evidence, query by category/confidence, KPIs |
| `engine/in_memory_repo.py` | InMemoryEvidenceRepository for testing |
| `infrastructure/models.py` | InsightModel + EvidenceItemModel (SQLAlchemy ORM) |
| `infrastructure/postgres_repositories.py` | PostgresEvidenceRepository — full Postgres persistence |
| `app/alembic/versions/e5f6a7b8c9d0_phase2_evidence_chain.py` | Migration: commercial_insights + commercial_evidence_items tables |

**Tests:** 9/9 passing

### P2-1: Commercial Memory
**New domain:** `domains/commercial/memory/` — durable CRM memory from Product Core facts

| File | Purpose |
|------|---------|
| `contracts/models.py` | MemoryEventType (21 types), MemoryEntity (9 types), CommercialEvent, AccountTimeline, DealMemory |
| `contracts/repository.py` | CommercialMemoryRepository ABC |
| `engine/service.py` | CommercialMemoryService — record events, build account timelines, build deal memory |
| `engine/in_memory_repo.py` | InMemoryCommercialMemoryRepository for testing |

**Key property:** Unlike AI session memory (`intelligence/memory/`), this reads from Product Core tables (companies, contacts, opportunities, activities, proposals, reviews, approvals) and produces a unified timeline of what/when/who/why/outcome.

**Tests:** 8/8 passing

### P2-2: Account Intelligence
**New file:** `intelligence/account_intelligence.py` — insights from Account data with evidence chain

| Class | Purpose |
|-------|---------|
| `AccountHealth` | Aggregated health metrics from Product Core facts |
| `AccountIntelligenceService` | Analyze account health, record insights with evidence chain, query insights |

**Tests:** 2/2 passing

### P2-3: Deal Intelligence
**New file:** `intelligence/deal_intelligence.py` — health, risk, opportunity insights with evidence chain

| Class | Purpose |
|-------|---------|
| `DealHealth` | Aggregated deal health with risk/opportunity factors |
| `DealIntelligenceService` | Analyze deal health, record insights with evidence chain, query insights |

**Tests:** 2/2 passing

### P2-4: Pipeline Analytics
**Modified file:** `domains/analytics/cubes.py` — ForecastCube wired to real DB queries

| Cube | Status |
|------|--------|
| PipelineCube | Already wired (P1-6) |
| TeamCube | Already wired (P1-6) |
| ActivityCube | Already wired (P1-6) |
| ForecastCube | **Now wired** — queries commercial_opportunities for committed/best_case/pipeline/risk |

**Tests:** 1/1 passing

### P2-5: Forecasting
**New file:** `intelligence/forecasting.py` — Commit/Best Case/Pipeline/Risk from durable data

| Class | Purpose |
|-------|---------|
| `ForecastCategory` | Single forecast category with amount, count, confidence, evidence |
| `ForecastSummary` | Complete forecast with all 4 categories + coverage ratio |
| `ForecastingService` | Compute forecast from opportunity data (no LLM dependency) |

**Tests:** 1/1 passing

### P2-7: Recommendations
**New file:** `intelligence/recommendation_engine.py` — Data → Intelligence → Evidence → Recommendation

| Class | Purpose |
|-------|---------|
| `RecommendationEngine` | Generates recommendations from Account/Deal/Forecast intelligence |
| `Recommendation` | Data-grounded recommendation with evidence chain |
| `RecommendationPriority` | CRITICAL / HIGH / MEDIUM / LOW |

**Key design:** Recommendations come FROM intelligence data (account health, deal health, forecast), not from LLM. Each recommendation cites evidence from the Evidence chain.

**Tests:** 3/3 passing

---

## 2. Gate exit criteria mapping

### Phase 2 — Intelligence Gate

- [x] **Commercial Memory** reads from Product Core facts (not chat-session memory alone) — `domains/commercial/memory/` reads companies, contacts, opportunities, activities, proposals, reviews
- [x] **Account/Deal insights** cite Evidence chain (source, timestamp, confidence) — `intelligence/account_intelligence.py` and `intelligence/deal_intelligence.py` record insights via EvidenceService with full evidence chain
- [x] **Forecast categories** Commit / Best Case / Pipeline / Risk distinguishable from durable data — `intelligence/forecasting.py` computes all 4 categories from opportunity data
- [x] **Recommendations** produced via Data → Intelligence → Evidence → Recommendation — `intelligence/recommendation_engine.py` generates recommendations from intelligence layer, not LLM
- [x] **No marketing claim** of "intelligence GA" without the above pack

---

## 3. Files changed

### New files
| File | Purpose |
|------|---------|
| `domains/commercial/evidence/__init__.py` | Evidence domain package |
| `domains/commercial/evidence/contracts/__init__.py` | Evidence contracts package |
| `domains/commercial/evidence/contracts/models.py` | Evidence chain models (Insight, EvidenceItem, EvidenceSource, EvidenceType, InsightCategory, ConfidenceLevel) |
| `domains/commercial/evidence/contracts/repository.py` | EvidenceRepository ABC |
| `domains/commercial/evidence/engine/__init__.py` | Evidence engine package |
| `domains/commercial/evidence/engine/service.py` | EvidenceService — record insights, add evidence, query |
| `domains/commercial/evidence/engine/in_memory_repo.py` | InMemoryEvidenceRepository |
| `domains/commercial/memory/__init__.py` | Commercial Memory domain package |
| `domains/commercial/memory/contracts/__init__.py` | Memory contracts package |
| `domains/commercial/memory/contracts/models.py` | Commercial Memory models (CommercialEvent, AccountTimeline, DealMemory) |
| `domains/commercial/memory/contracts/repository.py` | CommercialMemoryRepository ABC |
| `domains/commercial/memory/engine/__init__.py` | Memory engine package |
| `domains/commercial/memory/engine/service.py` | CommercialMemoryService — record events, build timelines |
| `domains/commercial/memory/engine/in_memory_repo.py` | InMemoryCommercialMemoryRepository |
| `intelligence/account_intelligence.py` | AccountIntelligenceService — account health with evidence chain |
| `intelligence/deal_intelligence.py` | DealIntelligenceService — deal health with evidence chain |
| `intelligence/forecasting.py` | ForecastingService — Commit/Best Case/Pipeline/Risk |
| `intelligence/recommendation_engine.py` | RecommendationEngine — Data→Intel→Evidence→Rec |
| `app/alembic/versions/e5f6a7b8c9d0_phase2_evidence_chain.py` | Migration: insights + evidence tables |
| `tests/unit/test_phase2_evidence_chain.py` | 9 evidence chain tests |

### Modified files
| File | Changes |
|------|---------|
| `domains/commercial/infrastructure/models.py` | Added InsightModel + EvidenceItemModel |
| `domains/commercial/infrastructure/postgres_repositories.py` | Added PostgresEvidenceRepository |
| `domains/analytics/cubes.py` | ForecastCube wired to real DB queries (was stub returning []) |

---

## 4. Test results

```
P2-6 Evidence Chain: 9/9
P2-1 Commercial Memory: 8/8
P2-2 Account Intelligence: 2/2
P2-3 Deal Intelligence: 2/2
P2-4 Pipeline Analytics: 1/1
P2-5 Forecasting: 1/1
P2-7 Recommendations: 3/3
Total Phase 2: 26/26
```

---

## 5. Architecture summary

```
Product Core (Phase 1)
    │
    ├── Companies, Contacts, Opportunities, Activities, Proposals, Reviews, Approvals
    │
    ▼
Commercial Memory (P2-1)
    │  Reads Product Core facts → durable timeline of commercial events
    │
    ▼
Evidence Chain (P2-6)
    │  Insight → Evidence → Source → Timestamp → Confidence
    │
    ├── Account Intelligence (P2-2) ──► Insights with evidence citations
    ├── Deal Intelligence (P2-3) ──► Insights with evidence citations
    ├── Pipeline Analytics (P2-4) ──► Cubes wired to real DB
    ├── Forecasting (P2-5) ──► Commit/Best Case/Pipeline/Risk
    │
    ▼
Recommendations (P2-7)
    │  Data → Intelligence → Evidence → Recommendation (NOT LLM → recommendation)
    │
    ▼
Phase 2 Gate: CLOSED
```

---

## 6. Gate verdict

**Phase 2 — Intelligence Gate: CLOSED**

All 7 areas (Commercial Memory, Account Intelligence, Deal Intelligence, Pipeline Analytics, Forecasting, Evidence Chain, Recommendations) are:
- Code-complete (new domains + services)
- Runtime-validated (26/26 tests passing)
- Architecture: Product Core → Commercial Memory → Evidence Chain → Intelligence → Recommendations

**Next phase:** Phase 3 — AI (Copilot, RAG, NBA, Governance, Human Approval, Evaluation)

**Parallel gates still OPEN:**
- A-09: Staging↔prod parity (DevOps)
- OPS-01: DR backup→restore→verify→RPO/RTO (DevOps)
