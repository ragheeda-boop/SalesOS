# ADR-0113: Evidence Architecture — Bayesian Combination + Saudi-Specific Kinds

**Status:** ACCEPTED
**Date:** 2026-08-09
**Phase:** P2 (Tools + Evidence + Write Path)

---

## Context

Comp AI CRM uses a deterministic evidence scoring engine with Bayesian combination
and contradiction capping. SalesOS has `EvidenceItem` as a Pydantic schema only —
no runtime engine, no scoring, no banding. Agents currently produce LLM confidence
scores which are unreliable for factual claims.

## Decision

**Adopt Comp AI's deterministic evidence scoring** with SalesOS-specific evidence kinds.

### Three Separated Concepts

| Concept | Definition | Implementation |
|---------|-----------|----------------|
| **LLM Confidence** | Model self-reported confidence (0-1). Informational only. | IGNORED for facts |
| **Evidence Strength** | Deterministic score from evidence kind weights. | `EvidenceEngine.scoreEvidence()` |
| **Business Decision Confidence** | Whether to act on a fact. Band + sensitivity + policy. | `FactRecorder` + `FactDecisionPolicy` |

### Evidence Kinds (Saudi-specific)

| Kind | Weight | Primary | Authority Tier |
|------|-------:|:-------:|:--------------:|
| `source.official_registry` | 0.98 | Yes | OFFICIAL REGISTRY |
| `source.cr_number_exact_match` | 0.95 | Yes | OFFICIAL REGISTRY |
| `source.license_verified` | 0.90 | Yes | OFFICIAL REGISTRY |
| `source.entity_resolution_merge` | 0.85 | Yes | SYSTEM |
| `crm.email_signature` | 0.80 | Yes | DIRECT CRM |
| `crm.meeting_attendance` | 0.70 | Yes | DIRECT CRM |
| `web.government_source` | 0.65 | Yes | WEB RESEARCH |
| `web.cited_claim` | 0.40 | No | WEB RESEARCH |
| `source.name_match_only` | 0.35 | No | INFERRED |
| `source.employer_match_only` | 0.20 | No | INFERRED |
| `contradiction` | 0.00 | No | CAPPING RULE |

### Scoring Formula

```
score = 1 - ∏(1 - weight_i)
capped at 0.99
if contradiction present → capped at 0.45
```

### Fact Bands

| Band | Threshold | Behavior |
|------|-----------|----------|
| VERIFIED | score >= 0.85 AND has primary | Auto-apply to UBOM |
| PROBABLE | score >= 0.55 | Store as PROPOSED, create approval request |
| POSSIBLE | score >= 0.30 | Store as PROPOSED (weaker) |
| — | score < 0.30 | DISCARD (not stored) |

### Field-Aware Thresholds

`FactDecisionPolicy` allows per-field calibration:

| Field | Minimum Sources for VERIFIED | Special Rule |
|-------|:---:|-------|
| `cr_number` | 1 (official registry alone suffices) | |
| `industry` | 2 (need official + corroboration) | |
| `employees_count` | N/A | Always PROPOSED (fluctuates, needs human judgment) |
| `description` | N/A | Always PROPOSED (generative text) |

Evidence weights are configurable and should be calibrated against real data after Phase 2.

## Consequences

- Deterministic scoring eliminates LLM hallucinated confidence.
- Saudi-specific evidence kinds reflect actual data source authority tiers.
- Contradiction cap (0.45) prevents overconfident claims from conflicting sources.
- Field-aware thresholds prevent auto-applying facts to fields that need human judgment.
- Not in Phase 1 — evidence engine is Phase 2.

## Related

- ADR-0114: Canonical Write Boundary
