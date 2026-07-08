# SalesOS — EVENT CATALOG

> **سجل الأحداث — كل Event في النظام، منتجه، مستهلكه، ومخططه**
> Version 1.0 | Last Updated: 2026-06-30
> Owner: CTO / Chief Architect

---

## Event Format

All events follow CloudEvents 1.0:

```json
{
  "specversion": "1.0",
  "id": "uuid",
  "source": "//salesos/{capability}",
  "type": "com.salesos.{capability}.{event_name}",
  "subject": "{entity_type}/{entity_id}",
  "datacontenttype": "application/json",
  "time": "2026-06-30T10:00:00Z",
  "tenant_id": "uuid",
  "trace_id": "uuid",
  "data": { ... }
}
```

---

## IDENTITY EVENTS

### `com.salesos.identity.tenant_created`

| Field | Type | Description |
|-------|------|-------------|
| Producer | Identity (CAP-001) | |
| Consumers | Timeline, Analytics, Digital Twin | |
| Schema | `{ tenant_id, name, domain, plan, created_by }` | |

### `com.salesos.identity.user_created`

| Field | Type | Description |
|-------|------|-------------|
| Producer | Identity (CAP-001) | |
| Consumers | Timeline, Analytics, Notification | |
| Schema | `{ user_id, tenant_id, email, role }` | |

### `com.salesos.identity.user_logged_in`

| Field | Type | Description |
|-------|------|-------------|
| Producer | Identity (CAP-001) | |
| Consumers | Analytics, Security Audit | |
| Schema | `{ user_id, tenant_id, ip, user_agent, auth_method }` | |

### `com.salesos.identity.api_key_generated`

| Field | Type | Description |
|-------|------|-------------|
| Producer | Identity (CAP-001) | |
| Consumers | Audit | |
| Schema | `{ key_id, tenant_id, created_by, permissions, expires_at }` | |

### `com.salesos.identity.role_assigned`

| Field | Type | Description |
|-------|------|-------------|
| Producer | Identity (CAP-001) | |
| Consumers | Permission Engine, Audit | |
| Schema | `{ user_id, role, scope, assigned_by }` | |

---

## COMPANY EVENTS

### `com.salesos.company.organization_created`

| Field | Type | Description |
|-------|------|-------------|
| Producer | Company (CAP-002) | |
| Consumers | Timeline, Search, Analytics, Knowledge Graph, Digital Twin | |
| Schema | `{ org_id, name_ar, name_en, cr_number, industry, city, created_by }` | |

### `com.salesos.company.organization_updated`

| Field | Type | Description |
|-------|------|-------------|
| Producer | Company (CAP-002) | |
| Consumers | Timeline, Search, Knowledge Graph, Feature Store, Digital Twin | |
| Schema | `{ org_id, changes: [{field, old, new}] }` | |

### `com.salesos.company.contact_added`

| Field | Type | Description |
|-------|------|-------------|
| Producer | Company (CAP-002) | |
| Consumers | Timeline, Knowledge Graph | |
| Schema | `{ contact_id, org_id, name, email, phone, role }` | |

### `com.salesos.company.license_created`

| Field | Type | Description |
|-------|------|-------------|
| Producer | Company (CAP-002) | |
| Consumers | Timeline, Knowledge Graph | |
| Schema | `{ license_id, org_id, type, status, issue_date, expiry_date }` | |

---

## OPPORTUNITY EVENTS

### `com.salesos.opportunity.created`

| Field | Type | Description |
|-------|------|-------------|
| Producer | Opportunity (CAP-012) | |
| Consumers | Timeline, Pipeline, Forecast, Knowledge Graph, Digital Twin | |
| Schema | `{ opp_id, org_id, name, value, stage, probability, owner }` | |

### `com.salesos.opportunity.stage_changed`

| Field | Type | Description |
|-------|------|-------------|
| Producer | Opportunity (CAP-012) | |
| Consumers | Timeline, Pipeline, Forecast, Analytics, Digital Twin | |
| Schema | `{ opp_id, from_stage, to_stage, reason, moved_by }` | |

### `com.salesos.opportunity.closed_won`

| Field | Type | Description |
|-------|------|-------------|
| Producer | Opportunity (CAP-012) | |
| Consumers | Timeline, Forecast, Revenue Graph, Analytics, Digital Twin | |
| Schema | `{ opp_id, org_id, value, days_in_pipeline, closed_by }` | |

### `com.salesos.opportunity.closed_lost`

