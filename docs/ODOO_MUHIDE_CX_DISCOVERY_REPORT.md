# ODOO MUHIDE CX TEAM
# READ-ONLY DATA DISCOVERY & MIGRATION MAPPING REPORT

**Date:** 2026-08-26
**Prepared by:** Automated Discovery (Read-Only)
**Scope:** Source Database (SalesOS/PostgreSQL) → Odoo 17.0 Enterprise (Muhide CX Team)
**Status:** Discovery & Mapping Only — NO WRITES EXECUTED

---

## A. Source Database

| Property | Value |
|----------|-------|
| Engine | PostgreSQL 16.14 (Debian) |
| Database | `salesos` |
| Host | localhost:5432 (Docker: salesos-postgres-1) |
| User | `salesos` (via Docker exec) |
| Schemas | `public`, `audit`, `activity`, `company`, `crm`, `identity` |
| Total Tables | 155+ (public schema) |
| Alembic Version | `h2i3j4k5l6m8` |
| Access Method | `docker exec salesos-postgres-1 psql` (read-only queries) |

### Key Source Tables for Helpdesk Migration

| Table | Rows | Relevance |
|-------|------|-----------|
| `companies` | 5 | Customer/Company records → `res.partner` |
| `contacts` | 3 | Contact records → `res.partner` (individual) |
| `users` | 18 | System users → `res.users` |
| `tenants` | 30 | Multi-tenant isolation (mostly test/probe tenants) |
| `tasks` | 0 | Task tracking (empty) |
| `commercial_opportunities` | 1 | Sales opportunities |
| `activity_records` | 120 | Activity audit trail |
| `domain_events` | 127 | Domain event log |
| `timeline_entries` | 3 | Timeline events |
| `signal_catalog` | 22 | Signal definitions (platform content) |
| `rag_documents` | 5 | RAG corpus |
| `icp_profiles` | 1 | ICP profile (pif tenant) |
| `audit_logs` | 104 | Audit trail |
| `odoo_external_ids` | 0 | No existing Odoo sync mapping |

---

## B. Connection Test (Source DB)

| Test | Result |
|------|--------|
| Docker container running | PASS (`salesos-postgres-1` Up 4 days) |
| psql accessible | PASS |
| Database `salesos` exists | PASS |
| Read queries | PASS (all discovery queries succeeded) |
| Write operations | **NOT EXECUTED** (read-only protocol) |

---

## C. Odoo Connection Test

| Property | Value |
|----------|-------|
| URL | `https://odoo-ps-psae-ratl.odoo.com` |
| Database | `odoo-ps-psae-ratl-main-14005796` |
| Protocol | XML-RPC 2.0 (`/xmlrpc/2/common` + `/xmlrpc/2/object`) |
| User | Ragheed Al Madani (`ragheed.a@muhide.com`) |
| User ID | 43 |
| Company | Ratl Technology Ltd (ID=1) |
| Version | Odoo 17.0+e (Enterprise) |
| Auth Method | API Key via XML-RPC `common.authenticate` |
| JSON-RPC | FAILS (TypeError on `common.authenticate` — non-standard Odoo.com hosting) |
| `ir.model` access | DENIED (requires Administration/Access Rights group) |

| Test | Result |
|------|--------|
| Version check | PASS |
| Authentication | PASS (uid=43) |
| User info read | PASS |
| helpdesk.ticket read | PASS |
| helpdesk.team read | PASS |
| helpdesk.stage read | PASS |
| res.partner read | PASS |
| res.users read | PASS |
| res.company read | **FAIL** (security restriction: `attendance_kiosk_key` field) |
| ir.model enumeration | **FAIL** (requires admin group) |
| Write operations | **NOT EXECUTED** (read-only protocol) |

---

## D. Muhide CX Team Discovery

### Team: Muhide CX Team (ID=1)

| Property | Value |
|----------|-------|
| Team ID | 1 |
| Name | Muhide CX Team |
| Active | True |
| Company | Ratl Technology Ltd (ID=1) |
| Published on Website | True |
| Website URL | `/helpdesk/muhide-cx-team-1` |
| Alias | `customer-team@support.muhide.com` |
| Assign Method | Randomly |
| Auto Assignment | False |
| Member IDs | [2] (Mohamed Umair) |
| Privacy Visibility | Portal |
| Use SLA | True |
| Use Rating | True |
| Use Website Form | True |
| Use Livechat | True |
| Use Knowledge | True |
| Helpdesk Timesheet | False |
| Sale Timesheet | False |
| Total Tickets | 359 |
| Open Tickets | 12 |
| Unassigned | 3 |
| Closed | 1 |
| SLA Failed | 1 |
| Auto Close | False (7 days) |
| Resource Calendar | Standard 48 hours/week |
| Created | 2024-08-23 |
| Created By | OdooBot |
| Last Write | 2025-01-23 (by Mohamed Umair) |

