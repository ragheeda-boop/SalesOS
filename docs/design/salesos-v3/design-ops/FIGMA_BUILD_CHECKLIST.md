# Figma Build Checklist — SalesOS DS v3

One-sitting designer runbook. No Figma API from this repo — do everything in **Figma Desktop / browser**.

Companion files:

| File | Use |
|------|-----|
| [`tokens.figma.json`](./tokens.figma.json) | Variables import source |
| [`figma-library.md`](./figma-library.md) | Library publish detail |
| [`figma-component-inventory.md`](./figma-component-inventory.md) | Component variants / states |
| [`figma-frames-priority.md`](./figma-frames-priority.md) | Frame layout notes |

**Locked rule:** Ask AI is a **modal popup**, not page layout (no docked rail). See [`../ai/ai-experience.md`](../ai/ai-experience.md).

**Validation:** mark steps `[x]` as you go. Status remains **not validated** until Design QA. Do not claim Production GO.

Frame sizes: Desktop `1440×900` · Tablet `768×1024` · Mobile `390×844` (Desktop first).

---

## Phase 0 — Prep (5 min)

- [ ] Open Figma · signed in · fonts available: **Viga**, **IBM Plex Sans**, **IBM Plex Sans Arabic**, **IBM Plex Mono**
- [ ] Clone / download this repo path locally so you can pick `tokens.figma.json` in a plugin
- [ ] Optional: install **Tokens Studio for Figma** or a **Variables Import** plugin
- [ ] Create a Figma branch `feat/ds-v3-bootstrap` (keep `main` clean until Design Review)

---

## Phase 1 — Create the library file

- [ ] **New design file** → rename to `SalesOS DS v3`
- [ ] Create pages (exact names):

  | Page | Purpose |
  |------|---------|
  | `Foundations` | Swatches, type, space/radius rulers |
  | `Components` | Inventory components |
  | `Patterns` | Data Grid + form / empty / error |
  | `Dashboards` | Sales Home widgets |
  | `Templates` | Auth, Shell, objects, Ask AI overlay |
  | `Templates / Auth` | Login (optional sub-page or section) |
  | `Templates / Objects` | Lists + 360s |
  | `Templates / AI` | Ask AI popup overlays |

- [ ] Confirm **Local variables** panel is available (right sidebar)

---

## Phase 2 — Import Variables from `tokens.figma.json`

### Option A — Plugin (preferred)

- [ ] Open plugin → Import / Sync
- [ ] Select `docs/design/salesos-v3/design-ops/tokens.figma.json`
- [ ] Map collections to these **exact** names:
  - `Color/Light` (COLOR)
  - `Color/Dark` (COLOR)
  - `Space` (FLOAT, px)
  - `Radius` (FLOAT, px)
  - `Typography` (STRING families + FLOAT size/weight/line-height)
- [ ] Each collection mode = `Default` (Light/Dark are **separate collections**, not dual modes)
- [ ] Resolve opacity: `surface/glass`, `surface/overlay`, `overlay/scrim` as COLOR + alpha
- [ ] Spot-check brand: `brand/orange` = `#F57C1E` · `text/muted` (Light) = `#8C8374`
- [ ] Spot-check Ask AI sizing: `space/ai-popup` = `512` · `space/ai-popup-max-h` = `640`

### Option B — Manual

- [ ] Create collection `Color/Light` → add every key under `collections["Color/Light"].variables`
- [ ] Create collection `Color/Dark` → same names, dark values (parity required)
- [ ] Create `Space` → `space/1`…`space/16`, `space/sidebar`, `space/ai-popup`, `space/ai-popup-max-h`
- [ ] Create `Radius` → `radius/sm`…`radius/pill`
- [ ] Create `Typography` → families + sizes + weights + line-heights

### After import (both options)

- [ ] Create **Text styles**: Display (Viga) · Title · Subtitle · Body · Meta — bind sizes to Typography variables
- [ ] Create **Effect styles** from `effectStyles` in JSON (include `elevation/modal` for Ask AI)
- [ ] Foundations page: paint color swatches **bound to Variables** (no hard-coded hex on components later)

---

## Phase 3 — Build components from inventory

Follow [`figma-component-inventory.md`](./figma-component-inventory.md). Check off there; summary order:

### 3a Atoms (must ship before frames)

- [ ] `Button` (variant × size × tone; accent = brand orange CTA only)
- [ ] `IconButton`
- [ ] `Input` · `Textarea`
- [ ] `Checkbox` · `Radio` · `Switch`
- [ ] `Badge` (include **Preview** / `tone=ai`)
- [ ] `Avatar` · `Spinner` · `Kbd`

