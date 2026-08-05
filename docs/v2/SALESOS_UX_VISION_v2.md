# SalesOS UX Vision v2.0

> **Status:** Living Document — Pre-Implementation Design Strategy  
> **Author:** Design Architecture Review  
> **Date:** 2026-08-05  
> **Supersedes:** Current ad-hoc UI patterns  
> **Scope:** Full SalesOS frontend evolution  

---

## Table of Contents

1. [Product Philosophy](#1-product-philosophy)
2. [Workspace Architecture](#2-workspace-architecture)
3. [Navigation Architecture](#3-navigation-architecture)
4. [Information Architecture](#4-information-architecture)
5. [Enterprise Design Language](#5-enterprise-design-language)
6. [Executive Dashboard Vision](#6-executive-dashboard-vision)
7. [Company 360 Vision](#7-company-360-vision)
8. [Employee 360 Vision](#8-employee-360-vision)
9. [AI Everywhere Strategy](#9-ai-everywhere-strategy)
10. [Design System v2](#10-design-system-v2)
11. [Motion & Interaction Guidelines](#11-motion--interaction-guidelines)
12. [Responsive Strategy](#12-responsive-strategy)
13. [Accessibility Standards](#13-accessibility-standards)
14. [Implementation Roadmap](#14-implementation-roadmap)

---

## 1. Product Philosophy

### 1.1 Core Belief

SalesOS exists to transform scattered data into decisive action. Every screen must answer one question: **"What should I do next?"**

### 1.2 Design Principles

| # | Principle | Meaning | Anti-Pattern |
|---|-----------|---------|--------------|
| 1 | **Clarity Over Cleverness** | Show the answer, not the data that leads to the answer | Raw tables without narrative |
| 2 | **Progressive Disclosure** | Show 20% of information that drives 80% of decisions | 38-item flat sidebar |
| 3 | **Context Over Navigation** | Bring information to the user, don't make the user find information | Requiring 5 clicks to reach Company 360 |
| 4 | **Confidence Through Evidence** | Every AI recommendation shows its reasoning | Black-box AI outputs |
| 5 | **Respect the Role** | A CEO sees different things than an SDR | One-size-fits-all dashboard |
| 6 | **Bilingual by Default** | Arabic is not an afterthought — it is co-equal | RTL as a CSS hack |
| 7 | **Enterprise Trust** | The interface must feel like it handles millions, not thousands | Consumer-grade UI patterns |

### 1.3 Product Personality

SalesOS should feel like:

- **Stripe's precision** — every pixel is intentional
- **Linear's speed** — keyboard-first, instant feedback
- **Notion's calm** — information density without visual noise
- **Salesforce's authority** — enterprise-grade, trustworthy
- **Apple's restraint** — only what is needed, nothing more

### 1.4 What SalesOS Is NOT

- Not a chatbot with a dashboard attached
- Not a data warehouse with a UI skin
- Not a collection of isolated feature pages
- Not a consumer app dressed as enterprise software

SalesOS is an **intelligence platform** where AI assists human decision-making across the entire sales lifecycle.

---

## 2. Workspace Architecture

### 2.1 The Workspace Concept

SalesOS is not one application. It is a **platform** with multiple **workspaces**, each optimized for a specific user role and workflow.

```
┌─────────────────────────────────────────────────┐
│                  SalesOS Platform                │
├─────────────┬─────────────┬─────────────────────┤
│  Sales      │  Executive  │  Intelligence       │
│  Workspace  │  Workspace  │  Workspace          │
├─────────────┼─────────────┼─────────────────────┤
│  GTM        │  Studio     │  Admin              │
│  Workspace  │  Workspace  │  Workspace          │
└─────────────┴─────────────┴─────────────────────┘
```

### 2.2 Workspace Definitions

#### Sales Workspace (Default)
**Audience:** Sales reps, account executives, BDRs  
**Primary view:** Pipeline + Activities + Company/Contact lists  
**Key action:** "Close the next deal"

```
Default landing: /dashboard (My Day view)
Core modules: Companies, Contacts, Opportunities, Activities, Pipeline
Sidebar: 8 items max
```

#### Executive Workspace
**Audience:** CEOs, VPs, Sales Directors  
**Primary view:** Revenue dashboard + Team performance + Forecast  
**Key action:** "Understand the business health"

```
Default landing: /dashboard (Executive Brief)
Core modules: Revenue, Forecast, Analytics, Team, Monitor
Sidebar: 6 items max
```

#### Intelligence Workspace
**Audience:** Analysts, RevOps, Data teams  
**Primary view:** Decisions + Signals + Graph + Knowledge  
**Key action:** "Surface hidden patterns"

```
Default landing: /dashboard (Intelligence Hub)
Core modules: Decisions, Signals, Graph, Knowledge, Analytics
Sidebar: 7 items max
```

#### GTM Workspace
**Audience:** Growth marketers, Demand gen  
**Primary view:** ICP + Lead discovery + Outreach  
**Key action:** "Find and engage the right prospects"

```
Default landing: /gtm
Core modules: ICP, Market Sizing, Lead Discovery, Enrichment, Outreach, Sequences
Sidebar: 8 items max
```

#### Studio Workspace
**Audience:** Admins, Revenue ops  
**Primary view:** Configuration + Customization  
**Key action:** "Configure the platform"

```
Default landing: /studio
Core modules: Custom Fields, Scoring, Permissions, Workflows, Notifications, Branding, Territories, AI Config
Sidebar: 9 items max
```

#### Admin Workspace
**Audience:** Platform admins, IT  
**Primary view:** Users, billing, security  
**Key action:** "Manage the platform"

```
Default landing: /admin
Core modules: Users, Billing, Security, Integrations, Audit Log
Sidebar: 5 items max
```

### 2.3 Workspace Switching

- Workspace selector lives in the **top-left** of the header, next to the brand mark
- Switching workspace reconfigures the sidebar, dashboard, and available actions
- User's default workspace is set by admin based on role
- Users can pin a secondary workspace for quick switching (Cmd+Shift+1/2)

### 2.4 Why This Matters

The current 38-item sidebar exists because every feature was treated as equal. In reality:

- A sales rep never needs to see "AI Model Tiers"
- An executive never needs to see "Custom Fields"
- A GTM user never needs to see "Permissions"

**Workspace architecture eliminates 60-70% of navigation noise by role.**

---

## 3. Navigation Architecture

### 3.1 Current Problem

The sidebar (`NAV_KEYS` in `layout.tsx`) contains 38 items in a flat list. This is:
- Impossible to scan
- Impossible to memorize
- Impossible to navigate on mobile
- hostile to new users

### 3.2 Proposed Navigation Model

```
┌──────────────────────────────────────┐
│  [Brand]  [Workspace Selector ▾]     │
├──────────────────────────────────────┤
│  🔍 Search everything...     ⌘K     │
├──────────────────────────────────────┤
│  ⭐ Pinned                          │
│    └─ [User's 3 pinned modules]     │
├──────────────────────────────────────┤
│  📊 Core                            │
│    ├─ Dashboard                     │
│    ├─ Companies                     │
│    ├─ Employees                     │
│    ├─ Contacts                      │
│    └─ Opportunities                 │
├──────────────────────────────────────┤
│  📈 Intelligence                    │
│    ├─ Decisions                     │
│    ├─ Signals                       │
│    ├─ Analytics                     │
│    └─ Graph                         │
├──────────────────────────────────────┤
│  ⚙️ Quick Access                    │
│    ├─ Settings                      │
│    └─ Help                          │
└──────────────────────────────────────┘
```

### 3.3 Navigation Rules

| Rule | Implementation |
|------|---------------|
| Max 8 visible items in default group | Additional items in collapsible sections |
| Pinned items always visible | User can pin up to 3 modules from any workspace |
| Search is universal | Cmd+K searches across all modules, entities, actions |
| Active section is visually distinct | Left border pill + background tint + bold text |
| Collapse preserves context | Collapsed sidebar shows icons only, tooltips on hover |
| Mobile uses bottom tab bar | 5 primary tabs + "More" overflow |

### 3.4 Command Palette (Cmd+K)

The command palette is the **primary navigation tool** for power users:

```
┌─────────────────────────────────────────┐
│  🔍 Type a command or search...         │
├─────────────────────────────────────────┤
│  Recent                                │
│    ├─ Aramco → Company 360              │
│    ├─ Mohammed Ali → Employee Profile   │
│    └─ Deal #4521 → Opportunity          │
├─────────────────────────────────────────┤
│  Quick Actions                          │
│    ├─ Create Company                    │
│    ├─ Add Contact                       │
│    ├─ New Opportunity                   │
│    └─ Log Activity                      │
├─────────────────────────────────────────┤
│  Navigate                               │
│    ├─ /dashboard                        │
│    ├─ /companies                        │
│    ├─ /pipeline                         │
│    └─ /decisions                        │
└─────────────────────────────────────────┘
```

### 3.5 Breadcrumb Strategy

Every page deeper than level 2 gets breadcrumbs:

| Depth | Example | Breadcrumbs |
|-------|---------|-------------|
| 1 | /companies | None needed |
| 2 | /companies/acme-corp | Companies > Acme Corp |
| 3 | /companies/acme-corp/360 | Companies > Acme Corp > 360 |
| 3 | /employees/emp-123/performance | Employees > [Name] > Performance |

Breadcrumbs use the existing `<Breadcrumbs>` component from `@salesos/ui`, extended with entity icons and status badges.

---

## 4. Information Architecture

### 4.1 Entity Relationship Model

```
Platform
├── Tenant (multi-tenant isolation)
│   ├── Users (employees with roles)
│   ├── Companies (organizations)
│   │   ├── Contacts (people at companies)
│   │   ├── Opportunities (deals)
│   │   │   └── Activities (interactions)
│   │   ├── Contracts (signed agreements)
│   │   ├── Documents (files, emails)
│   │   └── Signals (intelligence events)
│   ├── Employees (internal team)
│   │   ├── Performance scores
│   │   ├── Signal contributions
│   │   └── Activity history
│   ├── Knowledge (company knowledge base)
│   ├── Decisions (AI-generated recommendations)
│   ├── Graph (relationship map)
│   └── GTM (go-to-market configuration)
│       ├── ICP Profiles
│       ├── Market Sizing
│       ├── Lead Discovery
│       └── Sequences
```

### 4.2 Page Hierarchy

```
Level 0: / (login, redirect)
Level 1: /dashboard, /companies, /employees, /opportunities, etc.
Level 2: /companies/acme-corp, /employees/emp-123
Level 3: /companies/acme-corp/360, /employees/emp-123/performance
Level 4: /companies/acme-corp/360?tab=financial (tab state, not URL)
```

**Rule:** No page should require more than 3 clicks from the dashboard. If it does, the information architecture is wrong.

### 4.3 Cross-Entity Navigation

Users frequently need to jump between related entities:

- Company → Contacts (tab within Company page)
- Company → Opportunities (related deals)
- Employee → Activities (their activity log)
- Opportunity → Company (parent entity)
- Decision → Company/Employee (subject entity)

**Implementation:** Every entity card/row shows a mini-relation map:
```
[Company: Acme Corp]
  → 12 Contacts
  → 3 Active Opportunities
  → 2 Assigned Employees
  → 8 Signals
```

---

## 5. Enterprise Design Language

### 5.1 Color Philosophy

The warm neutral palette is a **strength**. It differentiates SalesOS from the sea of blue-gray SaaS. Do not abandon it.

**Brand Colors (Preserve):**
| Token | Value | Use |
|-------|-------|-----|
| `--muhide-orange` | `#F57C1E` | Primary actions, brand identity, active states |
| `--muhide-ink` | `#151214` | Dark mode background, strong text |
| `--muhide-espresso` | `#403D38` | Secondary dark elements |
| `--muhide-sand` | `#CCC6BA` | Subtle borders, disabled states |
| `--muhide-paper` | `#FAFAFA` | Light backgrounds |

**Semantic Colors (Standardize):**
| Token | Light | Dark | Use |
|-------|-------|------|-----|
| `--status-success` | `#22C55E` | `#34D399` | Won, active, healthy, positive |
| `--status-danger` | `#EF4444` | `#F87171` | Lost, critical, error, negative |
| `--status-warning` | `#F59E0B` | `#FBBF24` | At risk, pending, caution |
| `--status-info` | `#3B82F6` | `#60A5FA` | Neutral info, links, progress |
| `--status-purple` | `#8B5CF6` | `#A78BFA` | AI, intelligence, premium features |

**Extended Palette (New):**
| Token | Value | Use |
|-------|-------|-----|
| `--surface-elevated` | `rgba(255,255,255,0.8)` | Glass morphism panels |
| `--surface-overlay` | `rgba(21,18,20,0.5)` | Modal backdrops |
| `--border-focus` | `#F57C1E` | Focus rings (use brand, not blue) |
| `--border-subtle` | `rgba(21,18,20,0.06)` | Very light dividers |

### 5.2 Typography System

**Type Scale:**
| Name | Size | Weight | Line Height | Use |
|------|------|--------|-------------|-----|
| `display-lg` | 40px | 700 | 1.1 | Hero KPI numbers |
| `display` | 32px | 700 | 1.15 | Page titles |
| `heading-1` | 24px | 700 | 1.2 | Section headers |
| `heading-2` | 20px | 600 | 1.3 | Card titles |
| `heading-3` | 16px | 600 | 1.4 | Subsection headers |
| `body-lg` | 14px | 400 | 1.6 | Primary body text |
| `body` | 14px | 400 | 1.5 | Default body text |
| `body-sm` | 12px | 400 | 1.4 | Secondary text, captions |
| `caption` | 11px | 500 | 1.4 | Labels, badges, metadata |
| `overline` | 10px | 600 | 1.3 | Category labels, uppercase |

**Font Stack (Preserve):**
- Display: Viga
- Body: IBM Plex Sans (400, 500, 600, 700)
- Arabic: IBM Plex Sans Arabic (400, 500, 600, 700)
- Code: IBM Plex Mono (400, 500, 600)

### 5.3 Spacing System

Use a 4px base unit. All spacing must be a multiple of 4.

| Token | Value | Use |
|-------|-------|-----|
| `space-0` | 0 | — |
| `space-1` | 4px | Tight gaps (icon-to-text) |
| `space-2` | 8px | Compact gaps (badge padding) |
| `space-3` | 12px | Default gaps (list item spacing) |
| `space-4` | 16px | Standard padding (card internal) |
| `space-5` | 20px | Section gaps |
| `space-6` | 24px | Page padding, card padding |
| `space-8` | 32px | Major section separation |
| `space-10` | 40px | Page-level spacing |
| `space-12` | 48px | Hero spacing |
| `space-16` | 64px | Maximum spacing |

### 5.4 Elevation System

| Level | Shadow | Use |
|-------|--------|-----|
| `elevation-0` | None | Flat surfaces, backgrounds |
| `elevation-1` | `0 1px 2px rgba(21,18,20,0.06)` | Cards, containers |
| `elevation-2` | `0 1px 3px rgba(21,18,20,0.08), 0 1px 2px rgba(21,18,20,0.04)` | Dropdowns, popovers |
| `elevation-3` | `0 4px 6px rgba(21,18,20,0.07), 0 2px 4px rgba(21,18,20,0.04)` | Sticky headers, floating elements |
| `elevation-4` | `0 10px 15px rgba(21,18,20,0.08), 0 4px 6px rgba(21,18,20,0.04)` | Modals, drawers |
| `elevation-5` | `0 20px 25px rgba(21,18,20,0.10), 0 8px 10px rgba(21,18,20,0.05)` | Command palette, toast |
| `elevation-6` | `0 25px 50px rgba(21,18,20,0.16)` | Full-screen overlays |

### 5.5 Border Radius System

| Token | Value | Use |
|-------|-------|-----|
| `radius-sm` | 2px | Inline elements, badges |
| `radius-md` | 6px | Buttons, inputs |
| `radius-lg` | 8px | Cards, dropdowns |
| `radius-xl` | 12px | Modals, panels |
| `radius-2xl` | 16px | Feature cards, hero elements |
| `radius-full` | 9999px | Pills, avatars, circular elements |

### 5.6 Icon Guidelines

| Size | Pixels | Use |
|------|--------|-----|
| `icon-sm` | 14px | Inline with text, badges |
| `icon-md` | 16px | Default for buttons, nav items |
| `icon-lg` | 20px | Section headers, card headers |
| `icon-xl` | 24px | Page headers, feature icons |
| `icon-2xl` | 32px | Empty states, hero illustrations |

**Icon library:** Lucide (already in use). Never mix icon libraries.

---

## 6. Executive Dashboard Vision

### 6.1 Current State

The dashboard is a widget registry (`widget-registry.tsx`) that renders a grid of cards. There is no narrative, no priority ordering, no "what matters today" view.

The `ExecutiveDashboard` component (`executive-dashboard.tsx`) exists separately with KPI cards, pipeline health, and growth metrics — but is not the default dashboard.

### 6.2 Vision: The Morning Brief

The executive dashboard should feel like a **morning briefing from a trusted advisor**, not a database query result.

```
┌─────────────────────────────────────────────────────────┐
│  Good morning, [Name]. Tuesday, Aug 5                   │
│                                                         │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐   │
│  │ Revenue  │ │ Pipeline │ │ Active   │ │ Team     │   │
│  │ $2.4M    │ │ $8.7M    │ │ 47       │ │ 12/15    │   │
│  │ ↑ 12%    │ │ ↑ 8%     │ │ deals    │ │ online   │   │
│  │ vs last  │ │ vs last  │ │          │ │          │   │
│  │ quarter  │ │ month    │ │          │ │          │   │
│  └──────────┘ └──────────┘ └──────────┘ └──────────┘   │
│                                                         │
│  ⚡ Today's Priorities                                   │
│  ┌─────────────────────────────────────────────────┐    │
│  │ 🔴 3 deals at risk of stalling                   │    │
│  │    → Acme Corp ($450K) — no activity in 14 days │    │
│  │    → STC ($280K) — competitor engaged            │    │
│  │    → SABIC ($190K) — decision maker changed      │    │
│  │                                                  │    │
│  │ 🟡 2 renewals due this month                     │    │
│  │    → Aramco ($1.2M) — renewal in 18 days         │    │
│  │    → Ma'aden ($340K) — renewal in 25 days        │    │
│  │                                                  │    │
│  │ 🟢 5 new opportunities from lead discovery       │    │
│  │    → Total pipeline value: $1.8M                 │    │
│  └─────────────────────────────────────────────────┘    │
│                                                         │
│  📊 Pipeline Health          📈 Revenue Trend            │
│  ┌────────────────────┐     ┌────────────────────┐     │
│  │ [Stage bars]        │     │ [Sparkline chart]   │     │
│  │ Prospecting: 12     │     │                      │     │
│  │ Qualification: 8    │     │   ╱╲  ╱╲            │     │
│  │ Proposal: 5         │     │  ╱  ╲╱  ╲╱╲         │     │
│  │ Negotiation: 3      │     │ ╱            ╲       │     │
│  │ Closed Won: 7       │     │                      │     │
│  └────────────────────┘     └────────────────────┘     │
│                                                         │
│  🏆 Team Performance     🔮 Forecast                    │
│  ┌────────────────────┐  ┌────────────────────┐        │
│  │ [Leaderboard]       │  │ [Scenario cards]    │        │
│  │ 1. Ahmed  $890K     │  │ Conservative: $2.1M │        │
│  │ 2. Noura  $650K     │  │ Baseline:    $3.4M │        │
│  │ 3. Fahad  $420K     │  │ Optimistic:  $4.2M │        │
│  └────────────────────┘  └────────────────────┘        │
└─────────────────────────────────────────────────────────┘
```

### 6.3 Dashboard Components

| Component | Source | Purpose |
|-----------|--------|---------|
| `MorningBriefHeader` | New | Greeting + date + user context |
| `KPISummaryBar` | Adapted from `ExecutiveDashboard` | 4 key metrics with trends |
| `TodaysPriorities` | New — powered by Decision Center | Top 3-5 actions requiring attention |
| `PipelineHealthChart` | Adapted from `ExecutiveDashboard` | Stage breakdown with visual bars |
| `RevenueTrendSparkline` | New | 12-month trend line |
| `TeamPerformanceLeaderboard` | Adapted from `ExecutiveDashboard` | Top reps by revenue |
| `ForecastScenarioCards` | Adapted from `forecast/page.tsx` | Pessimistic/Baseline/Optimistic |
| `RecentActivityFeed` | Adapted from `TimelineWidget` | Latest team activities |

### 6.4 Dashboard Personalization

Users can:
- Reorder widgets via drag-and-drop
- Hide widgets they don't need
- Switch between "Brief" (narrative) and "Data" (widget grid) views
- Set a default view per workspace

### 6.5 Dashboard Refresh Strategy

- KPI metrics: Real-time via WebSocket or 30-second polling
- Charts: Refresh on page load + manual refresh button
- Priorities: Refresh every 5 minutes (Decision Center recomputation)
- Activity feed: Real-time via WebSocket

---

## 7. Company 360 Vision

### 7.1 Current State

Company 360 (`companies/[id]/360/page.tsx`) has 5 tabs (Overview, Hierarchy, Financial, Activity, Insights) with a health score ring. The Overview and Insights tabs show identical content.

### 7.2 Vision: The Single Pane of Glass

Company 360 should be the **one screen** where everything about a company is visible, actionable, and connected.

```
┌─────────────────────────────────────────────────────────┐
│  [← Back]  Companies > Acme Corp > 360                  │
│                                                         │
│  ┌───────────────────────────────────────────────────┐  │
│  │ 🏢 Acme Corp                    [Health: 78/100]  │  │
│  │ CR: 1010123456 | Riyadh | Active                  │  │
│  │                                                    │  │
│  │ [Overview] [People] [Deal Room] [Intelligence]     │  │
│  │ [Activity] [Documents] [Graph] [AI Insights]       │  │
│  └───────────────────────────────────────────────────┘  │
│                                                         │
│  OVERVIEW TAB:                                          │
│  ┌─────────────────┐ ┌───────────────────────────────┐ │
│  │ Company DNA      │ │ Relationship Graph            │ │
│  │                  │ │                               │ │
│  │ Industry: Tech   │ │    [Acme]──[Contact A]       │ │
│  │ Size: 500-1000   │ │      │         │             │ │
│  │ Revenue: $50M    │ │  [Employee]──[Opp 1]         │ │
│  │ Founded: 2010    │ │                               │ │
│  │                  │ │  [Click to expand]            │ │
│  └─────────────────┘ └───────────────────────────────┘ │
│                                                         │
│  ┌─────────────────┐ ┌───────────────────────────────┐ │
│  │ AI Recommendation│ │ Buying Journey                │ │
│  │                  │ │                               │ │
│  │ "Schedule a     │ │ Awareness → Consideration →   │ │
│  │  meeting with    │ │ Evaluation → Decision         │ │
│  │  the CFO before  │ │                    ▲          │ │
│  │  Q4 budget cycle"│ │               [Current]       │ │
│  │                  │ │                               │ │
│  │ [Act on this]    │ │ Next: Decision meeting        │ │
│  └─────────────────┘ └───────────────────────────────┘ │
│                                                         │
│  ┌───────────────────────────────────────────────────┐  │
│  │ ⚡ Quick Actions                                   │  │
│  │ [📞 Call] [📧 Email] [📅 Meeting] [📝 Note]       │  │
│  │ [➕ Contact] [📊 Opportunity] [📄 Document]       │  │
│  └───────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────┘
```

### 7.3 Tab Differentiation

| Tab | Content | Key Difference from Current |
|-----|---------|----------------------------|
| **Overview** | Company DNA, AI Recommendation, Buying Journey, Relationship Graph summary | Remove duplicate from Insights |
| **People** | Contacts list, Decision Makers, Org chart, Assigned employees | Merge current Contacts + Hierarchy tabs |
| **Deal Room** | Active opportunities, Contracts, Revenue history, Financial summary | Merge current Financial + Opportunity views |
| **Intelligence** | Signals feed, Smart Timeline, Market signals, Competitor intelligence | Unique signal-driven view |
| **Activity** | Full activity timeline, Email history, Meeting logs, Call records | Dedicated timeline (no other content) |
| **Documents** | Document intelligence, Uploaded files, Contract excerpts | Dedicated document view |
| **Graph** | Full knowledge graph centered on this company | Expanded from current mini-graph |
| **AI Insights** | AI-generated analysis, Trend predictions, Recommendations, Risk alerts | Distinct from Overview's summary |

### 7.4 Company 360 Interaction Patterns

- **Health score ring:** Click to see breakdown (factors, weights, history)
- **AI Recommendation:** Click "Act on this" to create activity/opportunity
- **Buying Journey:** Visual progress bar with stage-specific actions
- **Relationship Graph:** Click nodes to expand, double-click to navigate
- **Quick Actions:** Always visible at top, context-aware (show relevant actions based on company state)

### 7.5 Company 360 Data Density

The page should show **at a glance:**
- Company health score (1 number)
- Revenue and deal status (2-3 numbers)
- Next recommended action (1 sentence)
- Current stage in buying journey (1 visual)
- Recent activity (last 3 items)
- Key relationships (mini graph)

**On demand (click to expand):**
- Full financial history
- Complete activity timeline
- All contacts and org chart
- Full knowledge graph
- AI analysis and predictions

---

## 8. Employee 360 Vision

### 8.1 Current State

Employee 360 (`employee-360-page.tsx`) has lazy-loaded tabs (Overview, Signals, Scoring, Timeline, Performance). The employee list page is 1122 lines with inline detail panels.

### 8.2 Vision: The Performance Cockpit

Employee 360 should help managers understand **who is performing, who needs help, and where to invest coaching time.**

```
┌─────────────────────────────────────────────────────────┐
│  Employees > Ahmed Al-Sudairi                           │
│                                                         │
│  ┌───────────────────────────────────────────────────┐  │
│  │ 👤 Ahmed Al-Sudairi           Score: 82/100 ↑+5  │  │
│  │ Senior Account Executive | Enterprise Team         │  │
│  │ ahmed@company.com | Riyadh                        │  │
│  │                                                    │  │
│  │ [Overview] [Performance] [Signals] [Activity]      │  │
│  │ [Scoring] [Team Context]                           │  │
│  └───────────────────────────────────────────────────┘  │
│                                                         │
│  OVERVIEW:                                              │
│  ┌──────────────┐ ┌──────────────┐ ┌──────────────┐    │
│  │ Score Trend   │ │ Activity     │ │ Pipeline     │    │
│  │ [Sparkline]   │ │ Summary      │ │ Contribution │    │
│  │ 82 ↑ +5      │ │ 24 activities│ │ $1.2M        │    │
│  │ this month    │ │ this month   │ │ 3 deals      │    │
│  └──────────────┘ └──────────────┘ └──────────────┘    │
│                                                         │
│  ┌─────────────────────────────────────────────────┐    │
│  │ 🧠 AI Insight                                    │    │
│  │ "Ahmed's engagement with Acme Corp has dropped   │    │
│  │  40% in the past 2 weeks. Consider a coaching    │    │
│  │  conversation about deal strategy."              │    │
│  │  [Schedule Coaching] [View Deal]                 │    │
│  └─────────────────────────────────────────────────┘    │
│                                                         │
│  ┌──────────────────────┐ ┌──────────────────────┐     │
│  │ Signal Breakdown      │ │ Recent Activities     │     │
│  │ ┌────┬────┬────┐     │ │ ┌────┬────┬────┐      │     │
│  │ │📧  │📞  │📅  │     │ │ │Last│Last│Last│      │     │
│  │ │ 12 │ 8  │ 5  │     │ │ │email│call│mtg│      │     │
│  │ └────┴────┴────┘     │ │ └────┴────┴────┘      │     │
│  └──────────────────────┘ └──────────────────────┘     │
└─────────────────────────────────────────────────────────┘
```

### 8.3 Employee 360 Tab Differentiation

| Tab | Content |
|-----|---------|
| **Overview** | Score summary, AI insight, Activity summary, Signal breakdown |
| **Performance** | Score trend chart, Quota attainment, Deal progression, Goal tracking |
| **Signals** | Full signal list with type/source/trend breakdown, Signal history |
| **Activity** | Complete activity timeline, Activity heat map, Communication patterns |
| **Scoring** | Score breakdown by factor, Confidence level, Score history, Benchmark comparison |
| **Team Context** | How this employee compares to team average, Top performers, Coaching opportunities |

### 8.4 Employee List Improvements

The 1122-line employee list page needs:
- **Decomposition** into smaller components (list, filters, detail panel, score panel)
- **Card view toggle** (table vs. card grid)
- **Bulk actions toolbar** that appears on selection (not always visible)
- **Quick filters** at top (Department, Role, Score range, Activity level)
- **Export** should use the `<Button>` component, not inline styles

---

## 9. AI Everywhere Strategy

### 9.1 Current State

AI is behind a feature flag (`feature_aiCopilot`). The AI page is a developer prompt editor. The Copilot panel exists but is gated. The `ExperimentalAiBadge` honestly signals "not production."

### 9.2 Vision: AI as Ambient Intelligence

AI should not be a separate page. It should be **woven into every workflow** as ambient intelligence that appears when relevant.

### 9.3 AI Touchpoints

| Touchpoint | AI Behavior | UI Pattern |
|------------|-------------|------------|
| **Dashboard** | Morning brief with priorities | AI-curated "Today's Priorities" section |
| **Company List** | Anomaly detection on company health | Subtle badge on at-risk companies |
| **Company 360** | Recommendation engine | "Next Best Action" card with reasoning |
| **Employee List** | Performance prediction | Score trend indicator with forecast |
| **Employee 360** | Coaching suggestions | Contextual AI insight card |
| **Pipeline** | Deal risk scoring | Risk badge on opportunity cards |
| **Decisions** | Audit trail with confidence | Confidence gauge + factor breakdown |
| **Graph** | Relationship discovery | "You might also know..." suggestions |
| **Search** | Natural language queries | "Ask in plain English" input |
| **Global** | Copilot sidebar | Floating AI assistant panel |

### 9.4 AI UI Principles

1. **Always show reasoning.** Never present an AI output without explaining why.
2. **Always show confidence.** Use the confidence gauge (percentage + color).
3. **Always allow rejection.** Every AI suggestion has a "Dismiss" action.
4. **Always label as AI.** Use the `ExperimentalAiBadge` or a subtle "AI" chip.
5. **Never auto-execute.** AI recommends, human decides.

### 9.5 Copilot Sidebar Design

```
┌──────────────────────────────┐
│  🤖 SalesOS Copilot    [×]  │
├──────────────────────────────┤
│                              │
│  Ask me anything about your  │
│  sales data...               │
│                              │
│  ┌────────────────────────┐  │
│  │ [Text input]     [Send]│  │
│  └────────────────────────┘  │
│                              │
│  Suggested:                  │
│  • "What deals are at risk?" │
│  • "Summarize Acme Corp"     │
│  • "Who should I call today?"│
│  • "Show revenue trend"      │
│                              │
│  ─────────────────────────── │
│                              │
│  Context: Company 360        │
│  Entity: Acme Corp           │
│                              │
│  [Previous conversations]    │
│                              │
└──────────────────────────────┘
```

### 9.6 AI Honesty Standards

| Label | Meaning | When to Use |
|-------|---------|-------------|
| `AI Insight` | Generated by AI, high confidence | Score > 80%, multiple data sources |
| `AI Suggestion` | Generated by AI, medium confidence | Score 50-80%, limited data |
| `AI Draft` | Generated by AI, needs review | Text generation, recommendations |
| `Experimental` | Feature not yet validated | New AI capabilities |

---

## 10. Design System v2

### 10.1 Current State

- `@salesos/design-system`: 4 color tokens, 10 spacing values, 3 motion values (alpha stubs)
- `@salesos/tokens`: Empty package (placeholder)
- `@salesos/ui`: 30+ components (functional but inconsistent)
- Actual design system: Scattered across `tailwind.config.ts`, `globals.css`, inline classes

### 10.2 Architecture

```
@salesos/tokens (Single Source of Truth)
├── colors.ts      (brand, semantic, status, chart)
├── typography.ts  (scale, families, weights)
├── spacing.ts     (4px base scale)
├── elevation.ts   (shadow levels)
├── motion.ts      (durations, easings)
├── radius.ts      (border radius scale)
├── z-index.ts     (layering system)
└── index.ts       (barrel export)

@salesos/design-system
├── tokens/        (re-exports from @salesos/tokens)
├── components/    (React component library)
│   ├── primitives/    (Button, Input, Badge, Card, etc.)
│   ├── composite/     (DataTable, CommandPalette, etc.)
│   └── layout/        (AppShell, PageHeader, Sidebar, etc.)
├── patterns/      (common UI patterns)
│   ├── empty-state/
│   ├── loading/
│   ├── error/
│   └── data-display/
└── guidelines/    (usage documentation)

@salesos/ui (Consumers import from here)
└── Re-exports from @salesos/design-system
```

### 10.3 Component Inventory

#### Primitives (Build First)

| Component | Current | Action |
|-----------|---------|--------|
| Button | ✅ Exists | Standardize, add icon-only variant |
| Input | ✅ Exists | Add textarea integration |
| Badge | ✅ Exists | Add `info` variant, icon support |
| Card | ⚠️ 3 versions | Unify into single component |
| Tabs | ✅ Exists | Add vertical variant, icon tabs |
| Modal | ✅ Exists | Add size variants (sm/md/lg/full) |
| Select | ✅ Exists | Add multi-select, async search |
| Checkbox | ✅ Exists | Verify consistency |
| Radio | ✅ Exists | Verify consistency |
| Switch | ✅ Exists | Verify consistency |
| Tooltip | ✅ Exists | Verify consistency |
| Skeleton | ✅ Exists | Add more shape variants |
| Spinner | ✅ Exists | Verify consistency |

#### Composites (Build Second)

| Component | Current | Action |
|-----------|---------|--------|
| DataTable | ✅ Exists | Add density toggle, column resize |
| CommandPalette | ⚠️ Partial | Full rebuild with sections, recents |
| DatePicker | ✅ Exists | Add range picker |
| Toast | ✅ Exists | Verify consistency |
| Breadcrumbs | ✅ Exists | Add entity icons |
| EmptyState | ✅ Exists | Add illustration variants |
| Pagination | ✅ Exists | Add infinite scroll option |

#### Layout (Build Third)

| Component | Current | Action |
|-----------|---------|--------|
| AppShell | ✅ Exists | Add workspace switching |
| PageHeader | ❌ Missing | Build: title + description + actions |
| SectionHeader | ❌ Missing | Build: title + count + expand |
| Sidebar | ⚠️ Inline | Extract from layout.tsx |
| MetricCard | ❌ Missing | Build: value + trend + sparkline |
| StatCard | ❌ Missing | Build: label + value + icon |
| KPIBar | ❌ Missing | Build: horizontal metric strip |

### 10.4 Token Migration Strategy

1. **Phase 1:** Create `@salesos/tokens` with all tokens defined
2. **Phase 2:** Update `tailwind.config.ts` to consume from `@salesos/tokens`
3. **Phase 3:** Update `globals.css` CSS vars to consume from `@salesos/tokens`
4. **Phase 4:** Update `@salesos/ui` components to use token imports
5. **Phase 5:** Remove inline color/spacing values from page components

**Rule:** After Phase 5, no component or page should contain raw hex values, raw pixel values, or raw shadow definitions. Everything comes from tokens.

---

## 11. Motion & Interaction Guidelines

### 11.1 Motion Philosophy

Motion in SalesOS serves three purposes:
1. **Orient** — help users understand where they are and what changed
2. **Feedback** — confirm that an action was received
3. **Delight** — make the product feel alive without being distracting

### 11.2 Duration Scale

| Token | Duration | Use |
|-------|----------|-----|
| `instant` | 0ms | State changes that should feel immediate |
| `fast` | 120ms | Hover states, focus rings, small toggles |
| `normal` | 200ms | Panel transitions, dropdown open/close, tab switches |
| `slow` | 300ms | Modal open/close, page transitions, sidebar collapse |
| `slower` | 500ms | Complex animations, chart transitions |

### 11.3 Easing Curves

| Token | Curve | Use |
|-------|-------|-----|
| `ease-standard` | `cubic-bezier(0.2, 0, 0, 1)` | Default for most transitions |
| `ease-decelerate` | `cubic-bezier(0, 0, 0, 1)` | Elements entering the screen |
| `ease-accelerate` | `cubic-bezier(0.3, 0, 1, 1)` | Elements leaving the screen |

### 11.4 Interaction Patterns

#### Hover States
| Element | Hover Effect |
|---------|-------------|
| Button (primary) | Brighten 10% (`hover:brightness-110`) |
| Button (secondary/ghost) | Background tint (`hover:bg-[var(--bg-secondary)]`) |
| Card | Subtle shadow lift (`hover:shadow-muhide-2`) |
| Table row | Background tint (`hover:bg-[var(--bg-secondary)]`) |
| Nav item | Background tint + text color shift |
| Icon button | Background circle + color shift |

#### Focus States
| Element | Focus Effect |
|---------|-------------|
| Button | `ring-2 ring-[var(--muhide-orange)] ring-offset-2` |
| Input | `ring-2 ring-[var(--muhide-orange)] border-[var(--muhide-orange)]` |
| Card | `ring-2 ring-[var(--muhide-orange)] ring-offset-2` |
| Nav item | `ring-2 ring-[var(--muhide-orange)] ring-offset-2` within sidebar |

#### Active/Pressed States
| Element | Active Effect |
|---------|-------------|
| Button | Scale down 1% (`active:scale-[0.98]`) |
| Card | No scale change (too heavy) |
| Nav item | Background darken |
| Kanban card | `opacity-50 ring-2 ring-[var(--muhide-orange)]/50` |

#### Loading States
| Context | Pattern |
|---------|---------|
| Page load | Skeleton screen matching expected layout |
| Data fetch | Skeleton with pulse animation |
| Button action | Spinner inside button, button disabled |
| Table load | 5 skeleton rows |
| Chart load | Skeleton card with chart-shaped placeholder |

### 11.5 Transition Specifications

| Transition | From → To | Duration | Easing |
|------------|-----------|----------|--------|
| Sidebar collapse | 256px → 64px | 200ms | standard |
| Modal open | hidden → visible | 200ms | decelerate |
| Modal close | visible → hidden | 150ms | accelerate |
| Dropdown open | hidden → visible | 150ms | decelerate |
| Tab switch | content swap | 200ms | standard |
| Toast enter | slide in from top | 300ms | decelerate |
| Toast exit | slide out to right | 200ms | accelerate |
| Page transition | crossfade | 200ms | standard |
| Drawer open | slide in from right | 300ms | decelerate |
| Tooltip | fade in | 100ms | standard |

### 11.6 Reduced Motion

All motion must respect `prefers-reduced-motion: reduce`. When this preference is active:
- All animations are instant (0ms)
- All transitions are instant (0ms)
- Skeleton pulse is disabled
- Slide animations are disabled

This is already implemented in `globals.css` — verify it is respected in all new components.

---

## 12. Responsive Strategy

### 12.1 Breakpoint System

| Breakpoint | Width | Target |
|------------|-------|--------|
| `sm` | 640px | Large phones (landscape) |
| `md` | 768px | Tablets (portrait) |
| `lg` | 1024px | Tablets (landscape), small laptops |
| `xl` | 1280px | Desktops |
| `2xl` | 1536px | Large desktops |

### 12.2 Layout Behavior

| Screen | Sidebar | Header | Content | Nav |
|--------|---------|--------|---------|-----|
| < 768px | Hidden (FAB drawer) | Compact (h-12) | Full width, p-3 | Bottom tab bar |
| 768-1024px | Collapsible (64/256px) | Standard (h-14) | Flex with sidebar | Sidebar nav |
| > 1024px | Always visible (256px) | Standard (h-14) | Flex with sidebar | Sidebar nav |

### 12.3 Component Responsive Behavior

#### Tables
- **Desktop:** Full table with all columns
- **Tablet:** Table with reduced columns (hide less important ones)
- **Mobile:** Card layout (already implemented in `globals.css`)

#### Dashboards
- **Desktop:** 3-4 column widget grid
- **Tablet:** 2 column widget grid
- **Mobile:** 1 column widget stack

#### Modals
- **Desktop:** Centered, max-width constrained
- **Mobile:** Full-screen (already implemented in `globals.css`)

#### Side Panels (Copilot, Search)
- **Desktop:** Fixed width panel (384px) sliding from right
- **Mobile:** Full-screen overlay

#### Kanban
- **Desktop:** Horizontal scroll with all columns visible
- **Tablet:** Horizontal scroll
- **Mobile:** Single column with stage selector

### 12.4 Mobile-Specific Patterns

#### Bottom Tab Bar (Replace FAB)
```
┌──────────────────────────────┐
│                              │
│       [Page Content]         │
│                              │
├──────────────────────────────┤
│ 🏠  🏢  📊  🔍  ⋯          │
│ Home Companies Pipeline Search More │
└──────────────────────────────┘
```

- 5 tabs: Home (Dashboard), Companies, Pipeline (Opportunities), Search, More
- "More" opens the full navigation drawer
- Active tab has filled icon + brand color

#### Pull-to-Refresh
- Already implemented in `globals.css` (`.pull-to-refresh`)
- Apply to list pages (Companies, Employees, Contacts)

#### Touch Targets
- Minimum 44x44px for all interactive elements (already implemented in some places via `min-h-[44px] min-w-[44px]`)
- Verify consistency across all components

### 12.5 Responsive Typography

| Screen | Body | Heading 1 | Heading 2 | KPI |
|--------|------|-----------|-----------|-----|
| Mobile | 14px | 18px | 16px | 24px |
| Tablet | 14px | 20px | 18px | 28px |
| Desktop | 14px | 24px | 20px | 32px |

---

## 13. Accessibility Standards

### 13.1 Target Standard

**WCAG 2.1 Level AA** compliance. This is the enterprise standard required by most procurement processes.

### 13.2 Current Gaps

| Area | Current Status | Gap |
|------|---------------|-----|
| Keyboard navigation | Partial (AppShell has Cmd+K) | No tab navigation for sidebar, tables, cards |
| Focus management | `focus-visible` ring implemented | Not all components have visible focus |
| ARIA labels | Some (`aria-label` on buttons) | Missing on many interactive elements |
| Color contrast | Generally good (warm neutrals) | Verify all text/bg combinations |
| Screen reader | `aria-live` regions exist | Not comprehensive |
| Touch targets | 44px minimum in some places | Not consistent across all components |
| Reduced motion | Implemented in `globals.css` | Verify all animations respect it |

### 13.3 Accessibility Requirements

#### Keyboard Navigation
| Key | Action |
|-----|--------|
| `Tab` | Move focus to next interactive element |
| `Shift+Tab` | Move focus to previous interactive element |
| `Enter` | Activate focused element |
| `Space` | Toggle checkbox, activate button |
| `Escape` | Close modal, dropdown, or panel |
| `Arrow keys` | Navigate within tab list, dropdown, or table |
| `Home` | Move to first item in list/table |
| `End` | Move to last item in list/table |

#### Focus Management Rules
1. Focus must be visible on all interactive elements
2. Focus must be trapped within modals (Radix Dialog does this)
3. Focus must return to trigger element when modal closes
4. Focus must move to new content after async load
5. Skip links must be provided for main content

#### ARIA Requirements
| Element | ARIA Requirement |
|---------|-----------------|
| Navigation | `role="navigation"`, `aria-label` |
| Main content | `role="main"` |
| Modals | `role="dialog"`, `aria-modal="true"`, `aria-labelledby` |
| Tables | `role="table"`, `aria-sort` on sortable columns |
| Tabs | `role="tablist"`, `role="tab"`, `role="tabpanel"`, `aria-selected` |
| Buttons | `aria-label` when icon-only |
| Loading | `aria-busy="true"`, `role="status"` |
| Errors | `role="alert"`, `aria-live="assertive"` |
| Toast | `role="status"`, `aria-live="polite"` |

#### Color Contrast Ratios
| Combination | Required | Current |
|-------------|----------|---------|
| Body text on white | 4.5:1 | ✅ `#26231E` on `#FFFFFF` = 15.4:1 |
| Secondary text on white | 4.5:1 | ✅ `#706A5D` on `#FFFFFF` = 5.2:1 |
| Muted text on white | 3:1 | ✅ `#8C8374` on `#FFFFFF` = 3.8:1 |
| Orange on white | 4.5:1 | ⚠️ `#F57C1E` on `#FFFFFF` = 2.8:1 (fails for text) |
| Orange on dark bg | 4.5:1 | ✅ `#F57C1E` on `#151214` = 4.6:1 |

**Action needed:** The brand orange `#F57C1E` fails WCAG contrast for text on white backgrounds. Use it only for large text (≥18px bold) or icons, never for body text on white.

### 13.4 Accessibility Testing Strategy

1. **Automated:** ESLint `jsx-a11y` plugin (already partially configured)
2. **Keyboard:** Manual testing of all flows via keyboard only
3. **Screen reader:** Test with VoiceOver (macOS) and NVDA (Windows)
4. **Contrast:** Chrome DevTools accessibility audit
5. **Automated CI:** Axe-core integration in Playwright tests

---

## 14. Implementation Roadmap

### 14.1 Guiding Principles

1. **No breaking changes to existing URLs.** All redirects must be mapped.
2. **Incremental delivery.** Each phase produces usable improvements.
3. **Token-first.** Design tokens must be established before component changes.
4. **Component deduplication before new components.** Fix existing before adding new.
5. **Mobile-last.** Desktop first, responsive second (enterprise users are desktop-first).

### 14.2 Phase 0: Design Token Foundation (Week 1-2)

**Goal:** Establish single source of truth for all design tokens.

| Task | Output | Dependencies |
|------|--------|-------------|
| Create `@salesos/tokens` package | `tokens/colors.ts`, `tokens/typography.ts`, `tokens/spacing.ts`, `tokens/elevation.ts`, `tokens/motion.ts`, `tokens/radius.ts` | None |
| Update `tailwind.config.ts` | Import from `@salesos/tokens` | Token package |
| Update `globals.css` | CSS vars generated from tokens | Token package |
| Audit all hex values in components | List of raw values to replace | None |
| Fix orange contrast issue | Adjust text usage of brand orange | Design decision |

**Deliverable:** Single source of truth for all design values. No raw hex/pixel/shadow values in any component.

### 14.3 Phase 1: Navigation Restructure (Week 3-5)

**Goal:** Transform 38-item flat sidebar into grouped, collapsible, role-aware navigation.

| Task | Output | Dependencies |
|------|--------|-------------|
| Define workspace configurations | Workspace config objects | Token package |
| Build grouped Sidebar component | Collapsible sections with icons | Token package |
| Add workspace selector to header | Dropdown in top-left | Sidebar component |
| Implement "Pinned" navigation | User-pinned modules | Sidebar component |
| Add breadcrumbs to all deep pages | Consistent breadcrumb pattern | Existing Breadcrumbs component |
| Build PageHeader component | Standardized page title/description/actions | Token package |
| Update MobileNav to bottom tab bar | 5-tab + More pattern | Sidebar component |

**Deliverable:** Navigation that scales to 50+ modules without cognitive overload.

### 14.4 Phase 2: Component Standardization (Week 6-8)

**Goal:** Eliminate component duplication and establish consistent patterns.

| Task | Output | Dependencies |
|------|--------|-------------|
| Unify Card component | Single Card with CVA variants | Token package |
| Standardize all buttons to `<Button>` | Replace raw `<button>` elements | Button component |
| Build MetricCard component | Reusable KPI display | Token package |
| Build StatCard component | Label + value + icon | Token package |
| Build SectionHeader component | Title + count + expand/collapse | Token package |
| Standardize empty states | Consistent EmptyState with illustrations | Token package |
| Standardize loading states | Consistent Skeleton patterns | Token package |
| Standardize error states | Consistent ErrorFallback pattern | Token package |

**Deliverable:** One way to do each thing. No more 3 Card variants.

### 14.5 Phase 3: Dashboard Evolution (Week 9-12)

**Goal:** Transform dashboard from widget registry to executive morning brief.

| Task | Output | Dependencies |
|------|--------|-------------|
| Build MorningBriefHeader | Greeting + date + context | MetricCard, StatCard |
| Build KPISummaryBar | 4 key metrics with trends | MetricCard |
| Build TodaysPriorities | Decision Center integration | API integration |
| Build PipelineHealthChart | Stage breakdown with bars | Chart component |
| Build RevenueTrendSparkline | 12-month trend line | Chart component |
| Build TeamPerformanceLeaderboard | Top reps with quota bars | StatCard |
| Build ForecastScenarioCards | Pessimistic/Baseline/Optimistic | Card component |
| Implement dashboard personalization | Widget reorder/hide | Drag-and-drop |

**Deliverable:** Dashboard that executives will check every morning.

### 14.6 Phase 4: Company 360 Redesign (Week 13-16)

**Goal:** Make Company 360 the single pane of glass for customer intelligence.

| Task | Output | Dependencies |
|------|--------|-------------|
| Redesign tab structure | 8 differentiated tabs | Sidebar/PageHeader |
| Build CompanyDNA component | Company profile summary | Card, StatCard |
| Build BuyingJourney component | Visual progress bar | New component |
| Build AIRecommendation card | Next best action with reasoning | Confidence gauge |
| Build QuickActions bar | Context-aware action buttons | Button component |
| Enhance RelationshipGraph | Click-to-expand, navigate | Existing graph |
| Integrate ActivityTimeline | Dedicated tab | Existing timeline |
| Add cross-entity navigation | "View related" links | Breadcrumbs |

**Deliverable:** Company 360 that shows everything about a company in one screen.

### 14.7 Phase 5: Employee 360 Redesign (Week 17-19)

**Goal:** Make Employee 360 a performance coaching tool.

| Task | Output | Dependencies |
|------|--------|-------------|
| Decompose 1122-line employee list | Separate components | Token package |
| Build ScoreTrendChart | Sparkline + history | Chart component |
| Build CoachingInsightCard | AI coaching suggestions | AI integration |
| Build TeamComparison component | vs. team average | StatCard |
| Build ActivityHeatMap | Visual activity patterns | Chart component |
| Add card/table view toggle | List vs. grid | Toggle component |

**Deliverable:** Employee 360 that managers use for coaching conversations.

### 14.8 Phase 6: AI Integration (Week 20-23)

**Goal:** Make AI ambient intelligence, not a separate feature.

| Task | Output | Dependencies |
|------|--------|-------------|
| Build Copilot sidebar | Floating AI assistant | Radix Dialog |
| Add AI insights to Company 360 | Context-aware recommendations | Decision API |
| Add AI insights to Employee 360 | Performance coaching suggestions | Scoring API |
| Add AI badges to lists | Anomaly detection indicators | Signal API |
| Rebuild AI page | End-user prompt builder (not developer tool) | Existing AI API |
| Add natural language search | "Ask in plain English" input | RAG API |
| Implement AI honesty labels | Insight/Suggestion/Draft badges | Design system |

**Deliverable:** AI that appears everywhere it is useful, with full transparency.

### 14.9 Phase 7: Accessibility & Polish (Week 24-26)

**Goal:** WCAG 2.1 AA compliance and enterprise polish.

| Task | Output | Dependencies |
|------|--------|-------------|
| Add keyboard navigation to all components | Tab/arrow key support | All components |
| Add ARIA labels to all interactive elements | Complete ARIA coverage | All components |
| Add skip links | "Skip to main content" | AppShell |
| Fix color contrast issues | All combinations ≥ 4.5:1 | Token adjustments |
| Add focus-visible to all components | Consistent focus ring | Token package |
| Test with screen readers | VoiceOver + NVDA testing | Manual testing |
| Add reduced-motion support | Verify all animations | All components |
| Final visual polish | Spacing, alignment, consistency audit | All pages |

**Deliverable:** Enterprise-grade accessibility that passes procurement audits.

---

## Appendix A: File Inventory

### Files to Modify

| File | Action | Phase |
|------|--------|-------|
| `packages/tokens/` | Complete rebuild | 0 |
| `packages/design-system/src/tokens.ts` | Replace with token imports | 0 |
| `packages/ui/src/card.tsx` | Unify with foundation/card.tsx | 2 |
| `packages/ui/src/button.tsx` | Add icon-only variant | 2 |
| `tailwind.config.ts` | Import from tokens | 0 |
| `src/app/globals.css` | Generate CSS vars from tokens | 0 |
| `src/app/(dashboard)/layout.tsx` | Grouped sidebar, workspace selector | 1 |
| `src/components/foundation/MobileNav.tsx` | Bottom tab bar | 1 |
| `src/components/foundation/card.tsx` | Remove (merge into @salesos/ui) | 2 |
| `src/app/(dashboard)/dashboard/page.tsx` | Executive brief layout | 3 |
| `src/app/(dashboard)/companies/[id]/360/page.tsx` | Tab redesign | 4 |
| `src/app/(dashboard)/employees/page.tsx` | Decompose 1122-line file | 5 |
| `src/components/employee-360-page.tsx` | Add coaching insights | 5 |
| `src/components/copilot-panel.tsx` | Full AI sidebar | 6 |

### Files to Create

| File | Purpose | Phase |
|------|---------|-------|
| `packages/tokens/src/colors.ts` | Color tokens | 0 |
| `packages/tokens/src/typography.ts` | Typography tokens | 0 |
| `packages/tokens/src/spacing.ts` | Spacing tokens | 0 |
| `packages/tokens/src/elevation.ts` | Elevation tokens | 0 |
| `packages/tokens/src/motion.ts` | Motion tokens | 0 |
| `packages/tokens/src/radius.ts` | Radius tokens | 0 |
| `packages/design-system/src/layout/PageHeader.tsx` | Page header component | 1 |
| `packages/design-system/src/layout/SectionHeader.tsx` | Section header component | 1 |
| `packages/design-system/src/layout/Sidebar.tsx` | Grouped sidebar component | 1 |
| `packages/design-system/src/primitives/MetricCard.tsx` | KPI card | 2 |
| `packages/design-system/src/primitives/StatCard.tsx` | Stat card | 2 |
| `packages/design-system/src/patterns/MorningBrief.tsx` | Dashboard morning brief | 3 |
| `packages/design-system/src/patterns/TodaysPriorities.tsx` | Priority list | 3 |
| `packages/design-system/src/patterns/CoachingInsight.tsx` | AI coaching card | 5 |

---

## Appendix B: Design Decisions Log

| # | Decision | Rationale | Date |
|---|----------|-----------|------|
| DD-01 | Preserve warm neutral palette | Differentiates from blue-gray SaaS, already established brand identity | 2026-08-05 |
| DD-02 | Workspace-based navigation | Eliminates 60-70% of navigation noise by role | 2026-08-05 |
| DD-03 | Brand orange for actions only, not body text | Fails WCAG contrast on white (2.8:1 < 4.5:1) | 2026-08-05 |
| DD-04 | 4px spacing base | Consistent with existing Tailwind config | 2026-08-05 |
| DD-05 | Radix UI primitives | Already in use, accessible by default | 2026-08-05 |
| DD-06 | CVA for component variants | Already in use, type-safe | 2026-08-05 |
| DD-07 | Bottom tab bar for mobile | Enterprise standard, replaces non-standard FAB | 2026-08-05 |
| DD-08 | WCAG 2.1 AA target | Enterprise procurement requirement | 2026-08-05 |
| DD-09 | AI always shows reasoning | Trust requires transparency | 2026-08-05 |
| DD-10 | No breaking URL changes | Existing bookmarks and integrations must work | 2026-08-05 |

---

*This document is the design strategy. No code should be written until all stakeholders approve the direction outlined here. Implementation begins only after Phase 0 tokens are established.*
