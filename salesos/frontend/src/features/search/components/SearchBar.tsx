'use client'

import { useState, useCallback } from 'react'
import { SearchInput } from './SearchInput'
import { cn } from '@salesos/ui'

interface SearchBarProps {
  onSearch: (value: string) => void
  placeholder?: string
  variant?: 'default' | 'hero'
  className?: string
}

export function SearchBar({ onSearch, placeholder, variant = 'default', className }: SearchBarProps) {
  const [value, setValue] = useState('')

  const handleSearch = useCallback((v: string) => {
    if (v.trim().length >= 2) onSearch(v)
  }, [onSearch])

  return (
    <div className={cn(variant === 'hero' && 'w-full', className)}>
      <SearchInput
        value={value}
        onChange={setValue}
        onSearch={handleSearch}
        placeholder={placeholder}
        variant={variant}
        autoFocus={variant === 'hero'}
        className={variant === 'hero' ? 'w-full' : undefined}
      />
    </div>
  )
}
