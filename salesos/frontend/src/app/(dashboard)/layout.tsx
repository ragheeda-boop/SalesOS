"use client"

import React, { useEffect, useCallback, useState, type ReactNode } from "react"
import Link from "next/link"
import { usePathname, useRouter } from "next/navigation"
import { cn } from "@salesos/ui"
import { AppShell, useAppShell } from "@/components/foundation/app-shell"
import { Building2, Users, DollarSign, Search, Settings, LayoutDashboard, Bell, Menu, Bot, User, Shield, Workflow, MessageSquareText, Activity, HeartHandshake, X } from "lucide-react"
import { CommandBar } from "@/components/command-bar"
import { SearchPanel } from "@/components/search-panel"
import { CopilotPanel } from "@/components/copilot-panel"
import { MobileNav } from "@/components/foundation/MobileNav"
import { useTheme } from "@salesos/hooks"
import { registerBuiltinCommands } from "@/lib/commands"
import { useTranslation } from "@/lib/i18n"
import { LanguageSwitcher } from "@/components/foundation/LanguageSwitcher"

const NAV_KEYS = [
  { href: "/dashboard", key: "nav.dashboard", icon: LayoutDashboard },
  { href: "/companies", key: "nav.companies", icon: Building2 },
  { href: "/employees/me", key: "nav.profile", icon: User },
  { href: "/contacts", key: "nav.contacts", icon: Users },
  { href: "/opportunities", key: "nav.opportunities", icon: DollarSign },
  { href: "/search", key: "nav.search", icon: Search },
  { href: "/automation", key: "nav.workflows", icon: Workflow },
  { href: "/rag", key: "nav.rag", icon: MessageSquareText },
  { href: "/monitoring", key: "nav.monitoring", icon: Activity },
  { href: "/settings", key: "nav.settings", icon: Settings },
  { href: "/customer-success", key: "nav.customer_success", icon: HeartHandshake },
  { href: "/admin", key: "nav.admin", icon: Shield },
]

function DashboardContent({ children }: { children: ReactNode }) {
  const pathname = usePathname()
  const router = useRouter()
  const { sidebarCollapsed, setSidebarCollapsed, commandOpen, setCommandOpen } = useAppShell()
  const [searchOpen, setSearchOpen] = React.useState(false)
  const [copilotOpen, setCopilotOpen] = React.useState(false)
  const [mobileSidebarOpen, setMobileSidebarOpen] = useState(false)
  const { toggle: toggleTheme } = useTheme()
  const { t } = useTranslation()

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

  useEffect(() => {
    if (mobileSidebarOpen) {
      document.body.style.overflow = "hidden"
    } else {
      document.body.style.overflow = ""
    }
    return () => { document.body.style.overflow = "" }
  }, [mobileSidebarOpen])

  const closeMobileSidebar = useCallback(() => setMobileSidebarOpen(false), [])

  useEffect(() => { closeMobileSidebar() }, [pathname, closeMobileSidebar])

  return (
    <>
      <header className="flex items-center h-14 px-3 sm:px-4 bg-white border-b border-[var(--border-default)] dark:bg-neutral-900 dark:border-neutral-700 flex-shrink-0">
        <button
          onClick={() => setMobileSidebarOpen(true)}
          className="md:hidden rounded-lg p-2 hover:bg-neutral-100 dark:hover:bg-neutral-800 min-h-[44px] min-w-[44px] flex items-center justify-center"
          aria-label="فتح القائمة الجانبية"
        >
          <Menu className="h-5 w-5" />
        </button>
        <button
          onClick={() => setSidebarCollapsed(!sidebarCollapsed)}
          className="hidden md:flex rounded-lg p-1.5 hover:bg-neutral-100 dark:hover:bg-neutral-800"
          aria-label={sidebarCollapsed ? "توسيع القائمة" : "طي القائمة"}
        >
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
          className="rounded-lg p-1.5 hover:bg-neutral-100 dark:hover:bg-neutral-800 min-h-[44px] min-w-[44px] flex items-center justify-center"
          aria-label="فتح المساعد الذكي"
        >
          <Bot className="h-5 w-5" />
        </button>
        <button className="rounded-lg p-1.5 hover:bg-neutral-100 dark:hover:bg-neutral-800 min-h-[44px] min-w-[44px] flex items-center justify-center" aria-label="الإشعارات">
          <Bell className="h-5 w-5" />
        </button>
        <LanguageSwitcher />
      </header>

      {mobileSidebarOpen && (
        <div className="fixed inset-0 z-40 md:hidden">
          <div className="absolute inset-0 bg-black/60" onClick={closeMobileSidebar} aria-hidden="true" />
          <aside className="absolute left-0 top-0 bottom-0 w-72 max-w-[80vw] bg-white dark:bg-neutral-900 shadow-muhide-6 overflow-y-auto animate-slide-in-left">
            <div className="flex items-center justify-between border-b border-neutral-200 dark:border-neutral-700 px-4 h-14">
              <span className="text-lg font-bold text-neutral-900 dark:text-neutral-100">SalesOS</span>
              <button
                onClick={closeMobileSidebar}
                className="rounded-lg p-2 hover:bg-neutral-100 dark:hover:bg-neutral-800 min-h-[44px] min-w-[44px] flex items-center justify-center"
                aria-label="إغلاق القائمة"
              >
                <X className="h-5 w-5" />
              </button>
            </div>
            <nav className="p-3 space-y-1">
              {NAV_KEYS.map((item) => {
                const Icon = item.icon
                const active = pathname.startsWith(item.href)
                const label = t(item.key)
                return (
                  <Link
                    key={item.href}
                    href={item.href}
                    className={cn(
                      "flex items-center gap-3 rounded-lg px-3 py-3 text-sm transition min-h-[44px]",
                      active
                        ? "bg-[var(--muhide-orange)]/10 text-[var(--muhide-orange)] dark:bg-[var(--muhide-orange)]/20 dark:text-orange-300 font-medium"
                        : "text-neutral-700 hover:bg-neutral-100 dark:text-neutral-300 dark:hover:bg-neutral-800"
                    )}
                  >
                    <Icon className="h-5 w-5 shrink-0" />
                    <span>{label}</span>
                  </Link>
                )
              })}
            </nav>
          </aside>
        </div>
      )}

      <div className="flex flex-1 overflow-hidden">
        <aside
          className={cn(
            "hidden md:flex h-full flex-col border-l bg-white transition-all dark:border-neutral-700 dark:bg-neutral-900",
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
            {NAV_KEYS.map((item) => {
              const Icon = item.icon
              const active = pathname.startsWith(item.href)
              const label = t(item.key)
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
                  title={sidebarCollapsed ? label : undefined}
                >
                  <Icon className="h-5 w-5 shrink-0" />
                  {!sidebarCollapsed && <span>{label}</span>}
                </Link>
              )
            })}
          </nav>
        </aside>
        <main className="flex-1 overflow-auto p-3 sm:p-4 lg:p-6">{children}</main>
      </div>
      <MobileNav />
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
