# SalesOS — Revised Implementation Roadmap

**Date:** July 2, 2026
**Context:** Response to architectural review — Platform → Product transformation
**Goal:** Business Operating System (not CRM, not Platform)

---

## Core Thesis

> SalesOS does NOT need rebuilding. It needs **transformation from Platform to Product**.

The DDD, Runtime, SDK, Design System, Data Fabric, Scrapers, Event System — all exist. They are world-class.

The only missing thing is: **connecting them to serve real business workflows.**

This roadmap replaces the 39-week plan with a **12-16 week plan** organized by **business value**, not by modules.

---

## PART 1 — Architectural Additions

### 1.1 Activity Runtime (NEW — The Spinal Column)

**Problem today:** Every module handles its own events. There is no unified Activity backbone. Employee 360, Company 360, Timeline, Knowledge Graph, AI — each independently rebuilds the same query patterns.

**Solution:** Replace scattered event handling with a single **Activity Runtime** that becomes the authoritative record of everything.

```
┌─────────────────────────────────────────────────────────────┐
│                     ACTIVITY RUNTIME                         │
│                                                              │
│  Email ──┐                                                  │
│  Meeting ─┤                                                  │
│  Task ────┤───→ Activity Stream ──→ Event Store              │
│  Contract ┤         │                                        │
│  Proposal ┤         │                                        │
│  Comment ─┤         │                                        │
│  Approval ┤         │                                        │
│  File ────┘         │                                        │
│                     ▼                                        │
│              ┌──────────────┐                                │
│              │  Activity DB  │──→ Timeline                   │
│              │  (PostgreSQL) │──→ Knowledge Graph            │
│              └──────────────┘──→ AI Context                  │
│                                │→ Notifications              │
│                                │→ Analytics                  │
│                                │→ Employee 360               │
│                                │→ Company 360                │
└─────────────────────────────────────────────────────────────┘
```

**Activity Schema:**
```
Activity {
    id: UUID
    tenant_id: UUID
    entity_type: string       // email, meeting, task, contract, proposal, comment, approval, file, note
    entity_id: UUID
    action: string            // created, updated, deleted, sent, received, completed, approved, rejected
    actor_id: UUID            // user who performed
    target_id: UUID           // company, contact, opportunity
    target_type: string
    metadata: JSONB           // type-specific payload
    timestamp: DateTime
    duration: int?            // for meetings, calls
    source: string            // gmail, outlook, salesos, notion, manual
}
```

**This replaces:**
- `sdk/events/` for business tracking (keeps events for infrastructure)
- Manual timeline building in every module
- Scattered notification logic
- Manual audit log construction

**What this enables instantly:**
- Employee Timeline: `SELECT * FROM activities WHERE actor_id = ? ORDER BY timestamp DESC`
- Company Timeline: `SELECT * FROM activities WHERE target_id = ? ORDER BY timestamp DESC`
- Daily Stats: `SELECT entity_type, COUNT(*) FROM activities WHERE actor_id = ? AND timestamp::date = today GROUP BY entity_type`
- Weekly Stats: Same pattern with date range
- KPIs: `COUNT(*) WHERE entity_type='meeting' AND actor_id = ? AND timestamp IN (this_week)`
- Knowledge Graph edges: Every activity is a potential edge between actor and target

---

### 1.2 Data Lake (NEW — Universal Ingestion)

**Problem today:** Data lives in Notion, Excel files, scrapers, CRM pipeline. No unified import path.

**Solution:**

```
┌──────────┐
│  Notion  │────┐
├──────────┤    │    ┌─────────────────┐    ┌──────────────────┐
│  Excel   │────┤    │                 │    │                  │
├──────────┤    ├───→│   DATA LAKE     │───→│  Unified Model   │
│  Gmail   │────┤    │  (PostgreSQL)   │    │  (Standardized)  │
├──────────┤    │    │                 │    │                  │
│  Scrapers│────┘    └─────────────────┘    └──────────────────┘
└──────────┘
```

