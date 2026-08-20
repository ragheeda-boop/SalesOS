# C.2 Sales Activity Attribution — Forensic Audit Report

**Status:** Audit Complete  
**Date:** 2026-08-09  
**Scope:** READ-ONLY — what CAN the current code link today?  
**Depends On:** ADR-029 (Canonical Opportunity), ADR-030 (Opportunity ↔ Contact)  
**Precedes:** ADR-C2 (Attribution Architecture Decision)

---

## Executive Summary

SalesOS has **no operational path to link emails or calendar events to opportunities**. The pipeline that syncs Google activity (Gmail + Calendar) stops at company-level resolution. The intelligence mapping pipeline that could perform deeper resolution (contact, opportunity) is architecturally complete but never instantiated. Two separate database systems exist for activity tracking — the sync pipeline (`employee_email_events`, `employee_calendar_events`) and the commercial domain (`meetings`, `emails`) — and they never intersect. Employee 360 shows pipeline data but cannot display which activities contributed to which deals.

**Critical gap:** There is no code that can answer the question: "Which emails and meetings are related to this opportunity?"

---

## 1. The Two-System Architecture

SalesOS has **two separate, disconnected systems** for tracking engagement activity:

```
┌─────────────────────────────────────┐  ┌─────────────────────────────────────┐
│  SYSTEM A: Google Sync Pipeline     │  │  SYSTEM B: Commercial Meetings/Emails │
│  (Operational, automated)           │  │  (Manual CRUD via REST API)          │
├─────────────────────────────────────┤  ├─────────────────────────────────────┤
│ employee_email_events               │  │ emails table                         │
│ ├── related_company_ids ✓ LIVE      │  │ ├── opportunity_id ✓ FK              │
│ ├── related_contact_ids ✗ DEAD      │  │ └── (populated via POST /api/v1/...) │
│ ├── related_opportunity_ids ✗ DEAD  │  │                                     │
│ └── 26 columns                      │  │                                     │
│                                     │  │ meetings table                       │
│ employee_calendar_events            │  │ ├── opportunity_id ✓ FK              │
│ ├── related_company_ids ✓ LIVE      │  │ └── (populated via POST /api/v1/...) │
│ ├── related_contact_ids ✗ DEAD      │  │                                     │
│ ├── related_opportunity_ids ✗ DEAD  │  │                                     │
│ └── 29 columns                      │  │                                     │
│                                     │  │                                     │
│ activity_records                    │  │                                     │
│ ├── entity_type: "communication"    │  │                                     │
│ ├── NO FK constraints              │  │                                     │
│ └── target_type/target_id set       │  │                                     │
│    but never consumed               │  │                                     │
└─────────────────────────────────────┘  └─────────────────────────────────────┘

        NO CODE BRIDGES THESE TWO SYSTEMS TOGETHER
```

**File evidence:**
- System A: `communication_hub/gmail_sync.py:207-243`, `calendar_sync.py:162-221`
- System B: `domains/commercial/infrastructure/models.py:267-286` (MeetingModel), `286+` (EmailModel)
- Migration: `alembic/versions/0013_meetings_emails.py:24-36`

---

## 2. What CAN the Current Code Link?

### Email Events (`employee_email_events`)

| Link | Status | Mechanism | Evidence |
|------|:------:|-----------|----------|
| Email → Employee | **YES** | `employee_id` set during INSERT | `gmail_sync.py:224` |
| Email → Company | **YES** | `related_company_ids` via domain match (LIKE query) | `gmail_sync.py:200-201, 242`; `company_linker.py:46-77` |
| Email → Contact | **PARTIAL** | Contact row created/updated in `contacts` table, but contact ID NOT written back to event row | `contact_sync.py:85-135`; `gmail_sync.py:177-178` returns count only |
| Email → Opportunity | **NO** | Zero code exists | `related_opportunity_ids` always `[]`; no `opportunity_id` reference in `communication_hub/` |

### Calendar Events (`employee_calendar_events`)

| Link | Status | Mechanism | Evidence |
|------|:------:|-----------|----------|
| Calendar → Employee | **YES** | `employee_id` set during INSERT | `calendar_sync.py:200` |
| Calendar → Company | **YES** | `related_company_ids` via domain match | `calendar_sync.py:179,196` |
| Calendar → Contact | **PARTIAL** | Contacts UPSERTED but contact IDs NOT written back to event row | `calendar_sync.py:146-148` (upsert only) |
| Calendar → Opportunity | **NO** | Zero code exists | `related_opportunity_ids` always `[]` |

