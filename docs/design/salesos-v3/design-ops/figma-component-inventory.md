# Figma Component Inventory — SalesOS DS v3

Source: [`design-system/components.md`](../design-system/components.md).  
Build in file **SalesOS DS v3** → page **Components**. Bind fills/strokes/spacing to Variables from `tokens.figma.json`.

**Variant system:** `variant` · `size` · `tone` (`neutral` / `accent` / `danger` / `ai`).  
**States (every interactive):** default · hover · focus · active · disabled · loading · error · success.

Checklist legend: `[ ]` = not built · `[x]` = built & reviewed.

---

## Atoms

### Button
| Figma name | Variants | States |
|------------|----------|--------|
| `Button` | **variant:** `solid` / `outline` / `ghost` / `link` · **size:** `sm` / `md` / `lg` · **tone:** `neutral` / `accent` / `danger` / `ai` | default · hover · focus · active · disabled · loading |

- [ ] All variant × size × tone combinations
- [ ] Loading shows Spinner + preserves width
- [ ] `tone=accent` uses brand `#F57C1E` (CTA only)
- [ ] Icon+label and label-only layouts
- [ ] RTL mirror

### IconButton
| Figma name | Variants | States |
|------------|----------|--------|
| `IconButton` | **size:** `sm` / `md` / `lg` · **tone:** `neutral` / `accent` / `danger` / `ai` · **shape:** `square` / `circle` | default · hover · focus · active · disabled · loading |

- [ ] Accessible name annotation (tooltip / aria note)
- [ ] Focus ring visible

### Input
| Figma name | Variants | States |
|------------|----------|--------|
| `Input` | **size:** `sm` / `md` / `lg` · **type:** `text` / `email` / `password` / `search` | default · hover · focus · disabled · error · success |

- [ ] Leading / trailing icon slots
- [ ] Clear affordance (optional)
- [ ] Error helper text spacing `space/2`

### Textarea
| Figma name | Variants | States |
|------------|----------|--------|
| `Textarea` | **size:** `sm` / `md` / `lg` · **resize:** `none` / `vertical` | default · hover · focus · disabled · error · success |

- [ ] Min-height + auto-grow annotation

### Checkbox
| Figma name | Variants | States |
|------------|----------|--------|
| `Checkbox` | **size:** `sm` / `md` · **checked:** `false` / `true` / `indeterminate` | default · hover · focus · disabled · error |

- [ ] Label + description layout

### Radio
| Figma name | Variants | States |
|------------|----------|--------|
| `Radio` | **size:** `sm` / `md` · **selected:** `false` / `true` | default · hover · focus · disabled · error |

- [ ] Radio group (3 options) as instance demo

### Switch
| Figma name | Variants | States |
|------------|----------|--------|
| `Switch` | **size:** `sm` / `md` · **on:** `false` / `true` | default · hover · focus · disabled · loading |

- [ ] Label left / right (LTR + RTL)

### Badge
| Figma name | Variants | States |
|------------|----------|--------|
| `Badge` | **tone:** `neutral` / `accent` / `danger` / `ai` / `success` / `warning` · **size:** `sm` / `md` · **style:** `solid` / `subtle` | default (static) |

- [ ] `Preview` badge for AI (tone=`ai`)

### Avatar
| Figma name | Variants | States |
|------------|----------|--------|
| `Avatar` | **size:** `xs` / `sm` / `md` / `lg` / `xl` · **type:** `image` / `initials` / `icon` | default · loading |

- [ ] Status dot optional
- [ ] AvatarGroup (stack) pattern frame

### Spinner
| Figma name | Variants | States |
|------------|----------|--------|
| `Spinner` | **size:** `sm` / `md` / `lg` · **tone:** `neutral` / `accent` / `inverse` | animating (prototype optional) |

- [ ] Reduced-motion note

### Kbd
| Figma name | Variants | States |
|------------|----------|--------|
| `Kbd` | **size:** `sm` / `md` | default |

- [ ] Single key + chord (`⌘K`) examples

---

## Molecules

