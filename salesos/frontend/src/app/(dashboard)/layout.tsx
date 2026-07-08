"use client"

import { useState, useEffect, useCallback, type ReactNode } from "react"
import Link from "next/link"
import { usePathname, useRouter } from "next/navigation"
import { Layout, LayoutSidebar, LayoutContent, LayoutHeader, cn } from "@salesos/ui"
import { Building2, Users, DollarSign, Search, Settings, LayoutDashboard, Bell, Menu, Bot, User, Shield } from "lucide-react"
import { CommandBar } from "@/components/command-bar"
import { SearchPanel } from "@/components/search-panel"
import { CopilotPanel } from "@/components/copilot-panel"
import { useTheme } from "@salesos/hooks"
import { registerBuiltinCommands } from "@/lib/commands"

const navItems = [
  { href: "/dashboard", label: "لوحة المعلومات", icon: LayoutDashboard },
  { href: "/companies", label: "الشركات", icon: Building2 },
  { href: "/employees/me", label: "ملفي", icon: User },
  { href: "/contacts", label: "جهات الاتصال", icon: Users },
  { href: "/opportunities", label: "الفرص", icon: DollarSign },
  { href: "/search", label: "البحث", icon: Search },
  { href: "/settings", icon: Settings },
  { href: "/admin", label: "الإدارة", icon: Shield },
]

export default function DashboardLayout({ children }: { children: ReactNode }) {
  const pathname = usePathname()
  const router = useRouter()
  const [collapsed, setCollapsed] = useState(false)
  const [commandOpen, setCommandOpen] = useState(false)
  const [searchOpen, setSearchOpen] = useState(false)
  const [copilotOpen, setCopilotOpen] = useState(false)
  const { toggle: toggleTheme } = useTheme()

  useEffect(() => {
    registerBuiltinCommands(router)
  }, [router])

  useEffect(() => {
    const onKeyDown = (e: KeyboardEvent) => {
      if ((e.metaKey || e.ctrlKey) && e.key === "k") {
        e.preventDefault()
        setCommandOpen(true)
      }
    }
    window.addEventListener("keydown", onKeyDown)
    return () => window.removeEventListener("keydown", onKeyDown)
  }, [])

  useEffect(() => {
    const toggleCopilot = () => setCopilotOpen((v) => !v)
    const toggleSearch = () => setSearchOpen((v) => !v)
    window.addEventListener("salesos:toggle-copilot", toggleCopilot)
    window.addEventListener("salesos:toggle-search", toggleSearch)
    window.addEventListener("salesos:toggle-theme", toggleTheme)
    return () => {
      window.removeEventListener("salesos:toggle-copilot", toggleCopilot)
      window.removeEventListener("salesos:toggle-search", toggleSearch)
      window.removeEventListener("salesos:toggle-theme", toggleTheme)
    }
  }, [toggleTheme])

  return (
    <Layout>
      <LayoutHeader>
        <button onClick={() => setCollapsed(!collapsed)} className="rounded-lg p-1.5 hover:bg-gray-100 dark:hover:bg-gray-800">
          <Menu className="h-5 w-5" />
        </button>
        <div className="flex-1" />
        <button
          onClick={() => setCommandOpen(true)}
          className="hidden md:flex items-center gap-2 rounded-lg border border-gray-300 px-3 py-1.5 text-sm text-gray-500 dark:border-gray-600 dark:text-gray-400"
        >
          <Search className="h-4 w-4" />
          <span>البحث السريع...</span>
          <kbd className="mr-auto rounded border border-gray-300 px-1.5 py-0.5 text-[10px] dark:border-gray-600">⌘K</kbd>
        </button>
        <button
          onClick={() => setCopilotOpen(!copilotOpen)}
          className="rounded-lg p-1.5 hover:bg-gray-100 dark:hover:bg-gray-800"
        >
          <Bot className="h-5 w-5" />
        </button>
        <button className="rounded-lg p-1.5 hover:bg-gray-100 dark:hover:bg-gray-800">
          <Bell className="h-5 w-5" />
        </button>
      </LayoutHeader>
      <div className="flex flex-1 overflow-hidden">
        <LayoutSidebar>
          <aside
            className={cn(
              "flex h-full flex-col border-l bg-white transition-all dark:border-gray-700 dark:bg-gray-900",
              collapsed ? "w-16" : "w-64"
            )}
          >
            <div
              className={cn(
                "flex h-14 items-center border-b px-4 dark:border-gray-700",
                collapsed && "justify-center px-0"
              )}
            >
              {!collapsed && <span className="text-lg font-bold">SalesOS</span>}
            </div>
            <nav className="flex-1 space-y-1 p-2">
              {navItems.map((item) => {
                const Icon = item.icon
                const active = pathname.startsWith(item.href)
                return (
                  <Link
                    key={item.href}
                    href={item.href}
                    className={cn(
                      "flex items-center gap-3 rounded-lg px-3 py-2 text-sm transition",
                      active
                        ? "bg-blue-50 text-blue-700 dark:bg-blue-900/50 dark:text-blue-300"
                        : "text-gray-700 hover:bg-gray-100 dark:text-gray-300 dark:hover:bg-gray-800",
                      collapsed && "justify-center px-2"
                    )}
                    title={collapsed ? item.label : undefined}
                  >
                    <Icon className="h-5 w-5 shrink-0" />
                    {!collapsed && <span>{item.label}</span>}
                  </Link>
                )
              })}
            </nav>
          </aside>
        </LayoutSidebar>
        <LayoutContent>{children}</LayoutContent>
      </div>
      <CommandBar open={commandOpen} onClose={() => setCommandOpen(false)} />
      <SearchPanel open={searchOpen} onClose={() => setSearchOpen(false)} />
      <CopilotPanel open={copilotOpen} onClose={() => setCopilotOpen(false)} entityType="company" />
    </Layout>
  )
}
