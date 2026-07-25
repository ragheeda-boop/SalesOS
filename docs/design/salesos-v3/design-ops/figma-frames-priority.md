# Figma Frames Priority — SalesOS DS v3

Build these frames first in file **SalesOS DS v3** → pages **Templates** / **Patterns**.  
Aligns with [`delivery/hifi-spec.md`](../delivery/hifi-spec.md) and [`ai/ai-experience.md`](../ai/ai-experience.md). Annotate each frame with the 18-point screen template where applicable.

Use Variables from `tokens.figma.json`. Prefer library components from `figma-component-inventory.md`.  
Step-by-step build: [`FIGMA_BUILD_CHECKLIST.md`](./FIGMA_BUILD_CHECKLIST.md).  
**Do not claim Production GO** from frame completion alone.

Frame sizes: Desktop `1440×900` · Tablet `768×1024` · Mobile `390×844` (build Desktop first unless noted).

**Locked layout rule:** Ask AI is a **modal popup**, never a docked rail, half-page panel, or tab body that consumes chrome.

---

## 1. Login

| | |
|--|--|
| **Page** | Templates / Auth |
| **Frame names** | `Auth / Login / Desktop` · `Auth / Login / Mobile` |
| **Sources** | [`screens/auth/README.md`](../screens/auth/README.md) |

### Layout
- **Desktop:** split — left brand panel (ink / paper atmosphere, logo as hero signal) · right form column (~420px content width, vertically centered).
- **Mobile:** stacked form; brand mark above fields; no side panel.
- Form stack: email `Input` → password `Input` → primary `Button` (tone=`accent`) → SSO / links (Forgot · Invite).
- Spacing: form gaps `space/4`; section gap `space/6`; outer padding `space/8`.

### States to draw
- Default · validation error · loading submit · lockout message  
- Optional: Org Select as sibling frame `Auth / Org Select / Desktop` (list + search + Continue)

### Components
`Input`, `FormField`, `Button`, `Badge` (optional SSO), brand logo mark.

---

## 2. Shell

| | |
|--|--|
| **Page** | Templates / Shell |
| **Frame names** | `Shell / Desktop` · `Shell / Tablet collapsed` · `Shell / Mobile bottom-nav` |
| **Sources** | [`screens/shell/workspace-shell.md`](../screens/shell/workspace-shell.md) |

### Layout
- **Desktop:** left sidebar `space/sidebar` (256) · topbar · **full-width** main outlet. **No right AI rail.**
- Topbar: SearchInput · `⌘K` Kbd · **Ask AI** button · NotificationInbox bell · ThemeToggle · UserMenu / Avatar.
- Sidebar: WorkspaceSwitcher (L1) · domain Nav (L2) · collapse control.
- Landmarks: skip-link annotation · `main` region.
- Ask AI opens as overlay only — draw closed Shell here; open state is priority frame **#8 Ask AI popup**.

### States
- Empty inbox · skeleton nav · permission-hidden admin domains · Ask AI closed (default)

### Components
`WorkspaceSwitcher`, `Nav`/`NavItem`, `CommandPalette`, `NotificationInbox`, `PageHeader` (in outlet), Ask AI topbar trigger, `ThemeToggle`, `UserMenu`.

---

## 3. Sales Home

| | |
|--|--|
| **Page** | Templates / Dashboards |
| **Frame names** | `Dashboard / Sales Home / Desktop` · `Dashboard / Sales Home / Mobile` |
| **Sources** | [`screens/dashboards/README.md`](../screens/dashboards/README.md) |

### Layout
- Inside Shell. Content: `PageHeader` (“Sales”) + filter bar + **12-col widget grid**.
- Widgets (priority): Pipeline · Forecast · My Work · NBA (Preview chip only — not a layout AI pane) · Activity Feed · KPI row.
- Desktop: full 12-col · Tablet: 2-col · Mobile: stacked widgets.
- Do not embed conversation AI as a home region; deep AI stays in Ask AI popup.

### States
Per-widget empty / error / loading / permission.

### Components
`PageHeader`, FilterChip, widget cards (Pattern), `Badge` Preview, `EmptyState` / `ErrorState`.

---

## 4. Company List

| | |
|--|--|
| **Page** | Templates / Objects |
| **Frame names** | `Objects / Company List / Desktop` |
| **Sources** | [`screens/objects/README.md`](../screens/objects/README.md) |

### Layout
- Shell + `PageHeader` (title, Create CTA, bulk actions) · filter row · full-bleed `DataGrid` (comfortable density default).
- Toolbar: SearchInput · FilterChips · view preset · Export.
- Row click → Company 360; CmdK create annotation.

### States
Loading skeleton · empty · error · multi-select bulk bar · permission denied.

### Components
`PageHeader`, `SearchInput`, `FilterChip`, `DataGrid`, `Button`, `Dropdown`, `PermissionState`.

---

## 5. Company 360

| | |
|--|--|
| **Page** | Templates / Objects |
| **Frame names** | `Objects / Company 360 / Desktop` · `Objects / Company 360 / Mobile accordion` |
| **Sources** | [`screens/objects/README.md`](../screens/objects/README.md) |

### Layout
- **Header band:** identity (name = h1) · health score chip · primary actions (include Ask AI with context) · meta.
- **Tabs:** Overview · Contacts · Relationships · Timeline · Financial · Contracts · Documents · Opportunities · Risks · Tasks · Activities · Intelligence · Graph · Health Score.  
  **Do not** make “AI Summary” a primary tab body that owns the page — use Ask AI popup with context label instead (Preview).
- **Body:** tab panel only (full width). No permanent right AI column.
- Desktop: header / tabs / body. Mobile: tabs → accordion; Ask AI remains modal.