### FormField
| Figma name | Variants | States |
|------------|----------|--------|
| `FormField` | **required:** `true` / `false` · **layout:** `vertical` / `horizontal` | default · error · success · disabled |

- [ ] Label · helper · error message slots
- [ ] Wraps Input / Select / Textarea / Combobox

### SearchInput
| Figma name | Variants | States |
|------------|----------|--------|
| `SearchInput` | **size:** `sm` / `md` / `lg` · **scope:** `global` / `local` | default · hover · focus · loading · disabled |

- [ ] Leading search icon · clear · Kbd hint

### MenuItem
| Figma name | Variants | States |
|------------|----------|--------|
| `MenuItem` | **tone:** `neutral` / `danger` · **leading:** `none` / `icon` / `avatar` · **trailing:** `none` / `kbd` / `chevron` | default · hover · focus · active · disabled |

### Tabs
| Figma name | Variants | States |
|------------|----------|--------|
| `Tabs` | **size:** `sm` / `md` · **orientation:** `horizontal` / `vertical` · **overflow:** `wrap` / `scroll` | default · hover · focus · active · disabled |

- [ ] Tab + TabList + TabPanel set
- [ ] Mobile accordion annotation (Company 360)

### Toast
| Figma name | Variants | States |
|------------|----------|--------|
| `Toast` | **tone:** `neutral` / `success` / `warning` / `danger` / `ai` · **action:** `none` / `undo` | default · dismissible |

- [ ] Stack position (top-right / bottom) note

### Tooltip
| Figma name | Variants | States |
|------------|----------|--------|
| `Tooltip` | **placement:** `top` / `right` / `bottom` / `left` | default · open |

### Dropdown
| Figma name | Variants | States |
|------------|----------|--------|
| `Dropdown` | **size:** `sm` / `md` · **trigger:** `button` / `icon` | closed · open · disabled |

- [ ] Menu surface elevation `elevation/md`

### Select
| Figma name | Variants | States |
|------------|----------|--------|
| `Select` | **size:** `sm` / `md` / `lg` · **multi:** `false` / `true` | default · hover · focus · open · disabled · error |

### Combobox
| Figma name | Variants | States |
|------------|----------|--------|
| `Combobox` | **size:** `sm` / `md` / `lg` · **creatable:** `false` / `true` | default · focus · open · loading · empty · error |

### DatePicker
| Figma name | Variants | States |
|------------|----------|--------|
| `DatePicker` | **mode:** `date` / `range` · **size:** `sm` / `md` | default · focus · open · disabled · error |

- [ ] Calendar panel + range highlight

### FilterChip
| Figma name | Variants | States |
|------------|----------|--------|
| `FilterChip` | **selected:** `false` / `true` · **removable:** `true` / `false` · **tone:** `neutral` / `accent` | default · hover · focus · disabled |

---

## Organisms

### Dialog
| Figma name | Variants | States |
|------------|----------|--------|
| `Dialog` | **size:** `sm` / `md` / `lg` · **tone:** `neutral` / `danger` / `ai` | default · loading |

- [ ] Header / body / footer slots
- [ ] Focus-trap annotation
- [ ] Prefer Sheet over stacked Dialogs (hi-fi rule)
- [ ] `tone=ai` used by Ask AI popup (not a layout region)

### AskAIPopup
| Figma name | Variants | States |
|------------|----------|--------|
| `AskAIPopup` | **size:** `md` (max-width `space/ai-popup`) · **capability:** `chat` / `summary` / `nba` | default · loading · empty · error · Preview · approval pending |

- [ ] **Modal only** — scrim `overlay/scrim` + dialog; never a docked rail or page column
- [ ] Always show **Preview** Badge when flag off
- [ ] Context label · sources / confidence · Human Approval CTA slots
- [ ] Max height `space/ai-popup-max-h` / ~85vh; elevation `elevation/modal`
- [ ] Can be a dedicated component or a published instance of `Dialog` tone=`ai`

