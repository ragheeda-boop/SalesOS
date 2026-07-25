# Architecture Decision Records (ADR) Index

> **Purpose**: Central registry of all architectural decisions for SalesOS.
> **Last updated**: 2026-07-17

---

## Active ADRs

| ID | Title | Date | Status | Domain |
|----|-------|------|--------|--------|
| ADR-001 | Modular Monolith Foundation | 2026-06-01 | ✅ Accepted | Architecture |
| ADR-002 | Executive Intelligence Workspace | 2026-06-05 | ✅ Accepted | Product |
| ADR-003 | Widget SDK v1 Freeze | 2026-06-10 | ✅ Accepted | Widget SDK |
| ADR-025 | Entity Resolution Pipeline | 2026-07-01 | ✅ Accepted | Entity Resolution |
| ADR-026 | Hybrid Search (Full-text + Semantic) | 2026-07-02 | ✅ Accepted | Search |
| ADR-027 | Feature Store Implementation | 2026-07-03 | ✅ Accepted | Feature Store |
| ADR-028 | Knowledge Graph Integration | 2026-07-04 | ✅ Accepted | Knowledge Graph |
| ADR-030 | Unified Provider Architecture | 2026-07-08 | ✅ Accepted | Architecture |
| ADR-031 | Webhook Auth API Key Assessment | 2026-07-09 | ✅ Accepted | Security |
| ADR-032 | Widget SDK Reconciliation | 2026-07-10 | ✅ Accepted | Widget SDK |
| ADR-033 | Decision Engine Lifecycle | 2026-07-11 | ✅ Accepted | Decision Engine |
| ADR-034 | Repository Pattern Compliance | 2026-07-12 | ✅ Accepted | Architecture |
| ADR-035 | Sprint 0 Architecture Reconciliation | 2026-07-17 | 📝 Proposed | Architecture |

---

## ADR File Locations

| Location | Scope |
|----------|-------|
| `docs/adr/` | Product-root ADRs (ADR-030 to ADR-035) |
| `engineering-os/adr/` | Engineering-platform ADRs (ADR-001 to ADR-003, ADR-032) |
| `salesos/docs/ARCHITECTURE_BOOK.md` | Comprehensive architecture reference |
| `salesos/docs/DECISION_PLATFORM_ARCHITECTURE.md` | Decision Platform decisions |
| `docs/vnext/DECISIONS.md` | Pending vNext architectural decisions |

---

## ADR Lifecycle

```mermaid
graph LR
    A[Draft] --> B[Proposed]
    B --> C[Reviewed]
    C --> D[Accepted]
    C --> E[Rejected]
    D --> F[Superseded]
```

| Status | Description |
|--------|-------------|
| Draft | Initial authoring, not yet reviewed |
| Proposed | Submitted for Architecture Review Board review |
| Reviewed | ARB review complete, awaiting final decision |
| Accepted | Approved and in effect |
| Rejected | Considered and declined with rationale |
| Superseded | Replaced by a newer ADR |

---

## ADR Template

All ADRs follow the format:

```markdown
# ADR-{NNN}: {Title}

**Status**: {Proposed | Accepted | Superseded}
**Date**: {YYYY-MM-DD}
**Author**: {Name / Team}

## Context

{Problem statement and background}

## Decision

{What was decided}

## Consequences

{Benefits, trade-offs, migration notes}
```

---

## Related Documents

- [Architecture Book](../salesos/docs/ARCHITECTURE_BOOK.md) — Full architecture reference
- [Architecture Inventory](../salesos/docs/ARCHITECTURE_INVENTORY.md) — Component registry
- [Current Architecture](../salesos/docs/CURRENT_ARCHITECTURE.md) — Current state analysis
- [Target Architecture](../salesos/docs/TARGET_ARCHITECTURE.md) — Future architecture
- [Architecture Compliance Scorecard](../salesos/docs/ARCHITECTURE_SCORECARD.md) — Compliance tracking
