# Widget SDK

## Manifest (required fields)

```json
{
  "id": "com.salesos.kpi.revenue",
  "version": "1.0.0",
  "title": "Revenue KPI",
  "slots": ["dashboard.main", "company.360"],
  "permissions": ["revenue.read"],
  "size": { "minW": 2, "minH": 2 },
  "configSchema": {}
}
```

## Concepts

| Concept | Role |
|---------|------|
| SDK | Render + config APIs |
| Manifest | Discovery + versioning |
| Slots | Where widgets may mount |
| Permissions | Tenant + RBAC |
| Lifecycle | install → configure → render → update → remove |
| API | Data fetch via platform client |
| Context | workspace, user, object, filters |
| Events | `widget.resized`, `widget.drilldown`, `widget.error` |

## Honesty

AI widgets must declare `ai: true` and honor Preview gating.
