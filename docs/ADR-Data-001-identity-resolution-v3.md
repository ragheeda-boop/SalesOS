# ADR-Data-001: Identity Resolution Strategy v3

**Status:** Accepted  
**Date:** 2026-07-19  
**Author:** SalesOS Data Pipeline  
**Supersedes:** Phase 4 v2 (auto-merge rate 0.01%)

---

## Context

Phase 4 v2 loaded 169,730 records from four Notion sources (Companies, Contractors,
SFDA, Lawyers) and attempted identity resolution. It produced 169,663 golden entities
— only **15** were multi-source (0.01%). The remaining 169,648 were singletons.

Root cause investigation revealed:

1. Companies and Contractors databases are **Sales Intelligence** sources built from
   Apollo/LinkedIn data. They **do not contain** CR, License, Phone, or Email fields
   in their Notion schema. They contain only Domain, Website, and LinkedIn URLs.

2. SFDA and Lawyers are **Regulatory** sources containing License, Phone, and Email
   — but in incompatible formats (e.g., SFDA license = `WL-2025-FO-0985`, Lawyer
   license = `471817`). No shared identifier bridges these sources.

3. Domain was the **only** cross-source matching bridge (coverage 69.9%). All 3,910
   review queue candidates matched on `domain_match` alone at score 85 — below the
   >95 auto-merge threshold.

4. The auto-merge threshold (>95) was not the problem. *Lowering it to 85 would
   merge on domain alone*, risking false mergers (holding company vs. subsidiary
   sharing a domain).

---

## Decision

We will redesign identity resolution as a **multi-layer blocking engine with
dynamic composite scoring**, structured as follows:

### Layer 1 — Strong Signals (primary blocking keys)

| Key | Coverage | Cross-Source? |
|-----|----------|---------------|
| Canonical Domain | 69.9% | Yes — all 4 sources |
| Canonical Arabic Name N-Gram Hash (3-gram) | 100% | Yes — all 4 sources |

**N-Gram Hash Design:** Arabic company names are normalized (Phase 3), then
split into character 3-grams. Each 3-gram is hashed to produce a blocking key.
Any two records sharing at least 2 3-gram hashes enter the same block. This is
resistant to word order changes, abbreviation differences, and minor spelling
variations common in Arabic business names.

### Layer 2 — Context Signals (scoring only, not blocking)

| Key | Coverage |
|-----|----------|
| City (canonical) | ~87% |
| Region (canonical) | ~60% |

### Layer 3 — Regulatory Signals (ready for future sources)

| Key | Source |
|-----|--------|
| CR Number | REGA, Balady, SOCPA (future) |
| License Number | SFDA, Lawyers (present), REGA (future) |
| Membership Number | Contractors (present) |

These exist in the data NOW for SFDA/Lawyers/Contractors and are used in
scoring. CR will be available when REGA/Balady/SOCPA sources are added.

---

### Dynamic Composite Scoring

Weights are **not fixed**. They are normalized by available fields:

```
available_weight = sum of weights for fields present in BOTH records
score = sum of matched signal weights
confidence = min(score / available_weight * 100, 100)
```

This prevents penalizing records from sources that lack certain fields. A
domain-only match between two Companies records (both lacking CR/Phone/Email)
receives maximum normalized confidence, since domain is the only bridge
available for those sources.

**Signal weights (unchanged from v2):**

| Signal | Weight |
|--------|--------|
| cr_match | 100 |
| license_match | 95 |
| membership_match | 90 |
| domain_match | 85 |
| website_match | 80 |
| phone_match | 70 |
| email_match | 70 |
| canonical_name (exact) | 60 |
| canonical_name (fuzzy >0.6) | 48 |
| canonical_name (contains) | 48 |
| city | 20 |
| region | 10 |

**Classification (unchanged):**

| Score | Action |
|-------|--------|
| >95 | auto_merge |
| 80–95 | review |
| <80 | separate |

---

### Source Profiles

Each source declares its authoritative fields. The engine uses these to:

1. Prioritize field values during survivorship (authoritative source wins)
2. Adapt scoring expectations (don't expect CR from Companies)

```yaml
companies:
  authoritative: [domain, website, linkedin, name_ar, city, region]

contractors:
  authoritative: [membership, domain, name_ar, city, region]

sfda:
  authoritative: [license, phone, email, name_ar, city, region]

lawyers:
  authoritative: [license, phone, name_ar, city, region]
```

---

### Confidence Explanation

Every merge candidate includes a breakdown:

```json
{
  "signals": {
    "domain_match": true,
    "canonical_name": true,
    "city": true
  },
  "explanation": "Domain + Name (exact) + City",
  "score": 165,
  "max_possible": 165,
  "confidence_pct": 100
}
```

---

## Consequences

### Positive

- Cross-source matching works **today** using domain + name n-grams — no new
  data sources required
- N-gram hashing bridges Arabic name variations (typos, abbreviations, word
  order) that exact matching misses
- Dynamic normalization prevents false low scores for sources lacking fields
- Source profiles make the engine self-documenting and extensible
- Threshold remains ≥95 — no risk of domain-only false mergers

### Negative

- N-gram hashing may produce more candidate pairs than v2 (mitigated by max
  block size of 200)
- Requires re-running Phase 4 from scratch (~50 seconds in v2, may increase
  to 2-5 minutes with n-gram blocking)
- Existing Phase 4 outputs will be overwritten

---

## Alternatives Considered

### A: Lower auto-merge threshold to 85
**Rejected.** Would auto-merge all 3,910 review queue candidates on domain
alone. Domain sharing does not guarantee entity identity (holding/subsidiary).

### B: Add CR/License sources first (REGA, Balady, SOCPA)
**Deferred.** Valuable but requires Phase 1-3 pipeline extensions for those
sources. The name-based approach works immediately.

### C: Use ML-based entity resolution (dedupe.io, Splink)
**Deferred.** Adds dependency and complexity. Rule-based approach is
sufficient at current scale (170K records).

---

## Implementation Plan

1. Write `phase4_identity_v3.py` with multi-layer blocking, dynamic composite
   scoring, source profiles, and n-gram Arabic name hashing
2. Run against existing normalized data (4 sources, 169,730 records)
3. Expect multi-source entities to jump from 15 to significant number
4. Review auto-merge quality and adjust n-gram similarity threshold if needed
5. Future: add REGA, Balady, SOCPA, NCNP, Taqeem sources with CR fields

---

## References

- `data/reports/identity_quality_report.md` — Audit of v2 output
- `data/scripts/phase4_identity.py` — v2 implementation
- `data/scripts/phase3_normalize.py` — Name normalization rules already in place
- `data/normalized/canonical_dictionary.json` — City/region mappings
