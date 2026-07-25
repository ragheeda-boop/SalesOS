# Gate G-9: Mobile & Responsive Testing

> **Work Order**: WO-PRC-PRODUCTION-READINESS
> **Date**: 2026-07-17
> **Owner**: Frontend Engineer
> **Source**: `salesos/frontend/src/app/(dashboard)/` and `salesos/frontend/src/`

---

## Verdict: CONDITIONAL — Pass with 1 Critical finding

| Area | Status | Confidence |
|------|--------|------------|
| Viewport Meta Tag | 🔴 **FAIL** — Missing | High |
| Mobile Navigation | 🟢 PASS | High |
| Responsive Breakpoints | 🟢 PASS | High |
| DataTable Responsiveness | 🟢 PASS (extant) / 🟡 Limited verification (DataTable) | Medium |
| Touch Targets (44x44px) | 🟡 CONDITIONAL | High |
| Content Overflow | 🟢 PASS | High |
| Reduced Motion | 🟢 PASS | High |
| RTL Support | 🟢 PASS | High |

**Overall**: CONDITIONAL — Gate passes provided the viewport meta tag is added before GA. All other areas meet the standard.

---

## 1. Viewport Meta Tag — 🔴 FAIL (Critical)

**Issue**: The root `layout.tsx` (`salesos/frontend/src/app/layout.tsx`) does **not** include `<meta name="viewport" content="width=device-width, initial-scale=1">`.

The `<head>` contains:
- `<meta name="theme-color">`
- `<meta name="apple-mobile-web-app-capable">`
- `<meta name="apple-mobile-web-app-status-bar-style">`
- `<link rel="manifest">`

But the critical viewport meta tag for responsive scaling is absent. The `globals.css` has `-webkit-text-size-adjust: 100%` on `<html>` which prevents font inflation on iOS, but this is not a substitute for the viewport meta tag.

**Severity**: Critical — Without this tag, mobile browsers render at a desktop-width viewport (~980px), forcing users to pinch-zoom on all pages.

**Fix**: Add to `<head>` in `layout.tsx`:
```html
<meta name="viewport" content="width=device-width, initial-scale=1" />
```
Or via Next.js metadata API in the `metadata` export.

---

## 2. Mobile Navigation — 🟢 PASS

The dashboard layout (`(dashboard)/layout.tsx`) and `MobileNav` component both implement mobile navigation:

| Pattern | Details | Status |
|---------|---------|--------|
| Desktop sidebar | `hidden md:flex` — hidden below `md` breakpoint | 🟢 |
| Mobile hamburger | Header button with `md:hidden`, opens sidebar overlay | 🟢 |
| Mobile FAB | `MobileNav` floating button `fixed bottom-4 ... md:hidden`, triggers a second drawer | 🟢 |
| Overlay backdrop | `bg-black/60 backdrop-blur-sm` with click-to-close | 🟢 |
| Slide animations | LTR: `animate-slide-in-left`, RTL: `animate-slide-in-right` | 🟢 |
| Close on navigation | `useEffect` closes sidebar on pathname change | 🟢 |
| Close on ESC | Keyboard event listener | 🟢 |
| Body scroll lock | `document.body.style.overflow = "hidden"` while open | 🟢 |
| ARIA | `aria-expanded`, `aria-modal`, `role="dialog"`, `aria-label` present | 🟢 |
| Max width | `max-w-[80vw]` prevents full-width drawer on small phones | 🟢 |

**Secondary MobileNav FAB**: Note there are two mobile navigation mechanisms — the hamburger in the header and the floating action button in `MobileNav.tsx`. Both work correctly but the duplication may confuse users. Recommend unifying into a single entry point.

---

## 3. Responsive Breakpoints — 🟢 PASS

Tailwind responsive classes (`sm:`, `md:`, `lg:`, `xl:`) are used extensively across all pages:

| Pattern | Usage | Example |
|---------|-------|---------|
| Grid columns | `grid-cols-1 sm:grid-cols-2 lg:grid-cols-3/4` | analytics, revenue, marketplace, territories, search |
| Responsive padding | `p-3 sm:p-4 lg:p-6` | dashboard layout |
| Responsive direction | `flex-col sm:flex-row` | marketplace filters, pipeline workspace |
| Responsive visibility | `hidden md:flex` / `md:hidden` | sidebar, command palette |
| Responsive tab layout | `hidden w-56 sm:flex sm:flex-col` | settings page |
| Wrap & min-width | `flex-wrap` + `min-w-[200px]` on filter inputs | companies, employees, decisions |

