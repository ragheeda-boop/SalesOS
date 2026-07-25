# Component Library Spec

Atomic Design + variants + tokens + a11y + responsive + motion + states.

## Atoms

Button, IconButton, Input, Textarea, Checkbox, Radio, Switch, Badge, Avatar, Spinner, Kbd.

## Molecules

FormField, SearchInput, MenuItem, Tabs, Toast, Tooltip, Dropdown, Select, Combobox, DatePicker, FilterChip.

## Organisms

Dialog, Sheet, CommandPalette, DataGrid, Kanban, Timeline, PageHeader, EmptyState, ErrorState, PermissionState, NotificationInbox, WorkspaceSwitcher, AIRail (Preview).

## Variant system

`variant` + `size` + `tone` (neutral/accent/danger/ai). No one-off colors in pages.

## States

default · hover · focus · active · disabled · loading · error · success.

## Rules

- Pages compose organisms; no raw HTML form controls in product surfaces.
- Every interactive icon has accessible name.
- AI components always support Preview badge.
