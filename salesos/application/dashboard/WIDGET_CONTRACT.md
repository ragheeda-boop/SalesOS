# Dashboard Widget Contract

> **Purpose:** Unified contract for all dashboard widgets — lifecycle, states, refresh, cache, error handling, permissions, and telemetry.
>
> **Applies to:** All 6 widgets (Mission Center, Decision Queue, Intelligence Feed, AI Brief, Market Pulse, Recent Activity).
>
> **Architecture:** ADR-002 — Dashboard as Projection.

---

## 1. Contract Interface

Every widget implements `DashboardWidget<T>`:

```typescript
interface DashboardWidget<T> {
  id: string               // Unique widget identifier
  title: string            // Human-readable title
  status: WidgetStatus     // Current lifecycle state
  lastUpdated: string | null  // ISO 8601 timestamp of last successful fetch
  data: T | null           // Widget-specific data payload
  actions: WidgetAction[]  // Available user actions
}

type WidgetStatus = 'ready' | 'loading' | 'degraded' | 'error'

interface WidgetAction {
  id: string
  label: string
  type: 'refresh' | 'navigate' | 'dismiss' | 'custom'
  payload?: Record<string, unknown>
}
```

---

## 2. Lifecycle

```
                  ┌──────────────┐
                  │   loading    │
                  └──────┬───────┘
                         │
              ┌──────────┼──────────┐
              ▼          ▼          ▼
        ┌─────────┐ ┌─────────┐ ┌───────┐
        │  ready  │ │degraded │ │ error │
        └────┬────┘ └────┬────┘ └───┬───┘
             │           │          │
             └───────────┼──────────┘
                         │
                    ┌────┴────┐
                    │ refresh │  (user or auto)
                    └─────────┘
                         │
                         ▼
                    ┌──────────────┐
                    │   loading    │  (back to start)
                    └──────────────┘
```

### States

| State | When | UI |
|-------|------|----|
| `loading` | Initial page load or refresh triggered | Skeleton / shimmer |
| `ready` | Data loaded successfully | Normal content |
| `degraded` | Data stale (timeout) or partially loaded | Content + warning banner |
| `error` | Source unavailable, request failed | Error card + retry button |

### Transitions

| From | To | Trigger |
|------|----|---------|
| `loading` → `ready` | Data received within timeout | Successful API response |
| `loading` → `degraded` | Data received after timeout | Late API response with stale-while-revalidate |
| `loading` → `error` | Request failed or timed out | Network error, 5xx, timeout |
| `ready` → `loading` | User refresh or auto-refresh | Manual refresh button, staleTime expiry |
| `ready` → `degraded` | Widget has data but source becomes unavailable | Background refresh fails, old data preserved |
| `degraded` → `ready` | Background refresh succeeds | Successful API response |
| `degraded` → `error` | Background refresh fails and data is too stale | Error + no usable data |
| `error` → `loading` | User clicks retry | Manual retry |

---

## 3. Refresh Policy

| Widget | Auto-refresh | Manual Refresh | Priority |
|--------|-------------|----------------|----------|
| Mission Center | Every 60s | Yes | High |
| Decision Queue | Every 60s | Yes | High |
| Intelligence Feed | Every 30s | Yes | High |
| AI Brief | Every 300s (5min) | Yes | Low |
| Market Pulse | Every 120s (2min) | Yes | Medium |
| Recent Activity | Every 60s | Yes | High |

All widgets refresh silently in background — no loading state unless user explicitly clicks refresh or the widget is empty.

**Refresh strategy:**
- Auto-refresh uses `staleTime` on React Query, not polling
- Background refetch does NOT show skeleton unless data is absent
- Manual refresh shows brief loading indicator (0.3s debounce minimum)

---

## 4. Cache Policy

| Widget | staleTime | cacheTime | Strategy |
|--------|-----------|-----------|----------|
| Mission Center | 60s | 5min | Stale-while-revalidate |
| Decision Queue | 60s | 5min | Stale-while-revalidate |
| Intelligence Feed | 30s | 2min | Network-first (freshness critical) |
| AI Brief | 300s | 10min | Cache-first (expensive to generate) |
| Market Pulse | 120s | 10min | Stale-while-revalidate |
| Recent Activity | 60s | 5min | Stale-while-revalidate |