### 3b Molecules

- [ ] `FormField`
- [ ] `SearchInput`
- [ ] `Tabs` · `MenuItem` · `Dropdown` · `Select` · `Combobox`
- [ ] `FilterChip` · `Toast` · `Tooltip` · `DatePicker`

### 3c Organisms

- [ ] `Dialog` (tones: neutral / danger / **ai**)
- [ ] `Sheet`
- [ ] `PageHeader`
- [ ] `DataGrid` (comfortable + compact)
- [ ] `EmptyState` · `ErrorState` · `PermissionState`
- [ ] `CommandPalette` · `NotificationInbox` · `WorkspaceSwitcher`
- [ ] `Timeline` · `Kanban`
- [ ] **`AskAIPopup`** (or `Dialog` tone=`ai` instance named `AskAIPopup`) — modal only; never a rail component

### 3d Shell helpers

- [ ] `Nav` / `NavItem` · `ThemeToggle` · `UserMenu` · `PreviewBadge`

**States on every interactive:** default · hover · focus · active · disabled · loading · error · success (as applicable).

---

## Phase 4 — Priority frames (build in this order)

Details: [`figma-frames-priority.md`](./figma-frames-priority.md). Place under Templates / Patterns as noted.

| # | Frame | Figma names | Done |
|---|--------|-------------|------|
| 1 | **Login** | `Auth / Login / Desktop` · `Auth / Login / Mobile` | [ ] |
| 2 | **Shell** | `Shell / Desktop` · `Shell / Tablet collapsed` · `Shell / Mobile bottom-nav` | [ ] |
| 3 | **Sales Home** | `Dashboard / Sales Home / Desktop` · `… / Mobile` | [ ] |
| 4 | **Company List** | `Objects / Company List / Desktop` | [ ] |
| 5 | **Company 360** | `Objects / Company 360 / Desktop` · `… / Mobile accordion` | [ ] |
| 6 | **Deal 360** | `Objects / Deal 360 / Desktop` (+ optional Pipeline Board) | [ ] |
| 7 | **Data Grid** | `Pattern / Data Grid / Comfortable` · `Compact` · `Keyboard legend` | [ ] |
| 8 | **Ask AI popup** | `AI / Ask AI Popup / Desktop` · `AI / Ask AI Popup / Mobile` | [ ] |

### Frame rules

- [ ] Use **library components + Variables only** (no one-off colors)
- [ ] Shell / product frames: **full-width main** — no reserved AI column
- [ ] Ask AI: draw as **overlay** on Shell (or Sales Home) with `overlay/scrim` + modal `space/ai-popup` wide; include Preview badge
- [ ] Annotate entry: topbar **Ask AI** · `Ctrl+Shift+A` · context label
- [ ] Annotate 18-point screen template where applicable (`screens/_TEMPLATE.md`)

### Ask AI popup acceptance (Phase 4 #8)

- [ ] Modal centered (desktop) / bottom sheet–friendly (mobile) — **not** a sidebar or half-page panel
- [ ] Width ≤ `space/ai-popup` (512) · height ≤ `space/ai-popup-max-h` (640) / ~85vh
- [ ] Header: sparkles · “Ask AI” · **Preview** badge · context line · close
- [ ] Body: honesty copy · disabled textarea (Preview) · sources/confidence slots (empty ok)
- [ ] Footer: Decision Center link · Close · optional Human Approval CTA for side effects
- [ ] Scrim dismiss + Escape noted in prototype / annotation
- [ ] States: default Preview · loading · empty · error · approval pending

---

## Phase 5 — Smoke + publish gate

- [ ] Light + one Dark theme spot-check on Shell + Ask AI
- [ ] Contrast: muted text on paper / ink readable
- [ ] No docked AI rail anywhere in Templates
- [ ] Design Review → DS Approval ([`review-release.md`](./review-release.md))
- [ ] Publish library from approved `main` only ([`figma-library.md`](./figma-library.md) §E)
- [ ] Enable library in product files; swap detached styles

---

## Done for today when

1. File `SalesOS DS v3` exists with pages + Variables imported  
2. Core atoms + Dialog/AskAIPopup + PageHeader + DataGrid exist  
3. All **8 priority frames** drafted (even if polish TBD)  
4. Ask AI proven as **modal overlay**, not layout  

Remaining polish (RBAC matrix, full variant matrices) can continue on `feat/*` without blocking this handoff.
