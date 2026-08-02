# STORY-11-03 — Lead Discovery (Stream A)

> **Honesty:** Not Production GO. DEC-085 untouched. No invented secrets.  
> No new Alembic / FORCE RLS (**POLICY_COUNT unchanged at 71**).  
> CI uses gov-dataset-**shaped** in-memory universe + `FakeSourceConnector` provider fallback.  
> Live **141,221** Postgres / live ERP pull — **not claimed**.

## Landed

| Piece | Detail |
|-------|--------|
| Models | `LeadDiscoveryQuery` / `DiscoveredLead` / `LeadDiscoveryRun` |
| Engine | Gov-first `search_government` then Integration Hub `SourceConnector` fill |
| Store | In-memory runs; demo gov universe + seeded FakeSourceConnector |
| HTTP | `POST/GET /api/v1/gtm/lead-discovery` + `/meta` |
| Tests | Gov-first ordering, empty-gov provider fallback, tenant isolation |

## Acceptance

Government-data-first sourcing with external-provider fallback via Integration Hub — covered in CI (fixture + FakeSourceConnector).

## Non-goals

- Live prod SELECT count of 141221
- Live Odoo/SAP/HubSpot pull in this land
- ICP Engine (STORY-11-01, AI-Lead)
- Territories BE (STORY-10-05)
- Production GO
