# Tutorial: Creating a Custom Widget

> **بناء واجهة مخصصة — دليل خطوة بخطوة لإنشاء Widget جديد**

This tutorial walks through building a "Company Health Score" widget from scratch.

---

## Prerequisites

- SalesOS tenant with `admin` role
- Widget SDK installed: `npm install @salesos/workspace`
- TypeScript project configured

---

## Step 1: Use the Widget Template

Always start from the template (per Engineering Constitution Article 9.5):

```bash
cp -r WidgetTemplate/ src/widgets/company-health/
cd src/widgets/company-health
```

---

## Step 2: Define the Widget

```typescript
// src/widgets/company-health/index.tsx
import { createDashboardWidget } from '@salesos/workspace'

interface HealthData {
  score: number
  label: string
  factors: Array<{ name: string; value: number; weight: number }>
  trend: 'up' | 'down' | 'stable'
}

const CompanyHealthWidget = createDashboardWidget<HealthData>({
  id: 'company-health-score',
  title: 'Company Health Score',
  description: 'Displays overall company health with factor breakdown',
  defaultSize: { w: 3, h: 3 },
  permissions: ['company:read'],
  featureFlag: 'ff_company_health_widget',

  async fetchData(ctx) {
    const { companyId } = ctx.workspace
    const response = await ctx.api.get(`/companies/${companyId}/scores`)
    return response.data
  },

  render(data, ctx) {
    return (
      <div className="health-widget" role="region" aria-label="Company health score">
        <div className="health-score">
          <span className="score-value">{Math.round(data.score * 100)}</span>
          <span className="score-label">{data.label}</span>
        </div>
        <div className="health-factors">
          {data.factors.map(f => (
            <FactorBar key={f.name} name={f.name} value={f.value} />
          ))}
        </div>
        <TrendIndicator trend={data.trend} />
      </div>
    )
  },
})

export default CompanyHealthWidget
```

---

## Step 3: Create the View Component

Pure component — no SDK dependencies:

```typescript
// src/widgets/company-health/HealthView.tsx
interface HealthViewProps {
  score: number
  label: string
  factors: Factor[]
  trend: 'up' | 'down' | 'stable'
}

export function HealthView({ score, label, factors, trend }: HealthViewProps) {
  return (
    <div className="health-view">
      <ScoreCircle value={score} label={label} />
      <FactorList factors={factors} />
      <TrendBadge trend={trend} />
    </div>
  )
}
```

---

## Step 4: Add Contract Tests

```typescript
// src/widgets/company-health/__tests__/contract.test.tsx
import { describeWidgetContract } from '@salesos/workspace/testing'
import CompanyHealthWidget from '../index'

describeWidgetContract({
  component: CompanyHealthWidget,
  name: 'Company Health Score Widget',
  scenarios: [
    {
      name: 'healthy company',
      state: {
        status: 'ready',
        data: {
          score: 0.85,
          label: 'Strong',
          factors: [
            { name: 'financial_health', value: 0.9, weight: 0.3 },
            { name: 'growth_trend', value: 0.8, weight: 0.2 },
          ],
          trend: 'up',
        },
      },
    },
    {
      name: 'loading',
      state: { status: 'loading' },
    },
    {
      name: 'error',
      state: { status: 'error', error: 'Failed to load company data' },
    },
  ],
})
```

---

## Step 5: Register the Widget

```typescript
// In your app's widget registry
import { registry } from '@salesos/workspace'
import CompanyHealthWidget from './widgets/company-health'

registry.registerWidget(CompanyHealthWidget)
```

---

## Widget Lifecycle

```
Widget Creation
      │
      ▼
┌─────────────────────────────────────────┐
│ createDashboardWidget / createWidget    │
│ • Define id, title, permissions        │
│ • Implement fetchData, render          │
└─────────────────────────────────────────┘
      │
      ▼
┌─────────────────────────────────────────┐
│ Registration                            │
│ • registry.registerWidget(widget)       │
└─────────────────────────────────────────┘
      │
      ▼
┌─────────────────────────────────────────┐
│ Runtime                                 │
│ • onMount → check permissions          │
│ • check feature flag                    │
│ • fetchData → render                    │
│ • onUnmount → cleanup                   │
└─────────────────────────────────────────┘
```

---

## Accessibility Requirements

| Requirement | Standard |
|-------------|----------|
| Keyboard navigation | All interactive elements focusable |
| ARIA labels | `role`, `aria-label`, `aria-describedby` |
| Color contrast | WCAG AA minimum (4.5:1) |
| Dark mode | Supports `prefers-color-scheme: dark` |
| Reduced motion | Respects `prefers-reduced-motion` |

---

## Testing Requirements

| Test | Required |
|------|----------|
| `describeWidgetContract()` | ✅ Mandatory |
| Loading state renders | ✅ Mandatory |
| Error state renders | ✅ Mandatory |
| Empty/no-permission state | ✅ Mandatory |
| Keyboard navigation test | ✅ Mandatory |
| Dark mode visual test | ✅ Recommended |

---

## Related

| Resource | Link |
|----------|------|
| Workspace SDK Reference | [SDK](../sdk/workspace-sdk.md) |
| Widget Template | `WidgetTemplate/` in repository |
| Contract Tests | `describeWidgetContract()` docs |
| Engineering Constitution (Article 9) | [Widget SDK Rules](../../../engineering-os/ENGINEERING_CONSTITUTION.md#-9) |