### States
Lazy tab loading · empty tab · permission on Financial · Ask AI closed with context ready.

### Components
`PageHeader`, `Tabs`, `DataGrid`, `Timeline`, `Badge`, `Sheet`, Ask AI trigger.

---

## 6. Deal 360

| | |
|--|--|
| **Page** | Templates / Objects |
| **Frame names** | `Objects / Deal 360 / Desktop` · `CRM / Pipeline Board / Desktop` (sibling) |
| **Sources** | objects README · CRM section |

### Layout
- Header: deal name · amount · stage · owner · primary actions (Ask AI with deal context).
- Stage stepper or stage `Badge` + probability.
- Two-column body: left activity/`Timeline` · right key fields + optional **NBA Preview** card (`ai/surface`) — card is a recommendation chip, **not** a chat rail.
- Side-effecting NBA → Human Approval `Dialog`; conversation → Ask AI popup.
- Sibling **Pipeline:** `Kanban` columns by stage; card → Deal 360.

### States
Won / Lost tones · loading · NBA Preview + Human Approval CTA · empty activity.

### Components
`PageHeader`, `Badge`, `Tabs`, `Timeline`, `Kanban`, NBA card (`ai/surface`), `Dialog` (approval), Ask AI trigger.

---

## 7. Data Grid

| | |
|--|--|
| **Page** | Patterns |
| **Frame names** | `Pattern / Data Grid / Comfortable` · `Pattern / Data Grid / Compact` · `Pattern / Data Grid / Keyboard legend` |
| **Sources** | [`engines/data-grid.md`](../engines/data-grid.md) |

### Layout
- Standalone pattern (still inside Shell chrome optional).
- Show: sort · filter · freeze first column · multi-select · bulk bar · density toggle · saved views · empty/error overlays.
- Keyboard legend frame: Arrows · Space · Enter · Shift+Arrow · `/` · `e`.

### States
default · loading (>100 row virtualization note) · empty · error · permission.

### Components
`DataGrid` (+ cell/header variants), `FilterChip`, `Dropdown`, `Checkbox`, `EmptyState`, `ErrorState`, `PermissionState`, `Kbd`.

---

## 8. Ask AI popup (modal — not layout)

| | |
|--|--|
| **Page** | Templates / AI |
| **Frame names** | `AI / Ask AI Popup / Desktop` · `AI / Ask AI Popup / Mobile` · optional `AI / Human Approval / Desktop` |
| **Sources** | [`ai/ai-experience.md`](../ai/ai-experience.md) · code `V3AiPopup` · AI_HONESTY |

### Layout (critical)
- Draw **on top of** Shell or Sales Home: full-bleed `overlay/scrim` + centered dialog.
- Dialog width ≤ `space/ai-popup` (512) · max height `space/ai-popup-max-h` (640) / ~85vh · radius `radius/lg` · elevation `elevation/modal`.
- **Desktop:** centered modal. **Mobile:** bottom-aligned / full-width friendly dialog (still modal, not a nav region).
- Does **not** resize the page grid, sidebar, or main outlet.
- Entry annotations: topbar Ask AI · `Ctrl+Shift+A` · `openV3AiPopup({ contextLabel })`.

### Structure
- **Header:** sparkles · “Ask AI” · persistent **Preview** Badge · context label · close
- **Body:** honesty copy · message `Textarea` (disabled in Preview) · sources / confidence slots
- **Footer:** Decision Center link · Close · (optional) Human Approval CTA for side effects
- Distinct `ai/*` tokens only where helpful; dialog chrome can use `bg/primary` + `border/default` like `V3AiPopup`

### States
default Preview · loading · empty · error · Preview-limited · approval pending · sources expanded · context-labeled (e.g. Company / Deal / Sales home)

### Components
`AskAIPopup` / `Dialog` tone=`ai`, `Badge` Preview, `Button`, `Textarea`, `EmptyState`, `Spinner`, feedback controls, optional approval `Dialog`/`Sheet`.

### Anti-patterns (do not draw)
- Permanent right rail · half-page chat column · AI as primary tab body · silent write affordances in Preview

---

## 9. RBAC (next after priority eight)

| | |
|--|--|
| **Page** | Templates / Admin |
| **Frame names** | `Admin / RBAC Permission Matrix / Desktop` |
| **Sources** | [`screens/modules/README.md`](../screens/modules/README.md) Admin |

### Layout
- `PageHeader`: Roles · Permission Matrix.
- Matrix: rows = permissions / resources · columns = roles · cells = allow / deny / inherit (Checkbox or icon states).
- Sticky first column + sticky header; compact density.
- Side panel or Sheet: role detail · audit hint.
- Dangerous changes: confirm `Dialog` tone=`danger`.

### States
loading · read-only viewer · save loading · error · permission denied (non-admin).

### Components
`PageHeader`, `DataGrid` (matrix mode), `Checkbox`, `Tabs`, `Dialog`, `Badge`, `PermissionState`.

---

## Suggested Figma page map

| Figma page | Frames |
|------------|--------|
| Foundations | Color swatches, type specimens, space/radius rulers |
| Components | Inventory from `figma-component-inventory.md` |
| Patterns | Data Grid, forms, empty/error/permission |
| Templates | Login → Shell → lists/360s → **Ask AI popup overlay** → RBAC |
| Dashboards | Sales Home + future cockpit variants |
| Templates / AI | Ask AI popup + Human Approval |

## Branching

`main` = approved library · `feat/*` = WIP frames. Publish from `main` only after Design Review.

## Validation status

**not validated** in Figma until designers mark frames built and Design QA signs off. Engineering audit remains **production no-go**.
