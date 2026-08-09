# ADR-0114: Canonical Write Boundary — FactRecorder + UBOM

**Status:** ACCEPTED
**Date:** 2026-08-09
**Phase:** P2 (Tools + Evidence + Write Path)

---

## Context

SalesOS has 20+ enrichment fields on `CompanyObject` and `ContactObject` that agents
could populate. Agents must never directly mutate canonical data — they must pass through
a governed write boundary with field classification, human-ownership protection, dismissal
guard, and band-based auto-apply.

## Decision

### Governed Write Boundary

```
Agent
  │
  └── WRITE
        │
        ├── Canonical Fact → FactRecorder (authoritative boundary)
        │     ├── fence check (lease_generation)
        │     ├── idempotency check
        │     ├── humanOwns() check
        │     ├── dismissal guard
        │     ├── band decision (VERIFIED→APPLIED, PROBABLE→PROPOSED)
        │     └── UBOM mutation (same transaction)
        │
        └── Other Business Mutation → Governed Tool/Repository (Phase 3)
```

**No agent may access domain ORM/repositories directly.**

### Field Classification

`BusinessObject.is_agent_updatable(field_name)` classifies fields:

**Identity fields (agent NEVER writes):**
`id`, `tenant_id`, `cr_number`, `created_at`, `updated_at`, `is_golden_record`,
`parent_company_id`, `source_ids`, `embedding`

**Enrichment fields (agent CAN write if VERIFIED):**
`city`, `region`, `industry`, `website`, `employees_count`, `annual_revenue`,
`activity_description`, `legal_form`, `latitude`, `longitude`, `phone`, `email`,
`address`, `capital`, `incorporation_date`, `confidence_score`

### FactRecorder Rules

1. **Never overwrite human-set fields.** If a user manually set a field (tracked
   via audit log or `source` column), agent facts are rejected.

2. **Never re-offer a dismissed fact.** Once a human dismisses `(entity_type, entity_id,
   field, value)`, the same combination is permanently blocked.

3. **Never write below POSSIBLE band.** Evidence score < 0.30 → fact is not stored.

4. **VERIFIED facts auto-apply.** Score >= 0.85 AND has primary source → create
   `canonical_facts` row with status=APPLIED + update UBOM field (single tx).

5. **PROBABLE/POSSIBLE facts are proposed.** Create `canonical_facts` row with
   status=PROPOSED + create `approval_request`. Do NOT update UBOM field.

6. **Supersession.** New APPLIED fact supersedes previous APPLIED fact on the
   same `(entity_type, entity_id, field)`. Previous → SUPERSEDED.

### Data Model

```
evidence_records (source of truth for evidence)
    └── fact_evidence (join table)
          └── canonical_facts (proposed/applied facts)
                └── UBOM objects (CompanyObject, ContactObject)
```

`canonical_facts` contains an `evidence_snapshot` JSONB column as an immutable
audit projection only — NOT the source of truth for evidence.

## Relationship with Security Boundary

ADR-0115 defines the security authorization chain (Auth → RBAC → PDP → Tool permissions).
The write path flows through two sequential gates:
1. **ToolDispatcher** (ADR-0115) — security gating: PDP, RBAC, tool-permission checks
2. **FactRecorder** (this ADR) — data integrity gating: field classification, humanOwns,
   dismissal guard, band-based auto-apply

Both gates must pass for a write to reach UBOM.

## Consequences

- Human-set fields are protected from agent overwrites.
- Dismissed facts never re-surfaced (data quality).
- Provenance tracked via `fact_evidence` → `evidence_records` → `agent_runs`.
- Not in Phase 1 — read-only agent only. Write path is Phase 2.

## Related

- ADR-0113: Evidence Architecture
- ADR-0115: Agent Security Boundary
