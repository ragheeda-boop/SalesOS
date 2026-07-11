'use client'

import { cn } from '@salesos/ui'
import { Search } from 'lucide-react'

interface SearchEmptyProps {
  query?: string
  suggestion?: string
  className?: string
}

export function SearchEmpty({ query, suggestion, className }: SearchEmptyProps) {
  return (
    <div className={cn('flex flex-col items-center justify-center py-12 text-center', className)}>
      <Search className="mb-3 h-10 w-10 text-[var(--text-muted)] opacity-30" />
      <p className="text-sm font-medium text-[var(--text-primary)]">
        {query ? `لا توجد نتائج لـ "${query}"` : 'لا توجد نتائج'}
      </p>
      <p className="mt-1 text-xs text-[var(--text-muted)]">
        {suggestion ?? 'حاول استخدام كلمات مختلفة أو تصفية أقل'}
      </p>
    </div>
  )
}
