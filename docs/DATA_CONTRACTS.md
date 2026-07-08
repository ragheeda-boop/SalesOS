# SalesOS — DATA CONTRACTS

> **عقود البيانات — Source → Normalized → Golden Record لجميع التكاملات**
> Version 1.0 | Last Updated: 2026-06-30
> Owner: CTO / Chief Architect

---

## Contract Template

```
Source: {name}
Type: Scraper | API | Webhook | Upload
Frequency: Daily | Weekly | Real-time | On-demand
Status: ✅ Active | 🟡 Partial | ❌ Missing
Field Count: {N}
Record Count: {N}
Last Sync: {date}
Contract:
  {source_field} → {normalized_field} → {golden_field}
```

---

## 1. BALADY (بلدي)

| Field | Value |
|-------|-------|
| Type | Scraper → JSON |
| Frequency | Daily |
| Status | ✅ Active |
| Field Count | 25+ |
| Record Count | ~40,000 companies |

### Contract

| Source Field | Normalized | Golden Record | Type |
|-------------|------------|---------------|------|
| `cr_number` | `commercial_registration.number` | `organization.cr_number` | str |
| `company_name_ar` | `organization.legal_name_ar` | `organization.legal_name_ar` | str |
| `company_name_en` | `organization.legal_name_en` | `organization.legal_name_en` | str |
| `city_ar` | `location.city_ar` | `address.city` | str |
| `city_en` | `location.city_en` | `address.city` | str |
| `street` | `location.street` | `address.street` | str |
| `building_number` | `location.building` | `address.building` | str |
| `postal_code` | `location.postal_code` | `address.postal_code` | str |
| `activity` | `industry.classification` | `organization.industry` | str |
| `license_status` | `registration.status` | `organization.status` | str |
| `issue_date` | `registration.issue_date` | `commercial_registration.issue_date` | date |
| `expiry_date` | `registration.expiry_date` | `commercial_registration.expiry_date` | date |
| `owner_name` | `person.full_name_ar` | `contact.full_name_ar` | str |
| `owner_nationality` | `person.nationality` | `contact.nationality` | str |
| `phone` | `contact.phone` | `contact.phone` | str |
| `email` | `contact.email` | `contact.email` | str |

---

## 2. TAQEEM (تقييم)

| Field | Value |
|-------|-------|
| Type | Scraper → JSON |
| Frequency | Weekly |
| Status | ✅ Active |
| Field Count | 20+ |
| Record Count | ~15,000 companies |

### Contract

| Source Field | Normalized | Golden Record | Type |
|-------------|------------|---------------|------|
| `company_name` | `organization.legal_name_ar` | `organization.legal_name_ar` | str |
| `cr_number` | `commercial_registration.number` | `organization.cr_number` | str |
| `city` | `location.city_ar` | `address.city` | str |
| `credit_score` | `financial.credit_score` | `financial_profile.credit_score` | int |
| `classification` | `industry.classification` | `organization.industry` | str |
| `employee_count` | `company.employee_count` | `organization.employee_count` | int |
| `revenue_range` | `financial.revenue_range` | `financial_profile.revenue_range` | str |
| `capital` | `financial.capital` | `commercial_registration.capital` | float |
| `status` | `registration.status` | `organization.status` | str |
| `establishment_date` | `registration.issue_date` | `commercial_registration.issue_date` | date |

---

## 3. NCNP (المنشآت)

| Field | Value |
|-------|-------|
| Type | Scraper → JSON |
| Frequency | Weekly |
| Status | ✅ Active |
| Field Count | 20+ |
| Record Count | ~25,000 companies |

### Contract

| Source Field | Normalized | Golden Record | Type |
|-------------|------------|---------------|------|
| `establishment_name` | `organization.legal_name_ar` | `organization.legal_name_ar` | str |
| `cr` | `commercial_registration.number` | `organization.cr_number` | str |
| `city` | `location.city_ar` | `address.city` | str |
| `size` | `company.size_classification` | `organization.size` | str |
| `sector` | `industry.sector` | `organization.industry_sector` | str |
| `activity` | `industry.activity` | `organization.industry_activity` | str |
| `employees_saudi` | `workforce.saudi_count` | `workforce_stats.saudi_employees` | int |
| `employees_total` | `workforce.total_count` | `workforce_stats.total_employees` | int |
| `wages_total` | `financial.total_wages` | `financial_profile.total_wages` | float |
| `establishment_type` | `company.type` | `organization.type` | str |

---

## 4. NAJIZ (ناجز)

| Field | Value |
|-------|-------|
| Type | Scraper → JSON |
| Frequency | Weekly |
| Status | 🟡 Partial |
| Field Count | 15+ |
| Record Count | ~10,000 |

### Contract

| Source Field | Normalized | Golden Record | Type |
|-------------|------------|---------------|------|
| `case_number` | `legal.case_number` | `legal_record.case_number` | str |
| `plaintiff` | `legal.plaintiff` | `legal_record.plaintiff` | str |
| `defendant` | `legal.defendant` | `legal_record.defendant` | str |
| `case_type` | `legal.case_type` | `legal_record.case_type` | str |
| `court` | `legal.court` | `legal_record.court` | str |
| `status` | `legal.case_status` | `legal_record.case_status` | str |
| `filing_date` | `legal.filing_date` | `legal_record.filing_date` | date |
| `amount` | `legal.claim_amount` | `legal_record.claim_amount` | float |

