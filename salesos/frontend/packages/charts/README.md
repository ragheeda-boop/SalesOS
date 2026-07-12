# @salesos/charts

Recharts-based chart components styled with MUHIDE design tokens.

## Purpose

Provides reusable chart components (bar, line, area, pie, radar, etc.) that integrate with `@salesos/ui` styling and `@salesos/design-language` tokens.

## Exports

| Export | Source | Description |
|--------|--------|-------------|
| `BarChart` | `index.tsx` | Vertical/horizontal bar chart |
| `LineChart` | `index.tsx` | Line chart with multiple series |
| `AreaChart` | `index.tsx` | Area/stacked area chart |
| `PieChart` | `index.tsx` | Pie/donut chart |
| `RadarChart` | `index.tsx` | Radar/spider chart |
| `ComposedChart` | `index.tsx` | Mixed chart types |

All charts support: responsive sizing, tooltips, legends, dark mode, RTL, and accessibility labels.

## Usage

```tsx
import { BarChart, LineChart } from '@salesos/charts'

function RevenueChart() {
  return (
    <BarChart
      data={revenueData}
      xKey="month"
      series={[{ key: 'revenue', color: 'brand.primary', label: 'Revenue' }]}
    />
  )
}
```