### Stage IDs in Muhide CX Team: [1, 6, 4, 5, 3]

| Stage ID | Name (from data) |
|----------|------------------|
| 1 | (New / Default) |
| 3 | On Hold |
| 4 | Solved |
| 5 | Canceled |
| 6 | In Progress |

### All Odoo Helpdesk Stages

| ID | Name | Sequence | Folded |
|----|------|----------|--------|
| 1 | New | 0 | False |
| 3 | On Hold | 20 | False |
| 4 | Solved | 40 | True |
| 5 | Canceled | 50 | True |
| 6 | In Progress | 3 | False |
| 7 | QA done | 40 | True |
| 8 | Tech support done | 40 | True |
| 9 | Onboard buyers / seller | 6 | False |
| 10 | UA & Transaction completion | 7 | False |
| 11 | onboarding completed | 12 | True |
| 12 | Account & Users setup | 4 | False |
| 13 | Training / DEMO | 5 | False |
| 14 | (onboarding stage) | - | - |
| 19 | dropped | 11 | True |
| 20 | TO DO (buyer/seller) List | 1 | False |
| 21 | on hold | 2 | False |

### All Helpdesk Teams

| ID | Name | Tickets | Published | SLA |
|----|------|---------|-----------|-----|
| 1 | Muhide CX Team | 359 | Yes | Yes |
| 2 | QA Team | 2 | No | Yes |
| 3 | Technical Team | 0 | No | Yes |
| 221 | Users Onboarding | 56 | No | Yes |

### Ticket Types

| ID | Name |
|----|------|
| 4 | Support |
| (others may exist — only type=4 observed in samples) |

### Tags

| ID | Name |
|----|------|
| 47 | (observed in samples) |
| 53 | (observed in samples) |
| 54 | (observed in samples) |

(Actual tag names not retrieved — tags are many2many, names require separate query)

### SLA Policies: 7 total
### SLA Status Records: 10 total

---

## E. Helpdesk Models & Fields

### helpdesk.ticket (Key Fields)

| Field | Type | Required | Relation | Notes |
|-------|------|----------|----------|-------|
| `name` | char | **REQ** | - | Subject/Title |
| `stage_id` | many2one | opt | helpdesk.stage | Current stage |
| `team_id` | many2one | opt | helpdesk.team | Assigned team |
| `user_id` | many2one | opt | res.users | Assigned agent |
| `partner_id` | many2one | opt | res.partner | Customer |
| `partner_email` | char | opt | - | Customer email |
| `partner_name` | char | opt | - | Customer name |
| `partner_phone` | char | opt | - | Customer phone |
| `priority` | selection | opt | - | 0=Low, 1=Medium, 2=High, 3=Urgent |
| `ticket_type_id` | many2one | opt | helpdesk.ticket.type | Ticket type |
| `tag_ids` | many2many | opt | helpdesk.tag | Tags |
| `description` | html | opt | - | Ticket body |
| `kanban_state` | selection | **REQ** | - | normal/done/blocked |
| `source_id` | many2one | opt | utm.source | Lead source |
| `campaign_id` | many2one | opt | utm.campaign | Campaign |
| `medium_id` | many2one | opt | utm.medium | Medium |
| `company_id` | many2one | opt | res.company | Company |
| `create_date` | datetime | opt | - | Created on |
| `write_date` | datetime | opt | - | Last updated |
| `close_date` | datetime | opt | - | Closed on |
| `ticket_ref` | char | opt | - | Ticket reference |
| `email_cc` | char | opt | - | CC emails |
| `sla_deadline` | datetime | opt | - | SLA deadline |
| `sla_fail` | boolean | opt | - | SLA failed |
| `sla_reached` | boolean | opt | - | SLA reached |
| `message_ids` | one2many | opt | mail.message | Messages/comments |
| `message_attachment_count` | integer | opt | - | Attachment count |
| `rating_ids` | one2many | opt | rating.rating | Ratings |
| `activity_ids` | one2many | opt | mail.activity | Activities |
| `properties` | properties | opt | - | Dynamic properties |

#### Custom Fields (x_studio_* on helpdesk.ticket)

