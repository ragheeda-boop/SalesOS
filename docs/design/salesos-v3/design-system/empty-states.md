# Empty State Library

| State | When | Content pattern |
|-------|------|-----------------|
| No Data | Empty collection | Title, explanation, primary CTA |
| No Permission | 403 | Why + request access |
| Loading | Pending | Skeleton matching layout |
| Disconnected | API unreachable | Retry |
| Offline | Navigator offline | Queued actions note |
| Error | 5xx / unexpected | Code ref + retry + support |
| Search Empty | No hits | Clear query + suggestions |
| Filtered Empty | Filters exclude all | Clear filters |
| AI Empty | No model/flag | Honesty copy + Preview |
| Widget Empty | Widget no data | Configure / remove |

All empty states are **action-oriented** (one primary action maximum).
