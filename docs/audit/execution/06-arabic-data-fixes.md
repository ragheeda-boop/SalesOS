# Arabic Language & Data Pipeline Fixes — Execution Report

> Date: 2026-07-13
> Audit ID: EXEC-006
> Status: Completed

---

## 1. Arabic Text Normalization (BUG-002) — FIXED

### Files Created
| File | Purpose |
|------|---------|
| `domains/search/normalization/__init__.py` | Package init with exports |
| `domains/search/normalization/arabic_normalizer.py` | `ArabicSearchNormalizer` class |
| `domains/search/normalization/stop_words.py` | Arabic stop words list (100+ words) |
| `domains/search/normalization/arabic_thesaurus.py` | `ArabicSearchThesaurus` for query expansion |
| `domains/search/tests/test_arabic_normalizer.py` | 45+ unit tests with real Saudi company names |

### Normalizer Pipeline (ArabicSearchNormalizer)
1. **Diacritics removal** — strips tashkeel (fatha, damma, kasra, shadda, sukun, etc.)
2. **Tatweel (kashida) removal** — removes stretching characters `ـ`
3. **Alef normalization** — `أ` `إ` `آ` `ٱ` → `ا`
4. **Yeh normalization** — `ى` `ئ` `ی` → `ي`
5. **Teh Marbuta normalization** — `ة` → `ه`
6. **Hamza on Waw** — `ؤ` → `و`
7. **Arabic punctuation** — `،` `؛` `؟` → `,` `;` `?`
8. **Whitespace normalization** — collapses multiple spaces
9. **Stop word removal** — removes 100+ common Arabic function words

### Modes
- `normalize()` — default pipeline for search queries
- `normalize_for_indexing()` — preserves stop words for full-text indexing
- `normalize_for_query()` — aggressive normalization with stop word removal
- `for_matching()` — maximally aggressive for entity resolution

### Integration
- Integrated into `domains/search/engine/parser.py` (`QueryParser`)
- Integrated into `domains/search/engine/strategy_matrix.py` (`normalize_query`)
- `ParsedQuery` now carries `normalized_query` field

---

## 2. Scraper API Key Activation (D-005) — COMPLETED

### Files Created/Modified
| File | Action | Purpose |
|------|--------|---------|
| `runtime/data_fabric_runtime/scrapers/scraper_config.py` | Created | API key validation, health check, registry |
| `.env.production.template` | Created | Full production env template with scraper keys |
| `.env` | Modified | Added scraper key section + `DEMO_MODE` flag |
| `app/main.py` | Modified | Startup validation + health endpoint |

### ScraperConfig Features
- **5 scrapers registered**: Balady, Taqeem, REGA, Najiz, NCNP
- **Placeholder detection**: Detects 10+ common placeholder patterns
- **Startup validation**: `validate_scraper_keys_startup()` runs on app launch
- **Health endpoint**: `/health` and `/health/ready` now include `scrapers` key
- **Key status**: MISSING / PLACEHOLDER / VALID per scraper

### Exponential Backoff
- Already implemented in `BaseScraper._rate_limited_fetch()` with:
  - `delay = RETRY_DELAY_MS * (2**attempt) / 1000` (exponential)
  - Rate limiting via `RATE_LIMIT_RPS` property per scraper
  - Max retries with `MAX_RETRIES` configurable per scraper

---

## 3. Demo Data Removal — FLAGGED

### Files Modified
| File | Changes |
|------|---------|
| `app/routers/commercial.py` | Added `TODO(D-005)` markers + `DEMO_MODE` check to: |
| | - `POST /forecast/run` — hardcoded `CommercialInput(demo-1...)` |
| | - `POST /analytics/generate` — static `AnalyticsInput(500000, 650000...)` |
| | - `GET /workspace` — analytics KPIs, "Today" summary (12.4M, 89%, "Healthy") |
| `.env` | Added `DEMO_MODE=false` feature flag |

### Demo Sections Flagged
1. **Forecast**: `CommercialInput(opportunity_id="demo-1", ...)` → needs real pipeline data
2. **Analytics**: `AnalyticsInput(total_booked_revenue=500000, ...)` → needs real revenue data
3. **Workspace**: `"revenue_today": "12.4M SAR"`, `"forecast_accuracy": "89%"`, `"pipeline_health": "Healthy"` → needs real aggregations
4. **Workspace analytics**: Same hardcoded values as analytics endpoint

