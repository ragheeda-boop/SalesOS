"use client"

import React, { useEffect, useCallback, type ReactNode } from "react"
import Link from "next/link"
import { usePathname, useRouter } from "next/navigation"
import { cn } from "@salesos/ui"
import { AppShell, useAppShell } from "@/components/foundation/app-shell"
import { Building2, Users, DollarSign, Search, Settings, LayoutDashboard, Bell, Menu, Bot, User, Shield, Workflow, MessageSquareText, Activity } from "lucide-react"
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
  { href: "/automation", label: "الأتمتة", icon: Workflow },
  { href: "/rag", label: "المساعد الذكي", icon: MessageSquareText },
  { href: "/monitoring", label: "المراقبة", icon: Activity },
  { href: "/settings", icon: Settings },
  { href: "/admin", label: "الإدارة", icon: Shield },
]

function DashboardContent({ children }: { children: ReactNode }) {
  const pathname = usePathname()
  const router = useRouter()
  const { sidebarCollapsed, setSidebarCollapsed, commandOpen, setCommandOpen } = useAppShell()
  const [searchOpen, setSearchOpen] = React.useState(false)
  const [copilotOpen, setCopilotOpen] = React.useState(false)
  const { toggle: toggleTheme } = useTheme()

  useEffect(() => {
    registerBuiltinCommands(router)
  }, [router])

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
    <>
      <header className="flex items-center h-14 px-4 bg-white border-b border-[var(--border-default)] dark:bg-neutral-900 dark:border-neutral-700 flex-shrink-0">
        <button onClick={() => setSidebarCollapsed(!sidebarCollapsed)} className="rounded-lg p-1.5 hover:bg-neutral-100 dark:hover:bg-neutral-800">
          <Menu className="h-5 w-5" />
        </button>
        <div className="flex-1" />
        <button
          onClick={() => setCommandOpen(true)}
          className="hidden md:flex items-center gap-2 rounded-lg border border-neutral-300 px-3 py-1.5 text-sm text-neutral-500 dark:border-neutral-600 dark:text-neutral-400"
        >
          <Search className="h-4 w-4" />
          <span>البحث السريع...</span>
          <kbd className="mr-auto rounded border border-neutral-300 px-1.5 py-0.5 text-[10px] dark:border-neutral-600">⌘K</kbd>
        </button>
        <button
          onClick={() => setCopilotOpen(!copilotOpen)}
          className="rounded-lg p-1.5 hover:bg-neutral-100 dark:hover:bg-neutral-800"
        >
          <Bot className="h-5 w-5" />
        </button>
        <button className="rounded-lg p-1.5 hover:bg-neutral-100 dark:hover:bg-neutral-800">
          <Bell className="h-5 w-5" />
        </button>
      </header>
      <div className="flex flex-1 overflow-hidden">
        <aside
          className={cn(
            "flex h-full flex-col border-l bg-white transition-all dark:border-neutral-700 dark:bg-neutral-900",
            sidebarCollapsed ? "w-16" : "w-64"
          )}
        >
          <div
            className={cn(
              "flex h-14 items-center border-b px-4 dark:border-neutral-700",
              sidebarCollapsed && "justify-center px-0"
            )}
          >
            {!sidebarCollapsed && <span className="text-lg font-bold">SalesOS</span>}
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
                      ? "bg-[var(--muhide-orange)]/10 text-[var(--muhide-orange)] dark:bg-[var(--muhide-orange)]/20 dark:text-orange-300"
                      : "text-neutral-700 hover:bg-neutral-100 dark:text-neutral-300 dark:hover:bg-neutral-800",
                    sidebarCollapsed && "justify-center px-2"
                  )}
                  title={sidebarCollapsed ? item.label : undefined}
                >
                  <Icon className="h-5 w-5 shrink-0" />
                  {!sidebarCollapsed && <span>{item.label}</span>}
                </Link>
              )
            })}
          </nav>
        </aside>
        <main className="flex-1 overflow-auto p-6">{children}</main>
      </div>
      <CommandBar open={commandOpen} onClose={() => setCommandOpen(false)} />
      <SearchPanel open={searchOpen} onClose={() => setSearchOpen(false)} />
      <CopilotPanel open={copilotOpen} onClose={() => setCopilotOpen(false)} entityType="company" />
    </>
  )
}

export default function DashboardLayout({ children }: { children: ReactNode }) {
  return (
    <AppShell>
      <DashboardContent>{children}</DashboardContent>
    </AppShell>
  )
}
