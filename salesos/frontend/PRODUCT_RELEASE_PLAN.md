# SalesOS Product Release Plan

> Executive Summary — Wave 1–4 Roadmap
> Last Updated: 2026-07-10

---

## Current Status

```
Discover     ████████████████████████████████ 100%  ✅
Understand   ████████████████████████████████ 100%  ✅
Take Action  ████████░░░░░░░░░░░░░░░░░░░░░░░  15%  🚧
Grow Revenue ████░░░░░░░░░░░░░░░░░░░░░░░░░░░   0%  ⏳
Enterprise   ████░░░░░░░░░░░░░░░░░░░░░░░░░░░   0%  ⏳
```

---

## Wave 1: Discover & Understand

**Status: ✅ 100% Complete**

| Delivery | Component | Status | Notes |
|----------|-----------|--------|-------|
| Sprint 0 | Engineering Platform | ✅ | Design Language, UI Kit, Foundation Components, Workspace SDK v1.0 |
| Sprint 1 | Product Foundation | ✅ | 22 Foundation Components, 15 UI Kit restyled, Dashboard Layout |
| Sprint 2 | Dashboard Workspace | ✅ | 6 Widgets (Mission Center, Intelligence Feed, Decision Queue, AI Brief, Market Pulse, Recent Activity) — 246 tests |
| Sprint 3 | Company Intelligence | ✅ | 10 Widgets (Company DNA, AI Recommendation Engine, Decision Makers, Relationship Graph, Smart Timeline, Signals Feed, Government Intelligence, Document Intelligence, Buying Journey, Golden Record) — 264 tests |
| Phase B | Universal Search | ✅ | Search SDK, Command Bar (Ctrl+K), Quick Overlay, Search Page, AI Answer, 16 Foundation Components — 81 tests |
| **Wave 1 Total** | | ✅ | **591 tests, 0 regressions** |

### Wave 1 Scorecard

| Domain | Score |
|--------|-------|
| Product Readiness | 9/10 |
| Architecture Compliance | 95% |
| Test Coverage (widgets) | 100% |
| Accessibility | WCAG AA |
| Performance | Within budgets |

---

## Wave 2: Revenue Execution Platform

**Status: 🚧 In Progress — Next Best Action Engine First**

### Philosophy

Wave 1 answers: "What does this company look like?"

Wave 2 answers: **"What should I do next?"**

This is the Action Layer. Everything transforms from intelligence into revenue operations.

### Architecture

```
Company Intelligence (Wave 1)
        ↓
AI Recommendation Engine (Built)
        ↓
Next Best Action Engine ← FIRST BUIL
        ↓
Opportunity Workspace
        ↓
Pipeline Intelligence
        ↓
Playbook Engine
        ↓
Meeting Intelligence
        ↓
Email Intelligence
        ↓
Task Intelligence
        ↓
Revenue Timeline
        ↓
Revenue (Wave 3)
```

### Build Order

| Phase | Component | Est. Effort | Depends On | Value |
|-------|-----------|-------------|------------|-------|
| **1** | **Next Best Action Engine** | 1 sprint | Company DNA + AI Recommendation | **Critical** |
| 2 | Opportunity Workspace | 2 sprints | NBA Engine | Critical |
| 3 | Pipeline Intelligence | 1 sprint | Opportunity | High |
| 4 | Playbook Engine | 2 sprints | Company Intelligence | High |
| 5 | Meeting Intelligence | 1 sprint | Decision Makers + Timeline | High |
| 6 | Email Intelligence | 1 sprint | Search SDK | Medium |
| 7 | Task Intelligence | 1 sprint | NBA Engine | Medium |
| 8 | Revenue Timeline | 1 sprint | All above | High |

### Phase 1: Next Best Action Engine — Detailed

The NBA Engine is the single most important widget in the entire product. It is the bridge between intelligence and action.

