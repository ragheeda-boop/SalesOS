# STORY-11-05 — Enrichment Waterfall (Stream A)

> **Honesty:** Not Production GO. DEC-085 untouched. No invented secrets.  
> No new Alembic / FORCE RLS (**POLICY_COUNT unchanged at 71**).  
> CI uses ≥2 in-memory swappable providers (`fake_a` / `fake_b`).  
> Live Clearbit/Apollo/ERP enrichment — **not claimed**.  
> Live **141,221** Postgres — **not claimed**.

## Landed

| Piece | Detail |
|-------|--------|
| Port | `EnrichmentProvider` protocol (Hub-shaped swap-in) |
| Engine | Waterfall — first non-empty value wins per field |
| Providers | `fake_a` (firmographics) + `fake_b` (contact) |
| HTTP | `POST/GET /api/v1/gtm/enrichment` + `/meta` |
| Tests | Two-provider fill, order override, known-value lock, tenant isolation |

## Acceptance

≥2 swappable providers behind Integration Hub-shaped port — covered in CI.

## Non-goals

- Live third-party enrichment network calls
- ICP ML backtest / Lookalikes (AI-Lead)
- Territories BE (STORY-10-05)
- Production GO
