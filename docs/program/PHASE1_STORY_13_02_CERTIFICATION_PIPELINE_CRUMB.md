# STORY-13-02 — Certification pipeline CAP-094 (Stream A)

> **Honesty:** Not Production GO. DEC-085 untouched.  
> **POLICY_COUNT unchanged at 71** (no Alembic / FORCE RLS).  
> `feature_ai_copilot` False. R-02 pilot soak OPEN (Ops).  
> Does **not** use `domains/marketplace/sandbox.py` (plugin iframe) as CAP-094.

## Landed

| Piece | Detail |
|-------|--------|
| Status machine | `draft`/`rejected` → `pending_certification` → `certified` \| `rejected` |
| Conformance | Reuses `certify_named_connector` → `certify_source_connector` |
| Security checklist | Same path for first-party; rejects secret-ish manifest keys |
| Trial sandbox | `marketplace_listings.trial_sandbox` — isolated trial tenant; no real-tenant leak |
| HTTP | `POST …/listings/{id}/submit`, `POST …/listings/{id}/certify`, `GET …/certify/meta` |
| Negative | `connector_key=broken` / unknown key → rejected |

## Non-goals

- STORY-13-03 FE browse UI / STORY-13-04 publish pack
- Live HubSpot/Odoo GO / R-02 invent-close
- Third-party submit form
- Production GO
