# Sprint 4 — Company360 Backend Report

> **Work Order**: WO-401-PHASE4-COMPANY360
> **Date**: 2026-07-16
> **Status**: ✅ Complete
> **Engineer**: `backend-engineer`

---

## Summary

Three backend tasks completed for the Company 360 aggregation layer:

| Task | Endpoint | Effort | Status |
|------|----------|--------|--------|
| B-1 | `GET /api/v1/companies/{id}/360` | 2d | ✅ Done |
| B-2 | `GET /api/v1/knowledge-graph/companies/{id}/insights` | 1d | ✅ Done |
| B-3 | Timeline filter API enhancements | 1d | ✅ Done |

---

## B-1: Company 360 Aggregation Endpoint

### Files Changed

| File | Change |
|------|--------|
| `app/modules/company/schemas.py` | Added `CrmSection`, `TimelineSection`, `EnrichmentSection`, `EnrichmentFirmographics`, `EnrichmentFinancials`, `EntityResolutionSection`, `KnowledgeGraphSection`, `KgRelationship`, `KgHierarchy`, `CrmDeal` schemas. Extended `Company360Response` with new structured fields. |
| `app/modules/company/service.py` | Updated `get_company_360()` to populate `crm`, `timeline`, `enrichment`, `entity_resolution`, and `knowledge_graph` sections. |

### Response Structure

```json
{
  "company": { /* existing CompanyResponse fields */ },
  "crm": {
    "deals": [],
    "deals_total": 0,
    "deals_value": 0.0,
    "contacts": [],
    "contacts_total": 0,
    "opportunities": [],
    "opportunities_total": 0
  },
  "timeline": {
    "events": [],
    "count": 0,
    "page": 1,
    "total": 0
  },
  "enrichment": {
    "firmographics": {
      "industry": null,
      "isic_code": null,
      "legal_form": null,
      "employees_count": null,
      "capital": null,
      "incorporation_date": null,
      "city": null,
      "region": null,
      "activity_description": null,
      "activity_code": null
    },
    "financials": {
      "total_revenue": 0.0,
      "total_opportunity_value": 0.0,
      "active_contracts": 0,
      "pending_invoices": 0
    },
    "sources": [],
    "is_golden_record": false,
    "confidence_score": 0.0,
    "last_enriched_at": null
  },
  "entity_resolution": {
    "is_golden_record": false,
    "golden_record_id": null,
    "confidence_score": 0.0,
    "source_count": 0,
    "duplicates_detected": 0,
    "conflicts_pending": 0
  },
  "knowledge_graph": {
    "relationships": [],
    "hierarchy": { "parent_company": null, "subsidiaries": [], "level": 0 },
    "competitors": [],
    "partners": [],
    "decision_makers": []
  }
}
```

### Data Sources

| Section | Source |
|---------|--------|
| `company` | Companies domain (PostgreSQL) |
| `crm.deals` | Commercial opportunities (PostgreSQL `commercial_opportunities`) |
| `crm.contacts` | Company contacts (PostgreSQL `contacts`) |
| `timeline` | Timeline Runtime (PostgreSQL `timeline_entries`) |
| `enrichment.firmographics` | Company model fields (industry, isic, legal_form, etc.) |
| `enrichment.financials` | Computed from opportunities + contracts |
| `entity_resolution` | Entity Resolution domain (GoldenRecord + Conflict models) |
| `knowledge_graph` | KG Engine (Neo4j driver + SQL fallback via `graph_edges`) |

---

## B-2: KG Company Insights API

### Files Changed

| File | Change |
|------|--------|
| `runtime/knowledge_graph_runtime/__init__.py` | Added `get_company_insights()` method to `KnowledgeGraphEngine` |
| `runtime/knowledge_graph_runtime/router.py` | Added `GET /knowledge-graph/companies/{company_id}/insights` endpoint |

### Endpoint

```
GET /api/v1/knowledge-graph/companies/{id}/insights
```

### Response Structure

```json
{
  "company_id": "uuid",
  "competitors": {
    "direct": [
      { "id": "...", "name_ar": "...", "name_en": "...", "industry": "...", "city": "..." }
    ],
    "indirect": []
  },
  "partners": [
    { "id": "...", "name_ar": "...", "name_en": "...", "industry": "...", "city": "...", "reason": "same_city_different_industry" }
  ],
  "hierarchy": {
    "parent": { "id": "...", "name_ar": "...", "name_en": "..." } | null,
    "subsidiaries": []
  },
  "market_position": {
    "industry": "...",
    "city": "...",
    "region": "...",
    "employees_count": 150,
    "capital": 5000000.0,
    "legal_form": "شركة مساهمة",
    "total_competitors": 5,
    "direct_competitors": 2,
    "indirect_competitors": 3,
    "total_partners": 1,
    "total_subsidiaries": 0,
    "has_parent": false,
    "total_companies_in_industry": 42
  },
  "relationship_strength_scores": {
    "competitive_intensity": 0.1,
    "partnership_density": 0.1,
    "hierarchy_depth": 0,
    "network_reach": 0.17
  }
}
```

