import { cn } from "@salesos/ui"
import { useState, useEffect, useRef, useCallback } from "react"

interface CommandItem {
  id: string
  label: string
  icon?: React.ReactNode
  description?: string
  shortcut?: string
  group?: string
  disabled?: boolean
  onSelect: () => void
}

interface CommandGroup {
  id: string
  label: string
  items: CommandItem[]
}

interface CommandBarProps {
  open: boolean
  onClose: () => void
  onSearch?: (query: string) => void
  suggestions?: { label: string; onClick: () => void }[]
  recentQueries?: string[]
  placeholder?: string
  children?: React.ReactNode
  groups?: CommandGroup[]
  loading?: boolean
  error?: string | null
  emptyMessage?: string
  className?: string
}

export function CommandBar({
  open,
  onClose,
  onSearch,
  suggestions,
  recentQueries,
  placeholder = "Search commands, pages, or data...",
  children,
  groups,
  loading = false,
  error = null,
  emptyMessage = "No results found.",
  className,
}: CommandBarProps) {
  const [query, setQuery] = useState("")
  const [selectedIndex, setSelectedIndex] = useState(0)
  const [selectedGroupIndex, setSelectedGroupIndex] = useState(0)
  const inputRef = useRef<HTMLInputElement>(null)
  const listRef = useRef<HTMLDivElement>(null)

  const flatItems = groups?.flatMap((g) => g.items) ?? []

  useEffect(() => {
    if (open) {
      setQuery("")
      setSelectedIndex(0)
      setSelectedGroupIndex(0)
      setTimeout(() => inputRef.current?.focus(), 50)
    }
  }, [open])

  useEffect(() => {
    setSelectedIndex(0)
    setSelectedGroupIndex(0)
  }, [query])

  const handleKeyDown = useCallback((e: React.KeyboardEvent) => {
    if (e.key === "Escape") {
      e.preventDefault()
      onClose()
      return
    }

    if (e.key === "ArrowDown") {
      e.preventDefault()
      setSelectedIndex((prev) => Math.min(prev + 1, flatItems.length - 1))
      return
    }

    if (e.key === "ArrowUp") {
      e.preventDefault()
      setSelectedIndex((prev) => Math.max(prev - 1, 0))
      return
    }

    if (e.key === "Enter") {
      e.preventDefault()
      const item = flatItems[selectedIndex]
      if (item && !item.disabled) {
        item.onSelect()
        onClose()
      }
      return
    }
  }, [flatItems, selectedIndex, onClose])

  useEffect(() => {
    if (!open) return
    const handler = (e: KeyboardEvent) => {
      if (e.key === "Escape") {
        onClose()
      }
    }
    window.addEventListener("keydown", handler)
    return () => window.removeEventListener("keydown", handler)
  }, [open, onClose])

  useEffect(() => {
    const selectedEl = listRef.current?.querySelector(`[data-index="${selectedIndex}"]`)
    selectedEl?.scrollIntoView({ block: 'nearest' })
  }, [selectedIndex])

  if (!open) return null

  const hasItems = flatItems.length > 0
  const hasResults = children || hasItems

  const handleInputChange = (value: string) => {
    setQuery(value)
    onSearch?.(value)
  }

  return (
    <div className="fixed inset-0 z-overlay flex items-start justify-center pt-[15vh]" role="dialog" aria-modal="true" aria-label="Command palette">
      <div className="fixed inset-0 bg-black/60 backdrop-blur-sm" onClick={onClose} />

      <div className={cn(
        'relative w-command bg-white rounded-xl shadow-muhide-6 border border-[var(--border-default)] overflow-hidden flex flex-col max-h-[60vh]',
        className
      )}>
        <div className="flex items-center gap-3 px-4 h-14 border-b border-[var(--border-default)]">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="text-[var(--text-muted)] flex-shrink-0" aria-hidden="true">
            <circle cx="11" cy="11" r="8" /><path d="m21 21-4.3-4.3" />
          </svg>
          <input
            ref={inputRef}
            type="text"
            value={query}
            onChange={(e) => handleInputChange(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder={placeholder}
            aria-label="Search commands"
            aria-activedescendant={flatItems[selectedIndex] ? `command-item-${flatItems[selectedIndex].id}` : undefined}
            className="flex-1 bg-transparent border-none outline-none text-sm text-[var(--text-primary)] placeholder:text-[var(--text-muted)]"
          />
          <kbd className="flex-shrink-0 flex items-center gap-0.5 px-1.5 py-0.5 text-[10px] font-medium bg-[var(--bg-secondary)] border border-[var(--border-default)] rounded-sm text-[var(--text-muted)]">
            ESC
          </kbd>
        </div>

        {!query && recentQueries && recentQueries.length > 0 && (
          <div className="px-4 py-3 border-b border-[var(--border-default)]">
            <div className="text-[10px] font-medium text-[var(--text-muted)] uppercase tracking-wider mb-2">Recent</div>
            <div className="flex flex-wrap gap-2">
              {recentQueries.map((q, i) => (
                <button
                  key={i}
                  onClick={() => handleInputChange(q)}
                  className="px-2.5 h-7 text-xs rounded-md bg-[var(--bg-secondary)] text-[var(--text-secondary)] hover:text-[var(--text-primary)] hover:bg-[var(--bg-tertiary)] transition-colors"
                >
                  {q}
                </button>
              ))}
            </div>
          </div>
        )}

        {!query && suggestions && suggestions.length > 0 && (
          <div className="px-4 py-3 border-b border-[var(--border-default)]">
            <div className="text-[10px] font-medium text-[var(--text-muted)] uppercase tracking-wider mb-2">Suggestions</div>
            <div className="flex flex-wrap gap-2">
              {suggestions.map((s, i) => (
                <button
                  key={i}
                  onClick={() => {
                    s.onClick()
                    onClose()
                  }}
                  className="px-2.5 h-7 text-xs rounded-full border border-[var(--border-default)] text-[var(--text-secondary)] hover:text-[var(--text-primary)] hover:border-[var(--border-hover)] transition-colors"
                >
                  {s.label}
                </button>
              ))}
            </div>
          </div>
        )}

        {loading && (
          <div className="flex items-center justify-center py-12" role="status" aria-live="polite">
            <div className="flex items-center gap-2 text-sm text-[var(--text-muted)]">
              <svg className="animate-spin h-4 w-4" viewBox="0 0 24 24" fill="none" aria-hidden="true">
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
              </svg>
              Searching...
            </div>
          </div>
        )}

        {error && (
          <div className="flex items-center gap-2 px-4 py-3 text-sm text-danger-600 bg-danger-50 border-b border-danger-100" role="alert">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="flex-shrink-0" aria-hidden="true">
              <circle cx="12" cy="12" r="10" /><line x1="12" y1="8" x2="12" y2="12" /><line x1="12" y1="16" x2="12.01" y2="16" />
            </svg>
            <span className="flex-1">{error}</span>
          </div>
        )}

        {!loading && !error && hasResults && (
          <div ref={listRef} className="flex-1 overflow-y-auto py-2" role="listbox" aria-live="polite">
            {children}

            {groups?.map((group, gi) => {
              const groupItems = group.items
              if (groupItems.length === 0) return null

              return (
                <div key={group.id}>
                  <div className="px-4 py-1.5">
                    <span className="text-[10px] font-medium text-[var(--text-muted)] uppercase tracking-wider">{group.label}</span>
                  </div>
                  {groupItems.map((item, ii) => {
                    const absoluteIndex = groups
                      .slice(0, gi)
                      .reduce((acc, g) => acc + g.items.length, 0) + ii
                    const isSelected = absoluteIndex === selectedIndex

                    return (
                      <button
                        key={item.id}
                        id={`command-item-${item.id}`}
                        data-index={absoluteIndex}
                        disabled={item.disabled}
                        role="option"
                        aria-selected={isSelected}
                        onClick={() => {
                          if (!item.disabled) {
                            item.onSelect()
                            onClose()
                          }
                        }}
                        onMouseEnter={() => {
                          setSelectedIndex(absoluteIndex)
                          setSelectedGroupIndex(gi)
                        }}
                        className={cn(
                          'flex items-center gap-3 w-full px-4 h-10 text-sm text-left transition-colors',
                          isSelected
                            ? 'bg-[var(--muhide-orange)]/10 text-[var(--text-primary)]'
                            : 'text-[var(--text-secondary)] hover:bg-[var(--bg-secondary)]',
                          item.disabled && 'opacity-40 cursor-not-allowed pointer-events-none',
                        )}
                      >
                        {item.icon && (
                          <span className="flex-shrink-0 w-4 h-4 flex items-center justify-center text-[var(--text-muted)]" aria-hidden="true">
                            {item.icon}
                          </span>
                        )}
                        <span className="flex-1 truncate">{item.label}</span>
                        {item.description && (
                          <span className="hidden sm:block text-xs text-[var(--text-muted)] truncate max-w-[160px]">{item.description}</span>
                        )}
                        {item.shortcut && (
                          <kbd className="flex-shrink-0 px-1.5 py-0.5 text-[10px] font-medium bg-[var(--bg-secondary)] border border-[var(--border-default)] rounded-sm text-[var(--text-muted)]">
                            {item.shortcut}
                          </kbd>
                        )}
                      </button>
                    )
                  })}
                </div>
              )
            })}
          </div>
        )}

        {!loading && !error && !hasResults && (
          <div className="flex flex-col items-center justify-center py-12 text-center" role="status">
            <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" className="text-[var(--text-muted)] mb-3" aria-hidden="true">
              <circle cx="11" cy="11" r="8" /><path d="m21 21-4.3-4.3" /><line x1="8" y1="11" x2="14" y2="11" />
            </svg>
            <p className="text-sm text-[var(--text-muted)]">{emptyMessage}</p>
          </div>
        )}

        {hasItems && (
          <div className="flex items-center gap-4 px-4 h-9 border-t border-[var(--border-default)] text-[10px] text-[var(--text-muted)]">
            <span className="flex items-center gap-1">
              <kbd className="px-1 py-0.5 bg-[var(--bg-secondary)] border border-[var(--border-default)] rounded-sm">&#8593;&#8595;</kbd> Navigate
            </span>
            <span className="flex items-center gap-1">
              <kbd className="px-1 py-0.5 bg-[var(--bg-secondary)] border border-[var(--border-default)] rounded-sm">&#8629;</kbd> Select
            </span>
            <span className="flex items-center gap-1">
              <kbd className="px-1 py-0.5 bg-[var(--bg-secondary)] border border-[var(--border-default)] rounded-sm">ESC</kbd> Close
            </span>
          </div>
        )}
      </div>
    </div>
  )
}
