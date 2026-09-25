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
| `crm.system_of_record` | 0.55 | No | TENANT CRM |
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

---

## Implementation addendum (2026-09-20)

The first deterministic scoring implementation is now present in the Python commercial evidence domain and the TypeScript decision evidence package.

- The runtime evidence kind is explicit and uses the ADR values and weights. Provider or model `confidence` is not used as evidence strength.
- Independent evidence combines with noisy-OR, the combined score is capped at `0.99`, and any contradiction caps the score at `0.45`.
- Field decisions implement the ADR bands, including one primary source for `cr_number`, two for `industry`, and mandatory proposal review for `employees_count` and `description`.
- Python persists `evidence_kind` inside the existing evidence JSON data column, so this change does not require a database migration. The TypeScript `averageConfidence` field remains a provider-quality metric; `evidenceStrength` is a separate result.
- `Insight.recompute_confidence()` uses deterministic evidence strength whenever evidence kinds are present. Old evidence with no kind retains the prior arithmetic average as a compatibility path and is marked `legacy_average_compatibility` in insight metadata.

This is an implementation milestone, not a production scoring approval. Eight shared vectors at `salesos/packages/platform/decision/evidence-engine/adr0113-golden.json` now pass in both Python and TypeScript for score, uncapped score, contradiction, primary-source count, and evidence count. The shared cases cover kind weights, confidence separation, source de-duplication, contradiction, empty/untyped input, and unkeyed records. Field-aware decisions remain Python-only; source classification, canonical write-boundary integration, freshness/point-in-time rules, and production calibration remain open. Focused Python and TypeScript tests pass; no production score approval is implied.

### CRM insight producer classification (2026-09-20)

Account and deal intelligence summaries now label CRM-derived aggregates and rule factors as `crm.system_of_record` and retain the account/opportunity ID as the source ID. This kind has a provisional non-primary weight of `0.55`: it can support a PROBABLE insight, but it cannot satisfy the primary-source requirement for VERIFIED or automatic fact application. Multiple factors from the same CRM entity and kind deduplicate to one source contribution. This is a conservative source classification; calibrate its weight against reviewed outcomes before production use.

### Field decision guard — 2026-09-21

- `decide_fact()` now fails closed if any evidence item lacks an explicit `evidence_kind`; the untyped item remains in its evidence/insight record but is not eligible to create a canonical fact decision. A classified subset cannot hide legacy evidence.
- ADR-0113's `cr_number` source threshold measures evidence strength; it does not grant permission to write the identity field. Under ADR-0114, a verified CR fact can only be retained as a human-review proposal and never auto-applied by the agent.
- Auto-apply now requires an explicit ADR-0114 enrichment-field allowlist. Unknown fields remain review proposals even when their evidence reaches VERIFIED. System identity/control fields are rejected by this fact policy.
- This is a policy guard only: repository search found no FactRecorder, canonical-fact tables, or call site for `decide_fact()` in the application write path. Canonical write-boundary integration, human review storage/UI, dismissal and ownership checks, and freshness/point-in-time behavior remain open. No DB migration or write was made.
- Focused regression: `tests/unit/test_evidence_scoring_adr0113.py` — **14/14 PASS**; Ruff E9/F and compile checks pass.

### Additional producer boundary — 2026-09-21

- Removed the reasoning pipeline's self-generated summary from `AgentAnalysis.evidence`; its source remains labeled `llm_reasoning`. Model-reported confidence is now explicitly described as informational only in the intelligence schemas.
- Account/Deal Intelligence is the only inspected commercial `EvidenceItem` producer that currently assigns ADR kinds. Grounded `Research EvidencePack`, Agent Reach's channel evidence model, and the alternate decision engine use separate contracts and are not currently convertible to ADR-0113 facts without explicit source semantics. They remain outside automatic fact decisions.
- Verification: ADR-0113 and reasoning suites **25/25 PASS**; Ruff E9/F and Python compile checks pass. Producer inventory is incomplete; no blanket classification was inferred.
