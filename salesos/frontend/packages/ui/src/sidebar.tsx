import { type ReactNode } from 'react'
import { cn } from './utils'

interface SidebarItem {
  icon: ReactNode
  label: string
  href?: string
  active?: boolean
  badge?: number
  children?: SidebarItem[]
}

interface SidebarProps {
  items: SidebarItem[]
  collapsed?: boolean
  onToggle?: () => void
  className?: string
}

export function Sidebar({ items, collapsed = false, onToggle, className }: SidebarProps) {
  return (
    <aside
      className={cn(
        'flex flex-col border-r bg-white transition-all duration-300 dark:border-gray-700 dark:bg-gray-900',
        collapsed ? 'w-16' : 'w-64',
        className
      )}
    >
      <div className="flex h-14 items-center justify-end px-4">
        <button
          onClick={onToggle}
          className="rounded-md p-1 text-gray-500 hover:bg-gray-100 dark:text-gray-400 dark:hover:bg-gray-800"
        >
          <svg
            className={cn('h-5 w-5 transition-transform', collapsed && 'rotate-180')}
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
          >
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M11 19l-7-7 7-7m8 14l-7-7 7-7" />
          </svg>
        </button>
      </div>
      <nav className="flex-1 space-y-1 px-2 pb-4">
        {items.map((item, i) => (
          <SidebarItemComponent key={i} item={item} collapsed={collapsed} />
        ))}
      </nav>
    </aside>
  )
}

function SidebarItemComponent({ item, collapsed }: { item: SidebarItem; collapsed: boolean }) {
  return (
    <div className="group relative">
      <button
        onClick={() => {
          if (item.href) {
            if (item.href.startsWith('http')) {
              window.open(item.href, '_blank')
            } else {
              window.location.href = item.href
            }
          }
        }}
        className={cn(
          'flex w-full items-center gap-3 rounded-lg px-3 py-2 text-sm font-medium transition-colors',
          item.active
            ? 'bg-blue-50 text-blue-700 dark:bg-blue-900/50 dark:text-blue-400'
            : 'text-gray-600 hover:bg-gray-100 hover:text-gray-900 dark:text-gray-400 dark:hover:bg-gray-800 dark:hover:text-gray-200'
        )}
      >
        <span className="shrink-0">{item.icon}</span>
        {!collapsed && (
          <>
            <span className="flex-1 truncate text-left">{item.label}</span>
            {item.badge !== undefined && (
              <span className="inline-flex h-5 min-w-5 items-center justify-center rounded-full bg-blue-600 px-1.5 text-xs font-medium text-white">
                {item.badge}
              </span>
            )}
          </>
        )}
      </button>
      {collapsed && (
        <div className="absolute left-full top-0 z-50 ml-2 hidden rounded-md bg-gray-900 px-3 py-1.5 text-xs text-white shadow-lg group-hover:block dark:bg-gray-700">
          {item.label}
          {item.badge !== undefined && (
            <span className="ml-2 rounded-full bg-blue-600 px-1.5 text-xs text-white">
              {item.badge}
            </span>
          )}
        </div>
      )}
      {!collapsed && item.children && item.children.length > 0 && (
        <div className="ml-8 mt-1 space-y-1">
          {item.children.map((child, j) => (
            <SidebarItemComponent key={j} item={child} collapsed={collapsed} />
          ))}
        </div>
      )}
    </div>
  )
}