| Field | Type | Label |
|-------|------|-------|
| `x_studio_muhide_user_id` | many2one | Muhide User ID |
| `x_studio_ticket_source` | many2one | Ticket Source |
| `x_studio_interaction_topic` | many2one | Interaction Topic |
| `x_studio_interaction_sub_topic` | many2one | Interaction Sub-topic |
| `x_studio_interaction_sub_sub_topic` | many2one | Interaction Sub Sub-topic |
| `x_studio_interaction_type_1` | many2one | Interaction Type |
| `x_studio_client_type` | selection | Client type (Buyer/Seller) |
| `x_studio_customer_team_agent` | many2one | Customer team Agent |
| `x_studio_customer_team_assignee` | char | Customer team Assignee |
| `x_studio_status` | char | Status |
| `x_studio_next_action` | char | Next Action |
| `x_studio_blocking_issue` | char | Blocking Issue |
| `x_studio_follow_up_date` | date | Follow-up Date |
| `x_studio_owner` | char | Owner |
| `x_studio_industry` | char | Industry |
| `x_studio_sector_sub_industry` | char | Sector, sub industry |
| `x_studio_city` | char | City |
| `x_studio_company_profile` | binary | Company Profile |
| `x_studio_any_needed_docs` | binary | Any needed - additional docs |
| `x_studio_expected_first_transaction` | date | Expected first transaction |
| `x_studio_expected_first_ua_signing` | date | Expected first UA signing |
| `x_studio_expected_number_of_transaction` | char | Expected number of transaction |
| `x_studio_identified_counterparty_name` | char | Identified Counterparty Name |
| `x_studio_counterparty_names` | char | Counterparty Names |
| `x_studio_related_parties` | many2one | Related parties |
| `x_studio_account_setup_complete_cr_vat_users_admin_access` | boolean | Account setup complete |
| `x_studio_kickoff_training_delivered` | boolean | Kickoff & training delivered |
| `x_studio_buyer_profile_complete` | boolean | Buyer profile complete |
| `x_studio_unified_agreement_signed` | boolean | Unified Agreement signed |
| `x_studio_first_transaction_completed` | boolean | First transaction completed |
| `x_studio_flyer_distributed` | boolean | Flyer distributed |
| `x_studio_follow_up_flyer_distributed` | boolean | Follow-up Flyer distributed |
| `x_studio_3_priority_counterparties_identified` | boolean | 3 priority counterparties identified |
| `x_studio_3_buyers_onboarded_with_ua_signed` | selection | 3 buyers onboarded (met/not met) |
| `x_studio_3_transactions_completed_1_per_buyer` | selection | 3 transactions completed (met/not met) |
| `x_studio_boolean_field_*` | boolean | Various checkboxes (New CheckBox) |
| `x_studio_*_1` | char | Various text fields |
| `x_studio_internal_order_process` | text | Internal order process |
| `x_studio_incentives` | selection | Incentives (Other/Not Agreed) |
| `x_studio_needs_support` | selection | Needs Support |
| `x_studio_many2many_field_*` | many2many | New Tags |

### helpdesk.team (Key Fields)

| Field | Type | Required | Relation |
|-------|------|----------|----------|
| `name` | char | **REQ** | - |
| `company_id` | many2one | opt | res.company |
| `member_ids` | many2many | opt | res.users |
| `stage_ids` | many2many | opt | helpdesk.stage |
| `auto_assignment` | boolean | opt | - |
| `assign_method` | selection | opt | - |
| `privacy_visibility` | selection | opt | - |
| `use_sla` | boolean | opt | - |
| `use_rating` | boolean | opt | - |
| `alias_id` | many2one | opt | mail.alias |

### helpdesk.stage (Key Fields)

| Field | Type | Required | Relation |
|-------|------|----------|----------|
| `name` | char | **REQ** | - |
| `sequence` | integer | opt | - |
| `folded` | boolean | opt | - |
| `template_id` | many2one | opt | mail.template |
| `company_id` | many2one | opt | res.company |

### res.partner (Key Fields)

| Field | Type | Required | Relation |
|-------|------|----------|----------|
| `name` | char | **REQ** | - |
| `email` | char | opt | - |
| `phone` | char | opt | - |
| `mobile` | char | opt | - |
| `street` / `street2` | char | opt | - |
| `city` | char | opt | - |
| `zip` | char | opt | - |
| `state_id` | many2one | opt | res.country.state |
| `country_id` | many2one | opt | res.country |
| `company_id` | many2one | opt | res.company |
| `is_company` | boolean | opt | - |
| `function` | char | opt | - (Job Position) |
| `parent_id` | many2one | opt | res.partner (Company link) |
| `category_id` | many2many | opt | res.partner.category |
| `comment` | text | opt | - (Notes) |
| `vat` | char | opt | - (Tax ID) |
| `x_studio_cr_number` | char | opt | CR Number (custom) |
| `x_studio_muhide_user_id` | many2one | opt | Muhide User ID (custom) |

