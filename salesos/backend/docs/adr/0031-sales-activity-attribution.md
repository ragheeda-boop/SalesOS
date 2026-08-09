# ADR-031: Sales Activity Attribution Architecture

**Status:** Proposed  
**Date:** 2026-08-09  
**Deciders:** CTO, Chief Architect, Backend Team  
**Tags:** architecture, attribution, activity, opportunity, confidence, evidence, provenance  
**Depends On:** ADR-029 (Canonical Opportunity Model), ADR-030 (Opportunity ↔ Contact Relationship)  
**Precedes:** C.2.1–C.2.6 (Attribution Implementation Phases)  
**Scope:** Architecture only — attribution data model, evidence/confidence model, ambiguity/unresolved policy. No implementation checklist.

---

## Context

C.2 forensic audit investigated whether SalesOS can link emails and calendar events to opportunities. The answer is **no** — the attribution chain is broken at multiple points, not just missing an algorithm:

| Link | Current State | Evidence |
|------|:------------:|----------|
| Email → Company | Implemented | `company_linker.py` domain match → `related_company_ids` |
| Calendar → Company | Implemented | Same mechanism |
| Email → Contact | Partial | Contacts upserted in `contacts` table but contact IDs not written back to event row |
| Calendar → Contact | Partial | Same gap |
| Contact → Opportunity | Not implemented | `opportunity_contacts` junction table proposed in ADR-030, not yet created |
| Email → Opportunity | No operational path | `related_opportunity_ids` is a dead column |
| Calendar → Opportunity | No operational path | Same dead column |
| Google Events ↔ commercial `meetings`/`emails` | No bridge | Two separate database systems, never joined |

Two disconnected activity systems exist:

| System | Tables | Opportunity Link | Status |
|--------|--------|:----------------:|:------:|
| Google Sync (automated) | `employee_email_events`, `employee_calendar_events` | Dead `related_opportunity_ids` columns | **Operational** |
| Commercial (manual CRUD) | `emails`, `meetings` (has FK `opportunity_id`) | Direct FK | **Operational** |

**The problem is not that SalesOS needs a new attribution algorithm. The fundamental entity chain itself is incomplete.**

### What C.2 Also Found

A 5-stage `MappingPipeline` (`intelligence/activity_intelligence/mapping/`) exists but is **never instantiated**. It has a priority chain (explicit_ref → opportunity_lookup → contact_lookup → domain_match → ai_match) with confidence scoring, but no concrete reader implementations (`CompanyReader`, `ContactReader`, `OpportunityReader` are ABCs only). The operational sync bypasses it entirely.

---

## Decision

### 1. Attribution Is a Separate Capability

Sales Activity Attribution will be a **standalone attribution engine**, not a field added to existing event tables. It resolves activities (emails, calendar events) to canonical `commercial_opportunities` through the entity chain: Contact → Company → `opportunity_contacts` → Opportunity.

### 2. Attribution Has Its Own Persistence

Attribution results are stored in a dedicated `activity_attributions` table. Attribution is NOT stored by filling `related_opportunity_ids` on event tables. This is because attribution requires:

- **Evidence** — why was this link made? (explicit reference, domain match, contact match, etc.)
- **Confidence** — how sure are we? (scored, comparable across methods)
- **Provenance** — which algorithm version made this decision? (reproducible, auditable)
- **Ambiguity** — what if there are multiple candidates? (ranked, not flattened to one ID)
- **Resolution state** — is this confirmed, candidate, or unresolved?

A JSONB array of opportunity IDs cannot express any of this.

### 3. Canonical Activity Sources

The attribution engine reads from:

| Source | Table | Rationale |
|--------|-------|-----------|
| Google Email | `employee_email_events` | Primary automated sync source |
| Google Calendar | `employee_calendar_events` | Primary automated sync source |
| Activity Runtime | `activity_records` | Cross-source aggregation (if entity_type supports it) |

**The legacy `emails` and `meetings` commercial tables are NOT attribution sources.** They already have direct `opportunity_id` FKs and serve a different purpose (user-managed opportunity notes). They are not unified with Google sync events, and unification is out of scope for this ADR.

### 4. Attribution Does Not Write to Event Tables

The `employee_email_events.related_opportunity_ids` and `employee_calendar_events.related_opportunity_ids` columns will remain as-is (dead) and will NOT be populated by the attribution engine. Attribution results live in `activity_attributions`, referenced by `activity_id` + `activity_type`.

### 5. Attribution Is Read-Back Only for Employee 360

