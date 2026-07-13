# Enrichment Sources — Knowledge Pack

> Reference guide for data enrichment in SalesOS, covering free/public sources, APIs, Saudi-specific sources, quality scoring, and freshness requirements.

---

## Free / Public Data Sources for Company Enrichment

### Global Sources

| Source | Type | Data Available | Rate Limits | Cost |
|--------|------|---------------|-------------|------|
| OpenCorporates | REST API | Company registry, officers, filings | 500 req/month (free) | Free tier available |
| Crunchbase | REST API | Funding, investors, key people | Limited free tier | Free tier + paid |
| Companies House (UK) | REST API | Company data, officers, filings | 600 req/5 min | Free |
| SEC EDGAR | REST API | US public company filings | 10 req/sec | Free |
| WHOIS | Protocol | Domain registration data | Varies | Free |
| Clearbit Logo API | REST API | Company logos from domain | 1000 req/month | Free tier |
| GitHub API | REST API | Open-source activity, company tech stack | 5000 req/hour | Free |
| Google Maps API | REST API | Location, reviews, contact info | $200/month credit | Free tier |
| Wikipedia API | REST API | Company summaries, history | No limit | Free |
| Wikidata SPARQL | SPARQL | Structured entity data | No limit | Free |

### Saudi-Specific Sources

| Source | URL | Data Available | Authentication |
|--------|-----|---------------|----------------|
| ZATCA E-Invoicing | zatca.gov.sa | VAT registration, e-invoicing compliance | API key |
| MISA (Ministry of Investment) | investsaudi.sa | Foreign investment licenses, company registration | Public data |
| Saudi Exchange (Tadawul) | tadawul.com.sa | Listed companies, financials, disclosures | Public data |
| Ministry of Commerce | mci.gov.sa | CR numbers, company status, registrations | Public data |
| Balady (Municipality) | balady.gov.sa | Business licenses, locations, categories | Scraping |
| STAT (General Authority) | stats.gov.sa | Economic indicators, sector data | Public data |
| Saudi Aramco (Tendering) | aramco.com | Vendor registration, tenders | Vendor portal |
| MODON | modon.gov.sa | Industrial zone data, tenant companies | Public data |
| Saudi Customs | customs.gov.sa | Import/export data, trade flows | Public data |
| CITC | citc.gov.sa | ICT sector data, licensed companies | Public data |

### Industry-Specific Sources

| Industry | Source | Data Types |
|----------|--------|------------|
| Real Estate | Bayut, Aqar | Property listings, developer profiles |
| Healthcare | MOH Registry | Licensed healthcare facilities |
| Education | NCA, MOHE | Accredited institutions |
| Finance | SAMA, CMA | Licensed financial institutions |
| Telecom | CITC | Licensed operators, spectrum data |
| Mining | Ma'aden, USGS | Mineral data, mining licenses |

---

## API Integration Details

### OpenCorporates

```python
# Base URL: https://api.opencorporates.com/v0.4
# Auth: API key in header or query param

# Search companies
GET /companies/search?q={query}&jurisdiction_code=sa

# Get company details
GET /companies/{jurisdiction_code}/{company_number}

# Get officers
GET /companies/{jurisdiction_code}/{company_number}/officers

# Key fields returned:
# - name, company_number, jurisdiction_code
# - status (Active, Dissolved, etc.)
# - incorporation_date, dissolution_date
# - registered_address
# - company_type, current_alternative_names
```

### Crunchbase (Free Tier)

```python
# Base URL: https://api.crunchbase.com/api/v4
# Auth: API key required

# Search organizations
GET /searches/organizations
Body: {"query": [{"type": "organization", "field_ids": ["name"], "operator_id": "contains", "value": "{query}"}]}

# Get organization details
GET /entities/organizations/{permalink}

# Key fields:
# - short_description, long_description
# - founded_on, closed_on
# - num_employees_min, num_employees_max
# - total_funding_usd, last_funding_type
# - categories, location_identifiers
```

### LinkedIn (Official API)

```python
# Marketing API (requires partnership)
# People API (limited)
# Organization API (limited)

# Alternative: Use company website + Clearbit for LinkedIn data
# LinkedIn profile URL pattern: linkedin.com/company/{slug}
```

### ZATCA (Saudi E-Invoicing)

```python
# Base URL: https://api.zatca.gov.sa
# Auth: API key from ZATCA portal

# Verify VAT number
GET /v2/validation/vat/{vat_number}

# Check compliance status
GET /compliance/status/{cr_number}

# Key use cases:
# - Validate prospect company VAT registration
# - Check e-invoicing compliance readiness
# - Verify company legal status
```

### MISA (Ministry of Investment)

```python
# Data available via investsaudi.sa portal
# Foreign investment license lookup
# Sector classification
# Incentive programs

# Use cases:
# - Check if prospect has MISA license
# - Identify foreign-owned companies
# - Find companies in special economic zones
```

### Tadawul (Saudi Exchange)