### Company Resolution (Bridge Layer)

| Link | Status | Mechanism | Evidence |
|------|:------:|-----------|----------|
| Domain → Company | **YES** | `company_linker.py` — LIKE match on `companies.website` or `companies.email` | `company_linker.py:71-74` |
| Email → Contact (Upsert) | **YES** | `contact_sync.py` — requires company match first; rejects free domains | `contact_sync.py:78-81, 85-135` |
| Email → Contact (on event row) | **NO** | `contact_sync.py` returns `{"created": X, "updated": Y}` — no contact IDs returned | `contact_sync.py:139-147` |

---

## 3. What CAN'T the Current Code Link?

### Dead Columns (exist in schema, never populated, never queried)

| Column | Tables | Evidence |
|--------|--------|----------|
| `related_contact_ids` (JSONB) | `employee_email_events`, `employee_calendar_events` | Never in any INSERT/UPDATET/SELECT. Migration `0044` lines 63, 104; Model lines 43, 93. |
| `related_opportunity_ids` (JSONB) | `employee_email_events`, `employee_calendar_events` | Same — completely dead. |
| `ai_summary` | `employee_email_events` | Model line 95. Not in INSERT. |
| `ai_sentiment` | `employee_email_events` | Model line 96. Not in INSERT. |
| `ai_action_items` | `employee_email_events` | Model line 97. Not in INSERT. |
| `response_time_seconds` | `employee_email_events` | Model line 91. Not in INSERT. |
| `sync_token` | `employee_calendar_events` | Stored on `google_accounts` instead, never written here. |

### Blocked Resolution Paths

| Desired Link | Why It's Blocked |
|-------------|-----------------|
| Email event → Contact | `contact_sync.py` upserts to `contacts` table but doesn't return contact IDs. `gmail_sync.py` stores `related_company_ids` (companies) but has no UPDATE step for `related_contact_ids`. |
| Calendar event → Contact | Same pattern as email — contacts upserted but not linked back. |
| Email event → Opportunity | No awareness of opportunities in `communication_hub/`. The `related_opportunity_ids` column is dead. No explicit reference detection in the sync path. |
| Calendar event → Opportunity | Same — no opportunity awareness. |
| Activity records → Opportunity | NBA engine queries `WHERE entity_id = opportunity_id` but production INSERTs use `entity_type="communication"` with `entity_id=message_id`, never `entity_id=opportunity_id`. |
| Contact → Opportunity (any path) | ADR-030 proposed `opportunity_contacts` junction table — not yet created. No code exists. |

---

## 4. Entity Resolution Layers

### Operational (Wired)

| Layer | Input → Output | Mechanism | File |
|-------|----------------|-----------|------|
| **Domain → Company** | Email domains → `related_company_ids` | LIKE `%domain%` on `companies.website` / `companies.email` | `company_linker.py:46-77` |
| **Email → Contact (Upsert)** | Email addresses → `contacts` table rows | Upsert by `(tenant_id, lower(email))`, requires company match first | `contact_sync.py:48-147` |
| **CR-Number → Golden Record** | Structured records → Merged company | Jaro-Winkler fuzzy match, source priority merge | `entity_resolution/service.py:66-189` |

### Blueprint (Implemented but NEVER instantiated)

The **5-stage MappingPipeline** (`intelligence/activity_intelligence/mapping/`) is architecturally complete:

| Stage | File | What It Does | Status |
|-------|------|-------------|:------:|
| 1. Normalizer | `normalizer.py` | Cleans email addresses, strips Re:/Fwd:, MIME decodes, extracts `[OPP-123]` hints | **Complete** |
| 2. Resolver | `resolver.py` | Extracts person name, company hint (from domain), opportunity hint (from `[OPP-...]` regex) | **Complete** |
| 3. Matcher | `matcher.py` | Priority chain: explicit_ref → opportunity_lookup → contact_lookup → domain_match → ai_match | **STUB** — CompanyReader/ContactReader/OpportunityReader have no concrete implementations |
| 4. Confidence | `confidence.py` | Method weights: explicit=1.0, opp_lookup=0.9, contact=0.8, domain=0.6, ai=0.4; threshold=0.5 | **Complete** |
| 5. Mapper | `mapper.py` | Builds `MappingResult` with company_id/contact_id/opportunity_id | **In-memory only** — no DB write |

**The entire pipeline is never instantiated anywhere in production code.** Tests confirm: `test_mapper.py` instantiates `MappingPersister()` with zero arguments (no DB session required) — proving it's purely in-memory.

