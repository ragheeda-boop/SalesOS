'use client'

import Link from 'next/link'
import { usePathname } from 'next/navigation'
import { PanelLeftClose, PanelLeft } from 'lucide-react'
import { cn } from '@salesos/ui'
import { V3_DOMAIN_NAV, isV3NavActive } from './nav'

type V3ShellProps = {
 collapsed: boolean
 onToggleCollapsed: () => void
}

export function V3Shell({ collapsed, onToggleCollapsed }: V3ShellProps) {
 const pathname = usePathname()

 return (
 <aside
 className={cn(
 'flex shrink-0 flex-col border-r border-[var(--border-default)] bg-[var(--bg-secondary)] transition-[width] duration-200 ease-out',
 collapsed ? 'w-14' : 'w-56',
 )}
 aria-label="Workspace navigation"
 >
 <div
 className={cn(
 'flex h-12 items-center border-b border-[var(--border-default)] px-2',
 collapsed ? 'justify-center' : 'justify-between gap-2 px-3',
 )}
 >
 {!collapsed && (
 <div className="min-w-0">
 <div
 className="truncate text-[11px] font-medium uppercase tracking-[0.08em] text-[var(--text-muted)]"
 style={{ fontFamily: 'var(--font-ui)' }}
 >
 SalesOS
 </div>
 <div className="truncate text-xs text-[var(--text-secondary)]">v3 Preview</div>
 </div>
 )}
 <button
 type="button"
 onClick={onToggleCollapsed}
 className="inline-flex h-8 w-8 items-center justify-center rounded-[var(--radius-md)] text-[var(--text-muted)] transition-colors hover:bg-[var(--bg-tertiary)] hover:text-[var(--text-primary)] focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[var(--focus-ring)]"
 aria-label={collapsed ? 'Expand sidebar' : 'Collapse sidebar'}
 aria-expanded={!collapsed}
 >
 {collapsed ? (
 <PanelLeft className="h-4 w-4" aria-hidden />
 ) : (
 <PanelLeftClose className="h-4 w-4" aria-hidden />
 )}
 </button>
 </div>

 <nav className="flex flex-1 flex-col gap-0.5 p-2" aria-label="Domains">
 {V3_DOMAIN_NAV.map((item) => {
 const active = isV3NavActive(pathname, item.href)
 const Icon = item.icon
 return (
 <Link
 key={item.href}
 href={item.href}
 title={collapsed ? item.label : undefined}
 aria-current={active ? 'page' : undefined}
 className={cn(
 'group flex items-center gap-2.5 rounded-[var(--radius-md)] px-2.5 py-1.5 text-[13px] transition-colors',
 'focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[var(--focus-ring)]',
 collapsed && 'justify-center px-0',
 active
 ? 'bg-[var(--muhide-orange)]/10 font-medium text-[var(--muhide-orange)]'
 : 'text-[var(--text-secondary)] hover:bg-[var(--bg-tertiary)] hover:text-[var(--text-primary)]',
 )}
 >
 <Icon
 className={cn(
 'h-4 w-4 shrink-0',
 active ? 'text-[var(--muhide-orange)]' : 'text-[var(--text-muted)] group-hover:text-[var(--text-primary)]',
 )}
 aria-hidden
 />
 {!collapsed && <span className="truncate">{item.label}</span>}
 {collapsed && <span className="sr-only">{item.label}</span>}
 </Link>
 )
 })}
 </nav>

 {!collapsed && (
 <div className="border-t border-[var(--border-default)] px-3 py-3">
 <p className="text-[11px] leading-relaxed text-[var(--text-muted)]">
 Design Program shell — not Production GO.
 </p>
 </div>
 )}
 </aside>
 )
}