### res.users (Key Fields)

| Field | Type | Required | Relation |
|-------|------|----------|----------|
| `name` | char | **REQ** | - |
| `email` | char | opt | - |
| `login` | char | **REQ** | - |
| `company_id` | many2one | **REQ** | res.company |
| `groups_id` | many2many | opt | res.groups |
| `active` | boolean | opt | - |
| `signature` | html | opt | - |

---

## F. Source → Odoo Data Mapping

### F1. Companies (SalesOS → Odoo res.partner)

| Source | Source Type | Odoo Model | Odoo Field | Odoo Type | Mapping |
|--------|------------|------------|------------|-----------|---------|
| `companies.id` | uuid | `res.partner` | `x_studio_muhide_user_id` | many2one | Custom link field |
| `companies.name_ar` | varchar(255) | `res.partner` | `name` | char | Direct (primary name) |
| `companies.name_en` | varchar(255) | `res.partner` | `name` | char | Fallback if name_ar empty |
| `companies.cr_number` | varchar(20) | `res.partner` | `x_studio_cr_number` | char | Custom field |
| `companies.status` | varchar(20) | `res.partner` | - | - | No direct Odoo field; use tags |
| `companies.city` | varchar(100) | `res.partner` | `city` | char | Direct |
| `companies.region` | varchar(100) | `res.partner` | `state_id` | many2one | Lookup required |
| `companies.country` | varchar(100) | `res.partner` | `country_id` | many2one | Lookup required |
| `companies.phone` | varchar(50) | `res.partner` | `phone` | char | Direct |
| `companies.email` | varchar(255) | `res.partner` | `email` | char | Direct |
| `companies.website` | varchar(255) | `res.partner` | `website` | char | Direct |
| `companies.address` | text | `res.partner` | `street` + `street2` | char | Split required |
| `companies.capital` | numeric | `res.partner` | - | - | No direct field; custom or notes |
| `companies.currency` | varchar(10) | `res.partner` | `currency_id` | many2one | Lookup required |
| `companies.employees_count` | integer | `res.partner` | `comment` | text | Notes field |
| `companies.activity_description` | text | `res.partner` | `function` | char | Direct |
| `companies.isic_code` | varchar(10) | `res.partner` | `category_id` | many2many | Tag lookup |
| `companies.legal_form` | varchar(50) | `res.partner` | - | - | No direct field |
| `companies.incorporation_date` | date | `res.partner` | - | - | No direct field |
| `companies.expiry_date` | date | `res.partner` | - | - | No direct field |
| `companies.is_active` | boolean | `res.partner` | `active` | boolean | Direct |
| `companies.tags` | jsonb | `res.partner` | `category_id` | many2many | Transform to tags |
| `companies.metadata` | jsonb | `res.partner` | `comment` | text | Append to notes |
| `companies.linkedin_url` | varchar(255) | `res.partner` | `website` | char | Direct |
| `companies.industry` | varchar(255) | `res.partner` | `function` | char | Direct |
| `companies.owner_id` | uuid | `res.partner` | `user_id` | many2one | Lookup by owner mapping |

**Confidence:** MEDIUM — requires region/country lookup tables, address splitting, owner mapping
**Transformation:** REQUIRED — Arabic names, JSON tags, address splitting

### F2. Contacts (SalesOS → Odoo res.partner)

| Source | Source Type | Odoo Model | Odoo Field | Odoo Type | Mapping |
|--------|------------|------------|------------|-----------|---------|
| `contacts.id` | uuid | `res.partner` | `x_studio_muhide_user_id` | many2one | Custom link |
| `contacts.name` | varchar(255) | `res.partner` | `name` | char | Direct |
| `contacts.email` | varchar(255) | `res.partner` | `email` | char | Direct |
| `contacts.phone` | varchar(50) | `res.partner` | `phone` | char | Direct |
| `contacts.position` | varchar(255) | `res.partner` | `function` | char | Direct |
| `contacts.company_id` | uuid | `res.partner` | `parent_id` | many2one | Lookup via company mapping |
| `contacts.is_active` | boolean | `res.partner` | `active` | boolean | Direct |

**Confidence:** HIGH — direct field mapping
**Transformation:** MINIMAL — company_id lookup required

### F3. Users (SalesOS → Odoo res.users)

