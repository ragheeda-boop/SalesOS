# ADR-024: Product Layer Freeze — SalesOS Blueprint V5.0

**Status:** Accepted  
**Date:** 2026-06-30  
**Deciders:** CTO, Platform Team  
**Tags:** architecture, product-layer, frontend, freeze

## Context

The platform has reached **Critical Mass**:
- 14 layers frozen (Kernel, Runtime, SDK, UX Runtime, Capability Framework, UBOM, Widget Engine, Schema UI, Decision Engine, Data Fabric, Knowledge Graph, Timeline, Search, Plugin Platform)
- 7 SDK packages (frontend, backend, widget, agent, plugin, integration, theme)
- 5 runtime engines (UI Schema, Form, Action, Extension, Plugin Sandbox)
- 33 hook points
- ADR-021 through ADR-023 ratified

No new Kernel or Runtime work. All development from this point is **Product Layer**.

## Decision

### 1. Everything Frozen

| Layer | Status | Changes |
|-------|--------|---------|
| Kernel | 🔒 Frozen | ADR required |
| Platform Runtime | 🔒 Frozen | ADR required |
| SDKs | 🔒 Frozen | ADR required |
| Capability Framework | 🔒 Frozen | ADR required |
| Widget Engine | 🔒 Frozen | ADR required |
| Schema UI | 🔒 Frozen | ADR required |

### 2. New Development is Only:

- **Applications** (Company Workspace, Deal Workspace, etc.)
- **Capabilities** (new business features)
- **Widgets** (new UI surfaces)
- **Business Logic** (domain-specific)

### 3. Frontend Architecture

```
@salesos/
  ├── ui/          — Design System components
  ├── icons/       — Icon library
  ├── charts/      — Chart components
  ├── forms/       — Form components (Schema-driven)
  ├── runtime/     — Frontend Runtime (State, Session, Realtime, etc.)
  ├── renderer/    — UISchema → React renderer
  └── hooks/       — Shared React hooks

apps/
  ├── company-workspace/
  ├── deal-workspace/
  ├── contact-workspace/
  ├── search/
  ├── command-center/
  ├── copilot/
  ├── marketplace/
  ├── admin/
  └── settings/
```

### 4. Architecture Mandates

- **Everything is Runtime-Driven** — UI, AI, Workflows, Permissions, Navigation, Commands, Widgets, Search all read from Runtime, not React
- **React is a Renderer**, not the architecture — Schema comes first, React renders it
- **Capability-First** — every feature is a Capability with spec, APIs, events, permissions, widgets, search, timeline, AI context, tests, docs, observability
- **Workspaces, not Pages** — Company360 is a Workspace, not a Page

### 5. New Frontend Runtimes

| Runtime | Responsibility |
|---------|---------------|
| State Runtime | Entity State, UI State, Workflow State, Agent State, Session State, Search State |
| Session Runtime | Search history, open tabs, filters, AI context, drafts, widget configs |
| Realtime Runtime | WebSocket, SSE, Events, Presence, Live Notifications |
| Cache Runtime | Browser Cache → Edge → Redis → Database |
| Rendering Runtime | Server Components, Client Components, Streaming, Suspense patterns |
| Accessibility Runtime | ARIA, keyboard nav, screen reader, focus management (from day one) |
| Localization Runtime | RTL, LTR, Arabic-first, pluralization, regional formats, calendars |
| Collaboration Runtime | Presence, cursors, locks, comments, mentions (Notion-like) |
| Offline Engine | Service Worker, IndexedDB, sync queue (architecture only) |

### 6. Design System Packages

Independent packages, not built inside the monolith:
- `@salesos/ui` — Button, Card, Modal, Dropdown, Input, Select, Table, Tabs, Sidebar, Layout
- `@salesos/icons` — All icons as React components (Lucide-based)
- `@salesos/charts` — Chart components (Line, Bar, Pie, Donut, Funnel, Scorecard)
- `@salesos/forms` — Form engine consumer (render form schemas as React forms)

## Consequences

### Positive
1. Platform is complete — all future work delivers visible customer value
2. Workspace architecture means infinite scalability (HR, Finance, Procurement later)
3. Schema-driven means AI can generate new views without code
4. Independent packages mean Marketplace plugins are first-class citizens
5. Runtime-driven means frontend is a thin rendering layer, not a monolith

### Negative
1. High initial frontend investment before Company Workspace is usable
2. Frontend Runtime must be built before any application
3. Team must shift from Python/backend to TypeScript/frontend mindset

### Compliance

- [x] No Kernel/Runtime changes without ADR
- [x] Everything is Runtime-Driven
- [x] React is a Renderer, not the architecture
- [x] Workspaces are not Pages
- [x] Design System is independent packages
- [x] Every capability includes spec, APIs, events, permissions, widgets, search, timeline, AI, tests, docs