---

## 5. REGA (رخصة)

| Field | Value |
|-------|-------|
| Type | Scraper → JSON |
| Frequency | Weekly |
| Status | 🟡 Partial |
| Field Count | 15+ |
| Record Count | ~5,000 |

### Contract

| Source Field | Normalized | Golden Record | Type |
|-------------|------------|---------------|------|
| `license_number` | `license.number` | `commercial_registration.license_number` | str |
| `company_name` | `organization.legal_name_ar` | `organization.legal_name_ar` | str |
| `cr_number` | `commercial_registration.number` | `organization.cr_number` | str |
| `license_type` | `license.type` | `license.type` | str |
| `license_status` | `license.status` | `license.status` | str |
| `issue_date` | `license.issue_date` | `license.issue_date` | date |
| `expiry_date` | `license.expiry_date` | `license.expiry_date` | date |

---

## 6. SOCPA (هيئة المحاسبين)

| Field | Value |
|-------|-------|
| Type | Scraper → JSON |
| Frequency | Monthly |
| Status | 🟡 Partial |
| Field Count | 10+ |
| Record Count | ~5,000 |

### Contract

| Source Field | Normalized | Golden Record | Type |
|-------------|------------|---------------|------|
| `accountant_name` | `person.full_name_ar` | `contact.full_name_ar` | str |
| `license_number` | `professional.license_number` | `professional_profile.license_number` | str |
| `license_status` | `professional.status` | `professional_profile.status` | str |
| `classification` | `professional.classification` | `professional_profile.classification` | str |
| `employer` | `professional.employer` | `contact.employer_name` | str |

---

## 7. APOLLO.IO (Planned)

| Field | Value |
|-------|-------|
| Type | REST API |
| Frequency | Daily (batch) + Real-time (webhook) |
| Status | 🟡 Planned |
| Priority | P1 |

### Contract

| Source Field | Normalized | Golden Record | Type |
|-------------|------------|---------------|------|
| `name` | `organization.legal_name_en` | `organization.legal_name_en` | str |
| `domain` | `organization.domain` | `organization.domain` | str |
| `phone` | `contact.phone` | `contact.phone` | str |
| `city` | `location.city_en` | `address.city` | str |
| `state` | `location.state` | `address.state` | str |
| `country` | `location.country` | `address.country` | str |
| `employee_count` | `company.employee_count` | `organization.employee_count` | int |
| `revenue` | `financial.revenue` | `financial_profile.revenue` | float |
| `industry` | `industry.name` | `organization.industry` | str |
| `linkedin_url` | `social.linkedin` | `organization.linkedin_url` | str |
| `website` | `organization.website` | `organization.website` | str |
| `description` | `organization.description` | `organization.description` | str |
| `founded_year` | `organization.founded_year` | `organization.founded_year` | int |
| `keywords` | `organization.tags` | `organization.tags` | list[str] |

---

## 8. HUBSPOT (Planned)

| Field | Value |
|-------|-------|
| Type | OAuth 2.0 + REST API |
| Frequency | Real-time (webhook) |
| Status | ❌ Missing |
| Priority | P2 |

### Contract

| Source Field | Normalized | Golden Record | Type |
|-------------|------------|---------------|------|
| `hs_object_id` | `external_id.hubspot` | `external_ids.hubspot_id` | str |
| `name` | `organization.legal_name_en` | `organization.legal_name_en` | str |
| `domain` | `organization.domain` | `organization.domain` | str |
| `phone` | `contact.phone` | `contact.phone` | str |
| `city` | `location.city_en` | `address.city` | str |
| `country` | `location.country` | `address.country` | str |
| `lifecyclestage` | `crm.stage` | `pipeline.current_stage` | str |
| `hs_lead_status` | `crm.lead_status` | `opportunity.status` | str |
| `notes_last_contacted` | `activity.last_contacted` | `activity.last_contact_date` | date |
| `num_associated_deals` | `crm.deal_count` | `pipeline.deal_count` | int |
| `total_revenue` | `financial.total_revenue` | `financial_profile.total_revenue` | float |

---

## Entity Resolution Strategy

### Golden Record Merge Rules

1. **CR Number is the primary key** for Saudi entities
2. **Domain is the primary key** for international entities
3. Highest-priority source wins on each field:
   - Legal name: Balady > NCNP > Taqeem > Apollo
   - Address: Balady > REGA > NCNP
   - Financials: Taqeem > Apollo
   - Workforce: NCNP > Taqeem
   - Legal: Najiz (single source of truth)
4. All conflicts are recorded in `entity_resolution.conflicts` with provenance
5. Fields can be locked per-tenant (customer overrides)

### Provenance Tracking

Every golden record field stores:
```json
{
  "value": "ACME Corp",
  "source": "BALADY",
  "source_record_id": "cr_12345",
  "confidence": 0.95,
  "timestamp": "2026-06-30T10:00:00Z",
  "verified_by": null
}
```

---

*This document defines the data contracts for every integration. All source-to-golden mappings must be registered here before integration code is written. Violations result in data quality issues tracked in the Technical Debt Register.*
