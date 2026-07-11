# Company DNA — Reference Widget Guide

> This widget is the reference implementation for all Company Intelligence widgets.

---

## Contract

Every widget must satisfy:

1. **Workspace Contract** — `describeWidgetContract()` from `@salesos/workspace/testing`
2. **Container Pattern** — Uses `createWidget()` from `@salesos/workspace`
3. **View Pattern** — Pure component receiving typed props
4. **States** — ready, loading, degraded, error, empty
5. **Accessibility** — ARIA roles, labels, keyboard navigation
6. **Dark Mode** — `dark:` variant classes
7. **RTL** — Arabic text, `dir="rtl"`, logical properties
8. **Reduced Motion** — `motion-reduce:transition-none`
9. **Permissions** — `permissions` in metadata
10. **Feature Flags** — `featureFlag` in metadata

---

## File Structure

```
widgets/{widget-name}/
  Container.tsx          # createWidget() call
  View.tsx               # Pure presentation component
  types.ts               # Props and data types
  index.ts               # Barrel exports
  __tests__/
    {WidgetName}.test.tsx # Contract tests + unit tests
```

---

## Test Template

```typescript
import { render, screen } from '@testing-library/react'
import { WidgetView } from '../WidgetView'
import { WidgetContainer } from '../WidgetContainer'
import { describeWidgetContract } from '@salesos/workspace/testing'
import type { WidgetViewProps } from '../types'

const sampleData = { ... }

describeWidgetContract({
  name: 'WidgetName',
  defaultData: sampleData,
  config: {
    metadata: { id: 'widget-id', title: 'العنوان', permissions: [...], featureFlag: {...} },
    render: ({ data }) => <WidgetView data={data} />,
  },
})

describe('WidgetView', () => {
  // States
  it('renders with data', ...)
  it('shows empty state', ...)
  // Accessibility
  it('has role="region"', ...)
  it('has dark mode', ...)
  it('has motion-reduce', ...)
  // Interaction
  it('handles click', ...)
  it('handles keyboard', ...)
})
```
