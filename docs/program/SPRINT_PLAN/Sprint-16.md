# Sprint 16 — 2027-03-01 → 2027-03-14

> **Phase:** 4 — GTM Intelligence Nativization · **Prior:** [Sprint 15](Sprint-15.md) · **Next:** [Sprint 17](Sprint-17.md) · **Index:** [ENGINEERING_ROADMAP.md](../ENGINEERING_ROADMAP.md)

**Sprint Goal:** ICP Engine + Market Sizing + Lead Discovery. Second-connector target selected.

| Story | Owner | Priority | Risk | Acceptance Criteria |
|---|---|---|---|---|
| STORY-11-01 (ICP Engine) | AI-Lead | P0 | Medium | `ICPProfile` versioned object, reusable across sessions |
| STORY-11-02 (TAM/SAM/SOM) | BE1 | P0 | Medium | **LANDED BE (Stream A):** TAM/SAM/SOM via `/api/v1/gtm/market-sizing` against gov-dataset-shaped universe (CI fixture; scale hint 141221). Crumb [`PHASE1_STORY_11_02_MARKET_SIZING_CRUMB.md`](../PHASE1_STORY_11_02_MARKET_SIZING_CRUMB.md). Live 141221 Postgres adapter not claimed. No new RLS. No Production GO. |
| FE-S11-02 (Market Sizing UI) | FE-Lead | P0 | Medium | **LANDED FE (Stream B):** `/gtm/market-sizing` against tip market-sizing HTTP. Crumb [`PHASE1_FE_S11_02_MARKET_SIZING_CRUMB.md`](../PHASE1_FE_S11_02_MARKET_SIZING_CRUMB.md). Live 141221 not claimed. No Production GO. |
| STORY-11-03 (Lead Discovery) | BE2 | P0 | Medium | Government-data-first, provider-fallback sourcing working |
| Second-connector decision | Chief Architect, Program Director | P0 | High (R-02) | SAP or HubSpot selected based on actual pilot pipeline demand, documented rationale |

**Expected Demo:** Run ICP scoring + TAM/SAM/SOM for a real pilot tenant's target market, show Lead Discovery sourcing hits from the government dataset first.

**Technical Debt Created:** None.
