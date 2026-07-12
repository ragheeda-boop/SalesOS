# @salesos/ui

Foundation UI components built on Radix primitives. The canonical component library for all SalesOS applications.

## Purpose

Provides accessible, themeable, reusable UI primitives that all widgets and pages consume. Includes layout, data display, feedback, and input components.

## Exports

| Export | Source | Description |
|--------|--------|-------------|
| `Button` | `button.tsx` | Button with variants (primary, secondary, ghost, danger) and sizes |
| `Card` | `card.tsx` | Card container with header, content, footer slots |
| `Badge` | `badge.tsx` | Status badge with color variants |
| `Avatar` | `avatar.tsx` | User avatar with fallback |
| `Spinner` | `spinner.tsx` | Loading spinner with size variants |
| `Input` | `input.tsx` | Text input with label, error, help text |
| `Select` | `select.tsx` | Radix-based select dropdown |
| `Modal` | `modal.tsx` | Radix dialog modal |
| `Tabs` | `tabs.tsx` | Radix tab navigation |
| `Toast` | `toast.tsx` | Radix toast notifications |
| `Tooltip` | `tooltip.tsx` | Radix tooltip |
| `Dropdown` | `dropdown.tsx` | Radix dropdown menu |
| `Table` | `table.tsx` | TanStack Table wrapper |
| `Kbd` | `kbd.tsx` | Keyboard shortcut display |
| `Layout` | `layout.tsx` | App shell (sidebar, header, content) |
| `Sidebar` | `sidebar.tsx` | Navigation sidebar |
| `cn` | `utils.ts` | Classname merge utility (clsx + tailwind-merge) |

## Usage

```tsx
import { Button, Card, Badge } from '@salesos/ui'

function Example() {
  return (
    <Card>
      <Card.Header>Title</Card.Header>
      <Card.Content>
        <Badge variant="success">Active</Badge>
        <Button variant="primary">Action</Button>
      </Card.Content>
    </Card>
  )
}
```
