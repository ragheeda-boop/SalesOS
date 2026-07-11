# Next Best Action Implementation Plan

> **الهدف:** خطة تنفيذ NBA Engine عبر Sprints مع تحليل المخاطر ومعايير الجودة
>
> **تاريخ:** 2026-07-11
> **المرحلة:** Phase 8 — Implementation Plan

---

## Sprint Breakdown

### Sprint 5.0 — NBA Architecture (2 weeks)

**الهدف:** بناء الأساس المعماري قبل أي كود تنفيذي

| Week | Tasks | Output |
|------|-------|--------|
| 1.1 | NBA Architecture Review + Approval | All architecture docs signed off |
| 1.2 | Platform Kernel — `contracts/ai/` + `contracts/revenue/` | TypeScript interfaces + Pydantic models |
| 1.3 | `opportunities` table + migration | Database schema |
| 1.4 | `opportunity_features` table + migration | Database schema |
| 1.5 | Opportunity Repository (backend) | CRUD operations |
| 1.6 | Initial NBA Engine — rules only (no AI) | Base pipeline: normalize → rules → score → rank |

**Quality Gates:**
- All contracts reviewed and approved
- Database migrations tested (up/down)
- Opportunity CRUD API tested
- NBA pipeline unit tests pass (rule-only mode)

---

### Sprint 5 — NBA Engine (2 weeks)

| Week | Tasks | Output |
|------|-------|--------|
| 1.1 | NBA Pipeline — Normalization stage | Signal normalization + context enrichment |
| 1.2 | NBA Pipeline — Business Rules (stage, time, signal, health) | 10+ rule implementations |
| 1.3 | NBA Pipeline — Scoring Engine | OpportunityScorer, UrgencyScorer, EffortEstimator |
| 1.4 | NBA Pipeline — Confidence Calculator + Ranker | Recommendation ranking + confidence |
| 1.5 | NBA REST API — `GET /nba`, `POST /nba/refresh` | NBA API endpoints |
| 1.6 | NBA Event Subscribers — opportunity events | Auto-recompute on stage change |
| 2.1 | NBA Frontend — `NBAWidget` + `RecommendationCard` | Workspace widget |
| 2.2 | NBA Frontend — `EvidencePanel` + `ConfidenceBadge` | Evidence display |
| 2.3 | NBA Frontend — `AlternativeActions` + `ActionLauncher` | Action execution |
| 2.4 | NBA Frontend — `FeedbackDialog` | Feedback collection |
| 2.5 | NBA Frontend — Integration with Opportunity Workspace | Widget in context |
| 2.6 | Integration tests: API → Engine → DB → Widget | End-to-end tests |

**Dependencies:** Sprint 5.0, Platform Kernel contracts

---

### Sprint 6 — Opportunity Workspace (3 weeks)

| Week | Tasks |
|------|-------|
| 1 | Opportunity CRUD full API (list, create, update, delete, stage management) |
| 1 | Opportunity Workspace — `createWorkspaceProvider(fetchOpportunity, deriveWidgets)` |
| 2 | Playbook Engine — Playbook CRUD + Playbook assignment to opportunities |
| 2 | Opportunity Workspace — Timeline widget (activities for this opportunity) |
| 2 | Deal Health — Health indicators computed and displayed |
| 3 | Opportunity Workspace — Company Snapshot (from Wave 1 Company Intelligence) |
| 3 | Integration: NBA widget embedded in Opportunity Workspace |
| 3 | Feature flag: NBA tier → `beta` |

**Dependencies:** Sprint 5 (NBA Engine)

---

### Sprint 7 — Pipeline Intelligence (3 weeks)

| Week | Tasks |
|------|-------|
| 1 | Pipeline Workspace — Kanban view (drag & drop stage changes) |
| 1 | Pipeline Workspace — List view (sortable, filterable table) |
| 2 | Pipeline Analytics — Velocity, Win Rate, Conversion Rate per stage |
| 2 | Health Map — Traffic light visualization for all open opportunities |
| 2 | Forecast Engine — Best Case, Commit, Pipeline forecasts |
| 3 | Pipeline export (CSV, PDF) |
| 3 | Pipeline API — `GET /pipeline`, `GET /pipeline/health`, `GET /pipeline/velocity` |
| 3 | Feature flag: Pipeline tier → `beta` |

**Dependencies:** Sprint 6

---

### Sprint 8 — Meeting & Email Intelligence (3 weeks)

| Week | Tasks |
|------|-------|
| 1 | Meeting data model + API (CRUD) |
| 1 | Meeting Workspace — Pre-Meeting Intelligence (Company Brief, Talking Points) |
| 1 | Meeting Workspace — During/Post-Meeting (Notes, Action Items) |
| 2 | AI Meeting Intelligence — AI Brief generation, Action Item extraction |
| 2 | Email data model + API (CRUD) |
| 2 | Email Intelligence — Sentiment analysis, Topic extraction |
| 3 | Email Integration — Gmail API connector |
| 3 | Email Integration — Outlook API connector |
| 3 | Meeting + Email integration with Activity Runtime |
| 3 | Feature flag: Meeting Intelligence tier → `beta` |

**Dependencies:** Sprint 6 (Opportunity Workspace), AI Platform

---

### Sprint 9 — Revenue Workspace & Integration (3 weeks)

