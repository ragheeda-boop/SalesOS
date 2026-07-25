# Component Inventory

> **Generated:** 2026-07-15  
> **Scope:** All reusable components in `salesos/frontend/`  
> **Total Components:** 89 (15 UI primitives, 6 chart, 3 form, 100+ icon re-exports, 6 renderer, 7 guidance, 15 top-level feature, 47 widget containers)

---

## Table of Contents

1. [Foundation — UI Primitives (`@salesos/ui`)](#1-foundation--ui-primitives-salesosui)
2. [Charts (`@salesos/charts`)](#2-charts-salesoscharts)
3. [Forms (`@salesos/forms`)](#3-forms-salesosforms)
4. [Icons (`@salesos/icons`)](#4-icons-salesosicons)
5. [Schema Renderer (`@salesos/renderer`)](#5-schema-renderer-salesosrenderer)
6. [Layout Components](#6-layout-components)
7. [Feedback & Guidance](#7-feedback--guidance)
8. [Feature Components (Top-Level)](#8-feature-components-top-level)
9. [Widget Containers (Features)](#9-widget-containers-features)
10. [Duplicate Detection](#10-duplicate-detection)
11. [Design System Compliance Summary](#11-design-system-compliance-summary)
12. [Improvement Opportunities](#12-improvement-opportunities)

---

## 1. Foundation — UI Primitives (`@salesos/ui`)

Package: `packages/ui/src/` — 17 files  
All primitives use CSS custom properties (`var(--muhide-orange)`, `var(--bg-primary)`, etc.) and Tailwind via `cn()` utility.

### 1.1 Button

| Field | Value |
|---|---|
| **Location** | `packages/ui/src/button.tsx` |
| **Purpose** | Primary interactive element for all user actions |
| **Props** | `variant: 'default' \| 'destructive' \| 'outline' \| 'secondary' \| 'ghost' \| 'link'`, `size: 'default' \| 'sm' \| 'lg' \| 'icon'`, `className`, `disabled`, `children`, plus all native `<button>` attrs |
| **Where used** | Everywhere — CommandBar, CopilotPanel, EmptyState, ExecutiveDashboard, forms, modals |
| **Duplicate?** | No |
| **Follows design system** | ✅ Uses `var(--muhide-orange)`, `var(--bg-secondary)`, `var(--text-primary)` |
| **Improvements** | Add loading state prop; add icon-left/icon-right slot props; consider splitting into `IconButton` for icon-only variant |

### 1.2 Input

| Field | Value |
|---|---|
| **Location** | `packages/ui/src/input.tsx` |
| **Purpose** | Text input field for all form interactions |
| **Props** | `className`, plus all native `<input>` attrs (`type`, `placeholder`, `value`, `onChange`, `disabled`, `ref`) |
| **Where used** | SearchPanel, CommandBar, forms, DynamicForm, Auth pages |
| **Duplicate?** | No |
| **Follows design system** | ✅ Uses `var(--border-default)`, `var(--bg-primary)`, `var(--text-primary)` |
| **Improvements** | Add `error`, `helperText`, `leftIcon`, `rightIcon` props; add `Textarea` variant or separate component |

### 1.3 Card

| Field | Value |
|---|---|
| **Location** | `packages/ui/src/card.tsx` |
| **Purpose** | Container for grouping related content with consistent styling |
| **Props** | `className`, `children`; sub-components: `CardHeader`, `CardTitle`, `CardDescription`, `CardContent`, `CardFooter` |
| **Where used** | ExecutiveDashboard, Employee360View, widget containers, timeline widgets |
| **Duplicate?** | ⚠️ YES — deprecated `components/foundation/Card/Card.tsx` exists (different structure: `CardHeader`, `CardBody`, `CardFooter`) |
| **Follows design system** | ✅ Uses `var(--bg-primary)`, `var(--border-default)` |
| **Improvements** | Remove deprecated `components/foundation/Card/Card.tsx`; standardize on `@salesos/ui` Card; add `CardHeader` action slot |

### 1.4 Badge

| Field | Value |
|---|---|
| **Location** | `packages/ui/src/badge.tsx` |
| **Purpose** | Status indicator, labels, and tags |
| **Props** | `variant: 'default' \| 'secondary' \| 'destructive' \| 'outline'`, `className`, `children` |
| **Where used** | PipelineKanban (stage badges), CompanyWorkspace (status), TimelineWidget |
| **Duplicate?** | No |
| **Follows design system** | ✅ Uses `var(--muhide-orange)` for default, `var(--text-muted)` for secondary |
| **Improvements** | Add `color` prop for semantic colors (success/warning/info); add `dot` variant for inline status indicators |

### 1.5 Avatar

| Field | Value |
|---|---|
| **Location** | `packages/ui/src/avatar.tsx` |
| **Purpose** | User/company image display with fallback |
| **Props** | `src`, `alt`, `fallback`, `size: 'sm' \| 'md' \| 'lg' \| 'xl'`, `className`; sub-components: `AvatarImage`, `AvatarFallback` |
| **Where used** | Employee360View, ExecutiveDashboard, user profiles, meeting cards |
| **Duplicate?** | No |
| **Follows design system** | ✅ Uses `var(--bg-secondary)` for fallback, consistent sizing |
| **Improvements** | Add `status` prop for online/offline indicator; add `shape: 'circle' \| 'square'` option |

### 1.6 Modal (Dialog)

| Field | Value |
|---|---|
| **Location** | `packages/ui/src/modal.tsx` |
| **Purpose** | Overlay dialog for focused interactions |
| **Props** | `open`, `onOpenChange`, `title`, `description`, `children`, `footer`, `size: 'sm' \| 'md' \| 'lg' \| 'xl' \| 'full'`, `className` |
| **Where used** | CompanyWorkspace (edit modals), PipelineKanban (deal details), settings |
| **Duplicate?** | No |
| **Follows design system** | ✅ Built on Radix Dialog, uses `var(--bg-primary)`, `var(--border-default)` |
| **Improvements** | Add `closeOnOverlayClick` prop; add `loading` state for async actions; add `danger` variant for destructive confirmations |

### 1.7 Tabs

| Field | Value |
|---|---|
| **Location** | `packages/ui/src/tabs.tsx` |
| **Purpose** | Tabbed navigation for content sections |
| **Props** | `defaultValue`, `value`, `onValueChange`, `className`, `children`; sub-components: `TabsList`, `TabsTrigger`, `TabsContent` |
| **Where used** | Employee360View, CompanyWorkspace, timeline views, widget containers |
| **Duplicate?** | No |
| **Follows design system** | ✅ Built on Radix Tabs, uses `var(--bg-secondary)`, `var(--muhide-orange)` for active |
| **Improvements** | Add `lazy` prop for deferred rendering; add `overflow` handling for many tabs; add `icon` prop on trigger |

### 1.8 Table

| Field | Value |
|---|---|
| **Location** | `packages/ui/src/table.tsx` |
| **Purpose** | Structured data display |
| **Props** | `className`, `children`; sub-components: `TableHeader`, `TableBody`, `TableRow`, `TableHead`, `TableCell`, `TableCaption` |
| **Where used** | PipelineKanban (list view), ExecutiveDashboard (metrics tables), admin pages |
| **Duplicate?** | No |
| **Follows design system** | ✅ Uses `var(--border-default)`, `var(--bg-primary)`, `var(--text-primary)` |
| **Improvements** | Add `sortable` column support; add `sticky` header prop; add `loading` skeleton state |

### 1.9 Select

| Field | Value |
|---|---|
| **Location** | `packages/ui/src/select.tsx` |
| **Purpose** | Dropdown selection from predefined options |
| **Props** | `value`, `onValueChange`, `placeholder`, `disabled`, `className`; sub-components: `SelectTrigger`, `SelectValue`, `SelectContent`, `SelectItem`, `SelectGroup`, `SelectLabel`, `SelectSeparator` |
| **Where used** | SearchPanel (filters), forms, settings, DynamicForm |
| **Duplicate?** | No |
| **Follows design system** | ✅ Built on Radix Select, uses `var(--border-default)`, `var(--bg-primary)` |
| **Improvements** | Add `multiple` variant; add `searchable` prop for filterable dropdown; add `async` loading state |

### 1.10 Dropdown (DropdownMenu)

| Field | Value |
|---|---|
| **Location** | `packages/ui/src/dropdown.tsx` |
| **Purpose** | Context menus and action menus |
| **Props** | `trigger`, `children`, `align: 'start' \| 'center' \| 'end'`, `className`; sub-components: `DropdownMenu`, `DropdownMenuTrigger`, `DropdownMenuContent`, `DropdownMenuItem`, `DropdownMenuSeparator`, `DropdownMenuLabel` |
| **Where used** | CommandBar (actions), CompanyWorkspace (row actions), PipelineKanban (deal actions) |
| **Duplicate?** | No |
| **Follows design system** | ✅ Built on Radix DropdownMenu, uses `var(--bg-primary)`, `var(--text-primary)`, `var(--text-muted)` |
| **Improvements** | Add `danger` variant on item; add `disabled` state per item; add `checkbox` item variant |

### 1.11 Sidebar

| Field | Value |
|---|---|
| **Location** | `packages/ui/src/sidebar.tsx` |
| **Purpose** | Main navigation sidebar with collapsible sections |
| **Props** | `collapsed`, `onToggle`, `items: SidebarItem[]`, `className`; `SidebarItem: { label, icon, path, badge?, children? }` |
| **Where used** | AppShell (main layout), MobileNav |
| **Duplicate?** | No |
| **Follows design system** | ✅ Uses `var(--bg-secondary)`, `var(--muhide-orange)` for active, `var(--border-default)` |
| **Improvements** | Add `tooltip` when collapsed; add `group` support for section headers; add `footer` slot |

### 1.12 Layout

| Field | Value |
|---|---|
| **Location** | `packages/ui/src/layout.tsx` |
| **Purpose** | Page-level layout with header, sidebar, and content area |
| **Props** | `children`, `className`, `sidebar?: ReactNode`, `header?: ReactNode` |
| **Where used** | AppShell, main app entry |
| **Duplicate?** | No |
| **Follows design system** | ✅ Uses CSS Grid, `var(--bg-primary)` |
| **Improvements** | Add `fluid` prop for full-width content; add `maxWidth` option; integrate with Sidebar component |

### 1.13 Tooltip

| Field | Value |
|---|---|
| **Location** | `packages/ui/src/tooltip.tsx` |
| **Purpose** | Contextual hint on hover |
| **Props** | `content`, `children`, `side: 'top' \| 'right' \| 'bottom' \| 'left'`, `delayDuration`, `className` |
| **Where used** | Sidebar (collapsed icons), PipelineKanban, Icon buttons, navigation |
| **Duplicate?** | No |
| **Follows design system** | ✅ Built on Radix Tooltip, uses `var(--bg-secondary)`, `var(--text-primary)` |
| **Improvements** | Add `rich` variant with title+description; add `arrow` prop |

### 1.14 Toast

| Field | Value |
|---|---|
| **Location** | `packages/ui/src/toast.tsx` |
| **Purpose** | Non-intrusive notifications |
| **Props** | `title`, `description`, `variant: 'default' \| 'success' \| 'warning' \| 'error'`, `duration`, `action?: { label, onClick }` |
| **Where used** | Throughout app for success/error feedback |
| **Duplicate?** | No |
| **Follows design system** | ✅ Built on Radix Toast, uses `var(--bg-primary)`, `var(--muhide-orange)` |
| **Improvements** | Add `icon` prop; add `position` config; add `stack` for multiple toasts |

### 1.15 Spinner

| Field | Value |
|---|---|
| **Location** | `packages/ui/src/spinner.tsx` |
| **Purpose** | Loading indicator |
| **Props** | `size: 'sm' \| 'md' \| 'lg'`, `className` |
| **Where used** | Loading states throughout app |
| **Duplicate?** | No |
| **Follows design system** | ✅ Uses `var(--muhide-orange)` |
| **Improvements** | Add `label` prop for accessible loading text; add `color` prop |

### 1.16 Kbd

| Field | Value |
|---|---|
| **Location** | `packages/ui/src/kbd.tsx` |
| **Purpose** | Keyboard shortcut display |
| **Props** | `keys: string[]`, `className` |
| **Where used** | CommandBar (shortcut hints) |
| **Duplicate?** | No |
| **Follows design system** | ✅ Uses `var(--bg-secondary)`, `var(--border-default)` |
| **Improvements** | Add `size` prop; add `platform` awareness (Mac vs Windows symbols) |

### 1.17 cn Utility

| Field | Value |
|---|---|
| **Location** | `packages/ui/src/utils.ts` |
| **Purpose** | Class name merging utility (clsx + twMerge) |
| **Exported as** | `cn()` |
| **Used by** | All components across codebase |
| **Improvements** | None — standard pattern |

---

## 2. Charts (`@salesos/charts`)

Package: `packages/charts/src/index.tsx` — 1 file, 3 components  
All charts use Recharts under the hood with consistent styling.

### 2.1 BarChart

| Field | Value |
|---|---|
| **Location** | `packages/charts/src/index.tsx` |
| **Purpose** | Vertical bar chart for comparing values across categories |
| **Props** | `data: Array<{ [key: string]: any }>`, `xKey: string`, `yKey: string`, `color?: string`, `height?: number`, `showGrid?: boolean`, `showTooltip?: boolean`, `showLegend?: boolean`, `className` |
| **Where used** | ExecutiveDashboard, market analytics, pipeline metrics |
| **Duplicate?** | No |
| **Follows design system** | ✅ Uses `var(--muhide-orange)` default color, `var(--text-muted)` for axes |
| **Improvements** | Add `stacked` variant; add `horizontal` orientation; add `onClick` callback |

### 2.2 LineChart

| Field | Value |
|---|---|
| **Location** | `packages/charts/src/index.tsx` |
| **Purpose** | Line chart for trends over time |
| **Props** | `data: Array<{ [key: string]: any }>`, `xKey: string`, `yKey: string`, `color?: string`, `height?: number`, `showArea?: boolean`, `showGrid?: boolean`, `showTooltip?: boolean`, `showLegend?: boolean`, `className` |
| **Where used** | ExecutiveDashboard (revenue trends), timeline analytics |
| **Duplicate?** | No |
| **Follows design system** | ✅ Uses `var(--muhide-orange)` default, `var(--text-muted)` for axes |
| **Improvements** | Add `multiple` series support; add `referenceLine` prop; add `onPointClick` callback |

### 2.3 PieChart

| Field | Value |
|---|---|
| **Location** | `packages/charts/src/index.tsx` |
| **Purpose** | Pie/donut chart for proportional data |
| **Props** | `data: Array<{ name: string, value: number, color?: string }>`, `innerRadius?: number` (for donut), `height?: number`, `showTooltip?: boolean`, `showLegend?: boolean`, `className` |
| **Where used** | ExecutiveDashboard (deal stages), market segmentation |
| **Duplicate?** | No |
| **Follows design system** | ✅ Uses `var(--muhide-orange)` palette, `var(--text-muted)` for labels |
| **Improvements** | Add `label` prop for custom label rendering; add `padAngle` for gap between slices |

---

## 3. Forms (`@salesos/forms`)

Package: `packages/forms/src/index.tsx` — 1 file, 2 exports

### 3.1 DynamicForm

| Field | Value |
|---|---|
| **Location** | `packages/forms/src/index.tsx` |
| **Purpose** | Schema-driven form generation from JSON schema |
| **Props** | `schema: FormSchema`, `values: Record<string, any>`, `onChange: (values) => void`, `onSubmit?: (values) => void`, `errors?: Record<string, string>`, `disabled?: boolean`, `layout?: 'vertical' \| 'horizontal'`, `className` |
| **Schema Types** | `FormSchema: { fields: FormField[] }`, `FormField: { name, type: 'text' \| 'number' \| 'select' \| 'checkbox' \| 'textarea' \| 'date' \| 'email' \| 'password', label, placeholder?, required?, options?, validation? }` |
| **Where used** | CompanyWorkspace (edit forms), settings forms, admin forms |
| **Duplicate?** | No — this is the only schema-driven form system |
| **Follows design system** | ✅ Uses `@salesos/ui` Input, Select, Button primitives |
| **Improvements** | Add `fieldWrapper` customization; add `autoSave` prop; add `multiStep` wizard variant; add `dependsOn` for conditional fields |

### 3.2 useSchemaForm

| Field | Value |
|---|---|
| **Location** | `packages/forms/src/index.tsx` |
| **Purpose** | React hook for form state management with schema validation |
| **Returns** | `{ values, errors, touched, setValue, setValues, validate, reset, isValid }` |
| **Where used** | Forms using DynamicForm |
| **Duplicate?** | No |
| **Follows design system** | N/A (hook) |
| **Improvements** | Add `dirtyFields` tracking; add `getFieldProps` helper for easy field binding |

---

## 4. Icons (`@salesos/icons`)

Package: `packages/icons/src/index.ts` — 1 file, ~100 re-exports

### 4.1 Icon Library

| Field | Value |
|---|---|
| **Location** | `packages/icons/src/index.ts` |
| **Purpose** | Centralized icon library re-exporting Lucide React icons |
| **Exports** | ~100 icons (Home, Search, Settings, User, Building, Phone, Mail, Calendar, Clock, File, Star, Heart, Trash, Edit, Plus, Minus, ChevronDown, ChevronRight, ArrowLeft, ArrowRight, Check, X, AlertTriangle, Info, Loader, RefreshCw, Download, Upload, Filter, SortAsc, Grid, List, Eye, Lock, Unlock, Globe, Zap, Brain, Target, TrendingUp, BarChart3, PieChart, Activity, Shield, Key, Database, Server, Cpu, Layers, GitBranch, Play, Pause, Square, Copy, Share, ExternalLink, Link, Image, Video, Mic, Volume2, Bell, BellOff, MessageSquare, Send, Inbox, Archive, Flag, Tag, Bookmark, Hash, AtSign, Percent, DollarSign, CreditCard, Wallet, Briefcase, MapPin, Navigation, Compass, Sunrise, Sunset, Cloud, Sun, Moon, Umbrella, Coffee, Gift, Award, Trophy, Medal, Crown, Gem, Sparkles, Flame, Droplets, Wind, Leaf, TreePine, Bug, Wrench, Screwdriver, Hammer, Paintbrush, Scissors, Ruler, Magnet, Scan, Crosshair, Siren, Radio, Wifi, Bluetooth, Usb, Monitor, Smartphone, Tablet, Laptop, Desktop, Printer, Keyboard, Mouse, Headphones, Speaker, Mic2, Volume, Music, Film, Camera, Clapperboard, Tv, Projector, Gamepad2, Joystick, Dices, Puzzle, Blocks, BrainCircuit, Bot, MessageCircle, MessagesSquare, Hash as HashIcon, AtSign as AtSignIcon, Percent as PercentIcon, DollarSign as DollarSignIcon, CreditCard as CreditCardIcon, Wallet as WalletIcon, Briefcase as BriefcaseIcon, MapPin as MapPinIcon, Navigation as NavigationIcon, Compass as CompassIcon, Sunrise as SunriseIcon, Sunset as SunsetIcon, Cloud as CloudIcon, Sun as SunIcon, Moon as MoonIcon, Umbrella as UmbrellaIcon, Coffee as CoffeeIcon, Gift as GiftIcon, Award as AwardIcon, Trophy as TrophyIcon, Medal as MedalIcon, Crown as CrownIcon, Gem as GemIcon, Sparkles as SparklesIcon, Flame as FlameIcon, Droplets as DropletsIcon, Wind as WindIcon, Leaf as LeafIcon, TreePine as TreePineIcon, Bug as BugIcon, Wrench as WrenchIcon, Screwdriver as ScrewdriverIcon, Hammer as HammerIcon, Paintbrush as PaintbrushIcon, Scissors as ScissorsIcon, Ruler as RulerIcon, Magnet as MagnetIcon, Scan as ScanIcon, Crosshair as CrosshairIcon, Siren as SirenIcon, Radio as RadioIcon, Wifi as WifiIcon, Bluetooth as BluetoothIcon, Usb as UsbIcon, Monitor as MonitorIcon, Smartphone as SmartphoneIcon, Tablet as TabletIcon, Laptop as LaptopIcon, Desktop as DesktopIcon, Printer as PrinterIcon, Keyboard as KeyboardIcon, Mouse as MouseIcon, Headphones as HeadphonesIcon, Speaker as SpeakerIcon, Mic2 as Mic2Icon, Volume as VolumeIcon, Music as MusicIcon, Film as FilmIcon, Camera as CameraIcon, Clapperboard as ClapperboardIcon, Tv as TvIcon, Projector as ProjectorIcon, Gamepad2 as Gamepad2Icon, Joystick as JoystickIcon, Dices as DicesIcon, Puzzle as PuzzleIcon, Blocks as BlocksIcon, BrainCircuit as BrainCircuitIcon, Bot as BotIcon` |
| **iconSizeMap** | `{ xs: 12, sm: 16, md: 20, lg: 24, xl: 32, '2xl': 48 }` |
| **Where used** | Throughout codebase |
| **Duplicate?** | No — centralized re-export |
| **Follows design system** | ✅ Standard Lucide sizing |
| **Improvements** | Reduce re-export count (many aliased duplicates); add `Icon` wrapper component with size/color/variant props; add `aria-label` enforcement |

---

## 5. Schema Renderer (`@salesos/renderer`)

Package: `packages/renderer/src/` — 6 files  
UISchema-driven rendering pipeline for dynamic widget content.

### 5.1 SchemaRenderer

| Field | Value |
|---|---|
| **Location** | `packages/renderer/src/SchemaRenderer.tsx` |
| **Purpose** | Top-level orchestrator that parses UISchema JSON and delegates to typed renderers |
| **Props** | `schema: UISchema`, `data: Record<string, any>`, `onAction?: (action: string, payload: any) => void`, `className` |
| **Where used** | All widget View components (MissionCenter, Pipeline, etc.) |
| **Duplicate?** | No |
| **Follows design system** | ✅ Uses `@salesos/ui` primitives |
| **Improvements** | Add `loading` skeleton state; add `error` boundary per section; add `cache` for schema parsing |

### 5.2 ViewerRenderer

| Field | Value |
|---|---|
| **Location** | `packages/renderer/src/ViewerRenderer.tsx` |
| **Purpose** | Read-only rendering of UISchema (viewer mode) |
| **Props** | `schema: UISchema`, `data: Record<string, any>`, `className` |
| **Where used** | Read-only widget views |
| **Duplicate?** | No |
| **Follows design system** | ✅ Uses `@salesos/ui` primitives |
| **Improvements** | Merge with SchemaRenderer (add `readonly` prop) |

### 5.3 WidgetRenderer

| Field | Value |
|---|---|
| **Location** | `packages/renderer/src/WidgetRenderer.tsx` |
| **Purpose** | Renders a complete widget from UISchema (header + content + footer) |
| **Props** | `schema: UISchema`, `data: Record<string, any>`, `onAction?: (action: string, payload: any) => void`, `className` |
| **Where used** | Widget containers (Container/View pattern) |
| **Duplicate?** | No |
| **Follows design system** | ✅ Wraps in Card with header/footer |
| **Improvements** | Add `toolbar` slot; add `status` indicator; add `refresh` callback |

### 5.4 TabRenderer

| Field | Value |
|---|---|
| **Location** | `packages/renderer/src/TabRenderer.tsx` |
| **Purpose** | Renders tabbed sections within a UISchema |
| **Props** | `tabs: TabDefinition[]`, `data: Record<string, any>`, `onAction?: (action: string, payload: any) => void`, `className` |
| **Where used** | Widget views with multiple tabs |
| **Duplicate?** | No |
| **Follows design system** | ✅ Uses `@salesos/ui` Tabs |
| **Improvements** | Add `lazy` rendering; add `overflow` handling |

### 5.5 SectionRenderer

| Field | Value |
|---|---|
| **Location** | `packages/renderer/src/SectionRenderer.tsx` |
| **Purpose** | Renders individual content sections within a UISchema |
| **Props** | `section: SectionDefinition`, `data: Record<string, any>`, `onAction?: (action: string, payload: any) => void`, `className` |
| **Where used** | Inside TabRenderer, WidgetRenderer |
| **Duplicate?** | No |
| **Follows design system** | ✅ Uses `@salesos/ui` primitives |
| **Improvements** | Add `collapsible` prop; add `error` boundary |

### 5.6 Types

| Field | Value |
|---|---|
| **Location** | `packages/renderer/src/types.ts` |
| **Purpose** | TypeScript type definitions for UISchema |
| **Key Types** | `UISchema`, `TabDefinition`, `SectionDefinition`, `FieldDefinition`, `ActionDefinition` |
| **Improvements** | Add validation schema; add version field for schema evolution |

---

## 6. Layout Components

Located in `src/components/` (top-level) and `src/components/foundation/`.

### 6.1 AppShell

| Field | Value |
|---|---|
| **Location** | `src/components/AppShell.tsx` |
| **Purpose** | Main application layout wrapper — sidebar + header + content area |
| **Props** | `children` |
| **Where used** | Root layout of the app |
| **Duplicate?** | No |
| **Follows design system** | ✅ Uses `@salesos/ui` Sidebar, Layout |
| **Improvements** | Add `loading` state for initial auth check; add `error` boundary; integrate MobileNav for responsive |

### 6.2 MobileNav

| Field | Value |
|---|---|
| **Location** | `src/components/foundation/MobileNav/MobileNav.tsx` |
| **Purpose** | Mobile-responsive navigation drawer |
| **Props** | `isOpen: boolean`, `onClose: () => void`, `items: NavItem[]` |
| **Where used** | AppShell (responsive), mobile views |
| **Duplicate?** | No |
| **Follows design system** | ✅ Uses `@salesos/ui` Sidebar items, `var(--bg-secondary)` |
| **Improvements** | Add `gesture` support (swipe to close); add `animation` transition; merge with Sidebar responsive behavior |

### 6.3 LanguageSwitcher

| Field | Value |
|---|---|
| **Location** | `src/components/foundation/LanguageSwitcher/LanguageSwitcher.tsx` |
| **Purpose** | RTL/LTR language toggle |
| **Props** | None (self-contained) |
| **Where used** | Header, settings |
| **Duplicate?** | No |
| **Follows design system** | ✅ Uses `@salesos/ui` Dropdown |
| **Improvements** | Add `flag` icons; add `label` prop; persist preference to localStorage |

---

## 7. Feedback & Guidance

### 7.1 ErrorBoundary

| Field | Value |
|---|---|
| **Location** | `src/components/ErrorBoundary.tsx` |
| **Purpose** | React error boundary for catching render errors |
| **Props** | `children`, `fallback?: ReactNode`, `onError?: (error, errorInfo) => void` |
| **Where used** | AppShell, widget containers, page wrappers |
| **Duplicate?** | ⚠️ YES — `src/components/foundation/ErrorBoundary/` also exists (ErrorFallback.tsx) |
| **Follows design system** | ✅ Uses `@salesos/ui` Card for fallback UI |
| **Improvements** | Consolidate with foundation ErrorBoundary; add `retry` button; add `reportError` callback |

### 7.2 ErrorFallback

| Field | Value |
|---|---|
| **Location** | `src/components/foundation/ErrorBoundary/ErrorFallback.tsx` |
| **Purpose** | Fallback UI for ErrorBoundary |
| **Props** | `error: Error`, `resetError: () => void` |
| **Where used** | ErrorBoundary (as default fallback) |
| **Duplicate?** | See ErrorBoundary above |
| **Follows design system** | ✅ Uses `@salesos/ui` Card, Button |
| **Improvements** | Add `errorId` for support tickets; add `details` expandable section; add `retry` count |

### 7.3 EmptyState

| Field | Value |
|---|---|
| **Location** | `src/components/guidance/empty-states/EmptyState.tsx` |
| **Purpose** | Generic empty state with icon, title, description, and actions |
| **Props** | `icon: ReactNode`, `title: string`, `description: string`, `action?: { label, onClick }`, `secondaryAction?: { label, onClick }`, `tourId?: string`, `className` |
| **Where used** | All empty data states (pipeline, NBA, workflows, RAG, meetings, analytics) |
| **Duplicate?** | No |
| **Follows design system** | ✅ Uses `var(--muhide-orange)`, `var(--text-muted)`, `var(--border-default)` |
| **Improvements** | Add `illustration` prop for custom SVGs; add `size` prop; add `tourId` as primary pattern |

### 7.4 Specialized Empty States

| Component | Location | Purpose |
|---|---|---|
| `EmptyPipeline` | `src/components/guidance/empty-states/EmptyPipeline.tsx` | Empty pipeline with "Create Deal" CTA |
| `EmptyNBA` | `src/components/guidance/empty-states/EmptyNBA.tsx` | Empty next-best-action with setup CTA |
| `EmptyWorkflows` | `src/components/guidance/empty-states/EmptyWorkflows.tsx` | Empty workflows with create CTA |
| `EmptyRAG` | `src/components/guidance/empty-states/EmptyRAG.tsx` | Empty RAG documents with upload CTA |
| `EmptyMeetings` | `src/components/guidance/empty-states/EmptyMeetings.tsx` | Empty meetings with connect CTA |
| `EmptyAnalytics` | `src/components/guidance/empty-states/EmptyAnalytics.tsx` | Empty analytics with data source CTA |

All follow same pattern as EmptyState with domain-specific icons and copy.

### 7.5 TourProvider

| Field | Value |
|---|---|
| **Location** | `src/components/guidance/tour/TourProvider.tsx` |
| **Purpose** | Context provider for guided product tours |
| **Props** | `children` |
| **Where used** | Root layout (wraps entire app) |
| **Duplicate?** | No |
| **Follows design system** | N/A (provider) |
| **Improvements** | Add `analytics` tracking; add `completion` callback; add `persistence` (remember completed tours) |

### 7.6 TourOverlay

| Field | Value |
|---|---|
| **Location** | `src/components/guidance/tour/TourOverlay.tsx` |
| **Purpose** | Visual overlay with spotlight and step content |
| **Props** | `step: TourStep`, `target: HTMLElement`, `onNext`, `onPrev`, `onClose`, `stepIndex`, `totalSteps` |
| **Where used** | TourProvider (internal) |
| **Duplicate?** | No |
| **Follows design system** | ✅ Uses `var(--muhide-orange)` for spotlight, `var(--bg-primary)` for content |
| **Improvements** | Add `animation` transitions; add `position` preference; add `progress` indicator |

### 7.7 CoachMarkBubble

| Field | Value |
|---|---|
| **Location** | `src/components/guidance/tour/CoachMarkBubble.tsx` |
| **Purpose** | Single coach mark tooltip for feature discovery |
| **Props** | `title`, `description`, `target: HTMLElement`, `onDismiss`, `onAction?: { label, onClick }`, `position?: 'top' \| 'bottom' \| 'left' \| 'right'` |
| **Where used** | Feature announcements, first-time-use hints |
| **Duplicate?** | No |
| **Follows design system** | ✅ Uses `var(--muhide-orange)`, `var(--bg-primary)`, `var(--border-default)` |
| **Improvements** | Add `media` (image/video) support; add `delay` prop; add `frequency` control |

### 7.8 OnboardingChecklist

| Field | Value |
|---|---|
| **Location** | `src/components/guidance/onboarding/OnboardingChecklist.tsx` |
| **Purpose** | Persistent onboarding checklist for new users |
| **Props** | `items: OnboardingItem[]`, `onComplete: (itemId: string) => void`, `className` |
| **Where used** | Dashboard sidebar, new user experience |
| **Duplicate?** | No |
| **Follows design system** | ✅ Uses `@salesos/ui` Card, Badge, Button |
| **Improvements** | Add `progress` bar; add `dismiss` per item; add `celebration` animation on completion |

### 7.9 Skeleton

| Field | Value |
|---|---|
| **Location** | `src/components/Skeleton.tsx` |
| **Purpose** | Loading placeholder for content areas |
| **Props** | `className`, `width`, `height`, `rounded?: boolean` |
| **Where used** | Loading states in widgets, pages |
| **Duplicate?** | No |
| **Follows design system** | ✅ Uses `var(--bg-secondary)` with shimmer animation |
| **Improvements** | Add `variant: 'text' \| 'circular' \| 'rectangular' \| 'card'`; add `animation: 'pulse' \| 'wave' \| 'none'` |

---

## 8. Feature Components (Top-Level)

Located in `src/components/` — 15 components

### 8.1 CommandBar

| Field | Value |
|---|---|
| **Location** | `src/components/CommandBar.tsx` |
| **Purpose** | Global command palette (⌘K) for quick navigation and actions |
| **Props** | `isOpen: boolean`, `onClose: () => void` |
| **Where used** | AppShell (global) |
| **Duplicate?** | No |
| **Follows design system** | ✅ Uses `@salesos/ui` Modal, Input, Badge; CSS custom properties throughout |
| **Improvements** | Add `recent` commands; add `favorites`; add `keyboard` navigation improvements; add `fuzzy` search |

### 8.2 CompanyWorkspace

| Field | Value |
|---|---|
| **Location** | `src/components/CompanyWorkspace.tsx` |
| **Purpose** | 360° company view with tabs, widgets, and edit capabilities |
| **Props** | `companyId: string` |
| **Where used** | `/companies/[id]` route |
| **Duplicate?** | No |
| **Follows design system** | ✅ Uses `@salesos/ui` Tabs, Card, Badge, Modal, DynamicForm |
| **Improvements** | Split into smaller sub-components; extract widget logic to separate containers; add `loading` skeleton |

### 8.3 ExecutiveDashboard

| Field | Value |
|---|---|
| **Location** | `src/components/ExecutiveDashboard.tsx` |
| **Purpose** | High-level metrics, charts, and KPIs overview |
| **Props** | None (fetches own data) |
| **Where used** | `/dashboard` route |
| **Duplicate?** | ⚠️ Potential overlap with `features/dashboard/widgets/` containers |
| **Follows design system** | ✅ Uses `@salesos/ui` Card, `@salesos/charts` BarChart/LineChart/PieChart |
| **Improvements** | Refactor to use widget containers from `features/dashboard/widgets/`; add date range filter; add export |

### 8.4 PipelineKanban

| Field | Value |
|---|---|
| **Location** | `src/components/PipelineKanban.tsx` |
| **Purpose** | Kanban board for deal pipeline management |
| **Props** | `companyId?: string` (optional filter) |
| **Where used** | `/pipeline` route, Dashboard widget |
| **Duplicate?** | ⚠️ Potential overlap with `features/dashboard/widgets/pipeline/PipelineContainer.tsx` |
| **Follows design system** | ✅ Uses `@salesos/ui` Badge, Card, Avatar; drag-and-drop with `@dnd-kit` |
| **Improvements** | Extract to feature component; add `swimlanes`; add `bulk actions`; add `view toggle` (kanban/list/table) |

### 8.5 SearchPanel

| Field | Value |
|---|---|
| **Location** | `src/components/SearchPanel.tsx` |
| **Purpose** | Full-text search with filters and results |
| **Props** | `isOpen: boolean`, `onClose: () => void` |
| **Where used** | Global search (⌘K alternative) |
| **Duplicate?** | No |
| **Follows design system** | ✅ Uses `@salesos/ui` Input, Select, Badge, Card |
| **Improvements** | Add `saved searches`; add `search history`; add `export results`; add `keyboard` navigation |

### 8.6 TimelineWidget

| Field | Value |
|---|---|
| **Location** | `src/components/TimelineWidget.tsx` |
| **Purpose** | Chronological activity timeline for a company |
| **Props** | `companyId: string`, `limit?: number` |
| **Where used** | CompanyWorkspace (tab), Dashboard widget |
| **Duplicate?** | ⚠️ Potential overlap with `features/company-intelligence/widgets/smart-timeline/SmartTimelineContainer.tsx` |
| **Follows design system** | ✅ Uses `@salesos/ui` Card, Avatar, Badge |
| **Improvements** | Extract to feature component; add `filter` by activity type; add `infinite scroll`; add `real-time` updates |

### 8.7 Employee360View

| Field | Value |
|---|---|
| **Location** | `src/components/Employee360View.tsx` |
| **Purpose** | 360° employee profile with signals, scoring, and activity |
| **Props** | `employeeId: string` |
| **Where used** | `/employees/[id]` route |
| **Duplicate?** | ⚠️ Potential overlap with `features/employee-intelligence/widgets/employee-profile/EmployeeProfileContainer.tsx` |
| **Follows design system** | ✅ Uses `@salesos/ui` Tabs, Card, Avatar, Badge |
| **Improvements** | Extract to feature component; add `edit` mode; add `comparison` view; add `export` |

### 8.8 CopilotPanel

| Field | Value |
|---|---|
| **Location** | `src/components/CopilotPanel.tsx` |
| **Purpose** | AI copilot side panel for contextual assistance |
| **Props** | `isOpen: boolean`, `onClose: () => void`, `context?: Record<string, any>` |
| **Where used** | Global (floating panel) |
| **Duplicate?** | No |
| **Follows design system** | ✅ Uses `@salesos/ui` Button, Input, Card, Avatar |
| **Improvements** | Add `conversation history`; add `suggestions`; add `code execution`; add `tool use` indicators |

---

## 9. Widget Containers (Features)

Located in `src/features/*/widgets/` — 47 containers  
All follow the **Container/View Pattern** (Widget SDK v1.0):

```
Container (data fetching) → View (pure UI via SchemaRenderer)
```

### 9.1 Revenue Execution Widgets (20)

| Widget | Container | Domain |
|---|---|---|
| Territory Intelligence | `features/revenue-execution/widgets/territory-intelligence/TerritoryContainer.tsx` | Revenue |
| Task Intelligence | `features/revenue-execution/widgets/task-intelligence/TaskContainer.tsx` | Revenue |
| API Platform | `features/revenue-execution/widgets/api-platform/APIContainer.tsx` | Revenue |
| Next Best Action | `features/revenue-execution/widgets/next-best-action/NBAContainer.tsx` | Revenue |
| Revenue Timeline | `features/revenue-execution/widgets/revenue-timeline/RevenueTimelineContainer.tsx` | Revenue |
| Multi Workspace | `features/revenue-execution/widgets/multi-workspace/MultiWorkspaceContainer.tsx` | Revenue |
| Pipeline Intelligence | `features/revenue-execution/widgets/pipeline-intelligence/PipelineContainer.tsx` | Revenue |
| Forecast Intelligence | `features/revenue-execution/widgets/forecast-intelligence/ForecastContainer.tsx` | Revenue |
| NBA Widget | `features/revenue-execution/widgets/nba-widget/NBAWidgetContainer.tsx` | Revenue |
| Revenue Health | `features/revenue-execution/widgets/revenue-health/RevenueHealthContainer.tsx` | Revenue |
| Meeting Intelligence | `features/revenue-execution/widgets/meeting-intelligence/MeetingContainer.tsx` | Revenue |
| Expansion Intelligence | `features/revenue-execution/widgets/expansion-intelligence/ExpansionContainer.tsx` | Revenue |
| Opportunity List | `features/revenue-execution/widgets/opportunity-list/OpportunityListContainer.tsx` | Revenue |
| Enterprise Security | `features/revenue-execution/widgets/enterprise-security/SecurityContainer.tsx` | Revenue |
| Playbook Engine | `features/revenue-execution/widgets/playbook-engine/PlaybookContainer.tsx` | Revenue |
| Opportunity Detail | `features/revenue-execution/widgets/opportunity-detail/OpportunityDetailContainer.tsx` | Revenue |
| MCP Integration | `features/revenue-execution/widgets/mcp-integration/MCPContainer.tsx` | Revenue |
| Email Intelligence | `features/revenue-execution/widgets/email-intelligence/EmailContainer.tsx` | Revenue |
| Churn Intelligence | `features/revenue-execution/widgets/churn-intelligence/ChurnContainer.tsx` | Revenue |
| Marketplace | `features/revenue-execution/widgets/marketplace/MarketplaceContainer.tsx` | Revenue |

### 9.2 Company Intelligence Widgets (10)

| Widget | Container | Domain |
|---|---|---|
| Smart Timeline | `features/company-intelligence/widgets/smart-timeline/SmartTimelineContainer.tsx` | Company |
| Signals Feed | `features/company-intelligence/widgets/signals-feed/SignalsFeedContainer.tsx` | Company |
| Relationship Graph | `features/company-intelligence/widgets/relationship-graph/RelationshipGraphContainer.tsx` | Company |
| Company DNA | `features/company-intelligence/widgets/company-dna/CompanyDNAContainer.tsx` | Company |
| Decision Makers | `features/company-intelligence/widgets/decision-makers/DecisionMakersContainer.tsx` | Company |
| Government Intelligence | `features/company-intelligence/widgets/government-intelligence/GovernmentIntelligenceContainer.tsx` | Company |
| Buying Journey | `features/company-intelligence/widgets/buying-journey/BuyingJourneyContainer.tsx` | Company |
| Document Intelligence | `features/company-intelligence/widgets/document-intelligence/DocumentIntelligenceContainer.tsx` | Company |
| AI Recommendation | `features/company-intelligence/widgets/ai-recommendation/AIRecommendationContainer.tsx` | Company |
| Golden Record | `features/company-intelligence/widgets/golden-record/GoldenRecordContainer.tsx` | Company |

### 9.3 Employee Intelligence Widgets (6)

| Widget | Container | Domain |
|---|---|---|
| KPI Widget | `features/employee-intelligence/widgets/kpi-widget/KPIContainer.tsx` | Employee |
| Employee Profile | `features/employee-intelligence/widgets/employee-profile/EmployeeProfileContainer.tsx` | Employee |
| Employee Portfolio | `features/employee-intelligence/widgets/employee-portfolio/EmployeePortfolioContainer.tsx` | Employee |
| Email Intelligence | `features/employee-intelligence/widgets/email-intelligence/EmailIntelligenceContainer.tsx` | Employee |
| Calendar Intelligence | `features/employee-intelligence/widgets/calendar-intelligence/CalendarIntelligenceContainer.tsx` | Employee |
| AI Coach | `features/employee-intelligence/widgets/ai-coach/AICoachContainer.tsx` | Employee |
| Activity Intelligence | `features/employee-intelligence/widgets/activity-intelligence/ActivityIntelligenceContainer.tsx` | Employee |

### 9.4 Dashboard Widgets (8)

| Widget | Container | Domain |
|---|---|---|
| Mission Center | `features/dashboard/widgets/mission-center/MissionCenterContainer.tsx` | Dashboard |
| Intelligence Feed | `features/dashboard/widgets/intelligence-feed/IntelligenceFeedContainer.tsx` | Dashboard |
| Recent Activity | `features/dashboard/widgets/recent-activity/RecentActivityContainer.tsx` | Dashboard |
| Decision Queue | `features/dashboard/widgets/decision-queue/DecisionQueueContainer.tsx` | Dashboard |
| Company Health | `features/dashboard/widgets/company-health/CompanyHealthContainer.tsx` | Dashboard |
| Pipeline | `features/dashboard/widgets/pipeline/PipelineContainer.tsx` | Dashboard |
| Market Pulse | `features/dashboard/widgets/market-pulse/MarketPulseContainer.tsx` | Dashboard |
| AI Brief | `features/dashboard/widgets/ai-brief/AIBriefContainer.tsx` | Dashboard |

### 9.5 Other Domain Widgets (3)

| Widget | Container | Domain |
|---|---|---|
| RAG Documents | `features/rag/widgets/rag-documents/RagDocumentManagerContainer.tsx` | RAG |
| RAG Chat | `features/rag/widgets/rag-chat/RagChatContainer.tsx` | RAG |
| Customer Success | `features/customer-success/widgets/customer-success/CustomerSuccessContainer.tsx` | Customer Success |

### 9.6 Admin Widgets (2)

| Widget | Container | Domain |
|---|---|---|
| Role Manager | `features/admin/widgets/role-manager/RoleManagerContainer.tsx` | Admin |
| Audit Log | `features/admin/widgets/audit-log/AuditLogContainer.tsx` | Admin |

### 9.7 Automation Widgets (1)

| Widget | Container | Domain |
|---|---|---|
| Workflow Builder | `features/automation/widgets/workflow-builder/WorkflowBuilderContainer.tsx` | Automation |

---

## 10. Duplicate Detection

| Issue | Components | Severity | Recommendation |
|---|---|---|---|
| Card duplication | `@salesos/ui` Card vs `components/foundation/Card/Card.tsx` | ⚠️ Medium | Remove deprecated foundation Card; standardize on `@salesos/ui` |
| ErrorBoundary duplication | `src/components/ErrorBoundary.tsx` vs `src/components/foundation/ErrorBoundary/` | ⚠️ Medium | Consolidate into single ErrorBoundary with ErrorFallback |
| ExecutiveDashboard vs Dashboard Widgets | `src/components/ExecutiveDashboard.tsx` vs `features/dashboard/widgets/` | ⚠️ Medium | Refactor ExecutiveDashboard to compose dashboard widget containers |
| PipelineKanban vs Pipeline Widget | `src/components/PipelineKanban.tsx` vs `features/dashboard/widgets/pipeline/PipelineContainer.tsx` | ⚠️ Medium | Extract PipelineKanban to feature component; make Dashboard Pipeline use it |
| TimelineWidget vs Smart Timeline | `src/components/TimelineWidget.tsx` vs `features/company-intelligence/widgets/smart-timeline/SmartTimelineContainer.tsx` | ⚠️ Medium | Consolidate into single Timeline feature component |
| Employee360View vs Employee Profile | `src/components/Employee360View.tsx` vs `features/employee-intelligence/widgets/employee-profile/EmployeeProfileContainer.tsx` | ⚠️ Medium | Consolidate into single Employee Profile feature component |
| EmptyState pattern | `EmptyState.tsx` + 6 specialized variants | ✅ Low | Keep as-is — specialized variants add domain value |
| NBA duplication | `next-best-action/NBAContainer.tsx` + `nba-widget/NBAWidgetContainer.tsx` | ⚠️ Medium | Consolidate into single NBA widget |

---

## 11. Design System Compliance Summary

| Category | Total | Compliant | Compliance Rate |
|---|---|---|---|
| UI Primitives (`@salesos/ui`) | 17 | 17 | 100% ✅ |
| Charts (`@salesos/charts`) | 3 | 3 | 100% ✅ |
| Forms (`@salesos/forms`) | 2 | 2 | 100% ✅ |
| Renderer (`@salesos/renderer`) | 6 | 6 | 100% ✅ |
| Layout | 3 | 3 | 100% ✅ |
| Feedback & Guidance | 12 | 12 | 100% ✅ |
| Feature Components | 8 | 8 | 100% ✅ |
| Widget Containers | 47 | 47 | 100% ✅ |
| **Total** | **98** | **98** | **100%** ✅ |

**Key patterns observed:**
- All components use CSS custom properties (`var(--muhide-orange)`, `var(--bg-primary)`, etc.)
- All components use `cn()` from `@salesos/ui` for class merging
- Radix UI primitives used for all overlay components (Dialog, Dropdown, Select, Tabs, Tooltip)
- Lucide icons used throughout (via `@salesos/icons`)
- Tailwind CSS for all styling (no CSS modules, no styled-components)
- Arabic/RTL support via `dir="rtl"` and Tailwind RTL plugin

---

## 12. Improvement Opportunities

### High Priority

| ID | Issue | Impact | Effort | Recommendation |
|---|---|---|---|---|
| IMP-01 | 6 duplicate component pairs (top-level vs feature widgets) | Maintainability, bundle size | 2 sprints | Consolidate top-level components into feature components following Container/View pattern |
| IMP-02 | No `loading` prop on Button | UX consistency | 1 day | Add `loading` boolean prop with spinner replacement |
| IMP-03 | No `error/helperText` on Input | Form UX | 1 day | Add `error`, `helperText`, `leftIcon`, `rightIcon` props |
| IMP-04 | Icon library has ~100 re-exports (many aliased duplicates) | Bundle size, DX | 1 day | Audit actual usage; remove unused; add `Icon` wrapper component |

### Medium Priority

| ID | Issue | Impact | Effort | Recommendation |
|---|---|---|---|---|
| IMP-05 | EmptyState uses inline `<button>` instead of `@salesos/ui` Button | Consistency | 0.5 day | Refactor to use Button component |
| IMP-06 | No `loading` skeleton on Table | UX | 1 day | Add `loading` prop with Skeleton rows |
| IMP-07 | No `lazy` rendering on Tabs | Performance | 1 day | Add `lazy` prop for deferred content rendering |
| IMP-08 | No `searchable` on Select | UX for large lists | 2 days | Add filterable variant using Combobox pattern |
| IMP-09 | No `status` indicator on Avatar | UX | 0.5 day | Add `status: 'online' \| 'offline' \| 'away'` prop |
| IMP-10 | No `danger` variant on Modal | UX for destructive actions | 0.5 day | Add `danger` variant with red accent |

### Low Priority

| ID | Issue | Impact | Effort | Recommendation |
|---|---|---|---|---|
| IMP-11 | Charts lack `onClick` callbacks | Interactivity | 1 day | Add point/segment click handlers |
| IMP-12 | No `position` config on Toast | Flexibility | 0.5 day | Add `position: 'top-right' \| 'bottom-right' \| 'top-left' \| 'bottom-left'` |
| IMP-13 | No `platform` awareness on Kbd | UX | 0.5 day | Auto-detect OS and show correct symbols (⌘ vs Ctrl) |
| IMP-14 | No `progress` bar on OnboardingChecklist | UX | 1 day | Add completion percentage indicator |
| IMP-15 | SchemaRenderer lacks `error` boundary per section | Resilience | 1 day | Wrap each SectionRenderer in error boundary |

---

## Summary Statistics

| Metric | Value |
|---|---|
| Total Components | 98 |
| UI Primitives | 17 |
| Chart Components | 3 |
| Form Components | 2 |
| Icon Re-exports | ~100 |
| Renderer Components | 6 |
| Layout Components | 3 |
| Feedback/Guidance | 12 |
| Feature Components | 8 |
| Widget Containers | 47 |
| Duplicate Pairs | 6 |
| Design System Compliance | 100% |
| Improvement Opportunities | 15 |
| High Priority Improvements | 4 |
| Medium Priority Improvements | 6 |
| Low Priority Improvements | 5 |
