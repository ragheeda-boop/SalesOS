import { cn } from "@salesos/ui"
import { useAppShell } from "./app-shell"

interface HeaderProps {
  title?: string
  breadcrumbs?: { label: string; href?: string }[]
  searchPlaceholder?: string
  onSearchClick?: () => void
  notificationCount?: number
  onNotificationClick?: () => void
  userAvatar?: React.ReactNode
  userMenu?: React.ReactNode
  className?: string
  children?: React.ReactNode
}

export function Header({
  title,
  breadcrumbs,
  searchPlaceholder = "Search anything...",
  onSearchClick,
  notificationCount,
  onNotificationClick,
  userAvatar,
  userMenu,
  className,
  children,
}: HeaderProps) {
  const { setCommandOpen } = useAppShell()

  const handleSearchClick = onSearchClick || (() => setCommandOpen(true))

  return (
    <header className={cn(
      'flex items-center h-topbar px-4 bg-white border-b border-[var(--border-default)] flex-shrink-0',
      className
    )}>
      <div className="flex items-center gap-2 flex-1 min-w-0">
        {breadcrumbs && breadcrumbs.length > 0 && (
          <nav className="flex items-center gap-1.5 text-sm text-[var(--text-muted)]" aria-label="Breadcrumbs">
            {breadcrumbs.map((crumb, i) => {
              const isLast = i === breadcrumbs.length - 1
              return (
                <span key={i} className="flex items-center gap-1.5">
                  {i > 0 && <span className="text-[var(--text-muted)]/40">/</span>}
                  {crumb.href ? (
                    <a href={crumb.href} className="hover:text-[var(--text-primary)] transition-colors" {...(isLast ? { 'aria-current': 'page' as const } : {})}>{crumb.label}</a>
                  ) : (
                    <span className="text-[var(--text-primary)] font-medium" {...(isLast ? { 'aria-current': 'page' as const } : {})}>{crumb.label}</span>
                  )}
                </span>
              )
            })}
          </nav>
        )}
        {title && !breadcrumbs && (
          <h1 className="text-base font-display text-[var(--text-primary)] truncate">{title}</h1>
        )}
        {children}
      </div>

      <div className="flex items-center gap-2 flex-shrink-0">
        <button
          onClick={handleSearchClick}
          aria-label="Search"
          className="flex items-center gap-2 h-8 px-3 rounded-md bg-[var(--bg-secondary)] border border-[var(--border-default)] text-sm text-[var(--text-muted)] hover:text-[var(--text-primary)] hover:border-[var(--border-hover)] transition-colors min-w-[180px]"
        >
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="flex-shrink-0" aria-hidden="true">
            <circle cx="11" cy="11" r="8" /><path d="m21 21-4.3-4.3" />
          </svg>
          <span className="flex-1 text-left truncate">{searchPlaceholder}</span>
          <kbd className="hidden sm:inline-flex items-center gap-0.5 px-1.5 py-0.5 text-[10px] font-medium bg-white border border-[var(--border-default)] rounded-sm text-[var(--text-muted)]">
            <span className="text-[9px]">&#8984;</span>K
          </kbd>
        </button>

        {notificationCount !== undefined && (
          <button
            onClick={onNotificationClick}
            aria-label={`Notifications${notificationCount > 0 ? ` (${notificationCount > 99 ? '99+' : notificationCount} unread)` : ''}`}
            className="relative flex items-center justify-center w-8 h-8 rounded-md text-[var(--text-muted)] hover:text-[var(--text-primary)] hover:bg-[var(--bg-secondary)] transition-colors"
          >
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
              <path d="M6 8a6 6 0 0 1 12 0c0 7 3 9 3 9H3s3-2 3-9" /><path d="M10.3 21a1.94 1.94 0 0 0 3.4 0" />
            </svg>
            {notificationCount > 0 && (
              <span className="absolute -top-0.5 -right-0.5 flex items-center justify-center min-w-[16px] h-4 px-1 text-[10px] font-bold text-white bg-[var(--muhide-orange)] rounded-full">
                {notificationCount > 99 ? '99+' : notificationCount}
              </span>
            )}
          </button>
        )}

        {userAvatar && (
          <div className="flex items-center">
            {userAvatar}
          </div>
        )}

        {userMenu}
      </div>
    </header>
  )
}