The attribution engine is a **consumer** of the entity chain, not a writer to it. It reads contacts, companies, `opportunity_contacts`, and opportunities. It writes only to `activity_attributions`. Employee 360 reads `activity_attributions` to display per-opportunity engagement.

---

## Attribution Data Model

### `activity_attributions` Table

```sql
CREATE TABLE activity_attributions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL REFERENCES tenants(id),

    -- What activity is being attributed
    activity_type VARCHAR(20) NOT NULL,          -- 'email', 'calendar_event', 'activity_record'
    activity_id UUID NOT NULL,                    -- FK to the source table (soft)
    activity_source_table VARCHAR(50) NOT NULL,    -- 'employee_email_events', 'employee_calendar_events', 'activity_records'

    -- What opportunity is this attributed to
    opportunity_id VARCHAR(36) NOT NULL,          -- References commercial_opportunities.id

    -- Resolution path: how did we get there?
    resolution_method VARCHAR(30) NOT NULL,       -- 'explicit_reference', 'contact_match', 'domain_match', 'company_match', 'ai_match'
    resolution_chain JSONB NOT NULL DEFAULT '[]',  -- Ordered list of resolution steps taken
        -- Example: [{"step": "domain_match", "domain": "acme.com", "company_id": "uuid"},
        --           {"step": "contact_match", "contact_id": "uuid", "contact_email": "..."},
        --           {"step": "opportunity_contact", "junction_id": "uuid"}]

    -- Evidence: why do we believe this link?
    evidence JSONB NOT NULL DEFAULT '{}',
        -- Example: {"company_ids": ["uuid1"], "contact_ids": ["uuid2"],
        --           "explicit_ref": null, "domain_match": "acme.com",
        --           "contact_email": "alice@acme.com"}

    -- Confidence
    confidence DECIMAL(4,3) NOT NULL,             -- 0.000 to 1.000
    confidence_breakdown JSONB NOT NULL DEFAULT '{}',
        -- Example: {"domain_match": 0.6, "contact_match": 0.8, "opportunity_contact": 0.9}

    -- Provenance
    algorithm_version VARCHAR(30) NOT NULL,        -- e.g., 'v1.0.0', for reproducibility
    resolved_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    -- Resolution state
    resolution_state VARCHAR(20) NOT NULL DEFAULT 'confirmed',
        -- 'confirmed': single clear match, confidence >= threshold
        -- 'candidate': below threshold, needs review
        -- 'ambiguous': multiple candidates above threshold
        -- 'unresolved': no match found

    -- For ambiguous cases: ranked alternatives
    alternative_candidates JSONB,                  -- Array of {opportunity_id, confidence, evidence}
        -- Only populated when resolution_state = 'ambiguous'

    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    UNIQUE (tenant_id, activity_type, activity_id, opportunity_id)
);

CREATE INDEX idx_aa_tenant ON activity_attributions(tenant_id);
CREATE INDEX idx_aa_activity ON activity_attributions(activity_type, activity_id);
CREATE INDEX idx_aa_opportunity ON activity_attributions(opportunity_id);
CREATE INDEX idx_aa_resolution_state ON activity_attributions(tenant_id, resolution_state);
CREATE INDEX idx_aa_tenant_opp ON activity_attributions(tenant_id, opportunity_id);
```

### Field Classification

| Field | Type | Classification | Rationale |
|-------|------|:--------------:|-----------|
| `id` | UUID PK | **REQUIRED** | Standard primary key |
| `tenant_id` | UUID FK→tenants | **REQUIRED** | RLS isolation |
| `activity_type` | VARCHAR(20) | **REQUIRED** | Distinguishes email from calendar from runtime |
| `activity_id` | UUID | **REQUIRED** | Soft FK to source row |
| `activity_source_table` | VARCHAR(50) | **REQUIRED** | Explicit table name for cross-source queries |
| `opportunity_id` | VARCHAR(36) | **REQUIRED** | References `commercial_opportunities.id` (ADR-029) |
| `resolution_method` | VARCHAR(30) | **REQUIRED** | Primary method that produced this link |
| `resolution_chain` | JSONB | **REQUIRED** | Full chain for audit/debug |
| `evidence` | JSONB | **REQUIRED** | Why this link exists |
| `confidence` | DECIMAL(4,3) | **REQUIRED** | Scorable, comparable |
| `confidence_breakdown` | JSONB | **REQUIRED** | Per-step scores |
| `algorithm_version` | VARCHAR(30) | **REQUIRED** | Reproducibility |
| `resolved_at` | TIMESTAMPTZ | **REQUIRED** | When the decision was made |
| `resolution_state` | VARCHAR(20) | **REQUIRED** | confirmed/candidate/ambiguous/unresolved |
| `alternative_candidates` | JSONB | **OPTIONAL** | Only populated for ambiguous |
| `created_at` | TIMESTAMPTZ | **REQUIRED** | Audit trail |
| `updated_at` | TIMESTAMPTZ | **REQUIRED** | Audit trail |