| Source | Source Type | Odoo Model | Odoo Field | Odoo Type | Mapping |
|--------|------------|------------|------------|-----------|---------|
| `users.id` | uuid | `res.users` | `x_studio_muhide_user_id` | many2one | Custom link |
| `users.email` | varchar(255) | `res.users` | `email` | char | Direct |
| `users.full_name` | varchar(255) | `res.users` | `name` | char | Direct |
| `users.role` | varchar(20) | `res.users` | `groups_id` | many2many | Role→Group mapping |
| `users.tenant_id` | uuid | `res.users` | `company_id` | many2one | Tenant→Company mapping |
| `users.is_active` | boolean | `res.users` | `active` | boolean | Direct |

**Confidence:** LOW — most SalesOS users are test/probe accounts; real users may already exist in Odoo
**Transformation:** REQUIRED — role→group mapping, duplicate detection by email

### F4. Tasks (SalesOS → helpdesk.ticket)

| Source | Source Type | Odoo Model | Odoo Field | Odoo Type | Mapping |
|--------|------------|------------|------------|-----------|---------|
| `tasks.id` | uuid | `helpdesk.ticket` | `x_studio_muhide_user_id` | many2one | Custom link |
| `tasks.title` | varchar(500) | `helpdesk.ticket` | `name` | char | Direct |
| `tasks.description` | text | `helpdesk.ticket` | `description` | html | Wrap in HTML |
| `tasks.status` | varchar(20) | `helpdesk.ticket` | `stage_id` | many2one | Status→Stage lookup |
| `tasks.priority` | varchar(10) | `helpdesk.ticket` | `priority` | selection | Priority mapping |
| `tasks.assignee_id` | uuid | `helpdesk.ticket` | `user_id` | many2one | User mapping |
| `tasks.company_id` | uuid | `helpdesk.ticket` | `partner_id` | many2one | Company→Partner mapping |
| `tasks.opportunity_id` | uuid | `helpdesk.ticket` | - | - | No direct field |
| `tasks.created_at` | timestamptz | `helpdesk.ticket` | `create_date` | datetime | Direct |

**Confidence:** LOW — 0 tasks in source; structure mapping is theoretical
**Transformation:** REQUIRED — status→stage mapping, user lookup

### F5. Activity Records (SalesOS → mail.message)

| Source | Source Type | Odoo Model | Odoo Field | Odoo Type | Mapping |
|--------|------------|------------|------------|-----------|---------|
| `activity_records.action` | varchar(100) | `mail.message` | `message_type` | selection | Action→Type mapping |
| `activity_records.entity_type` | varchar(50) | `mail.message` | `model` | char | Entity→Model mapping |
| `activity_records.entity_id` | varchar(36) | `mail.message` | `res_id` | many2one_reference | ID mapping |
| `activity_records.metadata` | jsonb | `mail.message` | `body` | html | Transform to HTML |
| `activity_records.timestamp` | timestamptz | `mail.message` | `date` | datetime | Direct |

**Confidence:** LOW — activity records are system events, not user messages
**Transformation:** REQUIRED — significant transformation needed

---

## G. Reference/Relation Mapping

### Customer → res.partner

| Strategy | Details |
|----------|---------|
| New records | Create `res.partner` with `is_company=True` for companies |
| Dedup by | `x_studio_cr_number` (CR number) or `name` + `email` |
| Existing Odoo partners | 450 companies + 628 individuals = 1,078 total |
| Source companies | 5 (mostly test data) |
| Overlap detection | **CRITICAL** — must check existing Odoo partners before creating |

### Ticket → helpdesk.ticket

| Strategy | Details |
|----------|---------|
| New records | Create tickets in Muhide CX Team (ID=1) |
| team_id | Fixed: 1 (Muhide CX Team) |
| stage_id | Map from SalesOS task status |
| Dedup by | `x_studio_muhide_user_id` (custom link field) |
| Existing Odoo tickets | 417 (359 in Muhide CX Team) |
| Source tasks | 0 (empty) |

### Team → helpdesk.team

| Strategy | Details |
|----------|---------|
| Target | Muhide CX Team (ID=1) |
| Fixed team | All tickets go to team_id=1 |

### Stage → helpdesk.stage

| SalesOS Status | Odoo Stage | Stage ID |
|----------------|------------|----------|
| `open` / `in_progress` | In Progress | 6 |
| `completed` / `done` | Solved | 4 |
| `cancelled` | Canceled | 5 |
| `on_hold` | On Hold | 3 |
| `new` / `pending` | New | 1 |

### Assignee → res.users

| Strategy | Details |
|----------|---------|
| Mapping | `users.email` → `res.users.email` |
| Fallback | If no match, ticket created unassigned |
| Existing users | 19 in Odoo |
| Source users | 18 in SalesOS (mostly test accounts) |

### Tags → helpdesk.tag

