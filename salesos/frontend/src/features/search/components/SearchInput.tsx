'use client'

import { useState, useCallback, useRef, useEffect, type KeyboardEvent, type ChangeEvent } from 'react'
import { cn } from '@salesos/ui'
import { Search, X } from 'lucide-react'

interface SearchInputProps {
  value: string
  onChange: (value: string) => void
  onSearch: (value: string) => void
  placeholder?: string
  autoFocus?: boolean
  loading?: boolean
  className?: string
  variant?: 'default' | 'minimal' | 'hero'
}

export function SearchInput({
  value, onChange, onSearch, placeholder = 'ابحث في المنصة…',
  autoFocus, loading, className, variant = 'default',
}: SearchInputProps) {
  const inputRef = useRef<HTMLInputElement>(null)

  useEffect(() => {
    if (autoFocus && inputRef.current) inputRef.current.focus()
  }, [autoFocus])

  const handleChange = useCallback((e: ChangeEvent<HTMLInputElement>) => {
    onChange(e.target.value)
  }, [onChange])

  const handleKeyDown = useCallback((e: KeyboardEvent) => {
    if (e.key === 'Enter') onSearch(value)
    if (e.key === 'Escape') onChange('')
  }, [value, onSearch, onChange])

  const handleClear = useCallback(() => {
    onChange('')
    inputRef.current?.focus()
  }, [onChange])

  const isHero = variant === 'hero'
  const isMinimal = variant === 'minimal'

  return (
    <div className={cn(
      'relative flex items-center',
      isHero ? 'w-full' : isMinimal ? 'w-auto' : 'w-full max-w-xl',
      className,
    )}>
      {!isMinimal && (
        <Search className={cn(
          'pointer-events-none absolute h-4 w-4 text-[var(--text-muted)]',
          isHero ? 'right-5 top-1/2 -translate-y-1/2 h-5 w-5' : 'right-3',
        )} />
      )}
      <input
        ref={inputRef}
        type="text"
        value={value}
        onChange={handleChange}
        onKeyDown={handleKeyDown}
        placeholder={placeholder}
        role="searchbox"
        aria-label={placeholder}
        aria-autocomplete="list"
        className={cn(
          'w-full rounded-xl border border-[var(--border-color)] bg-[var(--bg-primary)] text-[var(--text-primary)] transition-colors placeholder:text-[var(--text-muted)] focus:border-primary-500 focus:outline-none focus:ring-2 focus:ring-primary-500/20 dark:border-neutral-700 dark:bg-neutral-900',
          isHero ? 'px-5 py-4 pr-14 text-lg' : isMinimal ? 'border-none bg-transparent px-3 py-2 text-sm' : 'px-3 py-2.5 pr-10 text-sm',
        )}
      />
      {value && (
        <button
          onClick={handleClear}
          aria-label="مسح البحث"
          className={cn(
            'absolute left-2 rounded-lg p-1 text-[var(--text-muted)] hover:bg-[var(--bg-tertiary)] hover:text-[var(--text-primary)]',
            isHero && 'left-4',
          )}
        >
          <X className="h-4 w-4" />
        </button>
      )}
      {loading && (
        <div className={cn('absolute left-12 h-4 w-4 animate-spin rounded-full border-2 border-[var(--border-color)] border-t-primary-500', isHero && 'left-16')} />
      )}
    </div>
  )
}
