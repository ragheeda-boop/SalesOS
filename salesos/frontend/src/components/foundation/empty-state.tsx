import { cn } from "@salesos/ui"

type EmptyStateVariant = 'search' | 'signals' | 'timeline' | 'documents' | 'relationships' | 'default'

interface EmptyStateAction {
  label: string
  onClick: () => void
}

interface EmptyStateProps {
  variant?: EmptyStateVariant
  title: string
  description?: string
  action?: EmptyStateAction
  className?: string
}

const ICON_CLASSES = 'mx-auto mb-4 text-[var(--text-muted)]'

const VARIANT_ICONS: Record<EmptyStateVariant, { viewBox: string; paths: string[] }> = {
  search: {
    viewBox: '0 0 24 24',
    paths: [
      'M21 21l-5.197-5.197m0 0A7.5 7.5 0 105.196 5.196a7.5 7.5 0 0010.607 10.607z',
    ],
  },
  signals: {
    viewBox: '0 0 24 24',
    paths: [
      'M14.857 17.082a23.848 23.848 0 005.454-1.31A8.967 8.967 0 0118 9.75V9A6 6 0 006 9v.75a8.967 8.967 0 01-2.312 6.022c1.733.64 3.56 1.085 5.455 1.31m5.714 0a24.255 24.255 0 01-5.714 0m5.714 0a3 3 0 11-5.714 0',
    ],
  },
  timeline: {
    viewBox: '0 0 24 24',
    paths: [
      'M12 6v6h4.5m4.5 0a9 9 0 11-18 0 9 9 0 0118 0z',
    ],
  },
  documents: {
    viewBox: '0 0 24 24',
    paths: [
      'M19.5 14.25v-2.625a3.375 3.375 0 00-3.375-3.375h-1.5A1.125 1.125 0 0113.5 7.125v-1.5a3.375 3.375 0 00-3.375-3.375H8.25m2.25 0H5.625c-.621 0-1.125.504-1.125 1.125v17.25c0 .621.504 1.125 1.125 1.125h12.75c.621 0 1.125-.504 1.125-1.125V11.25a9 9 0 00-9-9z',
    ],
  },
  relationships: {
    viewBox: '0 0 24 24',
    paths: [
      'M15 19.128a9.38 9.38 0 002.625.372 9.337 9.337 0 004.121-.952 4.125 4.125 0 00-7.533-2.493M15 19.128v-.003c0-1.113-.285-2.16-.786-3.07M15 19.128v.106A12.318 12.318 0 018.624 21c-2.331 0-4.512-.645-6.374-1.766l-.001-.109a6.375 6.375 0 0111.964-3.07M12 6.375a3.375 3.375 0 11-6.75 0 3.375 3.375 0 016.75 0zm8.25 2.25a2.625 2.625 0 11-5.25 0 2.625 2.625 0 015.25 0z',
    ],
  },
  default: {
    viewBox: '0 0 24 24',
    paths: [
      'M2.25 13.5h3.86a2.25 2.25 0 012.012 1.244l.256.512a2.25 2.25 0 002.013 1.244h3.218a2.25 2.25 0 002.013-1.244l.256-.512a2.25 2.25 0 012.013-1.244h3.859M12 3v8.25m0 0l-3-3m3 3l3-3',
    ],
  },
}

export function EmptyState({ variant = 'default', title, description, action, className }: EmptyStateProps) {
  const icon = VARIANT_ICONS[variant]

  return (
    <div className={cn('flex flex-col items-center justify-center py-12 text-center', className)} role="status">
      <svg className={cn(ICON_CLASSES, variant === 'search' ? 'h-12 w-12' : 'h-10 w-10')} viewBox={icon.viewBox} fill="none" stroke="currentColor" strokeWidth={1.5} strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
        {icon.paths.map((d, i) => (
          <path key={i} d={d} />
        ))}
      </svg>
      <h3 className="text-base font-semibold text-[var(--text-primary)]">{title}</h3>
      {description && (
        <p className="mt-1 text-sm text-[var(--text-muted)] max-w-sm">{description}</p>
      )}
      {action && (
        <button
          type="button"
          onClick={action.onClick}
          className="mt-4 inline-flex items-center rounded-lg bg-[var(--muhide-orange)] px-4 py-2 text-sm font-medium text-white hover:brightness-110 transition-all"
        >
          {action.label}
        </button>
      )}
    </div>
  )
}
