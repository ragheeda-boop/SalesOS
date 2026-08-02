# SourceConnector interface (STORY-08-01)

> **Audience:** Engineers implementing a new Integration Hub adapter.  
> **Honesty:** Framework contract only. Not Production GO. No Odoo-specific symbols in the contract.  
> **Code:** `salesos/backend/app/modules/integration_hub/`

## Contract

Every external system adapter **must** implement `SourceConnector`:

| Method | Purpose |
|--------|---------|
| `test_connection(credential_ref, config)` | Probe connectivity via vault pointer (never raw secrets in `config`) |
| `pull_incremental(credential_ref, config, model, cursor, limit)` | Incremental pull using an opaque `IncrementalCursor` watermark |
| `write_back(credential_ref, config, request)` | Push one record create/update to the external system |

Property: `connector_key` — stable adapter id string.

Shared DTOs live in `types.py` (`PullRecord`, `WriteBackRequest`, `ConnectionTestResult`, …).

## Certification

Call `certify_source_connector(adapter)` (async). The reference `FakeSourceConnector` must pass. Any future adapter (Odoo, SAP, …) certifies against the **same** suite with **zero** framework changes.

## Non-goals (later stories)

- `ExternalSystemConnection` persistence / Fernet credentials — STORY-08-02
- Field mapping / drift — STORY-08-03
- Anti-corruption translators — STORY-08-04 (**LANDED** — `OdooTranslator`)
- Tenant UI / marketplace certification pipeline

## Entitlement

Live Integration Hub HTTP surfaces (when added) remain gated by DOM-021 entitlements (STORY-06-02/06-03). This story lands the Python contract only.