**Data Lake Schema (additional to existing company/contact/opportunity tables):**
- `import_jobs` — track import provenance
- `source_documents` — raw data storage
- `field_mappings` — source→unified field mapping
- `import_errors` — validation failures
- `sync_status` — per-source freshness tracking

**Priority order for connectors:**
1. Notion (exists — plug into Data Lake instead of separate scripts)
2. Excel/CSV (exists — add UI upload)
3. Gmail API
4. Outlook API
5. Google Calendar API
6. Outlook Calendar API
7. CRM API (HubSpot, Salesforce)
8. ERP API (future)

---

### 1.3 Work Intelligence Engine (NEW — Differentiator)

**Problem today:** No system measures how salespeople actually spend time. HubSpot/Salesforce track deals, not work.

**Solution:**

```
┌─────────────────────────────────────────────────────────────────┐
│                    WORK INTELLIGENCE ENGINE                       │
│                                                                   │
│  ┌──────────────┐  ┌──────────────┐  ┌────────────────────────┐ │
│  │ Calendar Feed │  │  Email Feed  │  │  Activity Stream       │ │
│  │ (Google/MS)   │  │ (Gmail/Out)  │  │  (SalesOS Internal)    │ │
│  └──────┬───────┘  └──────┬───────┘  └─────────┬──────────────┘ │
│         │                 │                     │                │
│         ▼                 ▼                     ▼                │
│  ┌──────────────────────────────────────────────────────────────┐│
│  │                    WORK INTELLIGENCE COMPUTER                  ││
│  │                                                              ││
│  │  Time Allocation:      meetings / emails / tasks / focus     ││
│  │  Meeting Load:         hours in meetings per day/week        ││
│  │  Email Load:           emails sent/received per day          ││
│  │  Customer Load:        unique customers contacted per day    ││
│  │  Focus Time:           blocks > 2h without meetings          ││
│  │  Work Balance:         internal vs external time             ││
│  │  Productivity Score:   output vs time invested               ││
│  │  Activity Score:       total meaningful actions per day      ││
│  └──────────────────────────────────────────────────────────────┘
│                              │
│                              ▼
│                    ┌─────────────────┐
│                    │  Employee 360    │
│                    │  Dashboard       │
│                    │  AI Coach        │
│                    └─────────────────┘
└───────────────────────────────────────────────────────────────────┘
```

**Key insight:** This data feeds **Employee 360** and **AI Coach** directly without additional integrations.

---

