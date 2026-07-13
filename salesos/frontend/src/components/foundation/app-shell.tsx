import { cn } from "@salesos/ui"
import { useState, createContext, useContext, useEffect, useCallback, useRef } from "react"
import { usePathname } from "next/navigation"

interface SidebarSection {
  id: string
  label: string
  items: NavItem[]
}

interface NavItem {
  id: string
  label: string
  icon: React.ReactNode
  href?: string
  badge?: number | string
  active?: boolean
  onClick?: () => void
}

interface AppShellContextType {
  sidebarCollapsed: boolean
  setSidebarCollapsed: (v: boolean) => void
  commandOpen: boolean
  setCommandOpen: (v: boolean) => void
}

const AppShellContext = createContext<AppShellContextType>({
  sidebarCollapsed: false,
  setSidebarCollapsed: () => {},
  commandOpen: false,
  setCommandOpen: () => {},
})

export function useAppShell() {
  return useContext(AppShellContext)
}

function RouteAnnouncer() {
  const pathname = usePathname()
  const isFirst = useRef(true)
  useEffect(() => {
    if (isFirst.current) { isFirst.current = false; return }
    const announcement = `Navigated to ${pathname}`
    const el = document.getElementById("route-announcer")
    if (el) el.textContent = announcement
  }, [pathname])
  return (
    <div id="route-announcer" aria-live="assertive" aria-atomic="true" className="sr-only" role="alert" />
  )
}

interface AppShellProps {
  children: React.ReactNode
  defaultSidebarCollapsed?: boolean
}

export function AppShell({ children, defaultSidebarCollapsed = false }: AppShellProps) {
  const [sidebarCollapsed, setSidebarCollapsed] = useState(defaultSidebarCollapsed)
  const [commandOpen, setCommandOpen] = useState(false)

  const handleKeyDown = useCallback((e: KeyboardEvent) => {
    if ((e.metaKey || e.ctrlKey) && e.key === "k") {
      e.preventDefault()
      setCommandOpen((prev) => !prev)
    }
    if (e.key === "Escape" && commandOpen) {
      setCommandOpen(false)
    }
  }, [commandOpen])

  useEffect(() => {
    document.addEventListener("keydown", handleKeyDown)
    return () => document.removeEventListener("keydown", handleKeyDown)
  }, [handleKeyDown])

  return (
    <AppShellContext.Provider value={{ sidebarCollapsed, setSidebarCollapsed, commandOpen, setCommandOpen }}>
        <div className="flex h-screen overflow-hidden bg-[var(--bg-primary)] text-[var(--text-primary)]" aria-label="Application shell">
        <RouteAnnouncer />
        <div aria-live="polite" aria-atomic="true" className="sr-only" role="status">
          {commandOpen ? 'Command palette opened. Press Escape to close.' : ''}
        </div>
        <span className="sr-only">Press Ctrl+K or Cmd+K to open the command palette</span>
        {children}
      </div>
    </AppShellContext.Provider>
  )
}