### NOT Included (Not Justified)

| Would-Be Field | Reason Excluded |
|---------------|-----------------|
| `related_opportunity_ids` on event tables | C.2 audit: these columns are dead. Filling them would discard evidence, confidence, provenance, and ambiguity. Attribution is richer than a JSONB array. |
| `opportunity_id` on event tables | Same — a single FK cannot express multiple candidates, confidence, or resolution state. |
| `source_event_id` on activities | The `activity_source_table` + `activity_id` soft reference provides this without FK coupling. |
| `user_id` / `employee_id` on attributions | Already available on the source event row; join through to get it. |

---

## Attribution Engine Boundary

### Inputs

```
employee_email_events           employee_calendar_events
        │                                   │
        ├── id                              ├── id
        ├── from_address                    ├── organizer_email
        ├── to_addresses                    ├── attendees (addresses)
        ├── related_company_ids ✓           ├── related_company_ids ✓
        ├── employee_id                     ├── employee_id
        └── subject / body_preview          └── title / description_md
```

### Resolution Paths (Priority Chain)

The engine resolves activities through a priority chain, attempting higher-confidence methods first:

| Priority | Method | Input | Confidence | When It Applies |
|:--------:|--------|-------|:----------:|-----------------|
| 1 | **Explicit Reference** | `[OPP-123]` in subject/body | **1.0** | User explicitly tags a deal reference |
| 2 | **Contact → Opportunity** | Email address → `contacts.email` → `opportunity_contacts` | **0.9** | Contact has active opportunities |
| 3 | **Company → Opportunity** | Domain → `companies.website` → `commercial_opportunities.company_id` → open opps | **0.6** | Company has open opportunities |
| 4 | **Contact → Company → Opportunity** | Email → contact → contact.company_id → open opps for that company | **0.7** | Contact exists with company but no direct opp link |
| 5 | **AI Match** | Subject/body NLP → opportunity name fuzzy match | **0.4** | Last resort, when other methods fail |

Each method produces candidates. Only candidates with confidence ≥ threshold (default 0.5) proceed. If multiple candidates pass the threshold, ambiguity handling applies.

### Engine Architecture

```
ActivityEvent
      │
      ▼
┌──────────────────┐
│  ResolutionEngine │   Priority chain execution
│  (try each method)│
└──────┬───────────┘
       │
       ▼
┌──────────────────┐
│ CandidateGenerator│   Produces list of (opportunity_id, confidence, evidence)
└──────┬───────────┘
       │
       ▼
┌──────────────────┐
│  Scorer           │   Computes composite confidence from breakdown
└──────┬───────────┘
       │
       ├── 0 candidates ──────────► resolution_state = 'unresolved' (no attribution row)
       │
       ├── 1 candidate ≥ threshold ─► resolution_state = 'confirmed'
       │
       ├── 1 candidate < threshold ─► resolution_state = 'candidate'
       │
       └── 2+ candidates ≥ threshold ► resolution_state = 'ambiguous'
                                       (primary = highest confidence, alternatives stored)
```

### Output

One or zero `activity_attributions` rows per (activity_type, activity_id, opportunity_id):
- **Unresolved:** No row written (absence = no known opportunity link)
- **Candidate:** Row written with `resolution_state='candidate'`
- **Confirmed:** Row written with `resolution_state='confirmed'`
- **Ambiguous:** Primary row at highest confidence + `alternative_candidates` JSONB array

---

## Evidence + Confidence + Provenance

### Evidence Model

Every attribution carries explicit evidence — a structured record of WHY this link exists:

```json
{
  "company_ids": ["uuid-1"],
  "contact_ids": ["uuid-2"],
  "opportunity_contact_ids": ["uuid-3"],
  "explicit_ref": {
    "pattern": "[OPP-123]",
    "source": "subject",
    "match_type": "regex"
  },
  "domain_match": "acme.com",
  "contact_email": "alice@acme.com",
  "opportunity_stage": "Prospect",
  "opportunity_status": "open"
}
```

This enables Employee 360 to display: "This email was linked to `Acme Corp deal` because `alice@acme.com` is a contact on this opportunity."

### Confidence Model

