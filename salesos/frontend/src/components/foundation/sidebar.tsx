import { cn } from "@salesos/ui"
import { useAppShell } from "./app-shell"

interface SidebarItem {
  id: string
  label: string
  icon: React.ReactNode
  href?: string
  badge?: number | string
  active?: boolean
  onClick?: () => void
}

interface SidebarSection {
  id: string
  label: string
  items: SidebarItem[]
}

interface SidebarProps {
  sections: SidebarSection[]
  companySection?: SidebarSection
  companyLogo?: React.ReactNode
  className?: string
}

export function Sidebar({ sections, companySection, companyLogo, className }: SidebarProps) {
  const { sidebarCollapsed, setSidebarCollapsed } = useAppShell()

  return (
    <aside aria-label="Sidebar" className={cn(
      'flex flex-col bg-[var(--muhide-ink)] text-white transition-all duration-200 ease-standard overflow-hidden',
      sidebarCollapsed ? 'w-sidebar-collapsed' : 'w-sidebar',
      className
    )}>
      <div className="flex items-center h-topbar px-3 border-b border-white/10">
        {companyLogo || <div className="w-8 h-8 rounded-md bg-[var(--muhide-orange)] flex items-center justify-center text-sm font-bold">S</div>}
      </div>

      <nav className="flex-1 overflow-y-auto py-3 px-2 space-y-6">
        {sections.map((section) => (
          <div key={section.id}>
            {!sidebarCollapsed && (
              <div className="px-2 mb-1">
                <span className="text-xs font-medium text-white/40 uppercase tracking-wider">{section.label}</span>
              </div>
            )}
            <div className="space-y-0.5">
              {section.items.map((item) => (
                <SidebarNavItem key={item.id} item={item} collapsed={sidebarCollapsed} />
              ))}
            </div>
          </div>
        ))}

        {companySection && (
          <div>
            {!sidebarCollapsed && (
              <div className="px-2 mb-1 mt-4">
                <span className="text-xs font-medium text-white/40 uppercase tracking-wider">{companySection.label}</span>
              </div>
            )}
            <div className="space-y-0.5">
              {companySection.items.map((item) => (
                <SidebarNavItem key={item.id} item={item} collapsed={sidebarCollapsed} />
              ))}
            </div>
          </div>
        )}
      </nav>

      <div className="p-2 border-t border-white/10">
        <button
          onClick={() => setSidebarCollapsed(!sidebarCollapsed)}
          className="flex items-center justify-center w-full h-9 rounded-md text-white/50 hover:text-white hover:bg-white/10 transition-colors"
          aria-label={sidebarCollapsed ? 'Expand sidebar' : 'Collapse sidebar'}
          aria-expanded={!sidebarCollapsed}
        >
          {sidebarCollapsed ? '\u2192' : '\u2190'}
        </button>
      </div>
    </aside>
  )
}

function SidebarNavItem({ item, collapsed }: { item: SidebarItem; collapsed: boolean }) {
  const Wrapper = item.href ? 'a' : 'button'
  return (
    <Wrapper
      href={item.href}
      onClick={item.onClick}
      className={cn(
        'flex items-center gap-3 px-2 h-9 rounded-md text-sm transition-colors w-full',
        item.active
          ? 'bg-[var(--muhide-orange)]/20 text-[var(--muhide-orange)] font-medium'
          : 'text-white/60 hover:text-white hover:bg-white/10',
        collapsed && 'justify-center px-0'
      )}
      title={collapsed ? item.label : undefined}
      aria-current={item.active ? 'page' as const : undefined}
    >
      <span className="flex-shrink-0 w-[18px] h-[18px] flex items-center justify-center" aria-hidden="true">{item.icon}</span>
      {!collapsed && (
        <>
          <span className="flex-1 truncate text-left">{item.label}</span>
          {item.badge && (
            <span className="flex-shrink-0 px-1.5 py-0.5 text-[10px] font-medium rounded-full bg-[var(--muhide-orange)]/20 text-[var(--muhide-orange)]">
              {item.badge}
            </span>
          )}
        </>
      )}
    </Wrapper>
  )
}