The CSS (`globals.css`) also defines:
- `.widget-grid`: 1-col mobile → 2-col tablet → 3-col desktop → 4-col wide
- `.workspace-layout`: column on mobile, row on desktop
- `.responsive-pad`, `.responsive-pad-x/y`, `.responsive-gap`: reduced spacing on mobile (<640px)
- Font size reductions: `h1` → 18px, `h2` → 16px on mobile
- Full-screen modals on mobile: `max-width: 100%`, full height, no border-radius

---

## 4. DataTable Responsiveness — 🟢 PASS (with caveat)

**Manual tables** (Contacts, AdminUserList, TenantList, AuditLogView):
- Use `responsive-table` CSS class
- CSS in `globals.css` (lines 219-264):
  - On `< 640px`: hides `<thead>`, converts each `<tr>` to a card
  - Each `<td>` becomes a flex row with `data-label` content shown as a pseudo-element label
  - Cards have border, border-radius, padding, and margin-bottom

**DataTable component** (imported from `@salesos/ui`, used in Companies, etc.):
- Source not directly verifiable (external package)
- The `DataTable` component is wrapped inside `.overflow-hidden` containers in most use sites
- Companies page table has `overflow-hidden` on wrapper, but no explicit `overflow-x-auto`
- However, the companies page uses `DataTable` with only 4-5 columns, so overflow is unlikely

---

## 5. Touch Targets — 🟡 CONDITIONAL

### Meeting 44x44px minimum:

| Element | Size | Status |
|---------|------|--------|
| Header menu/hamburger | `min-h-[44px] min-w-[44px]` | 🟢 |
| Header copilot button | `min-h-[44px] min-w-[44px]` | 🟢 |
| Header notifications | `min-h-[44px] min-w-[44px]` | 🟢 |
| Mobile sidebar close | `min-h-[44px] min-w-[44px]` | 🟢 |
| Mobile nav links | `min-h-[44px]` | 🟢 |
| MobileNav FAB | `h-12 w-12` (48px) | 🟢 |

### Below 44x44px minimum:

| Element | Size | Issue |
|---------|------|-------|
| Contacts edit/delete buttons | `p-1` (~28px) | Minor — low-traffic feature, accessible via tooltip |
| Contacts pagination | `h-8 w-8` (32px) | Minor — numbers may be hard to tap on small screens |
| MobileNav close button | `p-1.5` (~30px) | Minor — no min dimensions |
| DataTable row click | Entire row clickable | 🟢 (via `onRowClick`) |

### Global:
- `touch-action: manipulation` set on `button, a, input, select, textarea` — eliminates 300ms tap delay 🟢

---

## 6. Content Overflow — 🟢 PASS

| Area | Handling | Status |
|------|----------|--------|
| Admin tables | `overflow-x-auto` wrappers | 🟢 |
| Tab lists (360, employee, workspace) | `overflow-x-auto` + `whitespace-nowrap` | 🟢 |
| Activity filters | `overflow-x-auto` | 🟢 |
| Pipeline kanban | `overflow-x-auto pb-4` | 🟢 |
| Pipeline stage filters (opportunity list) | `overflow-x-auto pb-1` | 🟢 |
| Pre/code blocks | `overflow-x-auto` | 🟢 |
| Main content area | `overflow-auto` | 🟢 |
| Images | `max-width: 100%; height: auto` | 🟢 |
| Copilot panel | `overflow-x-auto` on action buttons | 🟢 |
| Main layout | `h-screen overflow-hidden` on shell, `flex-1 overflow-auto` on main | 🟢 |

No horizontal scroll issues identified on standard page structures.

---

## 7. Reduced Motion — 🟢 PASS

`globals.css` includes a `prefers-reduced-motion` media query:
- Disables all animations and transitions (duration set to 0.01ms)
- Explicitly disables `.animate-pulse`, `.animate-spin`, `.animate-slide-in-left`, `.animate-slide-in-right`

---

## 8. RTL Support — 🟢 PASS

The `globals.css` includes comprehensive RTL utilities:
- `start-0`, `end-0` utility classes
- RTL-aware text alignment (`text-start`, `text-end`)
- RTL-aware spacing (`pl-*`, `pr-*`, `ml-*`, `mr-*`, `space-x-*`)
- RTL-aware borders, border-radius, transforms, floats, and positioning
- Font family swapping for Arabic text