| Strategy | Details |
|----------|---------|
| Create tags | If not existing, create new `helpdesk.tag` records |
| Source tags | `companies.tags` (JSONB), `tasks.tags` (if any) |
| Existing tags | Unknown count (tags query returned but names not listed) |

### External ID Strategy

| Approach | Recommendation |
|----------|----------------|
| Custom field | `x_studio_muhide_user_id` (many2one → `x_muhide_user_ids`) |
| Purpose | Link Odoo records back to SalesOS source records |
| Type | UUID (SalesOS primary key) |
| uniqueness | Per-model: one `x_studio_muhide_user_id` per ticket/partner |

**Note:** `odoo_external_ids` table exists in SalesOS but is empty — no prior sync has occurred.

---

## H. Data Quality Findings

### Source Database (SalesOS)

| Issue | Severity | Count | Details |
|-------|----------|-------|---------|
| Duplicate contact emails | INFO | 0 | No duplicate emails in contacts |
| Contacts with null email | INFO | 0 | All contacts have emails |
| Contacts with null phone | WARN | 1 | 1 contact missing phone |
| Companies without contacts | WARN | 3 | 3 of 5 companies have no contacts |
| Tasks without assignee | INFO | 0 | 0 tasks total (empty table) |
| Arabic text in company names | INFO | 2 | `name_ar` fields contain Arabic |
| Test/probe tenants | INFO | 29 of 30 | Most tenants are test data |
| Test users | INFO | 17 of 18 | Most users are test accounts |

### Odoo Instance

| Issue | Severity | Count | Details |
|-------|----------|-------|---------|
| Duplicate partner emails | **HIGH** | 71 email groups | Many partners share emails (e.g., `ebtehal.m@ratlfintech.com`: 5 records) |
| Arabic text in emails field | **HIGH** | ~50+ | Some "email" fields contain Arabic text like "مصانع", "مقاولين" — used as tags/categories, not real emails |
| Tickets without partner | WARN | 37 | 37 tickets have no customer linked |
| Tickets without assignee | WARN | 104 | 104 tickets unassigned |
| Partners with `-` email | WARN | few | Some partners have `-` as email |
| User email overlap | INFO | Several | Some Odoo users have same email as SalesOS users (e.g., `amit@ratlfintech.com`) |

---

## I. Missing/Required Fields

### Source → Odoo Gaps

| Source Field | Odoo Field | Gap | Resolution |
|-------------|------------|-----|------------|
| `companies.region` | `res.partner.state_id` | Needs lookup table for Saudi regions | Create mapping or use `comment` |
| `companies.country` | `res.partner.country_id` | Needs ISO country code lookup | Map "Saudi Arabia" → country_id |
| `companies.address` | `res.partner.street` + `street2` | Single field → two fields | Split on newline/max length |
| `companies.capital` | No direct field | No Odoo field for company capital | Use `comment` or custom field |
| `companies.currency` | `res.partner.currency_id` | Needs currency code → ID lookup | Map "SAR" → currency_id |
| `companies.isic_code` | `res.partner.category_id` | Needs tag creation | Create tags from ISIC codes |
| `companies.legal_form` | No direct field | No Odoo field | Use `comment` or custom field |
| `companies.incorporation_date` | No direct field | No Odoo field | Use `comment` or custom field |
| `tasks.opportunity_id` | No direct field | No Odoo field for ticket→opportunity link | Use `comment` or custom field |
| `users.tenant_id` | `res.users.company_id` | Multi-tenant → single company | Map tenant to company |

### Odoo → Source Gaps

| Odoo Field | Source Field | Gap | Resolution |
|------------|-------------|-----|------------|
| `helpdesk.ticket.stage_id` | `tasks.status` | Different stage names | Create mapping table |
| `helpdesk.ticket.priority` | `tasks.priority` | Different priority scales | Map: low→0, medium→1, high→2, urgent→3 |
| `helpdesk.ticket.partner_id` | `tasks.company_id` | UUID → Odoo ID | Requires partner lookup |
| `helpdesk.ticket.user_id` | `tasks.assignee_id` | UUID → Odoo ID | Requires user lookup |
| `helpdesk.ticket.tag_ids` | `tasks.tags` | JSONB → many2many | Transform required |

---

## J. Duplicate Analysis

### Odoo Duplicate Partners (by email)