**Missing concrete implementations:**
- `CompanyReader` — ABC defined (`contracts/repository.py:71`) but no `PostgresCompanyReader` exists
- `ContactReader` — ABC defined (`contracts/repository.py:88`) but no `PostgresContactReader` exists
- `OpportunityReader` — Not even defined as an ABC; `matcher.py` just checks `self._opportunity_reader is not None`

### Explicit Opportunity Reference Detection

**Code EXISTS but is NOT INTEGRATED into the operational sync path.**

The `resolver.py:_extract_opportunity_hint()` method (lines 88-100) detects patterns:
```python
\[OPP[_-]?(\d+)\]
\[OPPORTUNITY[_-]?(\d+)\]
OPP[_-]?(\d+)
```

But this detection is only available within the un-wired `MappingPipeline`. The operational sync (`gmail_sync.py`, `calendar_sync.py`) never calls it.

**Odoo verification note:** The live Odoo instance had zero opportunities with bracket-pattern names. This detection would only be useful if users manually add `[OPP-...]` tags to email subjects.

---

## 5. Activity Runtime (`activity_records`)

**Schema:** `runtime/activity_runtime/__init__.py:46-69`

| Column | Type | Key |
|--------|------|-----|
| `id` | String(64) PK | UUID4 |
| `actor` | String(255) | Who |
| `action` | String(100) | What (`email.received`, `meeting.synced`, etc.) |
| `entity_type` | String(50) | Primary entity type |
| `entity_id` | String(64) | Primary entity ID (message_id, event_id) |
| `target_type` | String(50) | Secondary entity type (nullable) |
| `target_id` | String(64) | Secondary entity ID (nullable) |
| `metadata` | JSONB | Flexible payload |
| `tenant_id` | String(36) | Multi-tenancy |
| `timestamp` | DateTime | When |

**FOREIGN KEYS: NONE.** Zero FK constraints on any column.

### Entity Types in Production

| Value | Source | Code Path |
|-------|--------|-----------|
| `"communication"` | Email sync worker | `intelligence/activity_intelligence/sync/email_sync.py:87` |
| `"communication"` | Calendar sync worker | `intelligence/activity_intelligence/sync/calendar_sync.py:114` |
| Dynamic (from domain events) | `on_domain_event()` | `runtime/activity_runtime/__init__.py:393` |

**`"commercial_opportunities"` is NEVER used as an entity_type.** The string appears 82 times in the codebase but exclusively as a table name, never as an entity_type value.

### NBA Engine's Broken Join

The NBA engine (`runtime/nba_engine/__init__.py`) attempts to link activities to opportunities:
1. `_normalize()` (lines 333-374): Queries `commercial_opportunities`, then queries `activity_records WHERE entity_id = opportunity_id`
2. Joined **in Python memory**, not SQL

**The gap:** No production code writes opportunity IDs into `activity_records.entity_id`. The `target_id`/`target_type` columns could carry the link (sync workers DO set `target_type=result.entity_type` and `target_id=result.entity_id`) but the NBA engine queries by `entity_id`, not `target_id`.

---

## 6. Employee 360 — Opportunity Engagement

### What It Shows

| Component | Opportunity Data? | Evidence |
|-----------|:----------------:|----------|
| Backend: Portfolio pipeline query | **YES** | `service.py:205-226` — queries `commercial_opportunities` by `owner_id` |
| Backend: KPIs (revenue, pipeline, win_rate) | **YES** | `service.py:330-347` — computed from portfolio |
| Backend: AI coach actions | **YES** | `service.py:462-489` — "Build your pipeline", "Convert pipeline to revenue" |
| Frontend: Any tab or widget | **NO** | Zero UI components render `portfolio.pipeline` or `kpis.pipeline` |
| Backend: Per-opportunity engagement | **NO** | No join between portfolio opportunities and email/calendar/activity events |

### Scoring Algorithm

The `EmployeeScoringEngine` (`domains/employee/scoring.py:25-64`) uses **four factors only**:

| Factor | Weight | Method |
|--------|:------:|--------|
| Signal Volume | 30% | `min(len(signals) / 100.0, 1.0)` |
| Recency | 25% | Days since most recent signal, 90-day max |
| Diversity | 20% | Unique signal types / 6 + unique sources / 3 |
| Completion Rate | 25% | Completed tasks / total workflow signals |

**Zero awareness of opportunities, pipeline value, win rate, or deal count.**