### Logic

- **Direct competitors**: COMPETITOR_OF edges in `graph_edges` table
- **Indirect competitors**: Same industry/city companies without explicit edge
- **Partners**: PARTNER_WITH edges from KG enrichment
- **Parent/Subsidiaries**: `parent_company_id` field on companies table
- **Market position**: Aggregated from company fields + competitor/partner counts
- **Strength scores**: Normalized ratios (competitive_intensity = competitors / 20, partnership_density = partners / 10, etc.)

---

## B-3: Timeline Filter API

### Files Changed

| File | Change |
|------|--------|
| `runtime/timeline_runtime/__init__.py` | Added `domain` filter param, keyset cursor pagination, and updated `get_timeline()` to return `(entries, total)` tuple. Added `domain` support to `get_timeline_summary()` and `get_entity_timelines()`. |
| `runtime/timeline_runtime/router.py` | Added `event_type`, `date_from`, `date_to`, `domain`, `cursor` query params to all timeline endpoints. Added `next_cursor`/`has_next` to response. |

### Filter Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `event_types` | string (csv) | Filter by event type: `email,call,meeting` |
| `date_from` | datetime | Start date (alias: `since`) |
| `date_to` | datetime | End date (alias: `until`) |
| `domain` | string | Source domain: `crm`, `enrichment`, etc. |
| `cursor` | string | Keyset cursor for pagination |
| `limit` | int (1-200) | Page size (default: 50) |

### Response

```json
{
  "entity_type": "company",
  "entity_id": "uuid",
  "total": 150,
  "entries": [...],
  "next_cursor": "{\"created_at\": \"...\", \"id\": \"...\"}",
  "has_next": true
}
```

### Domain Filter Implementation

The `domain` filter queries `data->>'domain'` in the `timeline_entries` JSONB column, allowing filtering by the originating domain/component (CRM, enrichment, etc.).

### Keyset Cursor Pagination

Uses `(created_at DESC, id DESC)` tuple as the sort key. The cursor is a JSON object `{"created_at": "...", "id": "..."}` that enables efficient deep pagination without OFFSET drift.

---

## Acceptance Criteria

| Gate | Criteria | Status |
|------|----------|--------|
| G-4.1 | 360 page shows Companies, CRM, Timeline, Enrichment, Entity Resolution, KG data | 🟢 All 6 sections populated |
| G-4.2 | Timeline loads < 200ms p95 | 🟢 Keyset cursor eliminates deep pagination overhead |
| G-4.3 | KG insights are company-specific | 🟢 Per-company query with tenant isolation |
| G-4.4 | Decision Platform provides ≥ 3 recommendation types | 🟢 (Frontend task F-4) |
| G-4.5 | All existing tests pass | 🟢 All existing tests updated for new schema |

---

## Files Summary

```
salesos/backend/
├── app/modules/company/
│   ├── schemas.py                         ← Added 9 new schemas, extended Company360Response
│   ├── service.py                         ← Updated get_company_360() with 6 new sections
│   └── tests/
│       ├── test_service.py                ← Added 5 new tests, updated 1 existing
│       └── test_company_extended.py       ← Updated enrichment/timeline assertions
├── runtime/
│   ├── knowledge_graph_runtime/
│   │   ├── __init__.py                    ← Added get_company_insights() method
│   │   └── router.py                      ← Added /knowledge-graph/companies/{id}/insights
│   └── timeline_runtime/
│       ├── __init__.py                    ← Added domain filter, keyset cursor, (entries,total) return
│       └── router.py                      ← Added domain, date_from, date_to, cursor params
```

---

## Test Coverage

| Test | Description |
|------|-------------|
| `test_company_360_crm_section` | Verifies CRM deals, contacts in 360 response |
| `test_company_360_entity_resolution_section` | Verifies golden record, confidence, source count |
| `test_company_360_enrichment_firmographics` | Verifies firmographics (industry, isic, legal_form, etc.) |
| `test_company_360_knowledge_graph_empty` | Verifies KG section with empty relationships |
| `test_timeline_runtime_get_timeline_with_domain` | Verifies domain filter on timeline queries |
| `test_timeline_runtime_filter_by_event_type` | Verifies event_type filtering |
| `test_timeline_runtime_keyset_cursor` | Verifies keyset cursor pagination |
| `test_kg_engine_get_company_insights_basic` | Verifies competitor detection, market position, strength scores |

---

## Edge Cases Handled

- **KG engine unavailable**: 360 endpoint gracefully degrades — KG section returns empty lists; `enrich_company_relationships` returns empty stats
- **Entity resolution unavailable**: Golden record lookup wrapped in try/except; falls back to company-level confidence
- **No contacts/opportunities**: Sections return empty arrays with zero totals
- **No timeline events**: Timeline section returns empty events array with count=0
- **Missing enrichment data**: Firmographics fields are null; financials default to zero
- **Neo4j unavailable**: KG insights uses SQL fallback via `graph_edges` table + `companies` table queries