```python
METHOD_WEIGHTS = {
    "explicit_reference": 1.0,
    "contact_opportunity": 0.9,
    "contact_company_opportunity": 0.7,
    "company_opportunity": 0.6,
    "ai_match": 0.4,
}

DEFAULT_THRESHOLD = 0.5  # Below this → 'candidate', not 'confirmed'
```

Confidence is always stored with its breakdown so future algorithm versions can be compared:

```json
{
  "domain_match": 0.6,
  "contact_upsert": 0.8,
  "opportunity_contact_join": 0.9,
  "composite": 0.77
}
```

### Provenance

- `algorithm_version` — Tied to git tag or release version (e.g., `v1.0.0`, `v1.1.0-email-confidence-boost`)
- `resolution_chain` — Ordered steps taken, with timestamps and intermediate results
- `resolved_at` — When the decision was made (vs. `created_at` which tracks row creation)

This allows: "Re-score all attributions from algorithm v1.0.0 using v1.1.0 without losing v1.0.0 evidence."

---

## Ambiguity Policy

When multiple opportunities match with confidence above threshold:

1. **Store all candidates** — Primary row at highest confidence, alternatives in `alternative_candidates`
2. **Set `resolution_state = 'ambiguous'`**
3. **Employee 360 displays** — "This email may relate to Opportunity A (0.85) or Opportunity B (0.72)"
4. **Manual resolution** — UI allows user to confirm, reject, or split the attribution
5. **Re-resolution** — When new evidence arrives (e.g., `opportunity_contacts` updated), re-run attribution for affected activities

### When Ambiguity Is Acceptable

- Same company has two active opportunities → both are plausible
- Contact is linked to multiple opportunities (`opportunity_contacts`) → ambiguity is truthful
- Ambiguity is NOT a system failure — it's an accurate representation of uncertainty

---

## Unresolved Policy

When no candidate reaches the confidence threshold:

1. **No `activity_attributions` row is written** — absence of a row means "no known opportunity link"
2. **Periodic re-resolution** — Activities without attribution can be re-evaluated when:
   - New `opportunity_contacts` rows are added
   - New company domain matches appear
   - Algorithm version is upgraded
3. **No forced attribution** — Never attribute to a low-confidence match just to fill a gap
4. **Employee 360 displays** — "Attribution not available" or "No associated deal"

---

## Why NOT Fill `related_opportunity_ids` Directly

The `employee_email_events.related_opportunity_ids` and `employee_calendar_events.related_opportunity_ids` columns exist today as dead JSONB arrays. Filling them would be the simplest path but is rejected for these reasons:

1. **Loss of evidence** — A `["uuid-1"]` array answers "which opportunity?" but not "why?"
2. **No confidence** — Cannot distinguish a high-confidence explicit match from a low-confidence domain guess
3. **No provenance** — Cannot trace which algorithm version made the decision
4. **No ambiguity** — Cannot express "this email relates to Opportunity A OR B"
5. **No resolution state** — Cannot distinguish confirmed, candidate, unresolved
6. **Brittle updates** — Updating a JSONB array in-place loses history; `activity_attributions` rows are immutable + versioned
7. **Query complexity** — "Show emails attributed to opportunity X with confidence > 0.5" requires parsing JSONB; `activity_attributions` has indexed columns

**Decision: `related_opportunity_ids` columns remain as-is (dead). All attribution data lives in `activity_attributions`.**

---

## Relationship to ADR-029 and ADR-030

| Aspect | ADR-029 | ADR-030 | ADR-031 |
|--------|---------|---------|---------|
| Scope | Canonical Opportunity | Opportunity ↔ Contact | Activity → Opportunity Attribution |
| Table Created | (existing) `commercial_opportunities` | `opportunity_contacts` | `activity_attributions` |
| Cardinality | — | M:N (opportunity ↔ contact) | N:1 (activities → opportunity, but one activity MAY produce 0 or N attributions) |
| Source of Truth | Opportunity data | Contact relationship | Attribution evidence |
| Implementation Status | **Canonical** | Proposed (not yet created) | Proposed (not yet created) |

### Dependency Chain

```
ADR-029 (commercial_opportunities)
    │
    └── ADR-030 (opportunity_contacts)
            │
            └── ADR-031 (activity_attributions)
                    │
                    └── Employee 360 enrichment
```

**ADR-031 requires ADR-030's `opportunity_contacts` table to be created before it can resolve contact→opportunity links.**

---

## Consequences

### Positive

