"use client"

import { useState, useEffect, useRef, useCallback, type KeyboardEvent } from "react"
import { useCommands, useKeyboard } from "@salesos/hooks"
import { Search } from "lucide-react"
import { cn } from "@salesos/ui"
import type { Command } from "@salesos/hooks"

interface CommandBarProps {
  open: boolean
  onClose: () => void
}

export function CommandBar({ open, onClose }: CommandBarProps) {
  const [query, setQuery] = useState("")
  const [selectedIndex, setSelectedIndex] = useState(0)
  const inputRef = useRef<HTMLInputElement>(null)
  const { commands, execute } = useCommands()

  const filteredCommands = commands.filter(
    (cmd: Command) =>
      !query || cmd.label.includes(query) || cmd.description?.includes(query) || cmd.category?.includes(query)
  )

  useEffect(() => {
    if (open) {
      setQuery("")
      setSelectedIndex(0)
      setTimeout(() => inputRef.current?.focus(), 50)
    }
  }, [open])

  const handleKeyDown = useCallback(
    (e: KeyboardEvent) => {
      if (e.key === "ArrowDown") {
        e.preventDefault()
        setSelectedIndex((i) => Math.min(i + 1, filteredCommands.length - 1))
      } else if (e.key === "ArrowUp") {
        e.preventDefault()
        setSelectedIndex((i) => Math.max(i - 1, 0))
      } else if (e.key === "Enter" && filteredCommands[selectedIndex]) {
        execute(filteredCommands[selectedIndex].id)
        onClose()
      }
    },
    [filteredCommands, selectedIndex, execute, onClose]
  )

  useEffect(() => {
    const handler = (e: globalThis.KeyboardEvent) => {
      if ((e.metaKey || e.ctrlKey) && e.key === "k" && !open) {
        e.preventDefault()
        onClose()
      }
    }
    window.addEventListener("keydown", handler)
    return () => window.removeEventListener("keydown", handler)
  }, [open, onClose])

  if (!open) return null

  const categories = Array.from(new Set(filteredCommands.map((c: Command) => c.category || "عام")))

  return (
    <div className="fixed inset-0 z-50 flex items-start justify-center pt-[15vh]" onClick={onClose}>
      <div className="fixed inset-0 bg-black/50" />
      <div
        className="relative w-full max-w-xl rounded-xl border border-neutral-200 bg-white shadow-2xl dark:border-neutral-700 dark:bg-neutral-900"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="flex items-center gap-3 border-b border-neutral-200 px-4 dark:border-neutral-700">
          <Search className="h-5 w-5 text-neutral-400" />
          <input
            ref={inputRef}
            value={query}
            onChange={(e) => {
              setQuery(e.target.value)
              setSelectedIndex(0)
            }}
            onKeyDown={handleKeyDown}
            placeholder="اكتب أمر أو ابحث..."
            className="h-12 flex-1 bg-transparent text-sm text-neutral-900 outline-none placeholder:text-neutral-400 dark:text-neutral-100"
          />
          <kbd className="rounded border border-neutral-300 px-1.5 py-0.5 text-[10px] text-neutral-500 dark:border-neutral-600 dark:text-neutral-400">
            ESC
          </kbd>
        </div>
        <div className="max-h-80 overflow-y-auto p-2">
          {filteredCommands.length === 0 && (
            <p className="px-3 py-8 text-center text-sm text-neutral-500 dark:text-neutral-400">
              لا توجد نتائج
            </p>
          )}
          {categories.map((category: string) => {
            const catCommands = filteredCommands.filter((c: Command) => (c.category || "عام") === category)
            return (
              <div key={category}>
                <p className="px-3 py-2 text-[10px] font-medium uppercase tracking-wider text-neutral-500 dark:text-neutral-400">
                  {category}
                </p>
                {catCommands.map((cmd: Command, i: number) => {
                  const globalIndex = filteredCommands.indexOf(cmd)
                  return (
                    <button
                      key={cmd.id}
                      className={cn(
                        "flex w-full items-center gap-3 rounded-lg px-3 py-2.5 text-right text-sm transition",
                        globalIndex === selectedIndex
                          ? "bg-[var(--muhide-orange)]/10 text-[var(--muhide-orange)] dark:bg-[var(--muhide-orange)]/20 dark:text-orange-300"
                          : "text-neutral-700 hover:bg-neutral-50 dark:text-neutral-300 dark:hover:bg-neutral-800"
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
                          <p className="text-xs text-neutral-500 dark:text-neutral-400">{cmd.description}</p>
                        )}
                      </div>
                      {cmd.shortcut && (
                        <kbd className="rounded border border-neutral-300 px-1.5 py-0.5 text-[10px] dark:border-neutral-600">
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
