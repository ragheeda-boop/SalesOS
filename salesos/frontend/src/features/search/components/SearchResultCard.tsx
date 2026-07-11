'use client'

import { cn } from '@salesos/ui'
import { SearchHighlight } from '@salesos/search'
import type { SearchResult } from '@salesos/search'
import { Building2, User, FileText, Sparkles, Activity, Shield, Newspaper, Award, Briefcase } from 'lucide-react'

const ENTITY_ICON: Record<string, React.ReactNode> = {
  company: <Building2 className="h-4 w-4" />,
  person: <User className="h-4 w-4" />,
  signal: <Activity className="h-4 w-4" />,
  license: <Shield className="h-4 w-4" />,
  document: <FileText className="h-4 w-4" />,
  opportunity: <Award className="h-4 w-4" />,
  employee: <Briefcase className="h-4 w-4" />,
  ai_answer: <Sparkles className="h-4 w-4" />,
  timeline_event: <Activity className="h-4 w-4" />,
  government_record: <Newspaper className="h-4 w-4" />,
}

const BADGE_VARIANT: Record<string, string> = {
  info: 'bg-blue-50 text-blue-700 dark:bg-blue-900/30 dark:text-blue-300',
  success: 'bg-green-50 text-green-700 dark:bg-green-900/30 dark:text-green-300',
  warning: 'bg-amber-50 text-amber-700 dark:bg-amber-900/30 dark:text-amber-300',
  danger: 'bg-red-50 text-red-700 dark:bg-red-900/30 dark:text-red-300',
  neutral: 'bg-neutral-100 text-neutral-600 dark:bg-neutral-800 dark:text-neutral-400',
}

interface SearchResultCardProps {
  result: SearchResult
  onClick?: (result: SearchResult) => void
  highlighted?: boolean
}

export function SearchResultCard({ result, onClick, highlighted }: SearchResultCardProps) {
  const icon = ENTITY_ICON[result.entityType] ?? <FileText className="h-4 w-4" />

  return (
    <div
      role="option"
      aria-selected={highlighted}
      tabIndex={0}
      className={cn(
        'flex items-start gap-3 rounded-lg px-4 py-3 text-sm transition-colors motion-reduce:transition-none cursor-pointer',
        highlighted
          ? 'bg-primary-50 dark:bg-primary-900/20'
          : 'hover:bg-[var(--bg-tertiary)]',
      )}
      onClick={() => onClick?.(result)}
      onKeyDown={(e) => { if (e.key === 'Enter') onClick?.(result) }}
    >
      <div className="mt-0.5 flex h-8 w-8 shrink-0 items-center justify-center rounded-lg bg-[var(--bg-tertiary)] text-[var(--text-muted)] dark:bg-neutral-800">
        {icon}
      </div>
      <div className="flex-1 min-w-0">
        <div className="flex items-center gap-2">
          <span className="truncate font-medium text-[var(--text-primary)]">
            <SearchHighlight text={result.title} highlights={result.highlights.flatMap((h) => h.snippets)} />
          </span>
          <div className="flex shrink-0 items-center gap-1">
            {result.badges.map((badge, i) => (
              <span key={i} className={cn('rounded-full px-1.5 py-0.5 text-[10px] font-medium', BADGE_VARIANT[badge.variant] ?? BADGE_VARIANT.neutral)}>
                {badge.label}
              </span>
            ))}
          </div>
        </div>
        <p className="mt-0.5 text-xs text-[var(--text-muted)]">
          {result.subtitle}
        </p>
        {result.description && (
          <p className="mt-0.5 line-clamp-2 text-xs text-[var(--text-muted)]">
            {result.description}
          </p>
        )}
        <div className="mt-1 flex items-center gap-2 text-[10px] text-[var(--text-muted)]">
          <span className={cn('rounded px-1 py-0.5 font-medium', result.score > 0.8 ? 'text-green-600 dark:text-green-400' : result.score > 0.5 ? 'text-amber-600 dark:text-amber-400' : 'text-red-600 dark:text-red-400')}>
            %{Math.round(result.score * 100)}
          </span>
          <span>{result.source}</span>
          {result.relationships && result.relationships.length > 0 && (
            <span>{result.relationships.length} علاقة</span>
          )}
        </div>
      </div>
    </div>
  )
}
