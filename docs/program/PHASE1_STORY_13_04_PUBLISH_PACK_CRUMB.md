# STORY-13-04 — Publish pack (≥3 connectors + ≥1 playbook)

> **Honesty:** Not Production GO. Live HubSpot/Odoo/REST sync not claimed.  
> **POLICY_COUNT unchanged at 71** (no Alembic / FORCE RLS).  
> `feature_ai_copilot` False. Do not re-land STORY-13-02.  
> Catalog install ≠ plugin `/api/v1/marketplace/install` (CAP-036 stub).

## Landed

| Piece | Detail |
|-------|--------|
| Seed | `seed_publish_pack` — Odoo, HubSpot, REST/CSV + GCC outbound playbook |
| Status | All 4 seed listings `published` with `manifest.installable/certified` |
| Third connector | `RestCsvSourceConnector` (`rest_csv`) registered in Hub certify registry |
| Publish | `POST …/listings/{id}/publish` (certified → published) |
| Install | `POST …/listings/{id}/install` + `GET …/listings/installs` — tenant-scoped catalog receipt |
| HTTP aliases | `POST …/seed-publish-pack` (+ existing `seed-first-party`) |
| Tests | `tests/unit/test_story_13_04_publish_pack.py` |

## Seed shape

| slug | type | connector_key | status |
|------|------|---------------|--------|
| connector-odoo | connector | odoo | published |
| connector-hubspot | connector | hubspot | published |
| connector-rest-csv | connector | rest_csv | published |
| playbook-gcc-outbound | playbook | — | published |

## Non-goals

- Re-land 13-02 / invent AI 12-01..03 / Studio Postgres / for_each
- R-02 soak invent-close / third-party submit form
- Live ERP GO / Production GO
