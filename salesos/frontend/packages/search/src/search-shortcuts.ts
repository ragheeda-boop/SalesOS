export type SearchShortcutAction =
  | 'open_command_bar'
  | 'close_overlay'
  | 'nav_up'
  | 'nav_down'
  | 'select_result'
  | 'open_preview'
  | 'clear_search'
  | 'focus_search'
  | 'switch_facet'

export interface ShortcutBinding {
  key: string
  ctrl?: boolean
  meta?: boolean
  shift?: boolean
  alt?: boolean
  action: SearchShortcutAction
  handler: () => void
}

export function getDefaultShortcuts(handlers: Record<SearchShortcutAction, () => void>): ShortcutBinding[] {
  return [
    { key: 'k', ctrl: true, action: 'open_command_bar', handler: handlers.open_command_bar },
    { key: 'k', meta: true, action: 'open_command_bar', handler: handlers.open_command_bar },
    { key: 'Escape', action: 'close_overlay', handler: handlers.close_overlay },
    { key: 'ArrowUp', action: 'nav_up', handler: handlers.nav_up },
    { key: 'ArrowDown', action: 'nav_down', handler: handlers.nav_down },
    { key: 'Enter', action: 'select_result', handler: handlers.select_result },
    { key: 'Enter', ctrl: true, action: 'open_preview', handler: handlers.open_preview },
    { key: 'Escape', action: 'clear_search', handler: handlers.clear_search },
    { key: '/', action: 'focus_search', handler: handlers.focus_search },
    { key: 'Tab', action: 'switch_facet', handler: handlers.switch_facet },
    { key: 'Tab', shift: true, action: 'switch_facet', handler: handlers.switch_facet },
  ]
}

export function matchShortcut(e: KeyboardEvent, bindings: ShortcutBinding[]): ShortcutBinding | undefined {
  return bindings.find((b) => {
    if (b.key !== e.key) return false
    if (b.ctrl && !e.ctrlKey) return false
    if (b.meta && !e.metaKey) return false
    if (b.shift && !e.shiftKey) return false
    if (b.alt && !e.altKey) return false
    if (!b.ctrl && !b.meta && !b.shift && !b.alt) {
      if (e.ctrlKey || e.metaKey || e.altKey) return false
    }
    return true
  })
}
