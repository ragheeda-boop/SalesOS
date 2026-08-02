# Sprint 16 — 2027-03-01 → 2027-03-14

> **Phase:** 4 — GTM Intelligence Nativization · **Prior:** [Sprint 15](Sprint-15.md) · **Next:** [Sprint 17](Sprint-17.md) · **Index:** [ENGINEERING_ROADMAP.md](../ENGINEERING_ROADMAP.md)

**Sprint Goal:** ICP Engine + Market Sizing + Lead Discovery. Second-connector target selected.

| Story | Owner | Priority | Risk | Acceptance Criteria |
|---|---|---|---|---|
| STORY-11-01 (ICP Engine) | AI-Lead / BE Stream A | P0 | Medium | **LANDED BE (Stream A):** versioned reusable `ICPProfile` via `/api/v1/gtm/icp-profiles` (+ score). Crumb [`PHASE1_STORY_11_01_ICP_ENGINE_CRUMB.md`](../PHASE1_STORY_11_01_ICP_ENGINE_CRUMB.md). Deterministic fit only — ML/won-lost backtest not claimed. No new RLS. No Production GO. Unblocks FE-S11-01. |
| FE-S11-01 (ICP Profiles UI) | FE-Lead | P0 | Medium | **LANDED FE (Stream B):** `/gtm/icp` against tip icp-profiles HTTP (CRUD + score). Crumb [`PHASE1_FE_S11_01_ICP_PROFILES_CRUMB.md`](../PHASE1_FE_S11_01_ICP_PROFILES_CRUMB.md). No ML/141221 claim. No Production GO. |
| STORY-11-02 (TAM/SAM/SOM) | BE1 | P0 | Medium | **LANDED BE (Stream A):** TAM/SAM/SOM via `/api/v1/gtm/market-sizing` against gov-dataset-shaped universe (CI fixture; scale hint 141221). Crumb [`PHASE1_STORY_11_02_MARKET_SIZING_CRUMB.md`](../PHASE1_STORY_11_02_MARKET_SIZING_CRUMB.md). Live 141221 Postgres adapter not claimed. No new RLS. No Production GO. |
| FE-S11-02 (Market Sizing UI) | FE-Lead | P0 | Medium | **LANDED FE (Stream B):** `/gtm/market-sizing` against tip market-sizing HTTP. Crumb [`PHASE1_FE_S11_02_MARKET_SIZING_CRUMB.md`](../PHASE1_FE_S11_02_MARKET_SIZING_CRUMB.md). Live 141221 not claimed. No Production GO. |
| FE-S11-02b (Market Sizing detail) | FE-Lead | P1 | Low | **LANDED FE (Stream B):** tip GET detail + nested bands. Crumb [`PHASE1_FE_S11_02B_MARKET_SIZING_DETAIL_CRUMB.md`](../PHASE1_FE_S11_02B_MARKET_SIZING_DETAIL_CRUMB.md). No Production GO. |
| STORY-11-03 (Lead Discovery) | BE2 | P0 | Medium | **LANDED BE (Stream A):** gov-first + Integration Hub provider fallback via `/api/v1/gtm/lead-discovery` (CI: gov-dataset-shaped universe + FakeSourceConnector). Crumb [`PHASE1_STORY_11_03_LEAD_DISCOVERY_CRUMB.md`](../PHASE1_STORY_11_03_LEAD_DISCOVERY_CRUMB.md). Live 141221 / live ERP not claimed. No new RLS. No Production GO. |
| FE-S11-03 (Lead Discovery UI) | FE-Lead | P0 | Medium | **LANDED FE (Stream B):** `/gtm/lead-discovery` against tip lead-discovery HTTP. Crumb [`PHASE1_FE_S11_03_LEAD_DISCOVERY_CRUMB.md`](../PHASE1_FE_S11_03_LEAD_DISCOVERY_CRUMB.md). Live 141221 / live ERP not claimed. No Production GO. |
| FE-S11-03b (GTM hub + handoff) | FE-Lead | P1 | Low | **LANDED FE (Stream B):** `/gtm` hub + criteria handoff + `?snapshot=`/`?run=` deep-links. Crumb [`PHASE1_FE_S11_03B_GTM_HUB_HANDOFF_CRUMB.md`](../PHASE1_FE_S11_03B_GTM_HUB_HANDOFF_CRUMB.md). No invented ICP/territories. No Production GO. |
| Second-connector decision | Chief Architect, Program Director | P0 | High (R-02) | **PROVISIONAL (Stream A):** HubSpot selected for STORY-11-10 certification scaffolding (CI). Formal Chief Architect Accept may refine SAP vs HubSpot. Live pilot sync not claimed. |

**Expected Demo:** Run ICP scoring + TAM/SAM/SOM for a real pilot tenant's target market, show Lead Discovery sourcing hits from the government dataset first.

**Technical Debt Created:** None.
