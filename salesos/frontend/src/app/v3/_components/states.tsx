import Link from 'next/link'
import type { ReactNode } from 'react'

export function LoadingState({ label = 'Loading…' }: { label?: string }) {
 return (
 <div
 className="flex items-center justify-center rounded-[var(--radius-lg)] border border-[var(--border-default)] bg-[var(--bg-primary)] px-4 py-16 text-sm text-[var(--text-muted)]"
 role="status"
 aria-live="polite"
 >
 {label}
 </div>
 )
}

export function EmptyState({
 title,
 description,
 action,
}: {
 title: string
 description?: string
 action?: ReactNode
}) {
 return (
 <div className="rounded-[var(--radius-lg)] border border-dashed border-[var(--border-default)] bg-[var(--bg-primary)] px-4 py-12 text-center">
 <p className="text-sm font-medium text-[var(--text-primary)]">{title}</p>
 {description ? (
 <p className="mt-1 text-sm text-[var(--text-secondary)]">{description}</p>
 ) : null}
 {action ? <div className="mt-4 flex justify-center">{action}</div> : null}
 </div>
 )
}

export function ErrorState({
 title = 'Something went wrong',
 description,
 onRetry,
}: {
 title?: string
 description?: string
 onRetry?: () => void
}) {
 return (
 <div
 className="rounded-[var(--radius-lg)] border border-[var(--status-danger-border,#fecaca)] bg-[var(--status-danger-bg,#fef2f2)] px-4 py-10 text-center"
 role="alert"
 >
 <p className="text-sm font-medium text-[var(--status-danger,#991b1b)]">{title}</p>
 {description ? (
 <p className="mt-1 text-sm text-[var(--status-danger,#991b1b)]/80">{description}</p>
 ) : null}
 {onRetry ? (
 <button
 type="button"
 onClick={onRetry}
 className="mt-4 rounded-[var(--radius-md)] border border-[var(--border-default)] bg-[var(--bg-primary)] px-3 py-1.5 text-sm text-[var(--text-primary)] hover:bg-[var(--bg-secondary)] focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[var(--focus-ring)]"
 >
 Retry
 </button>
 ) : null}
 </div>
 )
}

export function PermissionState({
 nextPath,
 title = 'Sign in required',
 description = 'This workspace view needs an authenticated session. Use the same demo login as the legacy app.',
}: {
 nextPath: string
 title?: string
 description?: string
}) {
 const href = `/login?next=${encodeURIComponent(nextPath)}`
 return (
 <div className="rounded-[var(--radius-lg)] border border-[var(--border-default)] bg-[var(--bg-primary)] px-4 py-12 text-center">
 <p className="text-sm font-medium text-[var(--text-primary)]">{title}</p>
 <p className="mt-1 text-sm text-[var(--text-secondary)]">{description}</p>
 <Link
 href={href}
 className="mt-4 inline-flex rounded-[var(--radius-md)] bg-[var(--muhide-orange)] px-4 py-2 text-sm font-medium text-white hover:opacity-90 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[var(--focus-ring)]"
 >
 Sign in
 </Link>
 </div>
 )
}

export function PreviewBadge() {
 return (
 <span className="rounded-full border border-[var(--border-default)] bg-[var(--bg-secondary)] px-2 py-0.5 text-[11px] font-medium text-[var(--text-muted)]">
 Preview
 </span>
 )
}

export function GhostButtonLink({
 href,
 children,
 primary,
}: {
 href: string
 children: ReactNode
 primary?: boolean
}) {
 return (
 <Link
 href={href}
 className={
 primary
 ? 'rounded-[var(--radius-md)] bg-[var(--muhide-orange)] px-3 py-1.5 text-sm font-medium text-white hover:opacity-90 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[var(--focus-ring)]'
 : 'rounded-[var(--radius-md)] border border-[var(--border-default)] px-3 py-1.5 text-sm text-[var(--text-primary)] hover:bg-[var(--bg-secondary)] focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[var(--focus-ring)]'
 }
 >
 {children}
 </Link>
 )
}