### Sheet
| Figma name | Variants | States |
|------------|----------|--------|
| `Sheet` | **side:** `right` / `left` / `bottom` · **size:** `sm` / `md` / `lg` | default · loading |

- [ ] Mobile bottom sheet
- [ ] RTL: side flips
- [ ] Prefer Sheet for approvals/details — **not** for primary Ask AI conversation (use AskAIPopup)

### CommandPalette
| Figma name | Variants | States |
|------------|----------|--------|
| `CommandPalette` | **mode:** `default` / `empty` / `loading` / `error` | open · closed |

- [ ] Search + grouped MenuItems + Kbd
- [ ] Focus trap annotation

### DataGrid
| Figma name | Variants | States |
|------------|----------|--------|
| `DataGrid` | **density:** `compact` / `comfortable` · **selection:** `none` / `single` / `multi` | default · loading · empty · error · permission |

- [ ] Header · row · cell · checkbox · sort · freeze column
- [ ] Bulk action bar
- [ ] Keyboard legend frame (see `engines/data-grid.md`)

### Kanban
| Figma name | Variants | States |
|------------|----------|--------|
| `Kanban` | **columnTone:** `neutral` / `accent` / `danger` / `ai` | default · loading · empty · drag-over |

- [ ] Column · Card · WIP count

### Timeline
| Figma name | Variants | States |
|------------|----------|--------|
| `Timeline` | **density:** `compact` / `comfortable` · **tone:** `neutral` / `ai` | default · loading · empty |

### PageHeader
| Figma name | Variants | States |
|------------|----------|--------|
| `PageHeader` | **density:** `default` / `compact` · **actions:** `0` / `1` / `n` | default · loading |

- [ ] Title (h1) · breadcrumbs · primary/secondary actions · meta

### EmptyState
| Figma name | Variants | States |
|------------|----------|--------|
| `EmptyState` | **tone:** `neutral` / `accent` / `ai` · **cta:** `true` / `false` | default |

### ErrorState
| Figma name | Variants | States |
|------------|----------|--------|
| `ErrorState` | **severity:** `inline` / `page` · **retry:** `true` / `false` | default |

### PermissionState
| Figma name | Variants | States |
|------------|----------|--------|
| `PermissionState` | **level:** `hidden` / `denied` / `read-only` | default |

### NotificationInbox
| Figma name | Variants | States |
|------------|----------|--------|
| `NotificationInbox` | **filter:** `all` / `unread` | default · empty · loading · error |

- [ ] Row · unread dot · mark-all

### WorkspaceSwitcher
| Figma name | Variants | States |
|------------|----------|--------|
| `WorkspaceSwitcher` | **open:** `false` / `true` | default · loading · empty · error |

- [ ] Current org · search · last-used

### AIRail (deprecated as layout)
| Figma name | Variants | States |
|------------|----------|--------|
| ~~`AIRail`~~ | — | — |

- [ ] **Do not build as chrome.** Ask AI is modal (`AskAIPopup`) only — see `ai/ai-experience.md`.
- [ ] If an old rail frame exists, replace with Ask AI popup overlay on Shell.

---

## Shell helpers (build with organisms)

| Figma name | Notes |
|------------|-------|
| `Nav` / `NavItem` | Domain L2; collapsed icon-only |
| `ThemeToggle` | light / dark |
| `UserMenu` | Dropdown + MenuItem |
| `PreviewBadge` | Alias or Badge `tone=ai` labeled “Preview” |

---

## Build order (designers)

1. Atoms → Button, Input, Badge, Spinner  
2. Molecules → FormField, Tabs, Select, FilterChip  
3. Organisms → PageHeader, Dialog, **AskAIPopup**, Sheet, DataGrid, Empty/Error/Permission  
4. Shell → WorkspaceSwitcher, CommandPalette, NotificationInbox (Ask AI = topbar → popup, not rail)  
5. Publish library → consume in Templates frames  

---

## Validation

| Label | Meaning |
|-------|---------|
| **not validated** | Components exist only as this checklist until Figma build + Design QA |
| Production GO | **Not claimed** — see ga-engineering-audit |
