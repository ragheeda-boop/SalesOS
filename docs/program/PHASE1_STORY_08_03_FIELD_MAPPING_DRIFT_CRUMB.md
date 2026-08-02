# STORY-08-03 — FieldMappingConfig + drift detection (Stream A)

> **Honesty:** Not Production GO. DEC-085 untouched. No invented secrets.  
> STORY-06-04 left to Security.

## Landed

| Piece | Detail |
|-------|--------|
| Table | `field_mapping_configs` Alembic `f2b8c79d3e06` (revises `e1a7b68c2d05`) |
| RLS | FORCE tenant isolation (`app.tenant_id`) |
| Pure | `detect_field_drift` — missing mapped / possible rename / new fields |
| Job | `run_field_drift_job` — `status=alert` + loud `DRIFT ALERT` on rename |
| Service | `FieldMappingConfigService` — versioned mappings + baseline_fields |
| Tests | Simulated rename → critical `possible_rename`; cross-tenant harness |

## Acceptance

Drift-detection job alerts loudly on a simulated field rename — covered by
`test_simulated_field_rename_alerts_loudly`.

## Non-goals

- STORY-08-04 Anti-Corruption Layer / OdooTranslator
- Live ERP `fields_get` network calls (snapshot injected by caller)
- Integrations Studio UI