| Field | Type | Description |
|-------|------|-------------|
| Producer | Opportunity (CAP-012) | |
| Consumers | Timeline, Forecast, Analytics, Digital Twin | |
| Schema | `{ opp_id, org_id, value, lost_reason, competitor }` | |

---

## FORECAST EVENTS

### `com.salesos.forecast.updated`

| Field | Type | Description |
|-------|------|-------------|
| Producer | Forecast (CAP-014) | |
| Consumers | Timeline, Analytics, Digital Twin | |
| Schema | `{ forecast_id, period, projected_value, confidence, scenario }` | |

### `com.salesos.forecast.scenario_applied`

| Field | Type | Description |
|-------|------|-------------|
| Producer | Forecast (CAP-014) | |
| Consumers | Timeline, Digital Twin | |
| Schema | `{ forecast_id, scenario_name, parameters, projected_outcome }` | |

---

## SEARCH EVENTS

### `com.salesos.search.executed`

| Field | Type | Description |
|-------|------|-------------|
| Producer | Search (CAP-003) | |
| Consumers | Analytics, Digital Twin | |
| Schema | `{ query, filters, results_count, latency_ms, strategy_used }` | |

---

## ANALYTICS EVENTS

### `com.salesos.analytics.kpi_calculated`

| Field | Type | Description |
|-------|------|-------------|
| Producer | Analytics (CAP-015) | |
| Consumers | Timeline, Digital Twin | |
| Schema | `{ kpi_name, value, period, dimension, source_snapshot }` | |

### `com.salesos.analytics.snapshot_taken`

| Field | Type | Description |
|-------|------|-------------|
| Producer | Analytics (CAP-015) | |
| Consumers | Timeline, Data Lake, Audit | |
| Schema | `{ snapshot_id, period, kpis: [{name, value}] }` | |

---

## RECOMMENDATION EVENTS

### `com.salesos.recommendation.generated`

| Field | Type | Description |
|-------|------|-------------|
| Producer | Recommendation (CAP-016) | |
| Consumers | Timeline, AI Memory, Digital Twin | |
| Schema | `{ rec_id, type, target_entity, action, expected_value, confidence, evidence }` | |

### `com.salesos.recommendation.accepted`

| Field | Type | Description |
|-------|------|-------------|
| Producer | Recommendation (CAP-016) | |
| Consumers | Timeline, Analytics, Digital Twin | |
| Schema | `{ rec_id, accepted_by, execution_time }` | |

### `com.salesos.recommendation.rejected`

| Field | Type | Description |
|-------|------|-------------|
| Producer | Recommendation (CAP-016) | |
| Consumers | Timeline, Analytics, AI Memory | |
| Schema | `{ rec_id, rejected_by, reason }` | |

---

## DATA FABRIC EVENTS

### `com.salesos.data.collector_completed`

| Field | Type | Description |
|-------|------|-------------|
| Producer | Data Fabric (CAP-005) | |
| Consumers | Timeline, Entity Resolution, Digital Twin | |
| Schema | `{ source, records_collected, new_records, updated_records, errors }` | |

### `com.salesos.data.entity_resolved`

| Field | Type | Description |
|-------|------|-------------|
| Producer | Entity Resolution (CAP-033) | |
| Consumers | Timeline, Knowledge Graph, Feature Store, Digital Twin | |
| Schema | `{ golden_record_id, source_records: [id], resolution_method, confidence }` | |

### `com.salesos.data.golden_record_updated`

| Field | Type | Description |
|-------|------|-------------|
| Producer | Entity Resolution (CAP-033) | |
| Consumers | Timeline, Search, Knowledge Graph, Digital Twin | |
| Schema | `{ golden_record_id, changes: [{field, old, new, source}] }` | |

### `com.salesos.data.feature_computed`

| Field | Type | Description |
|-------|------|-------------|
| Producer | Feature Store (CAP-006) | |
| Consumers | Timeline, Digital Twin | |
| Schema | `{ feature_name, entity_id, value, computation_method, latency_ms }` | |

---

## AI EVENTS

### `com.salesos.ai.copilot_query`

| Field | Type | Description |
|-------|------|-------------|
| Producer | AI Copilot (CAP-022) | |
| Consumers | Timeline, AI Governance, Analytics | |
| Schema | `{ query, response_summary, tokens_used, model, latency_ms, confidence }` | |

### `com.salesos.ai.score_computed`

