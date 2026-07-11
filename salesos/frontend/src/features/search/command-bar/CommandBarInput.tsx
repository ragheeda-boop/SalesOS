'use client'

import { useState, useCallback, useEffect, useRef } from 'react'
import { cn } from '@salesos/ui'
import { Search, Command } from 'lucide-react'

interface CommandBarInputProps {
  value: string
  onChange: (value: string) => void
  onSearch: () => void
  onKeyDown: (e: React.KeyboardEvent) => void
  inputRef: React.RefObject<HTMLInputElement | null>
}

export function CommandBarInput({ value, onChange, onSearch, onKeyDown, inputRef }: CommandBarInputProps) {
  return (
    <div className="flex items-center gap-3 border-b border-[var(--border-color)] px-4 py-3 dark:border-neutral-700">
      <Search className="h-5 w-5 text-[var(--text-muted)]" />
      <input
        ref={inputRef}
        type="text"
        value={value}
        onChange={(e) => onChange(e.target.value)}
        onKeyDown={onKeyDown}
        placeholder="ابحث في المنصة…"
        role="searchbox"
        aria-label="البحث الشامل"
        className="flex-1 bg-transparent text-base text-[var(--text-primary)] placeholder:text-[var(--text-muted)] focus:outline-none"
      />
      <kbd className="hidden shrink-0 items-center gap-0.5 rounded-md border border-[var(--border-color)] px-1.5 py-0.5 text-[10px] text-[var(--text-muted)] sm:flex">
        <Command className="h-3 w-3" />
        K
      </kbd>
    </div>
  )
}