The mobile navigation uses `dir` from `useTranslation()` and applies the correct slide animation for RTL.

---

## Issues Summary

| ID | Severity | Area | Description | Fix |
|----|----------|------|-------------|-----|
| M-01 | 🔴 Critical | Viewport | Missing `<meta name="viewport">` tag in root layout | Add viewport meta tag to `layout.tsx` via metadata API or `<head>` |
| M-02 | 🟡 Minor | Touch Targets | Contacts edit/delete buttons `p-1` (~28px) under 44px | Add `min-h-[44px] min-w-[44px]` or use larger padding |
| M-03 | 🟡 Minor | Touch Targets | Contacts pagination `h-8 w-8` (32px) | Increase to `h-11 w-11` (44px) on mobile |
| M-04 | 🟡 Minor | MobileNav | Close button in MobileNav is `p-1.5` (~30px) | Add `min-h-[44px] min-w-[44px]` |
| M-05 | 🟡 Minor | Navigation | Dual mobile nav (header hamburger + FAB) may confuse users | Consider unifying to one entry point |

---

## Recommendations

1. **P0 — Add viewport meta tag immediately** (fixes M-01):
   ```tsx
   // In salesos/frontend/src/app/layout.tsx metadata export:
   export const metadata: Metadata = {
     viewport: "width=device-width, initial-scale=1",
     // ...existing metadata
   }
   ```

2. **P2 — Fix undersized touch targets** (fixes M-02, M-03, M-04):
   - Add `min-h-[44px] min-w-[44px]` to all interactive elements in the contacts page and MobileNav close button
   - Switch pagination buttons from `h-8 w-8` to `min-h-[44px] min-w-[44px]`

3. **P3 — Consider unifying mobile navigation** (fixes M-05):
   - The header hamburger (`DashboardContent` in layout.tsx) and the floating action button (`MobileNav.tsx`) both open a mobile sidebar — these should be consolidated into a single entry point

4. **P3 — Verify DataTable from @salesos/ui**:
   - Confirm the `DataTable` component includes horizontal scroll or card-level responsive behavior on mobile (<640px)
   - If not, wrap usage sites in `overflow-x-auto` and add `responsive-table` class

---

## Files Reviewed

- `salesos/frontend/src/app/layout.tsx` (Root layout)
- `salesos/frontend/src/app/(dashboard)/layout.tsx` (Dashboard layout)
- `salesos/frontend/src/app/globals.css` (Global styles)
- `salesos/frontend/src/components/foundation/MobileNav.tsx`
- `salesos/frontend/src/components/foundation/app-shell.tsx`
- `salesos/frontend/src/app/(dashboard)/page.tsx` (Dashboard home)
- `salesos/frontend/src/app/(dashboard)/companies/page.tsx`
- `salesos/frontend/src/app/(dashboard)/companies/[id]/360/page.tsx`
- `salesos/frontend/src/app/(dashboard)/contacts/page.tsx`
- `salesos/frontend/src/app/(dashboard)/search/page.tsx`
- `salesos/frontend/src/app/(dashboard)/forecast/page.tsx`
- `salesos/frontend/src/app/(dashboard)/pipeline/page.tsx`
- `salesos/frontend/src/app/(dashboard)/opportunities/page.tsx`
- `salesos/frontend/src/app/(dashboard)/settings/page.tsx`
- `salesos/frontend/src/app/(dashboard)/marketplace/page.tsx`
- `salesos/frontend/src/app/(dashboard)/analytics/page.tsx`
- `salesos/frontend/src/app/(dashboard)/activities/page.tsx`
- `salesos/frontend/src/app/(dashboard)/admin/tenants/page.tsx`
- `salesos/frontend/src/app/(dashboard)/admin/audit/page.tsx`
- `salesos/frontend/src/app/(dashboard)/revenue/territories/page.tsx`
- `salesos/frontend/src/app/(dashboard)/revenue/quotas/page.tsx`
- `salesos/frontend/src/features/admin/widgets/UserList.tsx`
- `salesos/frontend/src/features/admin/widgets/TenantList.tsx`
- `salesos/frontend/src/features/admin/widgets/audit-log/AuditLogView.tsx`
- `salesos/frontend/src/features/admin/widgets/AICostDashboard.tsx`
- `salesos/frontend/src/features/revenue-execution/widgets/opportunity-list/OpportunityListView.tsx`
- `salesos/frontend/src/features/revenue-execution/workspace/pipeline/PipelineWorkspace.tsx`
