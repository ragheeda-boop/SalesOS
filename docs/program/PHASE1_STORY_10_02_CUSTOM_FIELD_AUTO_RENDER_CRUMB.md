# STORY-10-02 — Custom field auto-render (Stream A BE unlock)

> **Honesty:** Not Production GO. DEC-085 untouched. No invented secrets.  
> No new Alembic / FORCE RLS (**POLICY_COUNT unchanged at 71**).  
> FE page wire-up may follow; BE lands Form Engine schema + metadata value bag.

## Landed

| Piece | Detail |
|-------|--------|
| Form schema | `GET /api/v1/studio/custom-fields/{object}/form-schema` |
| Renderer | FormField descriptors (`custom_fields_auto`) from CAP-082 defs |
| Values | `metadata.custom_fields` bag merge/filter helpers + `POST .../values` |
| Tests | Form includes defined fields; value round-trip; empty schema |

## Acceptance

Custom fields appear as auto-render form schema for Company/Contact/Opportunity
with zero per-field frontend code — covered by
`test_auto_render_form_includes_defined_fields`.

## Non-goals

- Hardcoded FE page components per field
- Alembic persistence of definitions/values
- STORY-10-03 Workflow Builder
- Production GO
