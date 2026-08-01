# ADR-036: Engineering Organization — Layer Separation

**Status**: Accepted
**Date**: 2026-08-01
**Author**: CTO (Architecture Review Board session)

---

## Context

Following the ARB assessment of the SalesOS Engineering Operating System, the `.engineering/` directory (EOS v3.1, 33 files) and `docs/program/` (program management, 17+ files, 45 decisions, 26 sprint plans) were evaluated for their relationship and whether they should be merged, connected, or kept independent.

The ARB audit (File 32) identified a factual accuracy gap (7 blocking findings, resolved in v3.1 correction), a coordination gap (EOS and Program systems do not cross-reference each other), and a fragility problem (hardcoded counts drift immediately when `HEAD` advances).

The ARB recommended retiring `.engineering/` as a living system and merging its governance rules into `docs/program/`, keeping only the Sprint Delivery Board as the single coordination point.

The CTO rejected this recommendation on the grounds that `.engineering/` is not documentation — it is an **Engineering Specification** — and should not be merged into `docs/program/`, which serves a different purpose (**Business Truth**).

---

## Decision

SalesOS adopts **four independent layers**, each with a clear responsibility. Layers must never be merged, only connected through references.

```
┌──────────────────────────────────────┐
│ docs/program                         │
│ Business Truth                       │
│ ماذا نبني؟                           │
│                                      │
│ Vision, Strategy, Roadmap, Sprint,   │
│ Decisions, Risks, Epics, Stories,    │
│ Release Plan                         │
└──────────────────────────────────────┘
                  │
                  │ references (linked, not duplicated)
                  ▼
┌──────────────────────────────────────┐
│ .engineering                         │
│ Engineering Specification            │
│ كيف يجب أن يعمل النظام؟              │
│                                      │
│ Architecture, ADR, Capability,       │
│ Ownership, Dependency, Routing,      │
│ Governance, Quality Gates            │
└──────────────────────────────────────┘
                  │
                  │ references (linked, not duplicated)
                  ▼
┌──────────────────────────────────────┐
│ .ai                                  │
│ AI Runtime                           │
│ من ينفذ وكيف ينسق؟                   │
│                                      │
│ Scheduler, Dispatcher, Locks,        │
│ Queues, Sessions, Memory, Events,    │
│ Telemetry, Recovery, Profiles        │
│                                      │
│ (Deferred — not yet built)           │
└──────────────────────────────────────┘
                  │
                  │ controls execution
                  ▼
┌──────────────────────────────────────┐
│ salesos/                             │
│ Implementation                        │
│ ما تم بناؤه فعليًا                   │
│                                      │
│ Backend, Frontend, Infra, Tests,     │
│ CI/CD, Deploy, Config                │
└──────────────────────────────────────┘
```

### Layer responsibilities

| Layer | Location | Role | Owns | Does NOT own |
|-------|----------|------|------|--------------|
| **Business Truth** | `docs/program/` | ماذا نبني؟ | Vision, Roadmap, Sprint, Decisions, Risks | Architecture, Ownership, Agent coordination |
| **Engineering Spec** | `.engineering/` | كيف يجب أن يعمل؟ | Architecture, ADR, Capability, Ownership, Dependency, Routing, Quality Gates | Sprint state, Business priorities |
| **AI Runtime** | `.ai/` (future) | من ينفذ؟ | Scheduling, Dispatching, Locks, Queues, Sessions, Events, Telemetry, Recovery | What to build (Program), How to design it (Engineering) |
| **Implementation** | `salesos/` | ما تم بناؤه؟ | Code, Tests, Infra, Config, Deploy scripts | Governance decisions |

### Key rules

1. **Layers reference each other; they do not copy each other.** A Sprint references a Capability. A Capability references a Module. A Module references a file path. No layer copies data from another.

2. **`.engineering/` is NOT retired.** It is preserved and strengthened as the permanent Engineering Specification layer. Its governance rules (truth hierarchy, honesty labels, change protocol, coordination rules) remain authoritative for all engineering work.

3. **`.ai/` is NOT built now.** It is deferred until the foundation is stable (Phase 0 complete, CI green, audit passed, drift resolved). When built, `.ai/` will be an **Agent Operating System**, not embedded inside `.engineering/`.

4. **The Sprint Delivery Board is NOT the single source of truth.** It owns story/task/status. It does not own architecture, ownership, dependency, locks, or blast radius. Those belong to `.engineering/`.

### Execution phases

| Phase | Priority | Scope |
|-------|----------|-------|
| **Phase 1 (NOW)** | Fix the foundation | Resolve ARB audit findings, eliminate Capability Registry drift, reconcile ADR index, achieve CI green, close Phase 0 |
| **Phase 2** | Connect the layers | Add bidirectional references between `docs/program/` and `.engineering/`; no data duplication |
| **Phase 3 (deferred)** | Build `.ai/` Runtime | After the system is stable, build the Agent Operating System based on real operational data, not assumptions |

---

## Consequences

### Benefits

1. **Clean separation of concerns.** Business priorities, engineering rules, runtime execution, and actual code each have a single owner.
2. **Engine-swappable.** Changing agents (Cursor → Gemini Code, Claude → Windsurf) requires updating `.ai/`, not `.engineering/` or `docs/program/`.
3. **No premature architecture.** `.ai/` is not built until real multi-agent coordination problems exist and can inform the design.
4. **`.engineering/` remains the authoritative specification** for how the system should be engineered, independent of which agents execute it.

### Trade-offs

1. **Three layers to maintain** instead of one merged system — higher documentation discipline required.
2. **Cross-references can drift** — bidirectional links between `docs/program/` and `.engineering/` must be validated (future CI gate).
3. **`.engineering/` fragility remains** — hardcoded counts and commit-pinned state must be addressed before `.ai/` can rely on it at runtime.

---

## Related

- `docs/program/MASTER_EXECUTION_PLAN.md` — Business Truth layer authority
- `.engineering/00_PROJECT_CONSTITUTION.md` — Engineering Spec authority
- `.engineering/32_EOS_VALIDATION_AUDIT.md` — ARB audit that identified the gaps
- `.engineering/27_ADR_INDEX.md` — Current ADR state (including known conflicts)
- `docs/program/DECISION_LOG.md` — Program decisions (DEC-001 through DEC-122)
- `docs/program/ENGINEERING_LAYER_BRIDGE.md` — Program → Engineering pointers (criterion 9.2 / DEC-141)
- `.engineering/33_PROGRAM_LAYER_BRIDGE.md` — Engineering → Program pointers (criterion 9.2 / DEC-141)
