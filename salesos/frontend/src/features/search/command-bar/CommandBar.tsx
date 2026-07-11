'use client'

import { useState, useCallback, useEffect, useRef } from 'react'
import { cn } from '@salesos/ui'
import { SearchProvider, useSearchContext, searchTelemetry } from '@salesos/search'
import type { SearchResult, SearchQuery, SearchResponse } from '@salesos/search'
import { CommandBarInput } from './CommandBarInput'
import { CommandBarResults } from './CommandBarResults'
import { searchApi } from '@/application/search/search.api'

interface CommandBarProps {
  onResultSelect?: (result: SearchResult) => void
  onNavigate?: (query: string) => void
}

function CommandBarInner({ onResultSelect, onNavigate }: CommandBarProps) {
  const { query, search, setQuery, clearSearch } = useSearchContext()
  const [open, setOpen] = useState(false)
  const [highlightedIndex, setHighlightedIndex] = useState(0)
  const inputRef = useRef<HTMLInputElement>(null)
  const overlayRef = useRef<HTMLDivElement>(null)

  const toggle = useCallback(() => {
    setOpen((prev) => !prev)
    if (!open) {
      searchTelemetry.record('search.command_bar_open', { metadata: { trigger: 'keyboard' } })
    }
  }, [open])

  const close = useCallback(() => {
    setOpen(false)
    clearSearch()
  }, [clearSearch])

  useEffect(() => {
    const handler = (e: KeyboardEvent) => {
      if ((e.ctrlKey || e.metaKey) && e.key === 'k') {
        e.preventDefault()
        toggle()
        return
      }
      if (e.key === 'Escape' && open) {
        close()
        return
      }
    }
    window.addEventListener('keydown', handler)
    return () => window.removeEventListener('keydown', handler)
  }, [open, toggle, close])

  useEffect(() => {
    if (open) {
      setTimeout(() => inputRef.current?.focus(), 50)
    }
  }, [open])

  useEffect(() => {
    setHighlightedIndex(0)
  }, [query.text])

  const handleChange = useCallback((value: string) => {
    setQuery({ text: value })
  }, [setQuery])

  const handleSearch = useCallback(() => {
    if (query.text.trim().length >= 2) search(query.text)
  }, [query.text, search])

  const handleKeyDown = useCallback((e: React.KeyboardEvent) => {
    const maxIndex = 20
    switch (e.key) {
      case 'ArrowDown':
        e.preventDefault()
        setHighlightedIndex((prev) => Math.min(prev + 1, maxIndex))
        break
      case 'ArrowUp':
        e.preventDefault()
        setHighlightedIndex((prev) => Math.max(prev - 1, 0))
        break
      case 'Enter':
        e.preventDefault()
        handleSearch()
        break
    }
  }, [handleSearch])

  const handleResultClick = useCallback((result: SearchResult) => {
    searchTelemetry.click(result.id, result.entityType, highlightedIndex, query.text)
    onResultSelect?.(result)
    close()
  }, [highlightedIndex, query.text, onResultSelect, close])

  const handleSuggestionClick = useCallback((text: string) => {
    setQuery({ text })
    search(text)
  }, [setQuery, search])

  const handleHistoryClick = useCallback((text: string) => {
    setQuery({ text })
    search(text)
  }, [setQuery, search])

  const handleOverlayClick = useCallback((e: React.MouseEvent) => {
    if (e.target === overlayRef.current) close()
  }, [close])

  if (!open) return null

  return (
    <div
      ref={overlayRef}
      className="fixed inset-0 z-50 flex items-start justify-center bg-black/30 pt-[15vh] backdrop-blur-sm"
      onClick={handleOverlayClick}
    >
      <div
        role="dialog"
        aria-label="البحث الشامل"
        className={cn(
          'w-full max-w-2xl overflow-hidden rounded-2xl border border-[var(--border-color)] bg-[var(--bg-primary)] shadow-2xl',
          'dark:border-neutral-700 dark:bg-neutral-900',
        )}
      >
        <CommandBarInput
          value={query.text}
          onChange={handleChange}
          onSearch={handleSearch}
          onKeyDown={handleKeyDown}
          inputRef={inputRef}
        />
        <CommandBarResults
          highlightedIndex={highlightedIndex}
          onResultClick={handleResultClick}
          onSuggestionClick={handleSuggestionClick}
          onHistoryClick={handleHistoryClick}
        />
        <div className="flex items-center gap-3 border-t border-[var(--border-color)] px-4 py-2 text-[10px] text-[var(--text-muted)] dark:border-neutral-700">
          <span>↑↓ للتنقل</span>
          <span>Enter للاختيار</span>
          <span>Esc للإغلاق</span>
        </div>
      </div>
    </div>
  )
}

export function CommandBar(props: CommandBarProps) {
  return (
    <SearchProvider onSearch={(q) => searchApi(q)}>
      <CommandBarInner {...props} />
    </SearchProvider>
  )
}
