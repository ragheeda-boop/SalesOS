# Phase 1/2 boundary — STORY-08-01 SourceConnector (Stream A)

> **Honesty:** Not Production GO. DEC-085 / auth / CSRF / RBAC untouched. BE-only.  
> No Stripe secrets. No Odoo adapter yet (EPIC-09). Calendar Sprint-08 BE-Lead P0.

## Why this story next

EPIC-06 BE (06-01..06-03) landed; **STORY-06-04** is Security-owned (skipped).  
EPIC-07 Owner Console MVP is FE-owned. Remaining billing BE is ops soak (env keys).  
Next Backend-owned board item: **STORY-08-01**.

## Landed

| Piece | Detail |
|-------|--------|
| Contract | `SourceConnector` Protocol — `test_connection`, `pull_incremental`, `write_back` |
| DTOs | `types.py` — cursor/records/write-back/connection result |
| Reference | `FakeSourceConnector` in-memory adapter |
| Certify | `certify_source_connector()` — same suite for every future adapter |
| Docs | [`SOURCE_CONNECTOR_INTERFACE.md`](SOURCE_CONNECTOR_INTERFACE.md) |
| Tests | `tests/unit/test_source_connector_story_08_01.py` |

## Non-goals

- STORY-08-02 `ExternalSystemConnection` / Fernet
- STORY-06-04 adversarial entitlement matrix (Security)
- Production GO / tenant UI
