# Shell — Workspace Chrome

## 1. Purpose
Global frame for all authenticated work: nav, find, notify, switch workspace, Ask AI.

## 2. User Goals
Orient, navigate ≤3 clicks, invoke commands, see alerts, switch tenant safely.

## 3. IA
L1 switcher · L2 domain nav · Topbar (search, CmdK, Ask AI, theme, user) · **AI as modal/popup only** (not a chrome region).

## 4. Layout
Left sidebar (collapsible) + topbar + main outlet. **No permanent right AI rail.** Ask AI opens a dialog over content and does not reserve page layout space.

## 5. Wireframe
Sidebar domains; topbar search; `⌘K`; Ask AI button; theme; avatar; main content. AI dialog centered/modal when invoked (`Ctrl+Shift+A` or `salesos-v3-open-ai` window event).

## 6. Components
WorkspaceSwitcher, Nav, CommandPalette, NotificationInbox, PageHeader, **V3AiPopup** (modal), ThemeToggle, UserMenu.

## 7. Flow
Login → Org select → Shell → Domain → Object. Ask AI anytime from topbar without leaving the page.

## 8–10. Responsive
Mobile: bottom nav domains + hamburger; Ask AI remains a full-screen-friendly dialog. Tablet: collapsed sidebar. Desktop: full. Ultra-wide: **still no docked AI rail** — popup only.

## 11. AI
Global Ask AI opens **popup/modal only** (Preview badge when flag off). Never embed AI as a page tab body, sidebar panel, or half-page insight cards. Event: `salesos-v3-open-ai`.

## 12–15. States
Empty inbox; error toast; skeleton nav; permission-hidden admin domains.

## 16. Perf
Shell hydrate <2s p95 target (instrument later).

## 17. A11y
Landmarks, skip link, focus trap in CmdK and AI dialog, Escape closes dialogs, RTL.

## 18. Future
Multi-product AQLIYA switcher (AuditOS etc.). Optional context label passed into AI popup — still not a layout region.
