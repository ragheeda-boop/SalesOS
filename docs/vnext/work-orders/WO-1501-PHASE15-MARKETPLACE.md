# Work Order WO-1501 — Phase 15: Marketplace

> **Issued by**: SalesOS Engineering OS
> **Date**: 2026-07-16
> **Status**: Active
> **Dependency**: Phase 1 ✅, Phase 2 ✅
> **Priority**: P1

---

## Scope

Plugin system: registry, manifest, lifecycle, marketplace UI, sandboxing, 2+ internal plugins.

## Tasks

### Backend

| # | Task | Effort |
|---|------|--------|
| B-1 | **Plugin registry** — manifest validation (name, version, hooks, permissions), install/uninstall | 2d |
| B-2 | **Plugin lifecycle** — Install → Disable → Enable → Active → Uninstall state machine | 1.5d |
| B-3 | **Plugin sandboxing** — widget plugins in iframe, backend plugins with import restrictions | 2d |
| B-4 | **Internal plugins** — Slack integration + Salesforce connector (2+ plugins) | 2d |

### Frontend

| # | Task | Effort |
|---|------|--------|
| F-1 | **Marketplace UI** — browse, search, install, configure, uninstall plugins | 3d |
| F-2 | **Plugin configuration** — settings modal per plugin | 1.5d |

## Acceptance Criteria

| Gate | Criteria |
|------|----------|
| G-15.1 | Manifest validated on install |
| G-15.2 | Full lifecycle: Install→Disable→Enable→Active→Uninstall |
| G-15.3 | Marketplace: browse, install, configure, uninstall |
| G-15.4 | Widget plugins in isolated iframe |
| G-15.5 | Backend plugins restricted by import policy |

---

**Engineering OS**: ✅ Approved