```python
# Base URL: https://www.tadawul.com.sa/wps/wcm/connect/en/tadawul
# API available for listed companies

# Get listed companies
GET /api/companies

# Get company financials
GET /api/companies/{symbol}/financials

# Key fields:
# - company_name (Arabic/English)
# - symbol, ISIN
# - sector, market_cap
# - financial statements (quarterly/annual)
# - dividend history, disclosures
```

---

## Data Quality Scoring Methodology

### Quality Score Components

```
Overall Score = Completeness * 0.30
             + Accuracy * 0.25
             + Freshness * 0.20
             + Consistency * 0.15
             + Uniqueness * 0.10
```

### Completeness (0-1)

**Formula**: `filled_fields / total_expected_fields`

**Required fields** (14 total):
- name, name_en, cr_number, vat_number
- email, phone, website, address
- city, region, industry, status
- revenue, employees

**Thresholds**:
| Score | Grade | Action |
|-------|-------|--------|
| 0.9-1.0 | Excellent | Ready for AI analysis |
| 0.7-0.89 | Good | Minor enrichment recommended |
| 0.5-0.69 | Fair | Significant enrichment needed |
| 0.3-0.49 | Poor | Major data gaps |
| <0.3 | Critical | Manual review required |

### Accuracy (0-1)

**Formula**: `source_reliability + field_corrections`

**Source reliability weights**:
| Source | Weight |
|--------|--------|
| Government | 0.95 |
| Manual (verified) | 0.90 |
| ERP | 0.85 |
| CRM | 0.80 |
| LinkedIn | 0.70 |
| Website | 0.60 |
| News | 0.50 |
| Enrichment API | 0.40 |
| AI Extraction | 0.30 |
| Web Scraper | 0.20 |

**Field corrections** (bonus):
- Valid email format (+0.1)
- Valid website URL (+0.1)
- Phone number >= 7 digits (+0.1)

### Freshness (0-1)

**Grades**:
| Grade | Max Hours | Score |
|-------|-----------|-------|
| REAL_TIME | 1 | 1.0 |
| FRESH | 24 | 0.9 |
| MODERATE | 168 (1 week) | 0.6 |
| STALE | 720 (30 days) | 0.3 |
| EXPIRED | >720 | 0.1 |

### Consistency (0-1)

**Checks performed**:
- Email domain matches website domain
- City/region combination is valid
- Revenue-per-employee ratio > 10,000 (sanity check)

### Trust Score

```
Trust Score = Source Reliability * 0.50
            + Data Age Factor * 0.30
            + Cross-Reference Factor * 0.20
```

**Cross-reference factor**: `min(cross_references * 0.1, 0.2)`

---

## Freshness Requirements per Data Type

### Data Freshness Tiers

| Tier | Max Age | Use Cases | Examples |
|------|---------|-----------|----------|
| Real-time | <1 hour | Transactional, compliance | VAT status, deal stage |
| Near-real-time | <24 hours | Operational decisions | Contact info, company status |
| Daily | <7 days | Reporting, analysis | Revenue, employee count |
| Weekly | <30 days | Strategic planning | Industry, description |
| Monthly | <90 days | Market research | Financials, market position |
| Quarterly | <1 year | Compliance, archival | Registration, legal status |

### Field-Specific Requirements

| Field | Tier | Max Valid Hours | Refresh Trigger |
|-------|------|----------------|-----------------|
| VAT Status | Real-time | 1 | Compliance check |
| Deal Stage | Near-real-time | 24 | Activity event |
| Contact Info | Daily | 168 | Outreach attempt |
| Company Status | Daily | 720 | Signal detection |
| Revenue | Weekly | 720 | Quarterly review |
| Employee Count | Weekly | 720 | Signal detection |
| Industry | Monthly | 2160 | Annual review |
| Registration | Quarterly | 8760 | Compliance audit |

---

## Enrichment Pipeline Architecture

### Parallel Fetching (from EnrichmentService)

```
                    ┌─────────────┐
                    │  Enrichment │
                    │   Request   │
                    └──────┬──────┘
                           │
              ┌────────────┼────────────┐
              ▼            ▼            ▼
         ┌─────────┐ ┌─────────┐ ┌─────────┐
         │   DB    │ │Scrapers │ │Feature  │
         │ Query   │ │ (Balady)│ │ Store   │
         └────┬────┘ └────┬────┘ └────┬────┘
              │            │            │
              └────────────┼────────────┘
                           ▼
                    ┌─────────────┐
                    │   Merge &   │
                    │  Prioritize │
                    └──────┬──────┘
                           │
                    ┌──────▼──────┐
                    │   Cache &   │
                    │   Store     │
                    └─────────────┘
```

### Circuit Breaker Pattern

```python
CIRCUIT_BREAKER_THRESHOLD = 3  # failures before opening
CIRCUIT_BREAKER_RESET_SECONDS = 60.0  # cooldown before retry

# States:
# CLOSED (normal) → OPEN (failing) → HALF_OPEN (testing) → CLOSED
```

### Cache Strategy

- **TTL**: 24 hours (86400 seconds)
- **Key**: Company ID
- **Invalidation**: Manual or on fresh data arrival
- **Eviction**: LRU when cache exceeds memory limit

---

*Last updated: 2026-07-13*
*Version: 1.0*
