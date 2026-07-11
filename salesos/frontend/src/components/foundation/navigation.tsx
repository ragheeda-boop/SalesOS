import { cn } from "@salesos/ui"

interface NavItem {
  id: string
  label: string
  icon?: React.ReactNode
  href?: string
  badge?: number | string
  active?: boolean
  disabled?: boolean
  onClick?: () => void
}

interface NavSection {
  id: string
  label?: string
  items: NavItem[]
}

interface NavigationProps {
  sections: NavSection[]
  orientation?: 'vertical' | 'horizontal'
  size?: 'sm' | 'md' | 'lg'
  variant?: 'default' | 'pills' | 'tabs'
  className?: string
}

const SIZE_MAP = {
  sm: 'text-xs h-7 px-2',
  md: 'text-sm h-9 px-3',
  lg: 'text-base h-10 px-4',
}

const VARIANT_MAP = {
  default: {
    base: 'rounded-md transition-colors',
    active: 'bg-[var(--muhide-orange)]/10 text-[var(--muhide-orange)] font-medium',
    inactive: 'text-[var(--text-muted)] hover:text-[var(--text-primary)] hover:bg-[var(--bg-secondary)]',
    disabled: 'opacity-40 cursor-not-allowed pointer-events-none',
  },
  pills: {
    base: 'rounded-full transition-colors',
    active: 'bg-[var(--muhide-orange)] text-white font-medium',
    inactive: 'text-[var(--text-muted)] hover:text-[var(--text-primary)] hover:bg-[var(--bg-secondary)]',
    disabled: 'opacity-40 cursor-not-allowed pointer-events-none',
  },
  tabs: {
    base: 'rounded-none border-b-2 border-transparent transition-colors',
    active: 'text-[var(--muhide-orange)] border-b-[var(--muhide-orange)] font-medium',
    inactive: 'text-[var(--text-muted)] hover:text-[var(--text-primary)] border-b-transparent hover:border-b-[var(--border-default)]',
    disabled: 'opacity-40 cursor-not-allowed pointer-events-none',
  },
}

export function Navigation({ sections, orientation = 'vertical', size = 'md', variant = 'default', className }: NavigationProps) {
  const styles = VARIANT_MAP[variant]

  return (
    <nav aria-label="Main navigation" className={cn(
      orientation === 'vertical' ? 'flex flex-col' : 'flex items-center',
      orientation === 'vertical' ? 'space-y-1' : 'space-x-1',
      className
    )}>
      {sections.map((section) => (
        <div key={section.id} className={cn(
          orientation === 'vertical' ? 'flex flex-col' : 'flex items-center',
          orientation === 'vertical' && section.label ? 'space-y-0.5' : '',
        )}>
          {section.label && orientation === 'vertical' && (
            <div className="px-2 py-1">
              <span className="text-[10px] font-medium text-[var(--text-muted)] uppercase tracking-wider">{section.label}</span>
            </div>
          )}
          <div className={cn(
            orientation === 'vertical' ? 'flex flex-col space-y-0.5' : 'flex items-center space-x-0.5',
          )} role="list">
            {section.items.map((item) => (
              <NavigationItem key={item.id} item={item} size={size} styles={styles} orientation={orientation} />
            ))}
          </div>
        </div>
      ))}
    </nav>
  )
}

interface NavigationItemProps {
  item: NavItem
  size: 'sm' | 'md' | 'lg'
  styles: typeof VARIANT_MAP.default
  orientation: 'vertical' | 'horizontal'
}

function NavigationItem({ item, size, styles, orientation }: NavigationItemProps) {
  const Wrapper = item.href ? 'a' : 'button'

  return (
    <Wrapper
      href={item.disabled ? undefined : item.href}
      onClick={item.disabled ? undefined : item.onClick}
      className={cn(
        'flex items-center gap-2 whitespace-nowrap',
        SIZE_MAP[size],
        styles.base,
        item.active ? styles.active : item.disabled ? styles.disabled : styles.inactive,
        orientation === 'vertical' ? 'w-full' : '',
      )}
      aria-disabled={item.disabled}
      aria-current={item.active ? 'page' as const : undefined}
      tabIndex={item.disabled ? -1 : 0}
      role="listitem"
    >
      {item.icon && (
        <span className="flex-shrink-0 w-4 h-4 flex items-center justify-center" aria-hidden="true">{item.icon}</span>
      )}
      <span className="flex-1 truncate text-left">{item.label}</span>
      {item.badge && (
        <span className={cn(
          'flex-shrink-0 px-1.5 py-0.5 text-[10px] font-medium rounded-full',
          item.active
            ? 'bg-[var(--muhide-orange)]/20 text-[var(--muhide-orange)]'
            : 'bg-[var(--bg-secondary)] text-[var(--text-muted)]',
        )}>
          {item.badge}
        </span>
      )}
    </Wrapper>
  )
}
