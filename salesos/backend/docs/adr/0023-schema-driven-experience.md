# ADR-023: Schema-Driven Experience Architecture

**Status:** Accepted  
**Date:** 2026-06-30  
**Deciders:** CTO, Platform Team  
**Tags:** architecture, experience-layer, schema, sdk, composable-ui

## Context

With XP1 approaching, we face a critical architectural choice:

- **Option A**: Build React components for Company360, Deal360, Contact360 directly
- **Option B**: Define a UI Schema language → build a Renderer → generate all 360 views from JSON

Option A is faster for the first view but requires rebuilding for every new entity, every custom layout, and every Marketplace widget.

Option B is the platform approach: one Renderer, infinite views.

We choose Option B.

## Decision

Adopt **Schema-Driven Experience Architecture**. The entire UI is defined as JSON schemas — no hardcoded pages, no hardcoded forms, no hardcoded actions.

### Architecture

```
Schema
  │
  ▼
Schema Engine (parses, validates, resolves)
  │
  ├── UI Schema  →  Layout Renderer  →  Screen
  ├── Form Schema →  Form Engine      →  Dynamic Form
  ├── Action Schema → Action Engine   →  Button → Action
  ├── Command Schema → Command Registry → Ctrl+K
  └── Policy Schema → UI Policy Engine → Show/Hide
```

### Principles

1. **Zero hardcoded pages** — every screen is a JSON `UISchema`
2. **Zero hardcoded forms** — every form is a JSON `FormSchema`
3. **Zero hardcoded actions** — every button is an `Action` from `ActionRegistry`
4. **Zero hardcoded commands** — every Ctrl+K command comes from `CommandRegistry`
5. **Zero hardcoded policies** — every show/hide/disable is a `UIPolicy`
6. **Everything is an SDK** — frontend, backend, widget, agent, plugin, integration, theme

### Platform SDK Structure

```
sdk/
├── frontend_sdk/   — UI Schema types, Action client, Command palette, Theme consumer
├── backend_sdk/    — Runtime client, Entity client, Query builder
├── widget_sdk/     — WidgetDefinition builder, Slot resolver, Permission checker
├── agent_sdk/      — AI agent builder, Context collector, Action executor
├── plugin_sdk/     — Extension hook registration, Sandbox config, Manifest
├── integration_sdk/ — Webhook builder, API client, Auth handler
└── theme_sdk/      — Token builder, CSS generator, Dark mode resolver
```

### UISchema

```json
{
  "$schema": "https://salesos.ai/schemas/ui-v1.json",
  "view": "object-viewer",
  "entity_type": "company",
  "layout": {
    "zones": ["top", "left", "center", "right", "bottom"],
    "defaults": { "left": ["ai_copilot"], "center": ["overview", "timeline"] }
  },
  "widgets": [
    {
      "id": "overview",
      "renderer": "OverviewWidget",
      "permissions": ["company.read"],
      "config": {}
    }
  ],
  "policies": [
    { "effect": "hide", "widget": "revenue", "role": "sdr" }
  ],
  "commands": [],
  "ai_context": { "entity_types": ["company", "contact"] }
}
```

### Action Schema

```json
{
  "id": "create-company",
  "label": "Create Company",
  "icon": "building",
  "handler": "company.create",
  "schema": { "type": "object", "properties": { "cr": { "type": "string" } } },
  "policies": [{ "effect": "disable", "condition": "!user.can('company.write')" }]
}
```

### Extension Hooks

```
BeforeCompanyCreated  →  Validate, Enrich
AfterCompanyCreated   →  Notify, Index, Sync
BeforeDecision        →  CheckPolicy, Log
AfterDecision         →  Execute, Notify
BeforeSearch          →  FilterByTenant
AfterSearch           →  EnrichResults
BeforeWidgetRender    →  CheckPermissions
AfterWidgetRender     →  TrackView
```

### Plugin Sandbox

Every plugin runs in a sandbox with:
- Limited API access (declared in manifest)
- No direct DB access
- Hook-based (not override-based)
- Resource limits (calls/sec, memory)
- Isolated storage

## Consequences

### Positive
1. **Company360 is a JSON config**, not a page — deploy without rebuilding
2. **Marketplace plugins are JSON + isolated code** — safe, versioned, auditable
3. **Forms are instant** — define schema, get form
4. **Actions are declarative** — no onClick spaghetti
5. **UI Policies without redeployment** — RBAC changes propagate instantly
6. **AI understands every widget** — schema exposes context

### Negative
1. Higher initial investment before first visible UI
2. Requires Schema Renderer (need to build it)
3. Schema versioning complexity

### Compliance

- [x] Company360 is JSON, not JSX
- [x] Marketplace widgets are pluggable without rebuild
- [x] Forms are schema-generated
- [x] Actions are registered, not hardcoded
- [x] UI policies are data, not code
- [x] Everything is an SDK
- [x] Plugins are sandboxed
- [x] Extension hooks for every major flow
