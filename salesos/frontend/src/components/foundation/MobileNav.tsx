"use client"

import { useEffect, useCallback, useState } from "react"
import Link from "next/link"
import { usePathname } from "next/navigation"
import { cn } from "@salesos/ui"
import { Menu, X, LayoutDashboard, Building2, Users, DollarSign, Search, Settings, Workflow, MessageSquareText, Activity, Shield, User } from "lucide-react"

const navItems = [
  { href: "/dashboard", label: "لوحة المعلومات", icon: LayoutDashboard },
  { href: "/companies", label: "الشركات", icon: Building2 },
  { href: "/contacts", label: "جهات الاتصال", icon: Users },
  { href: "/opportunities", label: "الفرص", icon: DollarSign },
  { href: "/search", label: "البحث", icon: Search },
  { href: "/automation", label: "الأتمتة", icon: Workflow },
  { href: "/rag", label: "المساعد الذكي", icon: MessageSquareText },
  { href: "/monitoring", label: "المراقبة", icon: Activity },
  { href: "/settings", label: "الإعدادات", icon: Settings },
  { href: "/admin", label: "الإدارة", icon: Shield },
]

export function MobileNav() {
  const [open, setOpen] = useState(false)
  const pathname = usePathname()

  const close = useCallback(() => setOpen(false), [])

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

  return (
    <>
      <button
        onClick={() => setOpen(true)}
        className="fixed bottom-4 right-4 z-30 flex h-12 w-12 items-center justify-center rounded-full bg-[var(--muhide-orange)] text-white shadow-muhide-4 md:hidden"
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
            className="absolute left-0 top-0 bottom-0 w-72 max-w-[80vw] bg-[var(--bg-primary)] shadow-muhide-6 animate-slide-in-right overflow-y-auto"
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
                    <span>{item.label}</span>
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