| Email | Count | Risk |
|-------|-------|------|
| `ebtehal.m@ratlfintech.com` | 5 | HIGH |
| `مصانع` | 9 | CRITICAL (not real email) |
| `مصانع وموزعين` | 22 | CRITICAL (not real email) |
| `موردين خرسانة` | 17 | CRITICAL (not real email) |
| `mohammed.a@ratlfintech.com` | 4 | HIGH |
| `nada@ratlfintech.com` | 4 | HIGH |
| `nojood.a@ratlfintech.com` | 4 | HIGH |
| `accounts@ratlfintech.com` | 4 | HIGH |
| `nada@ratlfintech.com` | 4 | HIGH |
| (71 total email groups with duplicates) | - | - |

**Impact:** Duplicate detection during import must handle these carefully. Arabic text entries are NOT emails — they appear to be used as category labels in the email field (data quality issue in Odoo).

---

## K. Migration Risks

| # | Risk | Severity | Mitigation |
|---|------|----------|------------|
| 1 | **Duplicate partner emails in Odoo** — 71+ email groups with multiple records | HIGH | Pre-migration dedup required; match by CR number + name, not email alone |
| 2 | **Arabic text in email fields** — Odoo has non-email text in partner emails | HIGH | Filter: only match valid email format; skip Arabic entries |
| 3 | **Source has minimal real data** — 5 companies, 3 contacts, 0 tasks | MEDIUM | Migration scope is very small; mostly structural validation |
| 4 | **Multi-tenant → single-company** — SalesOS is multi-tenant, Odoo is single-company | MEDIUM | Map tenant_id → company_id; or ignore tenant isolation |
| 5 | **No existing sync** — `odoo_external_ids` table is empty | LOW | No conflicting prior sync to worry about |
| 6 | **UUID → Integer ID** — Source uses UUID PKs, Odoo uses integer PKs | LOW | Use `x_studio_muhide_user_id` custom field for linking |
| 7 | **res.company read denied** — Non-admin user cannot read company fields | MEDIUM | Need admin user or workaround for company lookup |
| 8 | **JSON-RPC broken** — Odoo.com hosting blocks JSON-RPC auth | LOW | Use XML-RPC only |
| 9 | **Custom field proliferation** — 60+ x_studio_ fields on helpdesk.ticket | INFO | Many are empty/unused; migrate only populated ones |
| 10 | **Stage mapping complexity** — 16 stages across 4 teams | MEDIUM | Define explicit stage mapping before import |

---

## L. Migration Readiness Score

| Category | Score | Notes |
|----------|-------|-------|
| **Source Data Availability** | 3/10 | Very minimal data (5 companies, 3 contacts, 0 tasks) |
| **Target Readiness** | 9/10 | Odoo 17.0 Enterprise fully configured with Helpdesk |
| **Field Mapping Coverage** | 7/10 | Core fields mapped; some gaps in custom/lookup fields |
| **Data Quality** | 4/10 | Duplicate partners, Arabic text in wrong fields |
| **Reference Integrity** | 5/10 | FK relationships exist but mostly empty |
| **Duplicate Risk** | 3/10 | High duplicate risk in Odoo partners |
| **OVERALL READINESS** | **5/10** | **YELLOW — Needs transformation and dedup before import** |

---

## M. Recommended Import Sequence

```
Phase 0: Pre-Migration Setup
  0.1  Create admin API user in Odoo (for write operations)
  0.2  Verify x_studio_muhide_user_id field exists on all target models
  0.3  Create region/country lookup tables
  0.4  Define stage mapping table

Phase 1: Partners (Companies)
  1.1  Export companies from SalesOS (5 records)
  1.2  Dedup check against existing Odoo partners (by CR number)
  1.3  Create/update res.partner records (is_company=True)
  1.4  Set x_studio_muhide_user_id for tracking

Phase 2: Partners (Contacts)
  2.1  Export contacts from SalesOS (3 records)
  2.2  Dedup check by email
  2.3  Create res.partner records (is_company=False)
  2.4  Link to parent company via parent_id
  2.5  Set x_studio_muhide_user_id

Phase 3: Tags
  3.1  Create helpdesk.tag records for any new tags
  3.2  Map SalesOS tag JSONB to Odoo tag IDs

Phase 4: Users (if needed)
  4.1  Check if SalesOS users already exist in Odoo (by email)
  4.2  Create/res.users only for truly new users
  4.3  Assign appropriate groups

Phase 5: Tickets (Tasks)
  5.1  Export tasks from SalesOS (0 records currently)
  5.2  Map status → stage_id
  5.3  Map priority → priority selection
  5.4  Map assignee_id → user_id
  5.5  Map company_id → partner_id
  5.6  Create helpdesk.ticket records in Muhide CX Team
  5.7  Set x_studio_muhide_user_id

Phase 6: Messages/Activity
  6.1  Export activity_records from SalesOS (120 records)
  6.2  Transform to mail.message format
  6.3  Link to appropriate tickets/partners
```

