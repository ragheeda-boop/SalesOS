# STORY-08-04 — Anti-Corruption Layer / OdooTranslator (Stream A)

> **Honesty:** Not Production GO. DEC-085 untouched. No invented secrets.  
> No new Alembic / FORCE RLS (POLICY_COUNT unchanged).

## Landed

| Piece | Detail |
|-------|--------|
| Class | `OdooTranslator` — one public `translate`, six internal stages |
| Stages | Mapper → Validator → Transformer → Normalizer → ConflictResolver → Versioning |
| Loud fail | `AclValidationError` at Validator (never silent null) |
| Output | `CanonicalRecord` with `source_updated_at` + `sync_run_id` |
| Tests | `test_odoo_translator_acl_story_08_04.py` — all 6 responsibilities + demo path |

## Acceptance

`OdooTranslator`-pattern class passes unit tests for all 6 internal responsibilities.
Demo: malformed record fails at Validator with a clear error.

## Non-goals

- STORY-08-05 SyncRun + scheduling
- Live Odoo adapter / network I/O
- Integrations Studio UI
