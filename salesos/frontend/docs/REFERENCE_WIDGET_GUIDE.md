# Widget SDK Reference Guide

> الإصدار: v1.0 — تاريخ الاعتماد: 2026-07-10
> هذا المستند هو المرجع الرسمي الإلزامي لأي Widget جديدة في SalesOS.

---

## Table of Contents

1. [Architecture Overview](#1-architecture-overview)
2. [Widget Lifecycle](#2-widget-lifecycle)
3. [Container / View Pattern](#3-container--view-pattern)
4. [SDK Usage](#4-sdk-usage)
5. [Widget Metadata](#5-widget-metadata)
6. [Permission Model](#6-permission-model)
7. [Feature Flags](#7-feature-flags)
8. [Telemetry](#8-telemetry)
9. [Accessibility Checklist](#9-accessibility-checklist)
10. [Testing Contract](#10-testing-contract)
11. [Performance Guidelines](#11-performance-guidelines)
12. [Definition of Done](#12-definition-of-done)
13. [Common Anti-patterns](#13-common-anti-patterns)
14. [Reference Folder Structure](#14-reference-folder-structure)
15. [Example: Mission Center](#15-example-mission-center)

---

## 1. Architecture Overview

```
┌──────────────────────────────────────────────────────────────┐
│                    Dashboard Layout                          │
│  ┌──────────────────────────────────────────────────────┐   │
│  │                  Widget Container                     │   │
│  │  ┌────────────────────────────────────────────────┐  │   │
│  │  │              Widget View (Pure)                │  │   │
│  │  │  - عرض البيانات                               │  │   │
│  │  │  - لا يعرف شيئاً عن SDK                       │  │   │
│  │  │  - يشتق الحالات من Props                      │  │   │
│  │  └────────────────────────────────────────────────┘  │   │
│  │                                                       │   │
│  │  Container Layer: useData() → render(View)            │   │
│  │  SDK Layer: createWidget() / createDashboardWidget()  │   │
│  └──────────────────────────────────────────────────────┘   │
└──────────────────────────────────────────────────────────────┘
```

### Key Principles

| Principle | Description |
|-----------|-------------|
| **Container / View Separation** | Container مسؤول عن البيانات، View مسؤول عن العرض فقط |
| **SDK First** | كل Widget تُبنى عبر `createDashboardWidget()` أو `createWidget()` |
| **No Direct Data Access in View** | View لا تستخدم hooks أو APIs مباشرة |
| **Widget States** | `ready` / `loading` / `degraded` / `error` — كلها مغطاة في الـ SDK |
| **Per-Widget Degradation** | Widget واحد يفشل لا يسقط الصفحة كلها |

### Widget States

```typescript
type WidgetStatus = 'ready' | 'loading' | 'degraded' | 'error'
```

| State | Behavior | Render |
|-------|----------|--------|
| `ready` | Data available | Widget content |
| `loading` | Fetching data | Loading spinner |
| `degraded` | Partial data | Content with 50% opacity + warning overlay |
| `error` | Fetch failed | Error state with retry button |

---

## 2. Widget Lifecycle

```typescript
interface WidgetLifecycle {
  onMount?: (ctx: { id: string; metadata: WidgetMetadata }) => void
  onUnmount?: (ctx: { id: string; metadata: WidgetMetadata }) => void
  onRefresh?: (ctx: { id: string; metadata: WidgetMetadata }) => void
  onError?: (ctx: { id: string; metadata: WidgetMetadata; error: Error }) => void
  onStatusChange?: (ctx: { id: string; metadata: WidgetMetadata; status: WidgetStatus; previous: WidgetStatus }) => void
}
```

| Hook | Trigger | Use Case |
|------|---------|----------|
| `onMount` | Widget mounts | Log view, start polling |
| `onUnmount` | Widget unmounts | Cleanup, stop polling |
| `onRefresh` | Refresh clicked | Custom refresh logic |
| `onError` | Error state entered | Error reporting |
| `onStatusChange` | Status transitions | UI reactions |

### Telemetry Events (Automatic)

| Event | When |
|-------|------|
| `widget.mounted` | Component mounts |
| `widget.unmounted` | Component unmounts (cleanup) |
| `widget.loaded` | Data received (ready or degraded) |
| `widget.failed` | Error state entered |
| `widget.refreshed` | Refresh triggered |

---

## 3. Container / View Pattern

### Rules

1. **View** هو مكون React نقي:
   - يأخذ Props فقط
   - لا يستخدم أي hooks
   - لا يستخدم SDK
   - يمكن اختباره بدون Dashboard context

2. **Container** هو المكون الذي يستخدم SDK:
   - يستخدم `useData()` hook
   - يمرر البيانات إلى View
   - يعرّف metadata (permissions, feature flags)

3. **FilePath Convention**:
   ```
   widgets/your-widget/
   ├── index.ts          # إعادة تصدير Container
   ├── YourWidgetContainer.tsx   # Container (يستخدم SDK)
   ├── YourWidgetView.tsx        # View (مكون نقي)
   ├── types.ts                  # Props + Data types
   └── __tests__/
       └── YourWidget.test.tsx   # اختبارات
   ```

---

## 4. SDK Usage

### createDashboardWidget (للـ Dashboard Widgets المدمجة)

```typescript
import { createDashboardWidget } from '@/features/dashboard/sdk'

export const MyWidget = createDashboardWidget<MyData>('myWidget', {
  metadata: {
    title: 'My Widget',
    description: 'وصف الـ Widget',
  },
  render({ data }) {
    return <MyWidgetView data={data} />
  },
})
```

### createWidget (للاستخدام العام)

```typescript
import { createWidget } from '@/features/dashboard/sdk'

const MyWidget = createWidget<MyData>({
  metadata: {
    id: 'my-widget',
    title: 'My Widget',
    permissions: ['my:read'],
  },
  useData: () => useMyData(),
  render: ({ data }) => <div>{data.value}</div>,
})
```

### Widget Registration

كل Widget تحتاج تسجيل في `features/dashboard/_registry/widget-config.ts`:

```typescript
export type WidgetId = 'missionCenter' | 'intelligenceFeed' | 'yourWidget'

export function getWidgetConfig(id: WidgetId): WidgetConfigEntry {
  const configs: Record<WidgetId, WidgetConfigEntry> = {
    // ...existing configs
    yourWidget: {
      refreshIntervalMs: 30_000,
      staleThresholdMs: 60_000,
      gridColumn: 'span-2',
      minHeight: '250px',
    },
  }
  return configs[id]
}
```

---

## 5. Widget Metadata

```typescript
interface WidgetMetadata {
  id: string                    // Required — unique widget identifier
  title: string                 // Required — display title
  description?: string          // Optional — tooltip / description
  priority?: 'low' | 'medium' | 'high' | 'critical'
  category?: 'metrics' | 'signals' | 'decisions' | 'intelligence' | 'activity'
  icon?: string                 // Optional — emoji or icon identifier
  permissions?: string[]        // Optional — required permissions
  refreshInterval?: number      // Optional — ms between auto-refresh
  staleThreshold?: number       // Optional — ms before data is stale
  featureFlag?: WidgetFeatureFlag  // Optional — feature gate
  gridColumn?: string           // Optional — dashboard grid placement
  minHeight?: string            // Optional — minimum height (default: '200px')
}
```

---

## 6. Permission Model

### Declaration

```typescript
// In metadata:
metadata: {
  permissions: ['mission_center:read'],
}
```

### Enforcement

يتم التحقق تلقائياً في `createWidget()`:

```typescript
if (!checkPermissions(config.metadata.permissions)) {
  return config.fallback ?? null
}
```

### Testing

```typescript
import { mockPermissionsNone, mockPermissionsAll } from '@/features/dashboard/sdk/testing'

beforeEach(() => mockPermissionsAll())

it('hides content when permission denied', () => {
  mockPermissionsNone()
  renderWidget(config, { useData: () => mock.ready() })
  expect(screen.queryByRole('region')).not.toBeInTheDocument()
})
```

إذا لم تُحدد `permissions` في metadata، **لن يتم تطبيق أي فحص صلاحيات** — كل المستخدمين يمكنهم رؤية الـ Widget.

---

## 7. Feature Flags

### Declaration

```typescript
interface WidgetFeatureFlag {
  enabled: boolean
  tier?: 'enabled' | 'beta' | 'internal' | 'enterprise'
  from?: string  // Release version
}
```

### Enforcement

```typescript
// In metadata:
metadata: {
  featureFlag: { enabled: true, tier: 'beta' },
}
```

### Testing

```typescript
import { mockFeatureFlagsNone, mockFeatureFlagsAll } from '@/features/dashboard/sdk/testing'

it('hides content when feature disabled', () => {
  mockFeatureFlagsNone()
  renderWidget(config, { useData: () => mock.ready() })
  expect(screen.queryByRole('region')).not.toBeInTheDocument()
})
```

⚠️ **هام**: إذا لم يُحدد `featureFlag` في metadata، يُعتبر الـ Widget مفعّلاً دائماً. الفحص يحدث فقط عند وجود `featureFlag.enabled === true`.

---

## 8. Telemetry

### Automatic Events

| Event | Detail |
|-------|--------|
| `widget.mounted` | `{ widgetId }` |
| `widget.loaded` | `{ widgetId, status }` |
| `widget.failed` | `{ widgetId, error }` |
| `widget.refreshed` | `{ widgetId }` |
| `widget.unmounted` | `{ widgetId }` |
| `widget.render` | `{ widgetId, durationMs }` |

### Custom Telemetry

```typescript
import { widgetTelemetry } from '@/features/dashboard/sdk'

widgetTelemetry.record('widget.custom', 'my-widget', {
  status: 'filtered',
})
```

### Testing Telemetry

```typescript
import { TelemetrySpy } from '@/features/dashboard/sdk/testing'

const telemetry = new TelemetrySpy()
// Use telemetry.spy, telemetry.events, telemetry.clear()
```

---

## 9. Accessibility Checklist

| Critère | Requirement | How |
|---------|-------------|-----|
| **ARIA Labels** | كل عنصر تفاعلي له `aria-label` | `aria-label="42 شركات تحت المراقبة"` |
| **Roles** | Use semantic roles | `role="region"`, `role="list"`, `role="listitem"`, `role="progressbar"` |
| **Keyboard** | All interactive elements keyboard-accessible | `role="button"`, `tabIndex={0}`, `onKeyDown` (Enter + Space) |
| **Focus** | Visible focus indicators | `focus-visible:ring-2` |
| **Screen Reader** | Live region for dynamic content | `aria-live="polite" aria-atomic="true"` |
| **Reduced Motion** | Respect `prefers-reduced-motion` | `motion-reduce:transition-none` |
| **Dark Mode** | Full dark mode support | CSS variables + `dark:` Tailwind variants |
| **Color Contrast** | WCAG AA minimum (4.5:1) | Use design tokens, not hardcoded colors |
| **Disabled State** | Disabled elements clearly indicated | `aria-disabled` attribute |
| **States** | Loading/Error/Empty states announced | `role="status"` for loading, `role="alert"` for error |

### Testing Accessibility

```typescript
// In contract tests (automatic):
// - Refresh button has aria-label
// - Loading state has role="status"
// - Error state has role="alert"
// - Error state has retry button

// Custom tests:
it('each MissionMetric has aria-label', () => {
  renderView()
  expect(screen.getByLabelText('42 شركات تحت المراقبة')).toBeInTheDocument()
})
```

---

## 10. Testing Contract

### Mandatory Contract Tests

كل Widget جديدة **يجب** أن تمر باختبارات الـ Contract:

```typescript
import { describeWidgetContract } from '@/features/dashboard/sdk/testing'

describeWidgetContract({
  name: 'MyWidget',
  defaultData: { /* your data shape */ },
  config: {
    metadata: {
      id: 'my-widget',
      title: 'My Widget',
      minHeight: '200px',
      permissions: ['my:read'],      // Required for permission tests
      featureFlag: { enabled: true }, // Required for feature flag tests
    },
    render: ({ data }) => <MyWidgetView data={data} />,
  },
})
```

### Contract Test Coverage

| # | Category | Tests |
|---|----------|-------|
| 1 | Rendering | Title, children, fallback (permission + feature) |
| 2 | Widget States | Loading, ready, degraded (with/without data), error |
| 3 | Permissions | Granted, denied |
| 4 | Feature Flags | Enabled, disabled |
| 5 | Accessibility | Refresh aria-label, loading role, error role + retry |
| 6 | Interaction | Retry click → refetch, Refresh click → refetch |

### Mandatory Custom Tests

بالإضافة إلى Contract tests، كل Widget تحتاج:

- **View unit tests** — 100% of visual states
- **Accessibility tests** — ARIA labels, roles, keyboard, motion-reduce, dark mode
- **Interaction tests** — All user interactions (click, keydown)
- **Edge cases** — Empty state, null data, boundary values
- **SDK integration test** — Component is valid React component

### Test File Naming

```
__tests__/
├── MissionCenter.test.tsx    # كل الاختبارات في ملف واحد
├── WidgetContract.spec.tsx    # Contract tests (suffix .spec.tsx)
```

---

## 11. Performance Guidelines

### Requirements

| Metric | Budget | Enforcement |
|--------|--------|-------------|
| Initial render | < 100ms | Jest + jsdom |
| Re-render | < 50ms | React.memo + useCallback |
| Bundle size | < 20KB gzipped | Bundle analyzer |
| API calls | 1 per mount | Widget lifecycle |
| Telemetry events | < 5 per mount | Automatic |

### Best Practices

1. **`React.memo`** يُضاف تلقائياً عبر `createWidget()`
2. **`useCallback`** للـ handlers الممررة إلى View
3. **CSS variables** بدلاً من theme context لتجنب re-renders
4. **Avoid `useTheme()`** في View — استخدم Tailwind classes مباشرة
5. **Per-widget data fetching** — كل Widget تجلب بياناتها بشكل مستقل

---

## 12. Definition of Done

| # | Requirement | Verified By |
|---|-------------|-------------|
| 1 | Container/View pattern | Code Review |
| 2 | Uses `createDashboardWidget()` or `createWidget()` | Code Review |
| 3 | Registered in widget-config.ts | Code Review |
| 4 | All 4 states covered (ready/loading/degraded/error) | Contract tests |
| 5 | Permission model declared and tested | Contract tests |
| 6 | Feature flag declared and tested | Contract tests |
| 7 | Telemetry auto-events verified | Unit tests |
| 8 | WCAG AA accessibility (see checklist) | Code Review + Tests |
| 9 | Dark mode support (CSS variables + Tailwind dark:) | Visual + Tests |
| 10 | Reduced motion support | Tests |
| 11 | RTL layout support | Visual check |
| 12 | Keyboard navigation | Tests |
| 13 | Empty state handled | Custom tests |
| 14 | Error/retry UX | Contract tests |
| 15 | Contract tests pass (describeWidgetContract) | CI |
| 16 | Custom unit tests pass | CI |
| 17 | TypeScript clean (no regressions) | tsc |
| 18 | No hardcoded colors or values | Code Review |

---

## 13. Common Anti-patterns

### ❌ View يستخدم hooks مباشرة
```typescript
// BAD
function MyWidgetView() {
  const { data } = useDashboardContext()  // ❌
  return <div>{data}</div>
}

// GOOD
function MyWidgetView({ data }: { data: MyData }) {
  return <div>{data}</div>
}
```

### ❌ Container يخلط منطق العرض
```typescript
// BAD
export const Widget = createWidget({
  render: ({ data }) => (
    <div style={{ color: data.error ? 'red' : 'green' }}>
      {data.value}
    </div>
  ),
})

// GOOD — استخدم View
export const Widget = createWidget({
  render: ({ data }) => <MyWidgetView data={data} />,
})
```

### ❌ تجاهل حالات الـ Widget
```typescript
// BAD — فقط ready
render: ({ data }) => <View data={data} />,

// GOOD — كل الحالات مغطاة (تلقائي من SDK)
// createWidget() يدير loading/degraded/error تلقائياً
```

### ❌ Fallback بدون permission/feature flag في الاختبارات
```typescript
// BAD
config: {
  metadata: {
    id: 'test',
    title: 'Test',
    // permissions و featureFlag غير محددة
  },
}

// GOOD
config: {
  metadata: {
    id: 'test',
    title: 'Test',
    permissions: ['test:read'],        // ضروري لاختبارات الصلاحيات
    featureFlag: { enabled: true },    // ضروري لاختبارات feature flags
  },
}
```

### ❌ Hardcoded colors بدلاً من CSS variables
```typescript
// BAD
<div style={{ color: '#f97316' }}>...</div>

// GOOD
<div className="text-[var(--muhide-orange)]">...</div>
// أو أفضل: استخدم Tailwind semantic color
<div className="text-warning-600 dark:text-warning-400">...</div>
```

### ❌ تجاهل reduced motion
```typescript
// BAD
<div className="transition-all duration-300">

// GOOD
<div className="transition-all duration-300 motion-reduce:transition-none">
```

---

## 14. Reference Folder Structure

```
src/features/dashboard/
├── sdk/                           # Widget SDK — لا يُعدّل إلا بتغيّير معماري
│   ├── index.ts                   # Barrel export
│   ├── types.ts                   # كل أنواع Widget
│   ├── create-widget.tsx          # Widget factory
│   ├── create-dashboard-widget.ts # Dashboard-specific factory
│   ├── widget-lifecycle.ts        # Lifecycle hooks
│   ├── widget-telemetry.ts        # Telemetry system
│   ├── widget-permissions.ts      # Permission checker
│   ├── widget-feature-flags.ts    # Feature flag resolver
│   ├── testing/                   # ** جديد — أدوات الاختبار المعيارية **
│   │   ├── index.ts
│   │   ├── renderWidget.tsx       # Widget render helper
│   │   ├── mockWidgetContext.ts   # State factories
│   │   ├── mockTelemetry.ts       # Telemetry spy
│   │   ├── mockPermissions.ts     # Permission mocks
│   │   ├── mockFeatureFlags.ts    # Feature flag mocks
│   │   ├── types.ts               # Testing-specific types
│   │   └── WidgetContract.tsx     # Contract test suite
│   └── __tests__/
│       ├── create-widget.test.tsx # SDK unit tests
│       └── WidgetContract.spec.tsx # Contract self-test
│
├── widgets/
│   ├── mission-center/            # ** Reference Widget **
│   │   ├── index.ts
│   │   ├── MissionCenterContainer.tsx
│   │   ├── MissionCenterView.tsx
│   │   ├── MissionMetric.tsx
│   │   ├── MissionAction.tsx
│   │   ├── MissionProgress.tsx
│   │   ├── types.ts
│   │   └── __tests__/
│   │       └── MissionCenter.test.tsx
│   │
│   └── widget-card.tsx
│
├── _registry/
│   └── widget-config.ts           # Widget registration
├── _providers/
│   └── dashboard-provider.tsx
├── _layout/
└── _telemetry/
```

### WidgetTemplate (للبدء السريع)

```
src/features/dashboard/widgets/your-widget/
├── index.ts
├── YourWidgetContainer.tsx
├── YourWidgetView.tsx
├── types.ts
└── __tests__/
    └── YourWidget.test.tsx
```

انظر [WidgetTemplate](../../../../WidgetTemplate/) للنسخة الجاهزة.

---

## 15. Example: Mission Center

Mission Center هو **Reference Widget** — أول Widget بُنيت وفق هذا المعيار.

### Files

| File | Purpose |
|------|---------|
| `MissionCenterContainer.tsx` | Uses `createDashboardWidget`, defines metadata, passes data to View |
| `MissionCenterView.tsx` | Pure component, renders all 5 metrics + actions + progress |
| `MissionMetric.tsx` | Reusable metric display with `valueClassName`, trend, aria-label |
| `MissionAction.tsx` | Reusable action item with priority badge, keyboard, aria-disabled |
| `MissionProgress.tsx` | Reusable progress bar with aria-valuetext, motion-reduce |
| `types.ts` | `MissionCenterViewProps` + `MissionMetricProps` + etc. |

### Key Design Decisions

1. **Container لا يحتوي على أي منطق عرض** — فقط يحضر البيانات ويمررها
2. **View تتعامل مع كل الحالات** — empty state, all-zero, partial data
3. **كل مكون له `valueClassName` بدلاً من `color`** — لدعم dark mode
4. **CSS variables للـ backgrounds** — `bg-[var(--bg-secondary)]`
5. **Talwind semantic colors للنصوص** — `dark:text-success-400`
6. **`aria-live="polite"` في SummaryBanner** — للتحديثات الصوتية
7. **`motion-reduce:transition-none`** — احترام تفضيلات المستخدم
8. **EmptyState** — عرض رسالة عند عدم وجود بيانات

### Test Coverage

| Category | Tests | Status |
|----------|-------|--------|
| Contract Tests | 18 static tests | ✅ Pass |
| Today's Mission | 6 tests | ✅ Pass |
| Priority Actions | 7 tests | ✅ Pass |
| Revenue Opportunity | 2 tests | ✅ Pass |
| Completion Progress | 3 tests | ✅ Pass |
| Empty State | 4 tests | ✅ Pass |
| Summary Banner | 2 tests | ✅ Pass |
| Accessibility (Metrics) | 3 tests | ✅ Pass |
| Accessibility (Actions) | 3 tests | ✅ Pass |
| Accessibility (Progress) | 2 tests | ✅ Pass |
| Accessibility (Roles) | 1 test | ✅ Pass |
| Interaction | 2 tests | ✅ Pass |
| Dark Mode | 3 tests | ✅ Pass |
| Reduced Motion | 2 tests | ✅ Pass |
| MissionMetric | 4 tests | ✅ Pass |
| MissionAction | 4 tests | ✅ Pass |
| MissionProgress | 3 tests | ✅ Pass |
| SDK Integration | 1 test | ✅ Pass |
| **Total** | **~70 tests** | ✅ **All pass** |

---

## Appendix: SDK Feature Freeze

تم تثبيت Widget SDK v1.0 في 2026-07-10.

### Rules

1. لا تُقبل أي تغييرات على الـ SDK إلا إذا أثبتت Widget جديدة وجود نقص حقيقي
2. أي تغيير يحتاج:
   - ADR (Architecture Decision Record)
   - تحديث هذا الدليل
   - تحديث كل Widgets الموجودة
   - تحديث Contract tests
3. الأولوية الآن: بناء Widgets فوق الـ SDK المستقرة
