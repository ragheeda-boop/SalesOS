# STORY-09-05 — TaskCaseExtension VO on Task (Stream A)

> **Honesty:** Not Production GO. DEC-085 untouched. No invented Odoo secrets.  
> No new Alembic / FORCE RLS (**POLICY_COUNT unchanged at 71**).  
> Unlinked badge list API remains residual (not scoped here).

## Landed

| Piece | Detail |
|-------|--------|
| VO | `TaskCaseExtension` — `case_type` + `payload`, **no independent id** |
| Schema | JSON Schema per `financing` / `insurance` / `generic` (`jsonschema`) |
| Sync | `sync_project_tasks` from `project.task`; nests VO on Task projection |
| Classify | Studio fields → financing / insurance; plain tasks get no extension |
| Tests | VO-not-aggregate, schema reject, financing vs chore sync |

## Acceptance

Modeled as Value Object on `Task`, not standalone aggregate; JSON Schema
validated per `case_type` — covered by
`test_task_case_extension_is_vo_not_aggregate` +
`test_project_task_sync_attaches_case_extension_vo`.

## Non-goals

- `tasks.case_extension` ORM JSONB column migration (follow-on)
- Standalone `financing_cases` aggregate / table
- Unlinked badge list API
- Production GO