**Cache invalidation triggers:**
- Navigation to/from dashboard page
- User manually refreshes
- WebSocket event (future) — pushes new data to specific widgets

---

## 5. Error Policy

### Per-widget error handling

| Error Type | Frontend Behavior | Retry Strategy |
|------------|------------------|----------------|
| Network error (no connection) | `status='error'` + "No internet connection" | Auto-retry every 30s |
| Timeout (source > 500ms/1000ms) | `status='degraded'` + stale data if exists, else `status='error'` | Fallback in aggregator |
| 4xx (auth/not found) | `status='error'` + specific message | No retry (won't succeed) |
| 5xx (server error) | `status='error'` + "Server error" + retry button | Exponential backoff: 1s, 2s, 4s, 8s, max 30s |
| Empty data (no signals, no activity) | `status='ready'` + empty state component | N/A — not an error |

### Global error isolation

- **The dashboard never shows a full-page error.**
- Each widget fails/succeeds independently.
- Error in one widget does not affect others.
- The Aggregator guarantees this via per-source timeout + graceful degradation.

---

## 6. Loading Policy

| Phase | Duration | UI |
|-------|----------|----|
| Initial page load (all widgets) | < 3s | DashboardLayout skeleton (grid outline + widget skeletons) |
| Per-widget loading | < 500ms | Widget-specific skeleton |
| Background refresh | < 2s | No UI change (silent update) |
| Manual refresh | < 1s | Subtle spinner on the specific widget |

**Skeleton design rules:**
- Each widget has a dedicated skeleton matching its content shape
- Mission Center: 4 gray MetricCard rectangles
- Decision Queue: 3 gray RecommendationCard rectangles
- Intelligence Feed: 3 gray SignalCard rectangles
- AI Brief: 3 gray text lines
- Market Pulse: 2 gray TrendCard rectangles
- Recent Activity: 3 gray row rectangles

---

## 7. Permissions

| Widget | Required Permission | Fallback if Missing |
|--------|-------------------|---------------------|
| Mission Center | `dashboard:read` | `status='error'` + "Access denied" |
| Decision Queue | `scoring:read` | Widget hidden from layout |
| Intelligence Feed | `signals:read` | Widget hidden from layout |
| AI Brief | `ai:read` | Widget hidden from layout |
| Market Pulse | `signals:read` + `kgraph:read` | Widget hidden from layout |
| Recent Activity | `timeline:read` | Widget hidden from layout |

Users who lack permission for ALL widgets see a minimal dashboard with only a navigation prompt.

---

## 8. Telemetry

Every widget reports:

| Metric | When | Purpose |
|--------|------|---------|
| `widget.{id}.status` | On every status change | Dashboard health monitoring |
| `widget.{id}.latency` | On every successful fetch | Source performance tracking |
| `widget.{id}.error_count` | On error | Error rate tracking per source |
| `widget.{id}.refresh_count` | On manual refresh | User engagement |
| `widget.{id}.degraded_count` | On degraded state | Infrastructure health |
| `dashboard.total_load_time` | On initial render | User experience |
| `dashboard.num_degraded` | On status change | Overall dashboard health |

**Alert thresholds:**
- Any widget with `status='error'` for > 5 consecutive minutes → P2 alert
- Any widget with `status='degraded'` for > 15 minutes → P3 alert
- More than 3 widgets `status='error'` simultaneously → P1 incident

---

## 9. Adding a New Widget

To add a new widget to the dashboard:

1. **Define data type** — extend DashboardDTO with new field
2. **Create SourceReader** — add entry to DashboardAggregator
3. **Create Mapper** — domain model → DTO in `application/dashboard/mappers/`
4. **Define contract** — `DashboardWidget<NewData>` inherits contract automatically
5. **Build component** — `src/components/widgets/new-widget.tsx`
6. **Register widget** — add to DashboardLayout grid + permissions check
7. **Add telemetry** — widget.{id}.* metrics register automatically
8. **Update this document** — add widget to refresh/cache/error policy tables