---

## N. Items Requiring Human Decision

| # | Decision | Options | Recommendation |
|---|----------|---------|----------------|
| 1 | **Which tenants to migrate?** | All 30 / Only "Ragheed" tenant / Only specific tenants | Migrate only `a0000000-...` (Ragheed) — others are test data |
| 2 | **Handle duplicate Odoo partners?** | Skip / Merge / Create separate | Skip creation if CR number matches existing |
| 3 | **Arabic text in email fields?** | Clean up / Leave as-is | Clean up before import — move to `comment` field |
| 4 | **Multi-tenant mapping?** | Map tenant→company / Ignore | Map tenant_id to company_id for audit trail |
| 5 | **Import test data?** | Yes / No | No — only import real business data |
| 6 | **x_studio_muhide_user_id strategy?** | UUID / email / custom | UUID — unique, stable, non-guessable |
| 7 | **Handle 60+ custom x_studio_ fields?** | Migrate all / Only populated / Skip | Only migrate populated fields |
| 8 | **Existing Odoo tickets?** | Leave untouched / Update / Replace | Leave untouched — only ADD new tickets |
| 9 | **Admin user for writes?** | Use existing / Create new | Create dedicated `migration-agent` user |
| 10 | **Import attachments?** | Yes / No | Yes — upload via ir.attachment API |

---

## O. Final Go / No-Go Recommendation

### GO/NO-GO: **CONDITIONAL GO** (Yellow)

**Rationale:**
- Odoo connection is working (XML-RPC, uid=43)
- Muhide CX Team is fully configured and operational (359 tickets)
- All required models and fields are accessible
- Custom fields (`x_studio_muhide_user_id`) exist for source tracking
- Source database is accessible and readable

**Conditions before first Import:**
1. **CRITICAL:** Resolve duplicate partner emails in Odoo (71+ groups)
2. **CRITICAL:** Clean Arabic text from Odoo partner email fields
3. **HIGH:** Create admin/write-capable API user for import operations
4. **HIGH:** Verify `res.company` access (currently denied for uid=43)
5. **MEDIUM:** Define explicit stage mapping table
6. **MEDIUM:** Decide tenant migration scope
7. **LOW:** Create region/country lookup tables

---

## Appendix: What we CAN migrate

| Entity | Count | Confidence | Notes |
|--------|-------|------------|-------|
| Companies | 5 | HIGH | Direct field mapping |
| Contacts | 3 | HIGH | Direct field mapping |
| Users | 18 | LOW | Mostly test accounts; check overlap |
| Tasks | 0 | N/A | Empty table |
| Opportunities | 1 | MEDIUM | Limited fields |
| Activity Records | 120 | LOW | System events, not user content |

## What we CANNOT migrate yet

| Entity | Reason | Resolution Needed |
|--------|--------|-------------------|
| Tasks (real) | 0 tasks in source | Wait for real data |
| Meetings | 0 meetings in source | Wait for real data |
| Decisions | 2 decisions (may be test) | Verify if real |
| Emails | 0 emails in source | Wait for real data |
| Attachments | 0 in source | Wait for real data |

## What needs transformation

| Source | Target | Transformation |
|--------|--------|---------------|
| `companies.status` | Tags or notes | No direct Odoo field |
| `companies.tags` (JSONB) | `category_id` | JSON → many2many tags |
| `companies.address` | `street` + `street2` | Split on newline |
| `tasks.status` | `stage_id` | Status→Stage lookup |
| `tasks.priority` | `priority` | Scale mapping |
| `activity_records` | `mail.message` | Full format change |

## What needs manual mapping

| Item | Details |
|------|---------|
| Region → state_id | Need Saudi regions lookup |
| Country → country_id | Need ISO code mapping |
| Currency → currency_id | Need currency code mapping |
| ISIC code → tags | Need tag creation |
| Owner → user_id | Need user email matching |

## What permissions are missing

| Permission | Current | Needed | How to Get |
|------------|---------|--------|------------|
| `res.company` read | DENIED (field restriction) | Full read | Admin user or field-level fix |
| `ir.model` read | DENIED | Full read | Add to "Administration/Access Rights" group |
| Write operations | Not tested | Create/Write on all target models | Dedicated migration user with API key |

## Exact next step before first Import

1. **Create an Odoo user** with email `migration-agent@muhide.com` and groups:
   - Helpdesk / User
   - Contacts / User
   - Technical / Settings (or Administration / Access Rights)
2. **Generate an API key** for this user
3. **Test write access** by creating a test `res.partner` record
4. **Run the migration script** in DRY-RUN mode first (log changes without committing)