1. **Evidence-driven attribution** — Every link is explainable, auditable, and reproducible
2. **Confidence-scored** — Employee 360 can surface high-confidence links prominently, de-emphasize low-confidence ones
3. **Ambiguity-aware** — Multiple candidates are stored honestly, not flattened
4. **Algorithm-versioned** — Can upgrade attribution logic without losing history
5. **Immutable evidence** — Attribution rows are write-once, read-many; re-resolution creates new rows
6. **No event table pollution** — Event tables remain activity-focused, not attribution-focused
7. **Query-efficient** — Indexed columns for opportunity-scoped queries

### Negative

1. **New table** — Adds `activity_attributions` to the schema
2. **More storage** — Evidence + confidence JSONB per attribution row (acceptable trade-off)
3. **Re-resolution logic** — Requires periodic re-evaluation of unlinked activities
4. **Dependent on ADR-030** — Cannot resolve contact→opportunity without `opportunity_contacts`

### Risks

| Risk | Mitigation |
|------|-----------|
| `opportunity_contacts` remains empty → no contact→opportunity resolution | ADR-030 implementation is prerequisite; manual CRUD API provides population path |
| Company domain match is too broad (many opportunities per company) | Confidence scoring demotes weak matches; ambiguity policy surfaces multiple candidates |
| Explicit reference `[OPP-NNN]` never used in practice | Low priority (priority 1); falls back to lower-priority methods automatically |
| Attribution rows grow unbounded | Periodic cleanup of superseded rows; re-resolution soft-deletes old rows |

---

## Deferred Decisions

| Decision | Deferred To | Rationale |
|----------|------------|-----------|
| Integration with legacy `emails`/`meetings` tables | Future ADR if needed | Those tables already have direct `opportunity_id` FKs; no attribution engine needed |
| AI-based opportunity name matching (priority 5) | Future ADR | Requires NLP pipeline or LLM integration; out of scope for v1 |
| Real-time attribution (streaming) | Future ADR | v1 is batch/periodic via Celery |
| Attribution from non-Google sources (Slack, WhatsApp) | Future ADR | Only Google email + calendar are in scope |
| `activity_records` as attribution source | Future ADR | Currently entity_type="communication" only; needs entity type expansion |
| Cross-tenant attribution | Never | Tenant isolation is absolute |

---

## Migration / Implementation Boundary

### This ADR Covers

1. `activity_attributions` table schema (DDL)
2. Resolution path priority chain (algorithm design)
3. Evidence + confidence + provenance model
4. Ambiguity policy
5. Unresolved policy
6. Why NOT to fill `related_opportunity_ids`
7. Engine boundary: inputs, resolution, outputs
8. Relationship to ADR-029 and ADR-030

### This ADR Does NOT Cover

| Item | Boundary |
|------|----------|
| ResolutionEngine implementation code | **Implementation** — Python classes, Celery tasks |
| Contact → Company → Opportunity join logic in SQL | **Implementation** — query layer |
| Re-resolution Celery task | **Implementation** — scheduled task |
| Employee 360 enrichment with attribution data | **Implementation** — display layer |
| Manual resolution UI | **Implementation** — frontend |
| Alembic migration | **Implementation** — DDL generation |
| Attribution API endpoints | **Implementation** — router |
| Tests | **Implementation** — unit + integration |

### Implementation Sequence (Post-Ratification)

```
1. ADR-030 Execution: CREATE TABLE opportunity_contacts + CRUD API     ← C.2.1
2. Fix contact_sync.py: return contact IDs, write related_contact_ids   ← C.2.2
3. ADR-031 Execution: CREATE TABLE activity_attributions                ← C.2.3
4. Implement ResolutionEngine (priority chain, evidence, confidence)    ← C.2.3
5. Wire email attribution: employee_email_events → activity_attributions ← C.2.4
6. Wire calendar attribution: employee_calendar_events → same           ← C.2.5
7. Enrich Employee 360: _get_portfolio() joins activity_attributions    ← C.2.6
```

---

## References

- ADR-029: Canonical Opportunity Model (2026-08-09)
- ADR-030: Opportunity ↔ Contact Relationship (2026-08-09)
- C.2 Forensic Audit Report (2026-08-09) — `docs/audit/c2-attribution/C2_FORENSIC_AUDIT.md`
- `employee_email_events` model — `domains/employee/intelligence_models.py:66-117`
- `employee_calendar_events` model — `domains/employee/intelligence_models.py:15-63`
- `activity_records` Core Table — `runtime/activity_runtime/__init__.py:46-69`
- `MappingPipeline` (never instantiated) — `intelligence/activity_intelligence/mapping/__init__.py:25-98`
- `company_linker.py` (operational domain→company) — `communication_hub/company_linker.py:46-77`
- `contact_sync.py` (email→contact, no back-write) — `communication_hub/contact_sync.py:48-147`