### 1.4 Revised Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                         SALESOS ARCHITECTURE                          │
│                                                                      │
│  ┌─────────────────────────────────────────────────────────────────┐ │
│  │                     APPLICATION LAYER                             │ │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌────────────────┐  │ │
│  │  │ Company  │  │ Employee │  │Executive │  │    AI Copilot  │  │ │
│  │  │   360    │  │   360    │  │Dashboard │  │   (NLP→Query)  │  │ │
│  │  └──────────┘  └──────────┘  └──────────┘  └────────────────┘  │ │
│  └─────────────────────────────────────────────────────────────────┘ │
│                                  │                                   │
│  ┌─────────────────────────────────────────────────────────────────┐ │
│  │                     COMPOSITION LAYER                             │ │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌────────────────┐  │ │
│  │  │ Timeline │  │  Search  │  │  Graph   │  │  Workspace     │  │ │
│  │  │  Engine  │  │  Engine  │  │  Engine  │  │  Engine        │  │ │
│  │  └──────────┘  └──────────┘  └──────────┘  └────────────────┘  │ │
│  └─────────────────────────────────────────────────────────────────┘ │
│                                  │                                   │
│  ┌─────────────────────────────────────────────────────────────────┐ │
│  │                   ACTIVITY RUNTIME ★                              │ │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌────────────────┐  │ │
│  │  │ Calendar │  │  Email   │  │  Events  │  │  Work Intel    │  │ │
│  │  │  Intel   │  │  Intel   │  │  Stream  │  │  Engine ★      │  │ │
│  │  └──────────┘  └──────────┘  └──────────┘  └────────────────┘  │ │
│  └─────────────────────────────────────────────────────────────────┘ │
│                                  │                                   │
│  ┌─────────────────────────────────────────────────────────────────┐ │
│  │                   DATA LAKE ★                                     │ │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌────────────────┐  │ │
│  │  │  Notion  │  │  Excel   │  │  Gmail   │  │  Calendar      │  │ │
│  │  │  Import  │  │  Import  │  │  Import  │  │  Import        │  │ │
│  │  └──────────┘  └──────────┘  └──────────┘  └────────────────┘  │ │
│  └─────────────────────────────────────────────────────────────────┘ │
│                                  │                                   │
│  ┌─────────────────────────────────────────────────────────────────┐ │
│  │                     CORE PLATFORM (Existing — Unchanged)          │ │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌────────────────┐  │ │
│  │  │ DDD      │  │ Runtime  │  │   SDK    │  │  Design System │  │ │
│  │  │ Modules  │  │ (27)     │  │ (25)     │  │  + UI          │  │ │
│  │  └──────────┘  └──────────┘  └──────────┘  └────────────────┘  │ │
│  └─────────────────────────────────────────────────────────────────┘ │
│                                  │                                   │
│  ┌─────────────────────────────────────────────────────────────────┐ │
│  │                     INFRASTRUCTURE (Existing)                     │ │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌────────────────┐  │ │
│  │  │PostgreSQL│  │  Neo4j   │  │  Redis   │  │  Kafka         │  │ │
│  │  │ pgvector │  │  Graph   │  │  Cache   │  │  Events        │  │ │
│  │  └──────────┘  └──────────┘  └──────────┘  └────────────────┘  │ │
│  └─────────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────┘
```

---

## PART 2 — REVISED SPRINT PLAN (12-16 weeks)

### Sprint 1 — Data Foundation (Weeks 1-3)

**Theme:** All data in PostgreSQL. No more InMemory. Universal import.

| Item | Effort | Details |
|------|--------|---------|
| PostgreSQL for ALL commercial domains | 40h | Opportunity, Pipeline, Activity, Quote, Proposal, Contract, Forecast — replace InMemory with asyncpg |
| Contact module (full CRUD) | 24h | models, repos, schemas, service, router, tests |
| Notion → Data Lake import | 16h | Centralized import: NCNP, Balady, Najiz, REGA, Taqeem |
| Excel/CSV import (UI + API) | 16h | Upload → parse → validate → insert |
| Unified Data Model migration | 16h | Standardize company, contact, activity schemas across all sources |
| Database migrations (all schemas) | 8h | alembic revisions for everything |
| **Total** | **120h** | |

**Deliverable:** Single source of truth in PostgreSQL. All company data, contacts, Notion data, CRM data in one place.

---

### Sprint 2 — Activity Runtime + Core 360 (Weeks 4-7)

**Theme:** Build the Activity backbone. Ship Company 360 + Employee 360 MVP.

| Item | Effort | Details |
|------|--------|---------|
| **Activity Runtime** | 40h | Activity schema, Event→Activity pipeline, Activity Store (PostgreSQL), Activity API, Activity subscription |
| Activity Timeline Engine | 24h | Unified timeline from Activity Stream. `GET /api/v1/activities?actor=X&target=Y&since=Z` |
| Timeline UI (universal) | 16h | Single timeline component for Employee 360 and Company 360 |
| **Company 360 MVP** | 40h | Overview: profile, branches, licenses, contacts, assigned employees. Timeline: all activities. Data: contracts, invoices, opportunities. |
| **Employee 360 MVP** | 40h | Profile, portfolio (companies, contacts, pipeline, revenue), timeline, daily activity summary |
| Search across all entities | 16h | Unified search: companies, contacts, employees, activities |
| Employee list + Company list (frontend) | 16h | Table with search, filter, pagination |
| Login + Workspace (wire existing UI) | 8h | Connect frontend auth to backend, workspace routing |
| **Total** | **200h** | |

**Deliverable:** Muhide team can log in, see companies, see employees, search everything, view Company 360 and Employee 360 with real data.

**What Muhide sees after Sprint 2:**
- ✅ Company 360 (profile, contacts, timeline, contracts)
- ✅ Employee 360 (profile, portfolio, timeline, daily activity)
- ✅ Search (companies, contacts, employees)
- ✅ Timeline (everything in one stream)
- ✅ All Notion data in PostgreSQL
- ✅ Excel import

---

### Sprint 3 — Calendar + Email Intelligence (Weeks 8-11)

**Theme:** Connect real communication data. Enable Calendar Intelligence + Email Intelligence.

| Item | Effort | Details |
|------|--------|---------|
| Gmail API integration | 24h | OAuth2, watch, webhook, email parsing, store in Activity Runtime |
| Outlook API integration (Microsoft Graph) | 24h | OAuth2, delta query, webhook, email parsing |
| Email Intelligence Service | 16h | `emails_sent`, `emails_received`, `replies`, `response_time`, `top_contacts`, `top_companies` |
| Email UI (Employee 360) | 16h | Email list, thread view, sent/received counts per day |
| Google Calendar API integration | 16h | Events, webhook, meeting detection |
| Outlook Calendar API integration | 16h | Events, delta sync, meeting detection |
| Calendar Intelligence Service | 16h | `meetings_today`, `meetings_this_week`, `duration`, `frequency`, `cancellations`, `upcoming` |
| Calendar UI (Employee 360) | 16h | Meeting list, day/week/month view, time allocation |
| **Total** | **128h** | |

**Deliverable:** Employee 360 now shows real email and calendar data. Calendar Intelligence and Email Intelligence computed live.

**What Muhide sees after Sprint 3:**
- ✅ Emails sent/received per employee
- ✅ Meetings today, this week, this month
- ✅ Meeting duration, frequency
- ✅ Average response time per contact
- ✅ Top companies by email volume
- ✅ Calendar time allocation

---

### Sprint 4 — Knowledge Graph + KPIs + Work Intelligence (Weeks 12-16)

**Theme:** Connect everything in a graph. Add real KPIs. Deploy Work Intelligence Engine.

| Item | Effort | Details |
|------|--------|---------|
| Knowledge Graph population (Neo4j) | 24h | Companies, Employees, Contacts, Meetings, Emails, Tasks, Contracts → nodes + edges |
| Graph query API | 16h | `shortest_path`, `ego_network`, `mutual_connections`, `inactive_companies` |
| Graph visualization (frontend) | 16h | D3/vis.js explorer for Company 360 and Employee 360 |
| Performance KPIs (real-time) | 24h | Revenue, Pipeline, Win Rate, Response Rate, Follow-up Rate, Activities, Productivity |
| **Work Intelligence Engine** | 32h | Time Allocation, Meeting Load, Email Load, Customer Load, Focus Time, Work Balance, Productivity Score, Activity Score |
| KPI Dashboard + Employee 360 integration | 16h | KPI cards, trends, comparisons |
| AI Coach (rule-based MVP) | 16h | "Follow these companies", "Schedule meeting", "Renew contract", "Call customer", "Reply to email" — rule-based suggestions from Activity + Work Intelligence |
| Executive Dashboard MVP (CEO + Manager) | 24h | Revenue, Forecast, Team Performance, Risks, Renewals, Pipeline, Health, Growth |
| Activity Stream Dashboard | 8h | Real-time activity feed for manager |
| **Total** | **176h** | |

**Deliverable:** Everything connected. Knowledge Graph live. KPIs calculated in real time. Work Intelligence drives Employee 360. AI Coach gives actionable suggestions.

**What Muhide sees after Sprint 4:**
- ✅ Knowledge Graph: shortest path, ego network, inactive company detection
- ✅ KPIs: revenue, pipeline, win rate, activities, productivity
- ✅ Work Intelligence: meeting load, email load, focus time, work balance
- ✅ AI Coach: rule-based suggestions
- ✅ Executive Dashboard: revenue, forecast, team performance, risks

---

### Bonus Sprint 5 — AI Copilot (Weeks 17-20)

**Theme:** Real LLM on real data. Natural language queries.

| Item | Effort | Details |
|------|--------|---------|
| LLM abstraction layer | 16h | OpenAI + Anthropic, model switching |
| NL→Query router | 24h | NLP intent → structured query (SQL/Cypher/API) |
| "Show Company 360" | 4h | Route to Company 360 endpoint |
| "Show Employee 360" | 4h | Route to Employee 360 endpoint |
| "Which contracts expire next month?" | 8h | Contract query via NL |
| "How many meetings today?" | 4h | Calendar query |
| "Who owns this account?" | 4h | Account owner lookup |
| "Which companies are inactive?" | 8h | Activity analysis query |
| "Which employee has highest productivity?" | 8h | Work Intelligence query |
| Copilot Chat UI (wire to real backend) | 8h | Connect frontend copilot-panel to real API |
| **Total** | **88h** | |

**Deliverable:** AI Copilot answering real questions over live Muhide data.

---

## PART 3 — TIMELINE COMPARISON

| Approach | Total Time | Cost | Risk |
|----------|-----------|------|------|
| **Original (39 weeks)** | 2,335h | High | Low — but misses market |
| **Revised (16-20 weeks)** | 712h (S1-S4) + 88h (S5) = ~800h | Low | Medium — aggressive but achievable |

**Why the revised plan works:**
1. Everything already exists — just needs wiring
2. Activity Runtime replaces 5+ fragmented systems
3. Data Lake eliminates per-source complexity
4. Work Intelligence Engine leverages data already flowing
5. Sequential dependency removed — parallel teams possible

---

## PART 4 — WHAT GETS BUILT vs WHAT GETS REUSED

| Component | Sprint | Action | Source |
|-----------|--------|--------|--------|
| PostgreSQL for commercial | S1 | Build | New code |
| Contact module | S1 | Build | New code (empty module) |
| Notion import | S1 | Refactor | `import_to_notion.py` → Data Lake |
| Excel import | S1 | Build + UI | Pipeline logic exists, add UI |
| Unified Data Model | S1 | Build | New schema migration |
| Activity Runtime | S2 | **Build** | **New runtime** |
| Timeline Engine | S2 | Reuse | `domains/timeline/` exists |
| Company 360 | S2 | Build | New page + API |
| Employee 360 | S2 | Build | New page + API |
| Search | S2 | Reuse | `runtime/search_runtime/` exists |
| Login/Auth | S2 | Reuse | `app/modules/identity/` exists |
| Workspace | S2 | Reuse | `runtime/ux_runtime/` + frontend workspace exists |
| Gmail Integration | S3 | Build | New module |
| Outlook Integration | S3 | Build | New module |
| Google Calendar | S3 | Build | New module |
| Outlook Calendar | S3 | Build | New module |
| Calendar Intelligence | S3 | Build | New service |
| Email Intelligence | S3 | Build | New service |
| Knowledge Graph | S4 | Reuse + Populate | Neo4j schema exists, add data |
| KPIs | S4 | Build | New calculation engine |
| Work Intelligence Engine | S4 | **Build** | **New engine** |
| AI Coach | S4 | Build | Rule-based (MVP) |
| Executive Dashboard | S4 | Build | New page |
| AI Copilot | S5 | Build | LLM + NL queries |
| Company List UI | S2 | Reuse | Frontend page exists (fix debounce) |
| Employee List UI | S2 | Build | New page |
| Dashboard UI | S4 | Build | New pages |
| Copilot UI | S5 | Reuse | `copilot-panel.tsx` exists (remove mock) |
| Charts | S4 | Refactor | `packages/charts/` exists (upgrade to Recharts) |
| DDD Modules | All | Reuse | Identity, Company, Entity Resolution |
| SDK (25 modules) | All | Reuse | Auth, Audit, Cache, Events, Graph, etc. |
| Runtime (27 packages) | All | Reuse | 21 implemented, 6 planned |
| Frontend Runtime | All | Reuse | 9 runtimes |
| Frontend UI | All | Reuse | 17 components |
| Design System | All | Reuse | 15 token files, Arabic-first |
| Scrapers (5) | S1 | Refactor | Into Data Lake |
| Infrastructure | All | Reuse | Docker, K8s, Terraform |

---

## PART 5 — ARCHITECTURE PRINCIPLES (NEW + EXISTING)

### Activity Runtime (The Spinal Column)

```
┌─────────────────────────────────────────────────────────────┐
│                     ACTIVITY RUNTIME                         │
│                                                              │
│  Every user action → One Activity record → Everything else   │
│                                                              │
│  Activity = {actor, action, entity_type, entity_id,          │
│              target_type, target_id, metadata, timestamp}     │
│                                                              │
│  Sources:                                                    │
│    • SalesOS (internal actions)                              │
│    • Gmail (emails sent/received)                            │
│    • Outlook (emails sent/received)                          │
│    • Google Calendar (meetings created/cancelled)            │
│    • Outlook Calendar (meetings created/cancelled)           │
│    • Notion (imports)                                        │
│    • Excel/CSV (imports)                                     │
│    • Slack (future)                                          │
│    • ERP (future)                                            │
│                                                              │
│  Consumers:                                                  │
│    • Timeline                                                │
│    • Knowledge Graph                                         │
│    • Employee 360                                            │
│    • Company 360                                             │
│    • Work Intelligence                                       │
│    • AI Copilot                                              │
│    • Notifications                                           │
│    • Analytics                                               │
└─────────────────────────────────────────────────────────────┘
```

### Work Intelligence Engine

```
┌─────────────────────────────────────────────────────────────┐
│                   WORK INTELLIGENCE ENGINE                    │
│                                                              │
│  Input: Activity Stream (calendar, email, internal actions)  │
│                                                              │
│  Computers:                                                  │
│    • MeetingLoadComputer    = hours in meetings / day        │
│    • EmailLoadComputer      = emails sent+received / day     │
│    • CustomerLoadComputer   = unique targets / day           │
│    • FocusTimeComputer      = blocks >2h without meetings    │
│    • WorkBalanceComputer    = internal vs external time      │
│    • ProductivityComputer   = meaningful actions / time      │
│    • ActivityScoreComputer  = weighted activity count / day  │
│                                                              │
│  Output: Structured data for Employee 360 KPIs               │
│                                                              │
│  Design: Feature Store pattern (extends existing FS)         │
│  ┌────────────────────────────┐                              │
│  │ feature_store/features/    │                              │
│  │   work_intelligence.py    │  ← NEW file                  │
│  │   icp_computer.py         │  ← Existing                  │
│  │   ...                     │                              │
│  └────────────────────────────┘                              │
└─────────────────────────────────────────────────────────────┘
```

### Data Lake

```
┌─────────────────────────────────────────────────────────────┐
│                       DATA LAKE                              │
│                                                              │
│  ┌──────────────────────────────────────────────────────┐   │
│  │                    Import Layer                        │   │
│  │  ┌────────┐ ┌────────┐ ┌────────┐ ┌────────────────┐ │   │
│  │  │ Notion │ │ Excel  │ │ Gmail  │ │  Calendar      │ │   │
│  │  │ Import │ │ Import │ │ Import │ │  Import        │ │   │
│  │  └────────┘ └────────┘ └────────┘ └────────────────┘ │   │
│  └──────────────────────────────────────────────────────┘   │
│                         │                                    │
│                         ▼                                    │
│  ┌──────────────────────────────────────────────────────┐   │
│  │                 Validation + Mapping                   │   │
│  │  Source schemas → Unified Data Model                  │   │
│  │  Dedup → Entity Resolution → Golden Records           │   │
│  └──────────────────────────────────────────────────────┘   │
│                         │                                    │
│                         ▼                                    │
│  ┌──────────────────────────────────────────────────────┐   │
│  │                   Storage Layer                        │   │
│  │  ┌────────┐ ┌────────┐ ┌────────┐ ┌────────────────┐ │   │
│  │  │Postgres│ │ Neo4j  │ │  Redis │ │  S3 (Files)   │ │   │
│  │  │  (SQL) │ │ (Graph)│ │ (Cache)│ │               │ │   │
│  │  └────────┘ └────────┘ └────────┘ └────────────────┘ │   │
│  └──────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
```

---

## PART 6 — MUHIDE VALUE PER SPRINT

| Sprint | Week | Muhide Gets |
|--------|------|-------------|
| **S1** | 1-3 | All company data in one place. Notion + Excel + CRM unified. No more switching between tools. |
| **S2** | 4-7 | **Company 360** + **Employee 360** MVP. Team can log in, search, see profiles, view timelines. **First usable version of SalesOS.** |
| **S3** | 8-11 | Real email + calendar data inside Employee 360. See meetings, emails, response times. Calendar Intelligence. Email Intelligence. |
| **S4** | 12-16 | **Knowledge Graph** connects everything. **Work Intelligence** shows how team spends time. **AI Coach** gives suggestions. **Executive Dashboard** for leadership. |
| **S5** | 17-20 | **AI Copilot** answers questions in natural language. "Which contracts expire next month?" "Who owns this account?" "How many meetings today?" |

---

## PART 7 — FINAL ARCHITECTURE COMPARISON

| Before | After |
|--------|-------|
| 27 runtimes (good architecture, no product) | 28 runtimes (Activity Runtime added) |
| Fragmented event handling | Unified Activity Stream |
| All data in Excel files | All data in PostgreSQL |
| Employee 360: 3% | Employee 360: 100% |
| Company 360: 10% | Company 360: 100% |
| Knowledge Graph: 15% | Knowledge Graph: 90% |
| AI Copilot: 2% (mock) | AI Copilot: 100% (real LLM) |
| Work Intelligence: 0% | Work Intelligence Engine: 100% |
| Dashboards: 0% | Executive, Manager, Employee Dashboards: 100% |
| Integrations: Notion only | Gmail, Outlook, Google Calendar, Outlook Calendar |
| 39-week roadmap | 16-20 week roadmap |

---

## PART 8 — RISK MITIGATION

| Risk | Mitigation |
|------|------------|
| Gmail/Outlook API OAuth complexity | Start with service account + domain-wide delegation for Muhide |
| Activity Runtime scope creep | Minimum schema: actor, action, entity, target, timestamp. Extend later. |
| Neo4j population performance | Batch Cypher queries, use UNWIND + MERGE patterns |
| Frontend effort (many new pages) | Reuse SchemaRenderer + Workspace patterns — pages are generated, not built |
| Data quality from scrapers | Data Lake validation layer + quality scoring |
| Team capacity | Parallelize: Backend (S1) + Architecture (S2 runtime design) + Frontend (S2 UI) |
| LLM cost for AI Copilot | Start with gpt-4o-mini, cache responses, limit context window |

---

## PART 9 — EXECUTIVE SUMMARY

> **The original 39-week plan assumed building from scratch.**
>
> **The revised 16-week plan recognizes that everything already exists.**
>
> The DDD modules are ready.
> The runtimes are ready.
> The SDK is ready.
> The design system is ready.
> The scrapers are ready.
> The frontend architecture is ready.
>
> **What's needed is not construction — it's connection.**
>
> Connect the scrapers to PostgreSQL.
> Connect the events to the Activity Runtime.
> Connect the Activity Runtime to Employee 360 and Company 360.
> Connect Gmail and Calendar to the Activity Runtime.
> Connect the Knowledge Graph to the data.
>
> **SalesOS is not 12% built.**
> **SalesOS is 80% built and 20% unwired.**

---

*Revised Roadmap — July 2, 2026*
*Muhide Internal — Confidential*
