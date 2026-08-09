# ADR-0117: Signal → Agent Integration

**Status:** ACCEPTED
**Date:** 2026-08-09
**Phase:** P3 (Governance + Approval + Signals)

---

## Context

SalesOS's FeatureStore computes 7 feature scores (ICP, Funding, Hiring, Growth, Intent,
Expansion, Revenue) per company. Currently, feature changes are stored but do not trigger
agent execution. The system needs a path from detected signals to autonomous agent investigation.

## Decision

### Integration Chain

```
FeatureStore.recompute(company_id, tenant_id)
  → computes scores, stores results
  → publishes FeatureRecomputed event  (NEW: ~5 lines addition)
        │
        ▼
SignalDetector (new, Phase 3)
  → subscribes to FeatureRecomputed events
  → compares current scores vs. thresholds
  → detects: hiring_spike, expansion_signal, intent_shift, stagnation
        │
        ▼
EventRuntime.publish(SignalDetected(...))
        │
        ▼
AgentTaskCreator (new, Phase 3)
  → subscribes to SignalDetected events
  → evaluates signal → task transformation rules
  → calls AgentTaskService.create()
        │
        ▼
AgentDispatcher (existing, Phase 1)
  → claims and executes task
```

### Five Concrete Scenarios

All agents referenced below exist in the canonical Capability Matrix (12 agents).

| # | Signal | Task Kind | Agent | Evidence |
|---|--------|-----------|-------|----------|
| 1 | Hiring spike (+30% employees in 30 days) | `assess_hiring_spike` | ResearchAgent | Hiring data + CR activity |
| 2 | New branches or licenses detected | `investigate_expansion` | ResearchAgent | Branch data + license verification |
| 3 | New primary contact (executive change) | `executive_change` | RelationshipAgent | Contact details + prior timeline |
| 4 | New license in Data Fabric | `verify_new_license` | ResearchAgent | License + issuing authority |
| 5 | Opportunity inactive > 30 days | `stagnation_alert` | ResearchAgent | Activity timeline + competitors |

### Threshold Configuration

```python
SIGNAL_RULES = [
    SignalRule(
        name="hiring_spike",
        feature="hiring_growth_score",
        threshold=0.30,           # 30% change
        window_days=30,
        task_kind="assess_hiring_spike",
        priority=500,
    ),
    SignalRule(
        name="expansion_signal",
        feature="expansion_score",
        threshold=0.25,
        window_days=90,
        task_kind="investigate_expansion",
        priority=400,
    ),
    # ...
]
```

### FeatureStore Change Required

In `runtime/feature_store/__init__.py`, after `recompute()` commits, add:

```python
if self._event_runtime:
    await self._event_runtime.publish(FeatureRecomputed(
        tenant_id=tenant_id,
        aggregate_id=company_id,
        aggregate_type="company",
        data={
            "feature_scores": {name: result.score for name, result in results.items()},
            "previous_scores": previous,  # from cache/db
        }
    ))
```

This is a ~5-line change with zero impact on existing FeatureStore functionality.

## Consequences

- Signal→Agent path is event-driven, not polling-based.
- FeatureStore change is minimal (5 lines) and Phase 3.
- SignalDetector + AgentTaskCreator are Phase 3 components.
- Not in Phase 1 — Phase 1 uses explicit `AgentTaskService.create()`.

## Related

- ADR-0110: Agent Runtime re-scope
- ADR-0111: Task Queue
- Existing: `runtime/feature_store/__init__.py`
