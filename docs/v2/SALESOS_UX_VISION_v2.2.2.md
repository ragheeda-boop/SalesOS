# SalesOS UX Vision v2.2.2

> **Status:** Approved — Implementation Ready  
> **Supersedes:** UX Vision v2.0, v2.1, v2.2, v2.2.1, ARB Review  
> **Date:** 2026-08-05  
> **Decision Record:** ADR-DD-011 (Orange Contrast), AI_GOVERNANCE.md (AI Policy)  
> **Scope:** Frontend UX evolution — no product architecture changes  
> **Frozen:** After stakeholder sign-off, changes only via ADR or Design Decision  

---

## Decision Log

| # | Decision | Status | Rationale |
|---|----------|--------|-----------|
| DD-011 | Brand orange `#F57C1E` fails WCAG on white (2.8:1) | **Release Blocker** | Enterprise procurement requires 4.5:1 minimum |
| DD-012 | Workspace concept validated via prototype, not 2-week research | Accepted | Pattern proven in Salesforce, HubSpot, Monday, Linear |
| DD-013 | AI Governance is a separate document, not embedded in UX Vision | Accepted | AI policy requires legal, technical, and compliance review |
| DD-014 | All new components must be RTL-first | Accepted | RTL utilities exist; new components must enforce consistency |
| DD-015 | Design system migration enforced via linting, not just convention | Accepted | Unenforceable rules lead to dual systems |
| DD-016 | 12 product concepts rejected from UX Vision scope | Accepted | Revenue Recognition, Territory, Compliance = separate PRDs |
| DD-017 | Timeline: 32 weeks (plan), 27 weeks (optimistic minimum) | Accepted | 32 includes QA buffer; 27 achievable with ideal conditions |

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
9. [AI Contextual Insights](#9-ai-contextual-insights)
10. [Design System v2](#10-design-system-v2)
11. [Motion & Interaction Guidelines](#11-motion--interaction-guidelines)
12. [Responsive Strategy](#12-responsive-strategy)
13. [Accessibility Standards](#13-accessibility-standards)
14. [RTL-First Policy](#14-rtl-first-policy)
15. [Performance Budget](#15-performance-budget)
16. [Design Tokens Governance](#16-design-tokens-governance)
17. [UX Acceptance Criteria](#17-ux-acceptance-criteria)
18. [Implementation Roadmap](#18-implementation-roadmap)

---

## 1. Product Philosophy

### 1.1 Core Belief

SalesOS transforms scattered data into decisive action. Every screen answers: **"What should I do next, what should I monitor, and what should I avoid?"**

### 1.2 Design Principles

| # | Principle | Meaning | Anti-Pattern |
|---|-----------|---------|--------------|
| 1 | **Clarity Over Cleverness** | Show the answer, not raw data | 38-item flat sidebar |
| 2 | **Progressive Disclosure** | 20% of information drives 80% of decisions | Dumping all modules on every user |
| 3 | **Context Over Navigation** | Bring information to the user | 5 clicks to reach Company 360 |
| 4 | **Confidence Through Evidence** | Every AI recommendation shows reasoning | Black-box AI outputs |
| 5 | **Respect the Role** | CEO sees different things than SDR | One-size-fits-all dashboard |
| 6 | **Bilingual by Default** | Arabic is co-equal, not an afterthought | RTL as a CSS hack |
| 7 | **Enterprise Trust** | Interface must feel like it handles millions | Consumer-grade patterns |

### 1.3 Product Personality

SalesOS should feel like:

- **Stripe's precision** — every pixel intentional
- **Linear's speed** — keyboard-first, instant feedback
- **Notion's calm** — density without noise
- **Salesforce's authority** — enterprise-grade, trustworthy
- **Apple's restraint** — only what is needed

### 1.4 What SalesOS Is NOT

- Not a chatbot with a dashboard
- Not a data warehouse with a UI skin
- Not isolated feature pages
- Not a consumer app dressed as enterprise

SalesOS is an **intelligence platform** where AI assists human decision-making across the sales lifecycle.

---

## 2. Workspace Architecture

### 2.1 The Workspace Concept

SalesOS is a **platform** with multiple **workspaces**, each optimized for a user role and workflow.

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

**Default workspaces** are hardcoded in the platform (Sales, Executive, Intelligence, GTM, Studio, Admin). These cover 95% of use cases.

**Custom workspaces** are configurable by admins via Studio > Workspaces. Admins can:
- Create new workspaces (e.g., "Legal", "Finance", "Customer Success")
- Assign modules to custom workspaces
- Set default workspace per role
- Hide default workspaces they don't need

**Limit:** Max 12 workspaces per tenant (6 default + 6 custom). This prevents navigation overload from excessive workspace options.

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

- Workspace selector in **user avatar dropdown** (top-right, consistent with SaaS patterns)
- User chooses their default workspace (not admin-assigned)
- Users may switch only to workspaces they are authorized to access (role-based permissions)
- Switching reconfigures sidebar, dashboard, and available actions
- Pinned workspaces visible in sidebar header for quick switching

### 2.4 Validation Plan

Workspace concept is validated via:

1. **Prototype** — Interactive workspace switcher with grouped sidebar (1 day build)
2. **User test** — 3-5 power users per role (1 day)
3. **Measurement** — Task completion time, error rate, satisfaction
4. **Decision** — Proceed, modify, or fallback to grouped sidebar without workspaces

**Success Criteria:**

| Metric | Pass | Fail |
|--------|------|------|
| Task completion rate | ≥ 90% without help | < 80% without help |
| Task completion time | ≤ 120% of flat sidebar baseline | > 150% of baseline |
| User satisfaction (1-5) | ≥ 4.0 average | < 3.0 average |
| Navigation errors | ≤ 1 per session | > 3 per session |

**If any metric fails:** Implement fallback — grouped sidebar with role-based default visibility (same visual grouping, no workspace switching).

---

## 3. Navigation Architecture

### 3.1 Current Problem

The sidebar contains 38 items in a flat list. Impossible to scan, memorize, or navigate on mobile.

### 3.2 Proposed Navigation Model

```
┌──────────────────────────────────────┐
│  [Brand]                             │
├──────────────────────────────────────┤
│  🔍 Search everything...     ⌘K     │
├──────────────────────────────────────┤
│  ⭐ Pinned                          │
│    └─ [User's pinned modules]       │
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
| Pinned items always visible | User can pin unlimited modules |
| Search is universal | Cmd+K searches across all modules, entities, actions |
| Active section is visually distinct | Left border pill + background tint + bold text |
| Collapse preserves context | Collapsed sidebar shows icons only, tooltips on hover |
| Mobile uses bottom tab bar | 5 primary tabs + "More" overflow |

### 3.4 Command Palette (Cmd+K)

Primary navigation tool for power users:

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

**Note:** Command palette is a power-user tool. The sidebar must be equally performant for users who prefer clicking.

### 3.5 Breadcrumb Strategy

Every page deeper than level 2 gets breadcrumbs:

| Depth | Example | Breadcrumbs |
|-------|---------|-------------|
| 1 | /companies | None |
| 2 | /companies/acme-corp | Companies > Acme Corp |
| 3 | /companies/acme-corp/360 | Companies > Acme Corp > 360 |

**Rule:** If breadcrumbs exceed 4 items, truncate middle items with "..." and show full path on hover.

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
Level 1: /dashboard, /companies, /employees, /opportunities
Level 2: /companies/acme-corp, /employees/emp-123
Level 3: /companies/acme-corp/360, /employees/emp-123/performance
```

**Rule:** No page requires more than 3 clicks from dashboard.

### 4.3 Cross-Entity Navigation

Every entity card/row shows mini-relation map:
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

The warm neutral palette is a **strength**. It differentiates SalesOS from blue-gray SaaS. Preserve it.

**Brand Colors:**
| Token | Value | Use |
|-------|-------|-----|
| `--muhide-orange` | `#F57C1E` | Brand identity, icons, large headings (≥18px bold only) |
| `--muhide-ink` | `#151214` | Dark mode background, strong text |
| `--muhide-espresso` | `#403D38` | Secondary dark elements |
| `--muhide-sand` | `#CCC6BA` | Subtle borders, disabled states |
| `--muhide-paper` | `#FAFAFA` | Light backgrounds |

**Semantic Colors:**
| Token | Light | Dark | Use |
|-------|-------|------|-----|
| `--status-success` | `#22C55E` | `#34D399` | Won, active, healthy |
| `--status-danger` | `#EF4444` | `#F87171` | Lost, critical, error |
| `--status-warning` | `#F59E0B` | `#FBBF24` | At risk, pending |
| `--status-info` | `#3B82F6` | `#60A5FA` | Neutral info, links |
| `--status-purple` | `#8B5CF6` | `#A78BFA` | AI, intelligence |

**Primary Action Colors (WCAG Compliant):**
| Context | Color | Contrast on White | Use |
|---------|-------|-------------------|-----|
| Button text (on orange bg) | `#FFFFFF` | 4.6:1 ✅ | Primary CTA buttons |
| Button background | `#F57C1E` | N/A (bg, not text) | Primary CTA fill |
| Link text | `#D4660F` (orange-600) | 4.8:1 ✅ | Text links |
| Active nav text | `#D4660F` (orange-600) | 4.8:1 ✅ | Sidebar active state |
| Body text on white | `#26231E` (neutral-900) | 15.4:1 ✅ | Primary body text |
| Secondary text | `#706A5D` (neutral-600) | 5.2:1 ✅ | Descriptions, labels |

**Rule:** Brand orange `#F57C1E` is NEVER used as text color on white/light backgrounds. It is used as:
- Button fill color (with white text)
- Icon color (icons have sufficient contrast)
- Large heading accent (≥18px bold)
- Background tint (`bg-[var(--muhide-orange)]/10`)

### 5.2 Typography System

| Name | Size | Weight | Line Height | Use |
|------|------|--------|-------------|-----|
| `display-lg` | 40px | 700 | 1.1 | Hero KPI numbers |
| `display` | 32px | 700 | 1.15 | Page titles |
| `heading-1` | 24px | 700 | 1.2 | Section headers |
| `heading-2` | 20px | 600 | 1.3 | Card titles |
| `heading-3` | 16px | 600 | 1.4 | Subsection headers |
| `body-lg` | 14px | 400 | 1.6 | Primary body |
| `body` | 14px | 400 | 1.5 | Default body |
| `body-sm` | 12px | 400 | 1.4 | Secondary text |
| `caption` | 11px | 500 | 1.4 | Labels, badges |
| `overline` | 10px | 600 | 1.3 | Category labels |

**Font Stack:**
- Display: Viga
- Body: IBM Plex Sans (400, 500, 600, 700)
- Arabic: IBM Plex Sans Arabic (400, 500, 600, 700)
- Code: IBM Plex Mono (400, 500, 600)

### 5.3 Spacing System (4px base)

| Token | Value | Use |
|-------|-------|-----|
| `space-1` | 4px | Icon-to-text gaps |
| `space-2` | 8px | Badge padding, compact gaps |
| `space-3` | 12px | List item spacing |
| `space-4` | 16px | Card internal padding |
| `space-5` | 20px | Section gaps |
| `space-6` | 24px | Page padding |
| `space-8` | 32px | Major section separation |
| `space-10` | 40px | Page-level spacing |
| `space-12` | 48px | Hero spacing |

### 5.4 Elevation System

| Level | Shadow | Use |
|-------|--------|-----|
| `elevation-1` | `0 1px 2px rgba(21,18,20,0.06)` | Cards |
| `elevation-2` | `0 1px 3px rgba(21,18,20,0.08), 0 1px 2px rgba(21,18,20,0.04)` | Dropdowns |
| `elevation-3` | `0 4px 6px rgba(21,18,20,0.07), 0 2px 4px rgba(21,18,20,0.04)` | Sticky headers |
| `elevation-4` | `0 10px 15px rgba(21,18,20,0.08), 0 4px 6px rgba(21,18,20,0.04)` | Modals |
| `elevation-5` | `0 20px 25px rgba(21,18,20,0.10), 0 8px 10px rgba(21,18,20,0.05)` | Command palette |
| `elevation-6` | `0 25px 50px rgba(21,18,20,0.16)` | Full-screen overlays |

### 5.5 Border Radius

| Token | Value | Use |
|-------|-------|-----|
| `radius-sm` | 2px | Badges, inline elements |
| `radius-md` | 6px | Buttons, inputs |
| `radius-lg` | 8px | Cards, dropdowns |
| `radius-xl` | 12px | Modals, panels |
| `radius-2xl` | 16px | Feature cards |
| `radius-full` | 9999px | Pills, avatars |

### 5.6 Icon Guidelines

| Size | Pixels | Use |
|------|--------|-----|
| `icon-sm` | 14px | Inline with text |
| `icon-md` | 16px | Buttons, nav items |
| `icon-lg` | 20px | Section headers |
| `icon-xl` | 24px | Page headers |
| `icon-2xl` | 32px | Empty states |

**Library:** Lucide only. Never mix icon libraries.

---

## 6. Executive Dashboard Vision

### 6.1 Current State

Dashboard is a widget registry. No narrative, no priority ordering.

### 6.2 Vision: The Morning Brief

```
┌─────────────────────────────────────────────────────────┐
│  Good morning, [Name]. Tuesday, Aug 5                   │
│  Last updated: 2 minutes ago                            │
│                                                         │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐   │
│  │ Revenue  │ │ Pipeline │ │ Active   │ │ Team     │   │
│  │ $2.4M    │ │ $8.7M    │ │ 47       │ │ 12/15    │   │
│  │ ↑ 12%    │ │ ↑ 8%     │ │ deals    │ │ online   │   │
│  └──────────┘ └──────────┘ └──────────┘ └──────────┘   │
│                                                         │
│  ⚡ Today's Priorities                                   │
│  ┌─────────────────────────────────────────────────┐    │
│  │ 🔴 3 deals at risk                               │    │
│  │    → Acme Corp ($450K) — no activity in 14 days │    │
│  │    → STC ($280K) — competitor engaged            │    │
│  │    → SABIC ($190K) — decision maker changed      │    │
│  │                                                  │    │
│  │ 🟡 2 renewals due this month                     │    │
│  │ 🟢 5 new opportunities from lead discovery       │    │
│  └─────────────────────────────────────────────────┘    │
│                                                         │
│  📊 Pipeline Health          📈 Revenue Trend            │
│  ┌────────────────────┐     ┌────────────────────┐     │
│  │ [Stage bars]        │     │ [Sparkline chart]   │     │
│  └────────────────────┘     └────────────────────┘     │
│                                                         │
│  🏆 Team Performance     🔮 Forecast                    │
│  ┌────────────────────┐  ┌────────────────────┐        │
│  │ [Leaderboard]       │  │ [Scenario cards]    │        │
│  └────────────────────┘  └────────────────────┘        │
└─────────────────────────────────────────────────────────┘
```

### 6.3 Dashboard Components

| Component | Source | Purpose |
|-----------|--------|---------|
| `MorningBriefHeader` | New | Greeting + date + last updated timestamp |
| `KPISummaryBar` | Adapted from ExecutiveDashboard | 4 key metrics with trends |
| `TodaysPriorities` | New — Decision Center powered | Top 3-5 actions requiring attention |
| `PipelineHealthChart` | Adapted from ExecutiveDashboard | Stage breakdown |
| `RevenueTrendSparkline` | New | 12-month trend line |
| `TeamPerformanceLeaderboard` | Adapted from ExecutiveDashboard | Top reps by revenue |
| `ForecastScenarioCards` | Adapted from forecast/page.tsx | Pessimistic/Baseline/Optimistic |

### 6.4 Refresh Strategy

- **KPI metrics:** WebSocket when available, 30-second polling fallback
- **Charts:** Refresh on page load + manual refresh button
- **Priorities:** Refresh every 5 minutes
- **Activity feed:** Real-time via WebSocket
- **Freshness indicator:** Always show "Last updated: X minutes ago"

### 6.5 Personalization

- Users can reorder widgets via drag-and-drop
- Users can hide widgets they don't need
- Default view per workspace
- Reset to default option available

---

## 7. Company 360 Vision

### 7.1 Current State

5 tabs with duplicated content between Overview and Insights.

### 7.2 Vision: Single Pane of Glass

```
┌─────────────────────────────────────────────────────────┐
│  [← Back]  Companies > Acme Corp > 360                  │
│                                                         │
│  ┌───────────────────────────────────────────────────┐  │
│  │ 🏢 Acme Corp                    [Health: 78/100]  │  │
│  │ CR: 1010123456 | Riyadh | Active                  │  │
│  │                                                    │  │
│  │ [Overview] [People] [Deal Room] [Activity] [More] │  │
│  └───────────────────────────────────────────────────┘  │
│                                                         │
│  ┌─────────────────┐ ┌───────────────────────────────┐ │
│  │ Company DNA      │ │ AI Recommendation             │ │
│  │ Industry: Tech   │ │ "Schedule meeting with CFO    │ │
│  │ Size: 500-1000   │ │  before Q4 budget cycle"      │ │
│  │ Revenue: $50M    │ │ [Act on this] [Dismiss]       │ │
│  └─────────────────┘ └───────────────────────────────┘ │
│                                                         │
│  ┌─────────────────┐ ┌───────────────────────────────┐ │
│  │ Buying Journey   │ │ Relationship Graph             │ │
│  │ Awareness → ...  │ │    [Acme]──[Contact A]       │ │
│  │         [Current]│ │      │         │             │ │
│  └─────────────────┘ │  [Employee]──[Opp 1]         │ │
│                       └───────────────────────────────┘ │
│                                                         │
│  ⚡ Quick Actions                                       │
│  [📞 Call] [📧 Email] [📅 Meeting] [📝 Note]           │
│  [➕ Contact] [📊 Opportunity] [📄 Document]           │
└─────────────────────────────────────────────────────────┘
```

### 7.3 Tab Structure (5 tabs, not 8)

| Tab | Content | Key Difference |
|-----|---------|----------------|
| **Overview** | Company DNA, AI Recommendation, Buying Journey, Graph summary | Combined summary |
| **People** | Contacts, Decision Makers, Org chart, Assigned employees | Merged Contacts + Hierarchy |
| **Deal Room** | Opportunities, Contracts, Financial summary | Merged Financial + Deals |
| **Activity** | Full timeline, Email history, Meetings, Calls | Dedicated timeline |
| **More** | Documents, Graph (full), AI Insights, Export | Overflow for secondary content |

**Rationale:** 5 tabs instead of 8. "More" contains secondary tabs that users access on-demand. Overview shows everything needed "at a glance."

### 7.4 Quick Actions Bar

Always visible. Context-aware:
- Shows relevant actions based on company state
- "Call" appears if phone number exists
- "Opportunity" appears if no active deal
- "Renewal" appears if contract expiring within 90 days

---

## 8. Employee 360 Vision

### 8.1 Current State

Lazy-loaded tabs with 1122-line list page.

### 8.2 Vision: Performance Cockpit

```
┌─────────────────────────────────────────────────────────┐
│  Employees > Ahmed Al-Sudairi                           │
│                                                         │
│  ┌───────────────────────────────────────────────────┐  │
│  │ 👤 Ahmed Al-Sudairi           Score: 82/100 ↑+5  │  │
│  │ Senior Account Executive | Enterprise Team         │  │
│  │                                                    │  │
│  │ [Overview] [Performance] [Activity] [Scoring]     │  │
│  └───────────────────────────────────────────────────┘  │
│                                                         │
│  ┌──────────────┐ ┌──────────────┐ ┌──────────────┐    │
│  │ Score Trend   │ │ Activity     │ │ Pipeline     │    │
│  │ [Sparkline]   │ │ Summary      │ │ $1.2M        │    │
│  │ 82 ↑ +5      │ │ 24 activities│ │ 3 deals      │    │
│  └──────────────┘ └──────────────┘ └──────────────┘    │
│                                                         │
│  ┌─────────────────────────────────────────────────┐    │
│  │ 🧠 AI Insight                                    │    │
│  │ "Engagement with Acme Corp dropped 40% in       │    │
│  │  2 weeks. Consider coaching conversation."       │    │
│  │  [Schedule Coaching] [View Deal]                 │    │
│  └─────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────┘
```

### 8.3 Score Definition

The employee score is a **composite performance index** calculated as:

```
Score = (Quota Attainment × 0.4) + (Activity Level × 0.3) + (Deal Quality × 0.2) + (Peer Signal × 0.1)
```

| Factor | Weight | Source | Normalization |
|--------|--------|--------|---------------|
| Quota Attainment | 40% | Revenue closed / quota target | 0-100 scale |
| Activity Level | 30% | Calls + emails + meetings / team average | 0-100 scale |
| Deal Quality | 20% | Avg deal size, win rate, sales cycle length | 0-100 scale |
| Peer Signal | 10% | Cross-functional signal contributions | 0-100 scale |

**Default weights** are shown above. Weights are **tenant-configurable** via Studio > Scoring Rules. Admins can adjust factor weights, add/remove factors, and set normalization ranges per tenant. The defaults above are the recommended starting point.

**Display:** Score shows as number + trend arrow (↑↓→) + color (green ≥70, amber 40-69, red <40).

**Hover tooltip:** Shows factor breakdown with individual scores.

**Versioning:** When weights change in Studio, the new formula applies to **future score calculations only**. Historical scores are preserved with their original weights. The score card shows which formula version produced each historical entry.

**Non-sales employees:** Skip Quota Attainment; remaining weights are re-normalized to sum to 100%.

### 8.4 Tab Structure

| Tab | Content |
|-----|---------|
| **Overview** | Score summary, AI insight, Activity summary, Signal breakdown |
| **Performance** | Score trend chart, Quota attainment, Deal progression |
| **Activity** | Complete timeline, Activity heat map, Communication patterns |
| **Scoring** | Score breakdown by factor, Confidence level, Benchmark comparison |

---

## 9. AI Contextual Insights

### 9.1 Naming

Not "AI Everywhere." **Contextual AI Insights** — AI appears where relevant, not everywhere.

### 9.2 AI Touchpoints

| Touchpoint | AI Behavior | UI Pattern |
|------------|-------------|------------|
| Dashboard | Morning priorities | "Today's Priorities" section |
| Company List | Anomaly detection | Subtle badge on at-risk companies |
| Company 360 | Recommendation engine | "Next Best Action" card |
| Employee List | Performance prediction | Score trend indicator |
| Employee 360 | Coaching suggestions | AI insight card |
| Pipeline | Deal risk scoring | Risk badge on cards |
| Decisions | Audit trail + confidence | Confidence gauge + factors |
| Search | Natural language queries | "Ask in plain English" |
| Global | Copilot sidebar | Floating AI panel |

### 9.3 AI UI Principles

1. **Always show reasoning.** Never present output without explanation.
2. **Always show confidence.** Confidence gauge (percentage + color).
3. **Always allow rejection.** Every suggestion has "Dismiss."
4. **Always label as AI.** Use "AI" chip or `ExperimentalAiBadge`.
5. **Never auto-execute.** AI recommends, human decides.

### 9.4 Confidence Thresholds

| Level | Score | Label | Default Display |
|-------|-------|-------|-----------------|
| High | ≥ 80% | AI Insight | Visible — green gauge, full reasoning |
| Medium | 50-79% | AI Suggestion | Visible — amber gauge, reasoning shown |
| Low | < 50% | AI Draft | **Hidden by default** — available via "Show low-confidence insights" toggle |

**Toggle behavior:**
- Power users can enable "Show low-confidence insights" in Settings > AI Preferences
- When enabled, low-confidence items appear with a muted visual treatment (reduced opacity, "Low confidence" label)
- Toggle state is persisted per user
- Default is OFF — most users should not act on < 50% confidence recommendations

**Rationale:** Hiding all < 50% insights loses potentially useful signals. The toggle gives advanced users control while protecting default users from acting on unreliable outputs.

### 9.5 Governance

AI governance is defined in `AI_GOVERNANCE.md` (separate document). Key requirements:

- Confidence score calculation methodology documented
- Audit trail for all AI recommendations (logged, retrievable)
- Feedback mechanism (user marks recommendation as helpful/not helpful)
- Hallucination mitigation (validate outputs against known data)
- Data privacy (customer data not used for model training without consent)
- Model versioning and rollback capability

### 9.6 Copilot Sidebar

```
┌──────────────────────────────┐
│  🤖 SalesOS Copilot    [×]  │
├──────────────────────────────┤
│                              │
│  Context: Company 360        │
│  Entity: Acme Corp           │
│                              │
│  Ask about Acme Corp...      │
│                              │
│  ┌────────────────────────┐  │
│  │ [Text input]     [Send]│  │
│  └────────────────────────┘  │
│                              │
│  Suggested:                  │
│  • "What deals are at risk?" │
│  • "Summarize recent activity│
│  • "Who should I call?"      │
│                              │
└──────────────────────────────┘
```

**Context-aware:** When on Company 360, Copilot knows you're asking about that company. When on Employee page, it knows you're asking about that employee.

---

## 10. Design System v2

### 10.1 Architecture

```
@salesos/tokens (Single Source of Truth)
├── colors.ts
├── typography.ts
├── spacing.ts
├── elevation.ts
├── motion.ts
├── radius.ts
├── z-index.ts
└── index.ts

@salesos/design-system
├── tokens/        (re-exports from @salesos/tokens)
├── components/
│   ├── primitives/    (Button, Input, Badge, Card, etc.)
│   ├── composite/     (DataTable, CommandPalette, etc.)
│   └── layout/        (AppShell, PageHeader, Sidebar, etc.)
├── patterns/      (empty-state, loading, error, data-display)
└── guidelines/

@salesos/ui (Consumer import point)
└── Re-exports from @salesos/design-system
```

### 10.2 Component Inventory

#### Primitives

| Component | Status | Action |
|-----------|--------|--------|
| Button | ✅ Exists | Add icon-only variant, verify RTL |
| Input | ✅ Exists | Add textarea integration |
| Badge | ✅ Exists | Add `info` variant, icon support |
| Card | ⚠️ 3 versions | Unify into single component |
| Tabs | ✅ Exists | Add vertical variant |
| Modal | ✅ Exists | Add size variants |
| Select | ✅ Exists | Add multi-select |
| Tooltip | ✅ Exists | Verify consistency |
| Skeleton | ✅ Exists | Add more shapes |

#### Layout (New)

| Component | Purpose |
|-----------|---------|
| PageHeader | Title + description + actions |
| SectionHeader | Title + count + expand |
| Sidebar | Grouped, collapsible navigation |
| MetricCard | KPI value + trend + sparkline |
| StatCard | Label + value + icon |

### 10.3 Migration Strategy

#### Phase 0-2: Parallel Build
- New tokens and components built in `@salesos/design-system`
- Old code untouched (no breaking changes)
- Both systems coexist

#### Phase 3-4: Gradual Migration
- Old components get deprecation warnings
- Pages migrated one-by-one to new components
- Old + new coexist with clear import paths

#### Phase 5: Hard Cutoff
- Old components removed from exports
- Remaining pages forced to migrate
- ESLint rules enforce token usage

#### Enforcement

```js
// .eslintrc.js
rules: {
  'no-restricted-syntax': ['error', {
    selector: 'Literal[value=/^#[0-9a-fA-F]{6}$/]',
    message: 'Use design tokens instead of raw hex values. See @salesos/tokens.'
  }],
  'no-restricted-properties': ['error', {
    object: 'style',
    property: 'color',
    message: 'Use CSS custom properties from design tokens.'
  }]
}
```

#### CI Check

```yaml
# .github/workflows/design-system.yml
- name: Check for raw values
  run: |
    npx eslint --no-eslintrc -c .eslintrc.design-system.js 'src/**/*.{tsx,ts}'
    if [ $? -ne 0 ]; then
      echo "❌ Raw design values found. Use @salesos/tokens."
      exit 1
    fi
```

---

## 11. Motion & Interaction Guidelines

### 11.1 Duration Scale

| Token | Duration | Use |
|-------|----------|-----|
| `instant` | 0ms | Immediate state changes |
| `fast` | 120ms | Hover, focus, toggles |
| `normal` | 200ms | Panels, dropdowns, tabs |
| `slow` | 300ms | Modals, page transitions |
| `slower` | 500ms | Complex animations |

### 11.2 Easing Curves

| Token | Curve | Use |
|-------|-------|-----|
| `ease-standard` | `cubic-bezier(0.2, 0, 0, 1)` | Default |
| `ease-decelerate` | `cubic-bezier(0, 0, 0, 1)` | Elements entering |
| `ease-accelerate` | `cubic-bezier(0.3, 0, 1, 1)` | Elements leaving |

### 11.3 Interaction States

#### Hover
| Element | Effect |
|---------|--------|
| Button (primary) | `brightness-110` |
| Button (secondary) | `bg-[var(--bg-secondary)]` |
| Card | `shadow-muhide-2` |
| Table row | `bg-[var(--bg-secondary)]` |
| Nav item | Background tint + text shift |

#### Focus
| Element | Effect |
|---------|--------|
| Button | `ring-2 ring-[var(--muhide-orange)] ring-offset-2` |
| Input | `ring-2 ring-[var(--muhide-orange)] border-[var(--muhide-orange)]` |
| All interactive | `focus-visible:outline-none focus-visible:ring-2` |

#### Loading
| Context | Pattern |
|---------|---------|
| Page load | Skeleton matching expected layout |
| Button action | Spinner inside button, disabled |
| Table | Responsive skeleton rows (fill viewport) |

### 11.4 Reduced Motion

All motion respects `prefers-reduced-motion: reduce`:
- Animations: 0ms
- Transitions: 0ms
- Skeleton pulse: disabled
- Slide animations: disabled

---

## 12. Responsive Strategy

### 12.1 Breakpoints

| Name | Width | Target |
|------|-------|--------|
| `sm` | 640px | Large phones |
| `md` | 768px | Tablets portrait |
| `lg` | 1024px | Tablets landscape, small laptops |
| `xl` | 1280px | Desktops |
| `2xl` | 1536px | Large desktops |

### 12.2 Layout Behavior

| Screen | Sidebar | Header | Content |
|--------|---------|--------|---------|
| < 768px | Hidden (bottom tab bar) | Compact (h-12) | Full width |
| 768-1024px | Collapsible (64/256px) | Standard (h-14) | Flex |
| > 1024px | Visible (256px) | Standard (h-14) | Flex |

### 12.3 Mobile Bottom Tab Bar

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

- 5 tabs: Home, Companies, Pipeline, Search, More
- "More" opens full navigation drawer
- Active tab: filled icon + brand color

### 12.4 Component Responsive Behavior

| Component | Desktop | Tablet | Mobile |
|-----------|---------|--------|--------|
| Tables | Full columns | Reduced columns | Card layout |
| Dashboard | 3-4 col grid | 2 col grid | 1 col stack |
| Modals | Centered, max-width | Centered | Full-screen |
| Kanban | Horizontal scroll | Horizontal scroll | Stage selector |
| Side panels | Fixed 384px | Fixed 384px | Full-screen |

---

## 13. Accessibility Standards

### 13.1 Target

**WCAG 2.2 Level AA** compliance. WCAG 2.2 extends 2.1 with additional requirements for cognitive accessibility, focus appearance, and dragging movements — all relevant for enterprise dashboards.

### 13.2 Keyboard Navigation

| Key | Action |
|-----|--------|
| `Tab` | Next interactive element |
| `Shift+Tab` | Previous interactive element |
| `Enter` | Activate focused element |
| `Space` | Toggle checkbox, activate button |
| `Escape` | Close modal/dropdown/panel |
| `Arrow keys` | Navigate within tab list, dropdown, table |
| `Home/End` | First/last item in list |

### 13.3 Focus Management

1. Focus visible on all interactive elements
2. Focus trapped within modals
3. Focus returns to trigger on modal close
4. Focus moves to new content after async load
5. Skip links for main content

### 13.4 ARIA Requirements

| Element | ARIA |
|---------|------|
| Navigation | `role="navigation"`, `aria-label` |
| Modals | `role="dialog"`, `aria-modal="true"` |
| Tables | `aria-sort` on sortable columns |
| Tabs | `role="tablist"`, `aria-selected` |
| Buttons (icon-only) | `aria-label` |
| Loading | `aria-busy="true"`, `role="status"` |
| Errors | `role="alert"`, `aria-live="assertive"` |

### 13.5 Color Contrast

| Combination | Required | Actual |
|-------------|----------|--------|
| Body text on white | 4.5:1 | `#26231E` on `#FFFFFF` = 15.4:1 ✅ |
| Secondary text on white | 4.5:1 | `#706A5D` on `#FFFFFF` = 5.2:1 ✅ |
| Muted text on white | 3:1 | `#8C8374` on `#FFFFFF` = 3.8:1 ✅ |
| Orange button text | 4.5:1 | `#FFFFFF` on `#F57C1E` = 4.6:1 ✅ |
| Orange link text | 4.5:1 | `#D4660F` on `#FFFFFF` = 4.8:1 ✅ |

### 13.6 Accessibility Policy

#### Color Contrast
- All text/bg combinations must meet 4.5:1 (normal text) or 3:1 (large text ≥18px bold)
- Interactive elements must have 3:1 contrast against adjacent colors
- Focus indicators must have 3:1 contrast against background

#### Keyboard Navigation
- All interactive elements must be reachable via Tab
- Focus order must follow visual reading order
- Focus must be visible on all elements (never `outline: none` without replacement)
- Modals must trap focus (Radix Dialog handles this)
- Focus must return to trigger on modal close

#### Screen Readers
- All images must have `alt` text (decorative images use `alt=""`)
- All form inputs must have associated `<label>` elements
- All interactive elements must have accessible names
- Dynamic content changes must use `aria-live` regions
- Tables must have proper `<thead>`, `<th>`, and `aria-sort` attributes

#### Reduced Motion
- All animations must respect `prefers-reduced-motion: reduce`
- No animation should be essential to understanding content
- Skeleton loading pulse must be disabled when reduced motion is active

#### Touch Targets
- Minimum 44x44px for all interactive elements on touch devices
- Minimum spacing between adjacent touch targets: 8px

### 13.7 WCAG 2.2 Specific Requirements

| Criterion | Requirement | Implementation |
|-----------|-------------|----------------|
| **2.4.11 Focus Not Obscured (Minimum)** | Focused element must not be entirely hidden by sticky content | Ensure sticky headers don't cover focused elements |
| **2.4.13 Focus Appearance** | Focus indicator must have minimum area and contrast | Use `ring-2 ring-[var(--muhide-orange)] ring-offset-2` |
| **2.5.7 Dragging Movements** | Drag operations must have single-pointer alternative | Kanban: add "Move to" dropdown alternative to drag |
| **2.5.8 Target Size (Minimum)** | Interactive targets at least 24x24px | Already use 44x44px minimum |
| **3.2.6 Consistent Help** | Help mechanism must be in same relative location | Help link in sidebar, consistent across pages |
| **3.3.7 Redundant Entry** | Don't ask for same information twice in same flow | Pre-fill from previous steps in multi-step forms |

### 13.8 Testing Strategy

| Level | Tool | Frequency | Owner |
|-------|------|-----------|-------|
| **Automated** | ESLint `jsx-a11y` | Every commit | Developer |
| **Automated** | Axe-core in Playwright | Every PR | CI pipeline |
| **Manual** | Keyboard navigation testing | Every phase | QA |
| **Manual** | Screen reader (VoiceOver + NVDA) | Phase 7 full audit | QA + Accessibility specialist |
| **Manual** | Color contrast audit (Chrome DevTools) | Every phase | Designer |
| **Manual** | Touch target verification | Phase 7 | QA |
| **External** | WCAG 2.2 AA audit by specialist | Before GA | External auditor |

---

## 14. RTL-First Policy

### 14.1 Principle

> **RTL-first** means new components are designed to work in both directions from the start, not built LTR and mirrored later.

### 14.2 Existing RTL Infrastructure

The codebase already has:
- 500+ lines of RTL utilities in `globals.css`
- `useTranslation()` hook with `dir` prop
- `useDirection()` for dynamic direction
- Tailwind RTL utility overrides

### 14.3 RTL-First Requirements for New Components

Every new component must:

1. **Use CSS logical properties** instead of physical properties:
   ```
   ✅ margin-inline-start    ❌ margin-left
   ✅ padding-inline-end     ❌ padding-right
   ✅ border-inline-start    ❌ border-left
   ✅ inset-inline-start     ❌ left
   ```

2. **Use Tailwind logical utilities** where available:
   ```
   ✅ ms-3 (margin-start)    ❌ ml-3 (margin-left)
   ✅ pe-4 (padding-end)     ❌ pr-4 (padding-right)
   ✅ start-0                ❌ left-0
   ```

3. **Test in both directions** before merge:
   - Render component in LTR — verify layout
   - Render component in RTL — verify layout is mirrored
   - Verify text alignment, icon placement, spacing

4. **No hardcoded direction** in component code:
   ```
   ❌ style={{ textAlign: 'left' }}
   ✅ style={{ textAlign: 'start' }}
   
   ❌ className="ml-4"
   ✅ className="ms-4"
   ```

### 14.4 RTL Testing Checklist

| Check | LTR | RTL |
|-------|-----|-----|
| Text alignment | Left-aligned | Right-aligned |
| Icon placement | Left of text | Right of text |
| Spacing direction | Left-to-right | Right-to-left |
| Border radius | Standard | Mirrored (if directional) |
| Scroll direction | Left-to-right | Right-to-left |
| Number display | Left-to-right | Left-to-right (numbers don't mirror) |
| Date display | Left-to-right | Locale-appropriate |

### 14.5 CI Enforcement

```yaml
# Playwright RTL test
- name: Test component in RTL
  run: |
    npx playwright test --grep "RTL"
    # Renders each component in dir="rtl" and takes snapshot
    # Compares against LTR snapshot for correct mirroring
```

---

## 15. Performance Budget

### 15.1 Core Web Vitals Targets

| Metric | Target | Current Baseline | Measurement |
|--------|--------|-----------------|-------------|
| **LCP** (Largest Contentful Paint) | < 2.5s | To be measured | Page load on 4G |
| **INP** (Interaction to Next Paint) | < 200ms | To be measured | All interactive elements |
| **CLS** (Cumulative Layout Shift) | < 0.1 | To be measured | Page load stability |
| **FCP** (First Contentful Paint) | < 1.8s | To be measured | Initial render |
| **TTFB** (Time to First Byte) | < 800ms | To be measured | Server response |

### 15.2 Page Load Targets

| Page Type | Load Time (4G) | Load Time (WiFi) |
|-----------|---------------|------------------|
| Dashboard | < 3s | < 1.5s |
| List page (Companies, Employees) | < 2.5s | < 1.2s |
| Detail page (Company 360) | < 3s | < 1.5s |
| Graph visualization | < 4s | < 2s |
| Cold start (first visit) | < 5s | < 3s |

### 15.3 Bundle Size Budget

| Bundle | Max Size (gzipped) | Notes |
|--------|-------------------|-------|
| Total JS | < 500KB | Initial page load |
| First-load JS | < 300KB | Critical path |
| CSS | < 80KB | Tailwind purge + design tokens |
| Fonts | < 100KB | Viga + IBM Plex Sans + Arabic subset |
| Images (initial) | < 200KB | Above-the-fold only |

### 15.4 Interaction Performance

| Interaction | Max Delay | Notes |
|-------------|-----------|-------|
| Button click → visual feedback | < 100ms | `active:scale-[0.98]` + state change |
| Tab switch | < 150ms | Content swap animation |
| Dropdown open | < 100ms | Radix animation |
| Sidebar collapse | < 200ms | Width transition |
| Modal open | < 200ms | Overlay + content |
| Search results | < 300ms | Debounced input |
| Table sort | < 100ms | Client-side sort |
| Kanban drag | < 50ms | Visual feedback |

### 15.5 Data Freshness

| Data Type | Refresh Interval | Method |
|-----------|-----------------|--------|
| KPI metrics | 30 seconds (polling) or real-time (WebSocket) | WebSocket preferred |
| Dashboard widgets | On page load + manual refresh | HTTP |
| Decision Center priorities | 5 minutes | HTTP |
| Activity feed | Real-time | WebSocket |
| Table data | On page load | HTTP |
| Graph visualization | On page load | HTTP |

### 15.6 Performance Gates

Performance budgets are **CI enforcement gates**, not just targets. If a gate fails, the PR cannot merge.

**Budget governance:** Initial values are defined below. These should be reviewed quarterly via a Performance Budget ADR. As the codebase grows, budgets may need adjustment — the ADR process ensures changes are deliberate, not accidental.

| Gate | Initial Threshold | Enforcement |
|------|-------------------|-------------|
| **Bundle size** | Total JS < 500KB gzipped | CI fails if exceeded |
| **First-load JS** | < 300KB gzipped | CI fails if exceeded |
| **Lighthouse Performance** | Score ≥ 80 | CI warning at < 80, fail at < 60 |
| **LCP** | < 2.5s | CI warning at > 2.5s, fail at > 4s |
| **INP** | < 200ms | CI warning at > 200ms, fail at > 500ms |
| **CLS** | < 0.1 | CI fails if exceeded |
| **Unused JS** | < 20% of bundle | CI warning |

```yaml
# .github/workflows/performance-gate.yml
- name: Bundle size check
  run: |
    SIZE=$(gzip -c out/_next/static/chunks/*.js | wc -c)
    LIMIT=512000  # 500KB
    if [ $SIZE -gt $LIMIT ]; then
      echo "❌ Bundle size $(($SIZE/1024))KB exceeds 500KB limit"
      exit 1
    fi
    echo "✅ Bundle size $(($SIZE/1024))KB within budget"

- name: Lighthouse CI
  run: |
    npx lhci autorun --config=lighthouserc.json
    # Fails if Performance score < 80
```

**Override:** If a PR needs to exceed a budget (e.g., new chart library), it requires explicit approval from tech lead + 1-week follow-up to reduce.

### 15.7 Performance Monitoring

| Tool | Purpose | Frequency |
|------|---------|-----------|
| Lighthouse CI | Core Web Vitals check | Every PR |
| Web Vitals library | Real user monitoring | Continuous |
| Custom performance marks | Component render timing | Development |
| Bundle analyzer | Bundle size tracking | Every release |

---

## 16. Design Tokens Governance

### 16.1 Principle

> **All visual values come from `@salesos/tokens`. No exceptions.**

Every color, spacing value, font size, shadow, border-radius, and animation duration must originate from the token package. Hard-coded values are forbidden in production code.

### 16.2 Token Categories

| Category | Source | Examples |
|----------|--------|---------|
| **Colors** | `@salesos/tokens/colors` | `brand.orange`, `status.success`, `neutral.600` |
| **Typography** | `@salesos/tokens/typography` | `fontFamily.display`, `fontSize.base`, `fontWeight.semibold` |
| **Spacing** | `@salesos/tokens/spacing` | `space.1` (4px) through `space.16` (64px) |
| **Elevation** | `@salesos/tokens/elevation` | `elevation.1` through `elevation.6` |
| **Motion** | `@salesos/tokens/motion` | `duration.fast`, `easeStandard` |
| **Radius** | `@salesos/tokens/radius` | `radius.sm` through `radius.full` |
| **Z-index** | `@salesos/tokens/zIndex` | `z.dropdown`, `z.modal`, `z.toast` |

### 16.3 Enforcement Mechanisms

#### ESLint Rules

```js
// .eslintrc.design-system.js
module.exports = {
  rules: {
    // Forbid raw hex values in JSX
    'no-restricted-syntax': ['error', {
      selector: 'Literal[value=/^#[0-9a-fA-F]{3,8}$/]',
      message: 'Use design tokens. Import from @salesos/tokens. See: docs/tokens.md'
    }],
    
    // Forbid inline style with raw values
    'no-restricted-properties': ['error', {
      object: 'style',
      property: 'color',
      message: 'Use CSS custom properties from tokens.'
    }],
    
    // Forbid Tailwind arbitrary values for design properties
    'tailwindcss/no-arbitrary-value': ['error', {
      allow: ['z-index', 'opacity'] // exceptions
    }]
  }
}
```

#### CI Pipeline Check

```yaml
# .github/workflows/design-system-lint.yml
name: Design System Compliance
on: [pull_request]
jobs:
  token-compliance:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
      - run: npm ci
      - name: Check for raw design values
        run: |
          npx eslint --no-eslintrc \
            -c .eslintrc.design-system.js \
            'src/**/*.{tsx,ts}' \
            'packages/**/*.{tsx,ts}'
      - name: Check token imports
        run: |
          # Verify no component imports colors directly from hex
          if grep -rn "color: '#\|color: \"" src/ packages/ --include="*.tsx" --include="*.ts"; then
            echo "❌ Raw color values found. Use @salesos/tokens."
            exit 1
          fi
```

#### Visual Regression Testing

```yaml
# Playwright visual regression
- name: Visual regression check
  run: |
    npx playwright test --grep "visual"
    # Compares screenshots against baseline
    # Catches unintentional color/spacing/shadow changes
```

### 16.4 Migration Checklist

For each component/page being migrated:

- [ ] Remove all raw hex values → replace with token imports
- [ ] Remove all raw pixel values → replace with `space.*` tokens
- [ ] Remove all raw shadow values → replace with `elevation.*` tokens
- [ ] Remove all raw font-size values → replace with `fontSize.*` tokens
- [ ] Remove all raw border-radius values → replace with `radius.*` tokens
- [ ] Verify component renders correctly in LTR and RTL
- [ ] Verify component renders correctly in light and dark mode
- [ ] Run ESLint design system check → 0 errors
- [ ] Visual regression test passes

### 16.5 Deprecation Path

| Phase | Action | Timeline |
|-------|--------|----------|
| Phase 0-2 | Build new token system in parallel | Weeks 1-9 |
| Phase 3 | Deprecation warnings on old component imports | Week 10 |
| Phase 4 | ESLint warnings (non-blocking) on raw values | Week 14 |
| Phase 5 | ESLint errors (blocking) on raw values | Week 19 |
| Phase 6 | Remove old component exports | Week 23 |

---

## 17. UX Acceptance Criteria

### 17.1 Dashboard

| Criterion | Target | Measurement | Automated/Manual |
|-----------|--------|-------------|-----------------|
| Time to first meaningful paint | < 3s | Lighthouse | Automated |
| Time to executive brief (scan KPIs) | < 10s | User test | Manual |
| Task: "Find deals at risk" | < 15s (2 clicks) | User test | Manual |
| Task: "Check team performance" | < 10s (1 click) | User test | Manual |
| Task: "See revenue trend" | < 5s (visible on load) | User test | Manual |
| Empty state: "No data" | Shown when API returns empty | Automated test | Automated |
| Error state: "Failed to load" | Shown when API fails + retry button | Automated test | Automated |

### 17.2 Company List

| Criterion | Target | Measurement | Automated/Manual |
|-----------|--------|-------------|-----------------|
| Time to find a company | < 5s with search | User test | Manual |
| Task: "Create a new company" | < 30s (modal flow) | User test | Manual |
| Task: "Filter by industry" | < 3s (1 click + select) | User test | Manual |
| Task: "View company details" | < 3s (1 click) | User test | Manual |
| Pagination: navigate to page 5 | < 5s (2 clicks) | User test | Manual |
| Responsive: card layout on mobile | Automatic at < 640px | Automated test | Automated |

### 17.3 Company 360

| Criterion | Target | Measurement | Automated/Manual |
|-----------|--------|-------------|-----------------|
| Time to health score | < 2s (visible on load) | Automated | Automated |
| Time to AI recommendation | < 3s (visible on load) | Automated | Automated |
| Task: "View all contacts" | < 5s (1 click to People tab) | User test | Manual |
| Task: "See active deals" | < 5s (1 click to Deal Room) | User test | Manual |
| Task: "Log an activity" | < 15s (Quick Action) | User test | Manual |
| Task: "View relationship graph" | < 5s (1 click to More > Graph) | User test | Manual |
| Tab switching | < 200ms per switch | Automated | Automated |

### 17.4 Employee 360

| Criterion | Target | Measurement | Automated/Manual |
|-----------|--------|-------------|-----------------|
| Time to score breakdown | < 2s (visible on load) | Automated | Automated |
| Task: "Check quota attainment" | < 5s (1 click to Performance) | User test | Manual |
| Task: "See activity history" | < 5s (1 click to Activity) | User test | Manual |
| Task: "Compare to team" | < 5s (Score card shows comparison) | User test | Manual |
| Score trend chart renders | < 1s | Automated | Automated |

### 17.5 Pipeline Kanban

| Criterion | Target | Measurement | Automated/Manual |
|-----------|--------|-------------|-----------------|
| Drag and drop | < 50ms visual feedback | Automated | Automated |
| Task: "Move deal to next stage" | < 3s (drag or dropdown) | User test | Manual |
| Task: "Close deal as won" | < 10s (drag to Won + confirm) | User test | Manual |
| Column count updates | < 100ms | Automated | Automated |
| Mobile: stage selector works | Tap to switch stages | Manual test | Manual |

### 17.6 Command Palette

| Criterion | Target | Measurement | Automated/Manual |
|-----------|--------|-------------|-----------------|
| Open (Cmd+K) | < 100ms | Automated | Automated |
| Search results appear | < 300ms | Automated | Automated |
| Task: "Navigate to Companies" | < 5s (Cmd+K + type + Enter) | User test | Manual |
| Task: "Find Acme Corp" | < 5s (Cmd+K + type + select) | User test | Manual |
| Task: "Create new opportunity" | < 10s (Cmd+K + action) | User test | Manual |

### 17.7 Accessibility

| Criterion | Target | Measurement | Automated/Manual |
|-----------|--------|-------------|-----------------|
| Keyboard navigation | All pages navigable via keyboard only | Manual test | Manual |
| Screen reader | All content announced correctly | VoiceOver + NVDA test | Manual |
| Focus visible | All interactive elements have visible focus | Automated + manual | Both |
| Color contrast | All text ≥ 4.5:1, all large text ≥ 3:1 | Automated audit | Automated |
| Touch targets | All targets ≥ 44x44px | Automated | Automated |
| Reduced motion | All animations disabled when preference set | Manual test | Manual |

### 17.8 RTL

| Criterion | Target | Measurement | Automated/Manual |
|-----------|--------|-------------|-----------------|
| Layout mirroring | All layouts mirror correctly in RTL | Automated snapshot | Automated |
| Text alignment | All text right-aligned in RTL | Automated | Automated |
| Icon placement | All icons mirror position in RTL | Automated snapshot | Automated |
| Spacing direction | All spacing flips direction in RTL | Automated snapshot | Automated |
| Number display | Numbers remain LTR in RTL context | Manual test | Manual |

---

## 18. Implementation Roadmap

### 18.1 Timeline

**Plan: 32 weeks (8 months).** This includes build, QA, design review, and risk buffer for each phase.

**Optimistic minimum: 27 weeks.** Achievable only with ideal conditions: full-time dedicated team, no scope changes, no external blockers, fast approval cycles.

```
Plan (32 weeks):
├── Phase 0: Token Foundation + RTL     3 weeks
├── Phase 1: Navigation Restructure     3 weeks
├── Phase 2: Component Standardization  3 weeks
├── Phase 3: Dashboard Evolution        4 weeks
├── Phase 4: Company 360 Redesign       3 weeks
├── Phase 5: Employee 360 Redesign      3 weeks
├── Phase 6: AI Contextual Insights     4 weeks
├── Phase 7: Accessibility & Polish     3 weeks
└── Buffer: Risk + QA                   4 weeks  ← Included in plan
                                        ═══════
                                        32 weeks
```

### 18.2 Detailed Timeline Breakdown

| Phase | Build | Test/QA | Design Review | Buffer | Total |
|-------|-------|---------|---------------|--------|-------|
| Phase 0 | 1.5 weeks | 0.5 week | 0.5 week | 0.5 week | **3 weeks** |
| Phase 1 | 1.5 weeks | 0.5 week | 0.5 week | 0.5 week | **3 weeks** |
| Phase 2 | 1.5 weeks | 0.5 week | 0.5 week | 0.5 week | **3 weeks** |
| Phase 3 | 2 weeks | 1 week | 0.5 week | 0.5 week | **4 weeks** |
| Phase 4 | 1.5 weeks | 0.5 week | 0.5 week | 0.5 week | **3 weeks** |
| Phase 5 | 1.5 weeks | 0.5 week | 0.5 week | 0.5 week | **3 weeks** |
| Phase 6 | 2 weeks | 1 week | 0.5 week | 0.5 week | **4 weeks** |
| Phase 7 | 1.5 weeks | 1 week | 0.5 week | 0 | **3 weeks** |
| **Global Buffer** | — | 2 weeks | — | 2 weeks | **4 weeks** |
| **TOTAL** | **13 weeks** | **6 weeks** | **4 weeks** | **5 weeks** | **32 weeks** |

### 18.3 Phase 0: Token Foundation + RTL (Week 1-3)

**Goal:** Single source of truth for all design values. RTL-first foundation.

| Task | Output | Days |
|------|--------|------|
| Create `@salesos/tokens` package | All token files | 3 |
| Update `tailwind.config.ts` | Import from tokens | 1 |
| Update `globals.css` | CSS vars from tokens | 1 |
| Fix orange contrast (DD-011) | ADR-011 implementation | 1 |
| RTL-first component example | Button in LTR + RTL verified | 1 |
| Design review + approval | Sign-off on token values | 2 |
| **Phase 0 QA** | Token consistency check | 1 |

**Deliverable:** Token system, RTL-first policy enforced, orange contrast fixed.

### 18.4 Phase 1: Navigation Restructure (Week 4-6)

**Goal:** Grouped, collapsible, role-aware navigation.

| Task | Output | Days |
|------|--------|------|
| Workspace validation prototype | Interactive prototype | 2 |
| User test (3-5 users) | Decision: proceed/modify/fallback | 2 |
| Build grouped Sidebar component | Collapsible sections | 3 |
| Add breadcrumbs to deep pages | Consistent pattern | 2 |
| Build PageHeader component | Standardized header | 1 |
| **Phase 1 QA** | Navigation flow testing | 2 |

**Deliverable:** Navigation that scales to 50+ modules.

### 18.5 Phase 2: Component Standardization (Week 7-9)

**Goal:** Eliminate duplication, establish consistent patterns.

| Task | Output | Days |
|------|--------|------|
| Unify Card component | Single Card with variants | 2 |
| Standardize buttons to `<Button>` | Replace raw elements | 2 |
| Build MetricCard, StatCard | Reusable KPI components | 2 |
| Build SectionHeader | Title + count + expand | 1 |
| Standardize empty/loading/error states | Consistent patterns | 2 |
| **Phase 2 QA** | Component consistency audit | 2 |

**Deliverable:** One way to do each thing.

### 18.6 Phase 3: Dashboard Evolution (Week 10-13)

**Goal:** Executive morning brief.

| Task | Output | Days |
|------|--------|------|
| Build MorningBriefHeader | Greeting + timestamp | 2 |
| Build KPISummaryBar | 4 metrics with trends | 2 |
| Build TodaysPriorities | Decision Center integration | 3 |
| Build PipelineHealthChart | Stage breakdown | 2 |
| Build TeamPerformanceLeaderboard | Top reps | 2 |
| Dashboard personalization | Widget reorder/hide | 3 |
| **Phase 3 QA** | Dashboard flow testing | 2 |

**Deliverable:** Dashboard executives check daily.

### 18.7 Phase 4: Company 360 Redesign (Week 14-16)

**Goal:** Single pane of glass.

| Task | Output | Days |
|------|--------|------|
| Redesign tab structure | 5 tabs (not 8) | 2 |
| Build CompanyDNA component | Profile summary | 2 |
| Build BuyingJourney component | Visual progress | 2 |
| Build AIRecommendation card | Next best action | 2 |
| Build QuickActions bar | Context-aware actions | 2 |
| **Phase 3 QA** | Company 360 flow testing | 2 |

**Deliverable:** Everything about a company in one screen.

### 18.8 Phase 5: Employee 360 Redesign (Week 17-19)

**Goal:** Performance coaching tool.

| Task | Output | Days |
|------|--------|------|
| Decompose 1122-line employee list | Separate components | 3 |
| Build ScoreTrendChart | Sparkline + history | 2 |
| Build CoachingInsightCard | AI suggestions | 2 |
| Build TeamComparison | vs. team average | 2 |
| **Phase 5 QA** | Employee flow testing | 2 |

**Deliverable:** Tool managers use for coaching.

### 18.9 Phase 6: AI Contextual Insights (Week 20-23)

**Goal:** AI appears where relevant.

| Task | Output | Days |
|------|--------|------|
| Build Copilot sidebar | Floating AI panel | 3 |
| Add AI insights to Company 360 | Recommendations | 2 |
| Add AI insights to Employee 360 | Coaching suggestions | 2 |
| Add AI badges to lists | Anomaly indicators | 2 |
| Rebuild AI page | End-user prompt builder | 3 |
| **Phase 6 QA** | AI flow testing | 2 |

**Deliverable:** Contextual AI with full transparency.

### 18.10 Phase 7: Accessibility & Polish (Week 24-26)

**Goal:** WCAG 2.1 AA compliance.

| Task | Output | Days |
|------|--------|------|
| Keyboard navigation | All components | 3 |
| ARIA labels | All interactive elements | 2 |
| Skip links | Main content | 1 |
| Color contrast audit | All combinations | 1 |
| Screen reader testing | VoiceOver + NVDA | 2 |
| **Phase 7 QA** | Full accessibility audit | 3 |

**Deliverable:** Enterprise-grade accessibility.

### 18.11 Buffer (Week 27-32)

Reserved for:
- Bug fixes from QA cycles
- Design iteration based on feedback
- Approval delays
- Unexpected technical challenges
- Deployment and rollback preparation

---

## Appendix: File Changes

### Files to Modify

| File | Phase | Action |
|------|-------|--------|
| `packages/tokens/` | 0 | Complete rebuild |
| `packages/design-system/src/tokens.ts` | 0 | Replace with token imports |
| `packages/ui/src/card.tsx` | 2 | Unify with foundation/card |
| `packages/ui/src/button.tsx` | 2 | Add icon-only variant |
| `tailwind.config.ts` | 0 | Import from tokens |
| `src/app/globals.css` | 0 | Generate from tokens |
| `src/app/(dashboard)/layout.tsx` | 1 | Grouped sidebar |
| `src/components/foundation/MobileNav.tsx` | 1 | Bottom tab bar |
| `src/components/foundation/card.tsx` | 2 | Remove (merge) |
| `src/app/(dashboard)/dashboard/page.tsx` | 3 | Executive brief |
| `src/app/(dashboard)/companies/[id]/360/page.tsx` | 4 | 5-tab redesign |
| `src/app/(dashboard)/employees/page.tsx` | 5 | Decompose |
| `src/components/copilot-panel.tsx` | 6 | AI sidebar |

### Files to Create

| File | Phase | Purpose |
|------|-------|---------|
| `packages/tokens/src/colors.ts` | 0 | Color tokens |
| `packages/tokens/src/typography.ts` | 0 | Typography tokens |
| `packages/tokens/src/spacing.ts` | 0 | Spacing tokens |
| `packages/tokens/src/elevation.ts` | 0 | Elevation tokens |
| `packages/tokens/src/motion.ts` | 0 | Motion tokens |
| `packages/tokens/src/radius.ts` | 0 | Radius tokens |
| `packages/design-system/src/layout/PageHeader.tsx` | 1 | Page header |
| `packages/design-system/src/layout/SectionHeader.tsx` | 1 | Section header |
| `packages/design-system/src/layout/Sidebar.tsx` | 1 | Grouped sidebar |
| `packages/design-system/src/primitives/MetricCard.tsx` | 2 | KPI card |
| `packages/design-system/src/primitives/StatCard.tsx` | 2 | Stat card |
| `packages/design-system/src/patterns/MorningBrief.tsx` | 3 | Dashboard brief |
| `packages/design-system/src/patterns/TodaysPriorities.tsx` | 3 | Priority list |
| `packages/design-system/src/patterns/CoachingInsight.tsx` | 5 | AI coaching |

---

## Appendix: Design Decision Matrix

| # | Decision | Rationale | Alternatives Considered | Why Rejected |
|---|----------|-----------|------------------------|--------------|
| DD-01 | Preserve warm neutral palette | Brand differentiation from blue-gray SaaS | Switch to standard blue-gray | Loses brand identity, no differentiation |
| DD-02 | Workspace-based navigation | Role-based cognitive load reduction | Flat grouped sidebar, mega-menu | Flat sidebar doesn't scale to 50+; mega-menu is desktop-only |
| DD-03 | 4px spacing base | Consistent with existing Tailwind config | 8px base, 6px base | 4px allows finer control; 8px too coarse; 6px breaks existing |
| DD-04 | Radix UI primitives | Already in use, accessible by default | Headless UI, custom primitives | Radix already adopted; switching costs > benefits |
| DD-05 | CVA for variants | Already in use, type-safe | Stitches, vanilla-extract | CVA already adopted; switching costs > benefits |
| DD-06 | Bottom tab bar for mobile | Enterprise standard (Salesforce, HubSpot) | FAB (current), hamburger menu | FAB non-standard for enterprise; hamburger hides navigation |
| DD-07 | WCAG 2.2 AA target | Enterprise procurement requirement | WCAG 2.1 AA, WCAG 2.2 AAA | 2.1 lacks 2.2 cognitive features; AAA too strict for timeline |
| DD-08 | AI always shows reasoning | Trust requires transparency | Black-box AI, confidence only | Black-box kills trust; confidence without reasoning is meaningless |
| DD-09 | No breaking URL changes | Existing integrations and bookmarks | URL restructure | Breaks integrations, bookmarks, SEO, customer workflows |
| DD-10 | 5 tabs for Company 360 | "At a glance" principle | 8 tabs (original), 3 tabs | 8 too many; 3 insufficient for data density |
| DD-011 | Orange `#F57C1E` not for text | WCAG 2.8:1 fails 4.5:1 minimum | Darker orange (#D4660F), keep as-is | Darker orange works for text; keep original for brand/bg |
| DD-012 | Workspace validated via prototype | Pattern proven in multiple SaaS products | Full 2-week user research | Research is overkill for proven pattern; prototype sufficient |
| DD-013 | AI Governance separate doc | Legal/compliance scope too large for UX vision | Embed in UX Vision | Mixes concerns; AI policy needs legal review |
| DD-014 | RTL-first for new components | Consistency enforcement from day one | LTR-first + retrofit | Retrofit is 3-5x more expensive; proven by audit findings |
| DD-015 | Design system enforced via linting | Unenforceable rules lead to dual systems | Convention-only, manual reviews | Convention breaks down at scale; CI enforcement is reliable |
| DD-016 | 12 product concepts rejected | Scope boundary — UX vision ≠ product bible | Include in UX Vision | Revenue Recognition, Territory, Compliance = separate PRDs |
| DD-017 | Timeline: 32 weeks (plan), 27 weeks (optimistic) | Realistic with buffer for QA + iteration | 26 too aggressive; 36 too conservative; 32 with buffer is balanced |

---

## Appendix: Design Decisions Log

| # | Decision | Rationale | Date |
|---|----------|-----------|------|
| DD-01 | Preserve warm neutral palette | Brand differentiation | 2026-08-05 |
| DD-02 | Workspace-based navigation | Reduces cognitive load by role | 2026-08-05 |
| DD-03 | 4px spacing base | Consistent with Tailwind config | 2026-08-05 |
| DD-04 | Radix UI primitives | Already in use, accessible | 2026-08-05 |
| DD-05 | CVA for variants | Already in use, type-safe | 2026-08-05 |
| DD-06 | Bottom tab bar for mobile | Enterprise standard | 2026-08-05 |
| DD-07 | WCAG 2.2 AA target | Enterprise procurement + cognitive accessibility | 2026-08-05 |
| DD-08 | AI always shows reasoning | Trust requires transparency | 2026-08-05 |
| DD-09 | No breaking URL changes | Existing integrations | 2026-08-05 |
| DD-10 | 5 tabs for Company 360 | "At a glance" principle | 2026-08-05 |
| DD-011 | Orange `#F57C1E` not for text | WCAG 2.8:1 fails 4.5:1 | 2026-08-05 |
| DD-012 | Workspace validated via prototype | Pattern proven, not novel | 2026-08-05 |
| DD-013 | AI Governance separate doc | Legal/compliance scope | 2026-08-05 |
| DD-014 | RTL-first for new components | Consistency enforcement | 2026-08-05 |
| DD-015 | Design system enforced via linting | Unenforceable rules fail | 2026-08-05 |
| DD-016 | 12 product concepts rejected | Scope boundary | 2026-08-05 |
| DD-017 | Timeline: 32 weeks (plan), 27 weeks (optimistic) | Realistic with buffer | 2026-08-05 |

---

*This is the approved implementation blueprint. Phase 0 begins after stakeholder sign-off on DD-011 (orange contrast resolution) and DD-013 (AI Governance document).*
