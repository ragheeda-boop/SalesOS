# ADR-022: Widget-Driven Experience Architecture (XP1)

**Status:** Accepted  
**Date:** 2026-06-30  
**Deciders:** CTO, Platform Team  
**Tags:** architecture, experience-layer, widgets, composable-ui

## Context

With RT0 (Kernel → Runtime → Data Fabric → Search → KG → Decision Engine) and RT0.5 (Capability Framework + UBOM) complete, we need to build the Experience Layer (XP1).

Traditional approach: build Company360, Deal360, Contact360 as hand-crafted pages. This is rejected because:

1. Every 360 view shares the same structure (Object → Viewer → Layout → Widgets)
2. The Capability Registry already declares what each entity can do
3. Widgets enable Marketplace extensibility
4. Users need customizable layouts (drag & drop)
5. Pages duplicate effort — Object Viewer generics solve all 360s at once

## Decision

Adopt **Widget-Driven Experience Architecture**. Key tenets:

### 1. No Pages, Only Object Viewers

- Company360, Deal360, Contact360 are all instances of **Universal Object Viewer**
- The Viewer reads the entity type → queries Capability Registry for applicable capabilities → generates tabs as Widget instances
- Widgets provide their own UI, API bindings, permissions, events, and configuration

### 2. Widget Engine

Every UI surface is a Widget:

```
Widget
├── id, name, description, version
├── capability_id (backlink to Capability Registry)
├── permissions_required[]
├── apis_used[]
├── events_subscribed[]
├── configuration_schema (JSON Schema)
├── slots (which zones the widget can occupy)
├── size_hints (min/max/default)
└── renderer (frontend component reference)
```

Widgets are registered at startup from Capability Registry + custom widgets.

### 3. Layout Runtime

Users can customize:

- Which widgets appear on their Object Viewer
- Position (zone: left/right/center/top/bottom)
- Size
- Visibility (per role/permission)

Layouts are persisted per-user, per-entity-type, per-tenant.

### 4. Design Token System

Before any widget, establish the design foundation:

```
Brand
└── Design Tokens
    ├── colors (primary, neutral, semantic, chart)
    ├── typography (family, scale, weight, line-height)
    ├── radius (none, sm, md, lg, full)
    ├── elevation (shadows: sm, md, lg, xl)
    ├── spacing (4, 8, 12, 16, 24, 32, 48, 64px)
    ├── icons (library reference + naming convention)
    ├── motion (easing, duration, transitions)
    └── breakpoints (sm, md, lg, xl)
```

Per-tenant theming via token overrides.

### 5. UX Runtime

Six runtime components:

| Runtime | Responsibility |
|---------|---------------|
| Navigation Runtime | Sidebar, breadcrumbs, route discovery from Capability Registry |
| Layout Runtime | Widget canvas, zones, drag-drop, per-user persistence |
| Widget Runtime | Widget lifecycle (load → render → destroy), state management |
| Theme Runtime | Design token resolution, tenant overrides, dark/light mode |
| Command Runtime | Global Ctrl+K, action registry, command palette |
| Notification Runtime | In-app notifications, toast, badge counts |

### 6. AI Copilot (Context-Aware)

Not a chat window. The Copilot knows:

- Current object context (e.g., which Company is being viewed)
- Timeline, Graph, Features, Decisions, Meetings, Emails
- Answers questions and suggests actions based on that context

## Consequences

### Positive
1. **Zero new page development** — every new entity type gets a 360 view automatically
2. **Marketplace-ready** — anyone can build and sell Widgets using the Widget SDK
3. **User customization** — every user tailors their workspace (adopts Linear/Notion model)
4. **Consistent experience** — all 360 views share layout, navigation, search, command bar
5. **AI everywhere** — every widget can declare AI context, Copilot uses it

### Negative
1. Higher initial complexity for Company360 (must build the engine first)
2. Requires frontend architecture capable of dynamic widget loading
3. Layout persistence needs database migration

### Compliance Check

- [x] Company360 generated from Capability Registry, not hand-coded
- [x] No page components — only Widgets
- [x] Layout customizable per user
- [x] Widget SDK enables third-party development
- [x] AI Copilot context-aware (not generic chat)
- [x] Design tokens make theming systematic