**Inputs:**
- Company DNA (industry, size, buying intent, risk, relationship strength)
- AI Recommendation (recommended action, confidence, revenue)
- Timeline (recent signals, events, meetings)
- Current pipeline state

**Output (per company):**
```
{
  action: "Schedule executive briefing",
  reason: "رئيس الشركة الجديد + إشارات توسع + نية شراء عالية",
  confidence: 0.88,
  expectedRevenue: "$500K",
  expectedImpact: "High — decision maker engaged",
  estimatedTime: "2 weeks",
  risks: ["مورد بديل قيد التقييم"],
  alternatives: ["Send proposal draft", "Invite to event"],
  playbook: "enterprise-expansion-v2"
}
```

**Widget Architecture:**
```
NBAContainer (createWidget)
  └── NBAView
       ├── Primary Action Card
       │    ├── Action label + icon
       │    ├── Reasoning (natural language)
       │    ├── Confidence gauge
       │    ├── Revenue impact
       │    └── Timeline
       ├── Risk Section
       ├── Alternatives Section
       ├── Context Section (why now)
       └── Execute Button → creates Opportunity/Task
```

---

## Wave 3: Revenue Intelligence

**Status: ⏳ Not Started — depends on Wave 2**

| Component | Description | Est. Effort |
|-----------|-------------|-------------|
| Forecast Intelligence | AI-powered pipeline forecasting | 2 sprints |
| Territory Intelligence | Territory allocation + optimization | 2 sprints |
| Revenue Health | Multi-company revenue scorecard | 1 sprint |
| Expansion Intelligence | Cross-sell/up-sell opportunities | 2 sprints |
| Churn Intelligence | At-risk account detection | 1 sprint |
| Revenue Timeline | Consolidated revenue view | 1 sprint |

### Dependencies
- Wave 2 must be complete (Opportunity, Pipeline, Meeting data sources)
- Requires pipeline data from Wave 2
- Requires meeting/email engagement data

---

## Wave 4: Enterprise

**Status: ⏳ Not Started — depends on Wave 2–3**

| Component | Description | Est. Effort |
|-----------|-------------|-------------|
| Marketplace | Plugin ecosystem | 3 sprints |
| MCP Integration | Model Context Protocol for external tools | 2 sprints |
| Multi-workspace | Cross-entity workspace switching | 2 sprints |
| Enterprise Security | SSO, RBAC, Audit, Compliance | 2 sprints |
| API Platform | Public API for integrations | 3 sprints |

---

## Overall Scorecard

| Domain | Current | Target | Δ |
|--------|---------|--------|---|
| Engineering Platform | 100% | 100% | ✅ |
| Design System | 100% | 100% | ✅ |
| Workspace SDK | 100% | 100% | ✅ |
| Search SDK | 100% | 100% | ✅ |
| Dashboard Workspace | 100% | 100% | ✅ |
| Universal Search | 100% | 100% | ✅ |
| Company Intelligence | 100% | 100% | ✅ |
| **Wave 1 (Discover & Understand)** | **100%** | **100%** | **✅** |
| **Wave 2 (Take Action)** | **15%** | **100%** | **🚧** |
| **Wave 3 (Grow Revenue)** | **0%** | **100%** | **⏳** |
| **Wave 4 (Enterprise)** | **0%** | **100%** | **⏳** |
| **Overall Product** | **~75%** | **100%** | **🟡** |

---

## Immediate Next Action

**Build the Next Best Action Engine.**

This is the single most important component. It transforms SalesOS from a discovery platform into a revenue execution platform.

1. Create `docs/revenue-execution/NEXT_BEST_ACTION_ARCHITECTURE.md`
2. Design the NBA Engine as a workspace widget using Workspace SDK
3. Build NBA Container + View + Tests
4. Connect to existing Company Intelligence data
5. Add Execute action → Opportunity creation flow

All Wave 2 depends on this component. Nothing else should be built until the NBA Engine is production-ready with full contract tests, accessibility, and documentation.
