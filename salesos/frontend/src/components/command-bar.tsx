"use client"

import { useState, useEffect, useCallback, type KeyboardEvent } from"react"
import { useCommands, useKeyboard } from"@salesos/hooks"
import { Search } from"lucide-react"
import { cn } from"@salesos/ui"
import { useFocusTrap } from"@/lib/hooks/useFocusTrap"
import { useTranslation } from"@/lib/i18n"
import type { Command } from"@salesos/hooks"

interface CommandBarProps {
 open: boolean
 onClose: () => void
}

export function CommandBar({ open, onClose }: CommandBarProps) {
 const { t } = useTranslation()
 const [query, setQuery] = useState("")
 const [selectedIndex, setSelectedIndex] = useState(0)
 const { commands, execute } = useCommands()
 const trapRef = useFocusTrap<HTMLDivElement>(open)

 const filteredCommands = commands.filter(
 (cmd: Command) =>
 !query || cmd.label.includes(query) || cmd.description?.includes(query) || cmd.category?.includes(query)
 )

 useEffect(() => {
 if (open) {
 setQuery("")
 setSelectedIndex(0)
 }
 }, [open])

 const handleKeyDown = useCallback(
 (e: KeyboardEvent) => {
 if (e.key ==="ArrowDown") {
 e.preventDefault()
 setSelectedIndex((i) => Math.min(i + 1, filteredCommands.length - 1))
 } else if (e.key ==="ArrowUp") {
 e.preventDefault()
 setSelectedIndex((i) => Math.max(i - 1, 0))
 } else if (e.key ==="Enter" && filteredCommands[selectedIndex]) {
 execute(filteredCommands[selectedIndex].id)
 onClose()
 } else if (e.key ==="Escape") {
 onClose()
 }
 },
 [filteredCommands, selectedIndex, execute, onClose]
 )

 if (!open) return null

 const categories = Array.from(new Set(filteredCommands.map((c: Command) => c.category || t("command.default_category"))))

 return (
 <div
 className="fixed inset-0 z-50 flex items-start justify-center pt-[15vh]"
 onClick={onClose}
 role="dialog"
 aria-modal="true"
 aria-label={t("command.title")}
 >
 <div className="fixed inset-0 bg-black/50" aria-hidden="true" />
 <div
 ref={trapRef}
 className="relative w-full max-w-xl rounded-xl border border-[var(--border-default)] bg-[var(--bg-primary)] shadow-2xl"
 onClick={(e) => e.stopPropagation()}
 >
 <div className="flex items-center gap-3 border-b border-[var(--border-default)] px-4">
 <Search className="h-5 w-5 text-[var(--text-disabled)]" aria-hidden="true" />
 <input
 value={query}
 onChange={(e) => {
 setQuery(e.target.value)
 setSelectedIndex(0)
 }}
 onKeyDown={handleKeyDown}
 placeholder={t("command.placeholder")}
 className="h-12 flex-1 bg-transparent text-sm text-[var(--text-primary)] outline-none placeholder:text-[var(--text-disabled)]"
 aria-label={t("command.search_label")}
 aria-autocomplete="list"
 aria-controls="command-list"
 aria-activedescendant={
 filteredCommands[selectedIndex] ? `cmd-${filteredCommands[selectedIndex].id}` : undefined
 }
 />
 <kbd className="rounded border border-[var(--border-hover)] px-1.5 py-0.5 text-[10px] text-[var(--text-muted)]">
 ESC
 </kbd>
 </div>
 <div
 id="command-list"
 role="listbox"
 aria-label={t("a11y.command_list")}
 className="max-h-80 overflow-y-auto p-2"
 >
 <div aria-live="polite" aria-atomic="true" className="sr-only">
 {t("command.count_available", { count: filteredCommands.length })}
 </div>
 {filteredCommands.length === 0 && (
 <p className="px-3 py-8 text-center text-sm text-[var(--text-muted)]">
 {t("command.no_results")}
 </p>
 )}
 {categories.map((category: string) => {
 const catCommands = filteredCommands.filter((c: Command) => (c.category || t("command.default_category")) === category)
 return (
 <div key={category} role="group" aria-label={category}>
 <p className="px-3 py-2 text-[10px] font-medium uppercase tracking-wider text-[var(--text-muted)]">
 {category}
 </p>
 {catCommands.map((cmd: Command, i: number) => {
 const globalIndex = filteredCommands.indexOf(cmd)
 return (
 <button
 key={cmd.id}
 id={`cmd-${cmd.id}`}
 role="option"
 aria-selected={globalIndex === selectedIndex}
 className={cn(
"flex w-full items-center gap-3 rounded-lg px-3 py-2.5 text-right text-sm transition",
 globalIndex === selectedIndex
 ?"bg-[var(--muhide-orange)]/10 text-[var(--muhide-orange)] dark:bg-[var(--muhide-orange)]/20 dark:text-orange-300"
 :"text-[var(--text-secondary)] hover:bg-[var(--bg-secondary)] dark:hover:bg-[var(--bg-secondary)]"
 )}
 onClick={() => {
 execute(cmd.id)
 onClose()
 }}
 onMouseEnter={() => setSelectedIndex(globalIndex)}
 >
 <div className="flex-1 text-right">
 <p>{cmd.label}</p>
 {cmd.description && (
 <p className="text-xs text-[var(--text-muted)]">{cmd.description}</p>
 )}
 </div>
 {cmd.shortcut && (
 <kbd className="rounded border border-[var(--border-hover)] px-1.5 py-0.5 text-[10px]">
 {cmd.shortcut}
 </kbd>
 )}
 </button>
 )
 })}
 </div>
 )
 })}
 </div>
 </div>
 </div>
 )
}