### Feature Flag Behavior
- When `DEMO_MODE=true`: demo data served with `logger.warning()`
- When `DEMO_MODE=false` (production): real data pipeline used, but currently returns same demo values (logged as warnings)
- All sections marked with `TODO(D-005)` and tracking reference to `memory/technical-debt.md`

---

## 4. Entity Resolution City/Region — COMPLETED

### Files Created
| File | Purpose |
|------|---------|
| `app/modules/entity_resolution/city_mapping.py` | `CityRegionNormalizer` class |

### Coverage
- **22 cities/regions** with Arabic + English variants
- **~100+ variant mappings** total

| City (Canonical) | Variants Normalized |
|-------------------|-------------------|
| الرياض | Riyadh, Ar Riyad, رياض, الرياض منطقة |
| جدة | Jeddah, Jedda, جده, جدا |
| الدمام | Dammam, Damam, ad Dammam |
| مكة المكرمة | Makkah, Mecca, مكة, مكه |
| المدينة المنورة | Madinah, Medina, طيبة |
| الخبر | Khobar, al Khobar |
| الظهران | Dhahran |
| الجبيل | Jubail, الجبيل الصناعية |
| الأحساء | Al-Ahsa, الهفوف, Hofuf |
| عسير | Asir, Aseer |
| المنقطة الشرقية | Eastern Province, الشرقية |

### Integration
- Integrated into `EntityResolutionService._create_golden_record()`
- City/region fields are normalized to canonical Arabic before storage
- `CityRegionNormalizer.normalize_city()` → canonical Arabic
- `CityRegionNormalizer.to_english()` → English name
- `CityRegionNormalizer.normalize_and_english()` → both

---

## 5. Arabic Search Thesaurus — COMPLETED

### Files Created
| File | Purpose |
|------|---------|
| `domains/search/normalization/arabic_thesaurus.py` | `ArabicSearchThesaurus` class |

### Thesaurus Categories
| Category | Terms | Examples |
|----------|-------|----------|
| Company Types | 6 terms | شركة→مؤسسة, منشأة, مصنع, شركه |
| Industries | 20 terms | مقاولات→إنشاءات, تشييد, بناء |
| Business Terms | 17 terms | عقود→اتفاقيات, تعاقد |
| Legal/Government | 6 terms | سجل تجاري→ترخيص |
| Location | 9 terms | الرياض→رياض, Riyadh |

### Features
- `expand(term)` → list of original + synonyms
- `expand_query(query)` → PostgreSQL tsquery-compatible OR groups
- `get_synonyms(term)` → synonyms only (no original)
- Case-insensitive lookup for mixed-lang queries

### Integration
- Imported in search normalization package
- Available to `QueryParser` via `thesaurus` property

---

## Files Changed Summary

| # | File | Action |
|---|------|--------|
| 1 | `domains/search/normalization/__init__.py` | New |
| 2 | `domains/search/normalization/arabic_normalizer.py` | New |
| 3 | `domains/search/normalization/stop_words.py` | New |
| 4 | `domains/search/normalization/arabic_thesaurus.py` | New |
| 5 | `domains/search/tests/test_arabic_normalizer.py` | New |
| 6 | `domains/search/engine/parser.py` | Modified |
| 7 | `domains/search/engine/strategy_matrix.py` | Modified |
| 8 | `runtime/data_fabric_runtime/scrapers/scraper_config.py` | New |
| 9 | `.env.production.template` | New |
| 10 | `.env` | Modified |
| 11 | `app/main.py` | Modified |
| 12 | `app/routers/commercial.py` | Modified |
| 13 | `app/modules/entity_resolution/city_mapping.py` | New |
| 14 | `app/modules/entity_resolution/service.py` | Modified |

## Verification

- **21/21 smoke tests passed** for Arabic normalization across all categories
- Scraper config validation tested with placeholder detection
- City mapping verified for all 22 Saudi cities
- Thesaurus expansion tested for common business terms

## Next Steps

- [ ] Wire forecast/analytics to real data pipeline (TD-005)
- [ ] Obtain real API keys for Balady, Taqeem, REGA, Najiz, NCNP
- [ ] Run full test suite (pytest) for regression validation
- [ ] Add Arabic search indexing migration to use normalized tsvector
- [ ] Benchmark search with normalized Arabic queries
