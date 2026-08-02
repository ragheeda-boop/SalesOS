# STORY-11-10 — Second connector certification (R-02)

> **Honesty:** Not Production GO. DEC-085 untouched. No invented secrets.  
> No new Alembic / FORCE RLS (**POLICY_COUNT unchanged at 71**).  
> **HubSpot** chosen as Stream A provisional second-connector target for certification  
> (Sprint-16 Chief Architect SAP-vs-HubSpot formal Accept may still refine).  
> Live HubSpot network / **production pilot tenant sync — NOT claimed**.

## Landed

| Piece | Detail |
|-------|--------|
| Adapter | `HubSpotAdapter` (`connector_key=hubspot`) — SourceConnector, not Odoo-authored module |
| Suite | Identical `certify_source_connector` used by Fake/Odoo |
| HTTP | `GET /api/v1/integrations/certify/meta` + `POST /api/v1/integrations/certify/{connector_key}` |
| Tests | HubSpot certifies; failure path; isolation from OdooAdapter class |

## Acceptance

| AC | Status |
|----|--------|
| Passes identical certification suite Odoo passed | **Yes** (CI) |
| Syncs in production for a pilot tenant | **OPEN** — residual ops; not claimed |

## Non-goals

- Live HubSpot OAuth / production CRM sync
- Claiming R-02 fully closed without pilot soak
- Territories / SMTP / ML invent
- Production GO
