"use client"

import { useEffect, useCallback, useState } from "react"
import Link from "next/link"
import { usePathname } from "next/navigation"
import { cn } from "@salesos/ui"
import { Menu, X, LayoutDashboard, Building2, Users, DollarSign, Search, Settings, Workflow, MessageSquareText, Activity, Shield, User } from "lucide-react"
import { useTranslation } from "@/lib/i18n"

export function MobileNav() {
  const [open, setOpen] = useState(false)
  const pathname = usePathname()
  const { t, dir } = useTranslation()

  const close = useCallback(() => setOpen(false), [])

  const navItems = [
    { href: "/dashboard", key: "nav.dashboard", icon: LayoutDashboard },
    { href: "/companies", key: "nav.companies", icon: Building2 },
    { href: "/contacts", key: "nav.contacts", icon: Users },
    { href: "/opportunities", key: "nav.opportunities", icon: DollarSign },
    { href: "/search", key: "nav.search", icon: Search },
    { href: "/automation", key: "nav.workflows", icon: Workflow },
    { href: "/rag", key: "nav.rag", icon: MessageSquareText },
    { href: "/monitoring", key: "nav.monitoring", icon: Activity },
    { href: "/settings", key: "nav.settings", icon: Settings },
    { href: "/admin", key: "nav.admin", icon: Shield },
  ]

  useEffect(() => {
    const handleEscape = (e: KeyboardEvent) => {
      if (e.key === "Escape") close()
    }
    if (open) {
      document.addEventListener("keydown", handleEscape)
      document.body.style.overflow = "hidden"
    }
    return () => {
      document.removeEventListener("keydown", handleEscape)
      document.body.style.overflow = ""
    }
  }, [open, close])

  useEffect(() => { close() }, [pathname, close])

  const slideAnim = dir === "rtl" ? "animate-slide-in-right" : "animate-slide-in-left"
  const fabPosition = dir === "rtl" ? "start-4" : "end-4"

  return (
    <>
      <button
        onClick={() => setOpen(true)}
        className={cn(
          "fixed bottom-4 z-30 flex h-12 w-12 items-center justify-center rounded-full bg-[var(--muhide-orange)] text-white shadow-muhide-4 md:hidden",
          fabPosition
        )}
        aria-label="فتح القائمة"
        aria-expanded={open}
      >
        <Menu className="h-6 w-6" />
      </button>

      {open && (
        <div className="fixed inset-0 z-40 md:hidden">
          <div
            className="absolute inset-0 bg-black/60 backdrop-blur-sm"
            onClick={close}
            aria-hidden="true"
          />
          <aside
            className={cn(
              "absolute top-0 bottom-0 w-72 max-w-[80vw] bg-[var(--bg-primary)] shadow-muhide-6 overflow-y-auto",
              "start-0",
              slideAnim
            )}
            role="dialog"
            aria-modal="true"
            aria-label="قائمة التنقل"
          >
            <div className="flex items-center justify-between border-b border-[var(--border-default)] px-4 h-14">
              <span className="text-lg font-bold text-[var(--text-primary)]">SalesOS</span>
              <button
                onClick={close}
                className="rounded-lg p-1.5 hover:bg-[var(--bg-secondary)]"
                aria-label="إغلاق القائمة"
              >
                <X className="h-5 w-5" />
              </button>
            </div>
            <nav className="p-3 space-y-1">
              {navItems.map((item) => {
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
                        ? "bg-[var(--muhide-orange)]/10 text-[var(--muhide-orange)] font-medium"
                        : "text-[var(--text-secondary)] hover:bg-[var(--bg-secondary)] hover:text-[var(--text-primary)]"
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

    </>
  )
}
