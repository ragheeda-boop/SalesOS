# Dashboard Engine

Dashboards are **not** static pages — they are views over the engine.

## Capabilities

| Capability | Description |
|------------|-------------|
| Builder | Add/remove/resize widgets |
| Layout | 12-col responsive grid |
| Saved Views | Named layouts |
| Personal Views | Per-user |
| Role Views | Default by persona |
| Shared Views | Workspace-published |
| Fullscreen | Focus mode |
| Export | PNG/PDF/CSV of widgets where allowed |
| Filters | Global time range, owner, segment |
| Drilldown | Widget → object list → record |
| Marketplace | Install widgets into slots |

## View model (conceptual)

```json
{
  "id": "view_…",
  "scope": "personal|role|shared",
  "filters": {},
  "widgets": [{ "id": "w1", "widgetType": "kpi", "slot": "a1", "config": {} }]
}
```

## Role homes consume the engine

Executive, Sales, Ops, CS, Finance, Marketing, Support, Data Quality, AI, Executive Cockpit — see `screens/dashboards/`.