| Week | Tasks |
|------|-------|
| 1 | Revenue Goals CRUD + tracking |
| 1 | Revenue Workspace — Executive Summary (Target vs Forecast) |
| 2 | Revenue Workspace — Team Performance dashboard |
| 2 | Revenue Workspace — AI Insights (At-Risk Deals, Coaching Recommendations) |
| 2 | NBA Feedback Engine — Feedback collection → Learning pipeline |
| 3 | Playbook Engine — full version with triggers and templates |
| 3 | Full integration: NBA → Pipeline → Meeting → Email → Revenue |
| 3 | Wave 2 E2E tests |
| 3 | Feature flags: all Wave 2 → `enterprise` (GA) |

**Dependencies:** Sprint 7, Sprint 8

---

## Dependency Graph

```
Sprint 5.0 (NBA Architecture)
    │
    ▼
Sprint 5 (NBA Engine) ──────────────────────────────────────────┐
    │                                                            │
    ▼                                                            │
Sprint 6 (Opportunity Workspace) ───┐                            │
    │                               │                            │
    ▼                               ▼                            ▼
Sprint 7 (Pipeline Intelligence)   Sprint 8 (Meeting & Email) ──┐
    │                               │                            │
    └───────────────────────────────┴────────────────────────────┘
                                    │
                                    ▼
                            Sprint 9 (Revenue Workspace)
```

**Parallel workstreams possible:**
- Sprint 7 (Pipeline) and Sprint 8 (Meeting/Email) can run in parallel
- Both depend on Sprint 6 but not on each other

---

## Risk Analysis

| Risk | Probability | Impact | Mitigation |
|------|-----------|--------|------------|
| AI API latency > 2s budget | Medium | High | Timeout + fallback to rule-only; cache AI results |
| OpenAI API key not configured | Medium | High | Rule-only mode works without AI; NBA degrades gracefully |
| Email integration (Gmail API) scope/complexity | High | Medium | Start with manual email logging; sync in Sprint 8 |
| Calendar integration scope | High | Medium | Manual meeting creation first; calendar sync in Sprint 8 |
| Opportunity Workspace scope creep | Medium | Medium | Strict MVP: NBA + Timeline + Company Snapshot only |
| Pipeline workspace drag-and-drop complexity | Medium | Medium | Use existing @dnd-kit library; test on mobile |
| NBA adoption < 60% target | Low | High | NBA Feedback Loop adjusts rules; user training; NBA-first UI |

---

## Quality Gates

### Gate 1: Sprint 5.0 Complete
- [ ] All architecture documents approved
- [ ] Database migrations written and tested
- [ ] Contracts (TypeScript + Pydantic) reviewed
- [ ] Opportunity Repository unit tests pass

### Gate 2: Sprint 5 Complete
- [ ] NBA Engine pipeline end-to-end: Signal → NBA
- [ ] NBA API: GET + POST /nba endpoints tested
- [ ] NBA Widget renders in Opportunity Workspace
- [ ] Rule-only mode works (no AI dependency)
- [ ] NBA unit tests > 80% coverage
- [ ] Explainability: every NBA includes evidence + reason

### Gate 3: Sprint 6 Complete
- [ ] Opportunity CRUD: all operations tested
- [ ] Opportunity Workspace: NBA + Timeline + Snapshot render
- [ ] Playbook Engine: CRUD + assignment tested
- [ ] Deal Health: indicators computed correctly
- [ ] Feature flag: beta tier enabled for internal users

### Gate 4: Sprint 7 Complete
- [ ] Pipeline Workspace: Kanban + List views render
- [ ] Pipeline Analytics: all metrics computed correctly
- [ ] Health Map: traffic light logic verified
- [ ] Forecast Engine: Best/Case/Commit forecasts match expectations

### Gate 5: Sprint 8 Complete
- [ ] Meeting Workspace: Pre/During/Post flows work
- [ ] Meeting Intelligence: AI summary generates in < 3s
- [ ] Email Intelligence: sentiment analysis returns valid results
- [ ] Email integration: Gmail sync working (OAuth)

### Gate 6: Sprint 9 Complete
- [ ] Revenue Workspace: all sections render with real data
- [ ] NBA Feedback Engine: feedback recorded + rules adjust
- [ ] Wave 2 E2E tests: NBA → Pipeline → Meeting → Revenue
- [ ] Feature flags: GA enabled
- [ ] Integration tests: Wave 1 + Wave 2 data flows

---

## Exit Criteria for Wave 2

| Criteria | Target | Verification |
|----------|--------|-------------|
| NBA Engine generates recommendations | 100% of opportunities | API test |
| NBA includes evidence trail | 100% of recommendations | Schema validation |
| NBA acceptance rate | > 60% | Feedback analytics |
| NBA engine latency (rule-only) | < 200ms | Performance test |
| NBA engine latency (with AI) | < 3s | Performance test |
| Pipeline accuracy | > 80% | Forecast vs actual comparison |
| Meeting Intelligence gen time | < 3s | Performance test |
| Email sync latency | < 30s | Integration test |
| Opportunity to Close Time reduction | > 30% | Before/after comparison (3 months post-launch) |

---

*NBA Implementation Plan complete. Ready for Phase 9: Architecture Validation Report.*
