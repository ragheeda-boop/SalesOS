# STORY-10-01 — Custom Object/Field definition mechanism (Stream A)

> **Honesty:** Not Production GO. DEC-085 untouched. No invented secrets.  
> No new Alembic / FORCE RLS (**POLICY_COUNT unchanged at 71**).  
> In-memory definition store — Postgres persistence is a follow-on.

## Landed

| Piece | Detail |
|-------|--------|
| Reserved | Collision registry for `company` / `contact` / `opportunity` ORM columns |
| Definitions | Versioned `CustomFieldDefinition` (string/number/date/enum) |
| Service | `MemCustomFieldDefinitionService` — tenant-scoped create/list |
| HTTP | `POST/GET /api/v1/studio/custom-fields` (definition only) |
| Tests | Reserved reject, version bump, duplicate reject, multi-tenant isolation |

## Acceptance

Collision-checked against reserved columns; versioned schema — covered by
`test_reserved_column_collision_rejected` +
`test_define_scalar_field_bumps_schema_version`.

## Non-goals

- Alembic `custom_*` tables / FORCE RLS
- Value persistence on Company/Contact/Opportunity rows
- FE auto-render (STORY-10-02)
- Production GO
