# STORY-08-02 — ExternalSystemConnection (Stream A)

> **Honesty:** Not Production GO. DEC-085 `set_config` / `get_db()` untouched.  
> No invented Stripe/vault secrets. STORY-06-04 left to Security.

## Landed

| Piece | Detail |
|-------|--------|
| Table | `external_system_connections` Alembic `e1a7b68c2d05` (revises `d0f6e89b1a37`) |
| RLS | FORCE tenant isolation via `generate_policy_sql` (`app.tenant_id`) |
| Model | `ExternalSystemConnectionModel` — `credential_ref` + Fernet `credentials_encrypted` |
| Hygiene | `connection_config` rejects secret-like keys; ref must be `vault://` or `ref://` |
| Service | `ExternalSystemConnectionService` — always filters by `tenant_id` |
| Crypto | `sdk.security` Fernet; env `integration_hub_encryption_key` or `secret_key` |
| Tests | `tests/unit/test_external_system_connection_story_08_02.py` (Fernet + STORY-01-04 cross-tenant) |

## Non-goals

- Integrations Studio UI / HTTP surface
- Real vault provider wiring (pointer contract only)
- Odoo adapter (EPIC-09)
- STORY-08-03 field mapping
