"use client"

import { useState, useRef, useCallback, useEffect, type KeyboardEvent } from 'react'
import { cn } from './utils'
import { Input } from './input'
import { Spinner } from './spinner'
import { ChevronDown } from 'lucide-react'

interface ComboboxOption {
  label: string
  value: string
}

interface ComboboxProps {
  options: ComboboxOption[]
  value?: string
  onChange?: (value: string) => void
  onSearch?: (query: string) => void
  label?: string
  placeholder?: string
  disabled?: boolean
  loading?: boolean
  error?: string
  className?: string
}

export function Combobox({
  options,
  value,
  onChange,
  onSearch,
  label,
  placeholder = 'Search...',
  disabled = false,
  loading = false,
  error,
  className,
}: ComboboxProps) {
  const [open, setOpen] = useState(false)
  const [search, setSearch] = useState('')
  const [activeIndex, setActiveIndex] = useState(-1)
  const inputRef = useRef<HTMLInputElement>(null)
  const listRef = useRef<HTMLUListElement>(null)
  const containerRef = useRef<HTMLDivElement>(null)

  const selectedOption = options.find((o) => o.value === value)
  const filteredOptions = search
    ? options.filter((o) => o.label.toLowerCase().includes(search.toLowerCase()))
    : options

  useEffect(() => {
    setActiveIndex(-1)
  }, [filteredOptions.length])

  useEffect(() => {
    function handleClickOutside(e: MouseEvent) {
      if (containerRef.current && !containerRef.current.contains(e.target as Node)) {
        setOpen(false)
      }
    }
    document.addEventListener('mousedown', handleClickOutside)
    return () => document.removeEventListener('mousedown', handleClickOutside)
  }, [])

  const handleInputChange = useCallback(
    (e: React.ChangeEvent<HTMLInputElement>) => {
      const q = e.target.value
      setSearch(q)
      onSearch?.(q)
      setOpen(true)
    },
    [onSearch]
  )

  const selectOption = useCallback(
    (opt: ComboboxOption) => {
      onChange?.(opt.value)
      setSearch('')
      setOpen(false)
      inputRef.current?.focus()
    },
    [onChange]
  )

  const handleKeyDown = useCallback(
    (e: KeyboardEvent) => {
      switch (e.key) {
        case 'ArrowDown':
          e.preventDefault()
          setActiveIndex((prev) => (prev + 1) % filteredOptions.length)
          break
        case 'ArrowUp':
          e.preventDefault()
          setActiveIndex((prev) => (prev - 1 + filteredOptions.length) % filteredOptions.length)
          break
        case 'Enter':
          e.preventDefault()
          if (activeIndex >= 0 && activeIndex < filteredOptions.length) {
            selectOption(filteredOptions[activeIndex])
          }
          break
        case 'Escape':
          e.preventDefault()
          setOpen(false)
          break
      }
    },
    [filteredOptions, activeIndex, selectOption]
  )

  useEffect(() => {
    if (activeIndex >= 0 && listRef.current) {
      const item = listRef.current.querySelector<HTMLLIElement>(`[data-index="${activeIndex}"]`)
      item?.scrollIntoView({ block: 'nearest' })
    }
  }, [activeIndex])

  return (
    <div ref={containerRef} className={cn('relative', className)}>
      <div className="relative">
        <Input
          ref={inputRef}
          label={label}
          placeholder={selectedOption ? selectedOption.label : placeholder}
          value={search}
          onChange={handleInputChange}
          onFocus={() => setOpen(true)}
          onKeyDown={handleKeyDown}
          disabled={disabled}
          error={error}
          rightIcon={
            loading ? (
              <Spinner className="h-4 w-4" />
            ) : (
              <ChevronDown className={cn('h-4 w-4 transition-transform', open && 'rotate-180')} />
            )
          }
          role="combobox"
          aria-expanded={open}
          aria-autocomplete="list"
          aria-activedescendant={activeIndex >= 0 ? `combobox-option-${activeIndex}` : undefined}
          aria-controls="combobox-listbox"
          autoComplete="off"
        />
      </div>
      {open && (
        <ul
          ref={listRef}
          id="combobox-listbox"
          role="listbox"
          className="absolute z-dropdown mt-1 max-h-60 w-full overflow-auto rounded-lg border border-[var(--border-default)] bg-[var(--bg-primary)] p-1 shadow-muhide-4"
        >
          {filteredOptions.length === 0 ? (
            <li className="px-3 py-2 text-sm text-[var(--text-muted)]">No results found</li>
          ) : (
            filteredOptions.map((opt, i) => (
              <li
                key={opt.value}
                id={`combobox-option-${i}`}
                data-index={i}
                role="option"
                aria-selected={opt.value === value}
                className={cn(
                  'flex cursor-pointer items-center rounded-md px-3 py-2 text-sm outline-none hover:bg-[var(--bg-secondary)]',
                  activeIndex === i && 'bg-[var(--bg-secondary)]',
                  opt.value === value && 'font-medium text-[var(--muhide-orange)]'
                )}
                onMouseDown={(e) => {
                  e.preventDefault()
                  selectOption(opt)
                }}
                onMouseEnter={() => setActiveIndex(i)}
              >
                {opt.label}
              </li>
            ))
          )}
        </ul>
      )}
    </div>
  )
}