### Signal Pipeline

Two signal types (`DEAL_ASSIGNED`, `DEAL_STAGE_CHANGED`) are opportunity-related (`domains/employee/signals.py:73`), but they only detect keywords in action strings — they don't extract or store `opportunity_id`. The metadata is a passthrough dict.

---

## 7. Summary: What's Needed for Attribution

### Current State

```
Email/Meeting → [domain match] → Company       ✓ WORKING
Email/Meeting → [contact sync] → Contacts table ✓ WORKING (but not linked back to event row)
Email/Meeting → [dead column]  → Contact        ✗ related_contact_ids never populated
Email/Meeting → [dead column]  → Opportunity     ✗ related_opportunity_ids never populated
Contact       → [no table]     → Opportunity     ✗ opportunity_contacts not yet created
Activity      → [broken join]  → Opportunity     ✗ entity_id never holds opportunity IDs
```

### Attribution Chain (Required for C.2)

```
Email / Meeting    [employee_email_events, employee_calendar_events]
      │
      ▼
Email → Contact    [contact_sync.py — EXISTS but return value not used]
      │                 FIX: return contact IDs, write to related_contact_ids
      ▼
Contact → Opportunity  [opportunity_contacts — proposed in ADR-030, NOT YET CREATED]
      │                 IMPLEMENT: create junction table per ADR-030
      ▼
Activity → Attribution [NEW: activity_attributions table or enrichment of activity_records]
      │                 DESIGN: candidate generation → evidence → confidence → persistence
      ▼
Employee 360         [enrich _get_portfolio() with junction join + attribution data]
```

### Prerequisites to C.2 Attribution

| Prerequisite | Status | Required For |
|-------------|:------:|-------------|
| ADR-029: Canonical Opportunity | **READY** | Source of truth for opportunity IDs |
| ADR-030: `opportunity_contacts` junction table | **RATIFIED** | Contact → Opportunity link |
| Fix: `contact_sync.py` return contact IDs | **GAP** | Email → Contact (on event row) |
| Fix: Write `related_contact_ids` in sync pipeline | **GAP** | Email/Calendar → Contact (on event row) |
| Implement: `opportunity_contacts` table | **GAP** | Contact → Opportunity |

---

## 8. Key Files Referenced

| File | Lines | Content |
|------|-------|---------|
| `communication_hub/gmail_sync.py` | 200-243 | Email INSERT — fields populated/not populated |
| `communication_hub/calendar_sync.py` | 162-249 | Calendar INSERT/UPDATE — fields populated/not populated |
| `communication_hub/contact_sync.py` | 48-147 | Email → Contact upsert, no back-link to events |
| `communication_hub/company_linker.py` | 46-77 | Domain → Company LIKE match |
| `domains/employee/intelligence_models.py` | 15-117 | ORM models for both event tables |
| `alembic/versions/0044_create_calendar_email_events.py` | 38-113 | DDL for both event tables |
| `runtime/activity_runtime/__init__.py` | 46-69 | activity_records Core Table (no FKs) |
| `runtime/nba_engine/__init__.py` | 333-374 | Broken join: activities WHERE entity_id = opportunity_id |
| `intelligence/activity_intelligence/mapping/__init__.py` | 25-98 | MappingPipeline — never instantiated |
| `intelligence/activity_intelligence/mapping/matcher.py` | 43-53 | 5-layer priority chain — no concrete readers |
| `intelligence/activity_intelligence/mapping/mapper.py` | 26-60 | In-memory only, no DB write |
| `intelligence/activity_intelligence/mapping/resolver.py` | 88-100 | [OPP-NNN] detection — not wired |
| `intelligence/activity_intelligence/sync/email_sync.py` | 83-97 | Production INSERT into activity_records |
| `employee_360/service.py` | 198-399 | Portfolio, activity, signals, timeline — no cross-reference |
| `domains/employee/scoring.py` | 25-64 | 4-factor scoring — zero opportunity awareness |
| `domains/employee/signals.py` | 57-89 | CRM signals — keyword detection only, no opportunity_id |
| `entity_resolution/service.py` | 572-665 | Company merge moves opportunities — contact→opp not handled |
| `domains/commercial/infrastructure/models.py` | 267-286 | MeetingModel — has opportunity_id FK |
| `alembic/versions/0013_meetings_emails.py` | 24-36 | Meetings DDL with opportunity_id FK |
| `docs/adr/0030-opportunity-contact-relationship.md` | — | ADR-030 — opportunity_contacts junction table proposal |