| Field | Type | Description |
|-------|------|-------------|
| Producer | Scoring Engine (CAP-023) | |
| Consumers | Timeline, Feature Store, Digital Twin | |
| Schema | `{ entity_id, score_type, score, components, model_version }` | |

### `com.salesos.ai.memory_updated`

| Field | Type | Description |
|-------|------|-------------|
| Producer | AI Memory (CAP-025) | |
| Consumers | Timeline, Digital Twin | |
| Schema | `{ entity_id, memory_type, content, importance, decay_factor }` | |

---

## DIGITAL TWIN EVENTS

### `com.salesos.digital_twin.state_refreshed`

| Field | Type | Description |
|-------|------|-------------|
| Producer | Digital Twin (CAP-032) | |
| Consumers | Timeline, Analytics | |
| Schema | `{ workspace_id, snapshot_id, state_summary, computation_latency }` | |

### `com.salesos.digital_twin.risk_detected`

| Field | Type | Description |
|-------|------|-------------|
| Producer | Digital Twin (CAP-032) | |
| Consumers | Timeline, Notification, Revenue Brain | |
| Schema | `{ risk_type, entity_id, probability, impact, mitigation }` | |

### `com.salesos.digital_twin.recommendation_generated`

| Field | Type | Description |
|-------|------|-------------|
| Producer | Digital Twin (CAP-032) | |
| Consumers | Timeline, Notification, Revenue Brain | |
| Schema | `{ action, expected_value, confidence, context }` | |

---

## WORKFLOW EVENTS

### `com.salesos.workflow.triggered`

| Field | Type | Description |
|-------|------|-------------|
| Producer | Workflow Engine (CAP-009) | |
| Consumers | Timeline, Analytics, Digital Twin | |
| Schema | `{ workflow_id, trigger_event, condition_results }` | |

### `com.salesos.workflow.completed`

| Field | Type | Description |
|-------|------|-------------|
| Producer | Workflow Engine (CAP-009) | |
| Consumers | Timeline, Analytics, Digital Twin | |
| Schema | `{ workflow_id, actions_executed, duration_ms, success }` | |

### `com.salesos.workflow.failed`

| Field | Type | Description |
|-------|------|-------------|
| Producer | Workflow Engine (CAP-009) | |
| Consumers | Timeline, Alerting, Dead Letter Queue | |
| Schema | `{ workflow_id, failed_action, error, retry_count }` | |

---

## EXPERIMENT EVENTS

### `com.salesos.experiment.started`

| Field | Type | Description |
|-------|------|-------------|
| Producer | Experiment Engine (CAP-030) | |
| Consumers | Timeline, Analytics | |
| Schema | `{ experiment_id, variant_a, variant_b, metric, sample_size }` | |

### `com.salesos.experiment.completed`

| Field | Type | Description |
|-------|------|-------------|
| Producer | Experiment Engine (CAP-030) | |
| Consumers | Timeline, Analytics, Digital Twin | |
| Schema | `{ experiment_id, winner, lift, confidence, duration }` | |

---

## EVENT CONSUMER MAP

```
Event                    Timeline  Search  KG  FS  Analytics  DT  Notification  Audit
─────────────────────────────────────────────────────────────────────────────────────
tenant_created             ✅               ✅   ✅   ✅        ✅                ✅
user_created               ✅                            ✅        ✅            ✅
organization_created       ✅        ✅     ✅   ✅   ✅        ✅                ✅
organization_updated       ✅        ✅     ✅   ✅   ✅        ✅                ✅
opportunity_created        ✅              ✅   ✅   ✅        ✅                ✅
opportunity.stage_changed  ✅              ✅   ✅   ✅        ✅                ✅
opportunity.closed_won     ✅              ✅   ✅   ✅        ✅                ✅
forecast.updated           ✅                            ✅        ✅                ✅
search.executed            ✅                            ✅        ✅                ✅
recommendation.generated   ✅                                    ✅   ✅
collector_completed        ✅              ✅   ✅   ✅        ✅                ✅
entity_resolved            ✅              ✅   ✅   ✅        ✅                ✅
feature_computed           ✅                            ✅        ✅                ✅
copilot_query              ✅                            ✅        ✅          ✅
risk_detected              ✅                                    ✅   ✅
workflow.completed         ✅                            ✅        ✅                ✅
experiment.completed       ✅                            ✅        ✅                ✅
```

---

*This event catalog is the authoritative registry of all domain events. Every new event type must be registered here before implementation. Consumers must be updated when event schemas change.*
