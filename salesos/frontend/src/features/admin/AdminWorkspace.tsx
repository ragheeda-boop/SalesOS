"use client"

import { useState } from "react"
import { cn } from "@salesos/ui"
import {
  LayoutDashboard, Building2, KeyRound, Users, Flag, Briefcase, DollarSign, HeartPulse,
} from "lucide-react"
import { useAdminTenants, useAdminPlans, useAdminUsers, useAdminDetailedHealth } from "@/lib/hooks/adminQueries"
import { TenantList } from "./widgets/TenantList"
import { PlanManager } from "./widgets/PlanManager"
import { UserList } from "./widgets/UserList"
import { FeatureFlagManager } from "./widgets/FeatureFlagManager"
import { JobList } from "./widgets/JobList"
import { AICostDashboard } from "./widgets/AICostDashboard"
import { HealthDashboard } from "./widgets/HealthDashboard"

type AdminTab = "overview" | "tenants" | "plans" | "users" | "flags" | "jobs" | "ai-costs" | "health"

const TABS: { id: AdminTab; label: string; icon: React.ElementType }[] = [
  { id: "overview", label: "الرئيسية", icon: LayoutDashboard },
  { id: "tenants", label: "العملاء", icon: Building2 },
  { id: "plans", label: "الباقات والتراخيص", icon: KeyRound },
  { id: "users", label: "المستخدمين", icon: Users },
  { id: "flags", label: "الميزات", icon: Flag },
  { id: "jobs", label: "الوظائف", icon: Briefcase },
  { id: "ai-costs", label: "تكاليف AI", icon: DollarSign },
  { id: "health", label: "صحة النظام", icon: HeartPulse },
]

export function AdminWorkspace() {
  const [activeTab, setActiveTab] = useState<AdminTab>("overview")

  const renderContent = () => {
    switch (activeTab) {
      case "overview": return <AdminOverview onNavigate={setActiveTab} />
      case "tenants": return <TenantList />
      case "plans": return <PlanManager />
      case "users": return <UserList />
      case "flags": return <FeatureFlagManager />
      case "jobs": return <JobList />
      case "ai-costs": return <AICostDashboard />
      case "health": return <HealthDashboard />
    }
  }

  return (
    <div className="flex flex-1 h-full overflow-hidden">
      <aside className="w-56 flex-shrink-0 border-l bg-white dark:bg-neutral-900 dark:border-neutral-700 overflow-y-auto">
        <nav className="p-2 space-y-1">
          {TABS.map((tab) => {
            const Icon = tab.icon
            const active = activeTab === tab.id
            return (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={cn(
                  "w-full flex items-center gap-3 rounded-lg px-3 py-2.5 text-sm text-right transition min-h-[44px]",
                  active
                    ? "bg-[var(--muhide-orange)]/10 text-[var(--muhide-orange)] dark:bg-[var(--muhide-orange)]/20 font-medium"
                    : "text-neutral-700 hover:bg-neutral-100 dark:text-neutral-300 dark:hover:bg-neutral-800"
                )}
              >
                <Icon className="h-5 w-5 shrink-0" />
                <span>{tab.label}</span>
              </button>
            )
          })}
        </nav>
      </aside>
      <main className="flex-1 overflow-y-auto p-6">
        {renderContent()}
      </main>
    </div>
  )
}

function AdminOverview({ onNavigate }: { onNavigate: (tab: AdminTab) => void }) {
  const { data: tenants } = useAdminTenants()
  const { data: plans } = useAdminPlans()
  const { data: users } = useAdminUsers()
  const { data: health } = useAdminDetailedHealth()

  const totalTenants = tenants?.length || 0
  const activeTenants = tenants?.filter((t: { is_active: boolean }) => t.is_active).length || 0
  const totalUsers = users?.length || 0
  const totalPlans = plans?.length || 0
  const healthStatus = health?.overall_status || "unknown"

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold">لوحة الإدارة</h1>
      <p className="text-neutral-500">نظرة عامة على حالة المنصة وجميع العملاء</p>

      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <OverviewCard
          label="إجمالي العملاء"
          value={totalTenants}
          sub={`${activeTenants} نشط`}
          icon={Building2}
          onClick={() => onNavigate("tenants")}
        />
        <OverviewCard
          label="الباقات"
          value={totalPlans}
          sub="خطة تسعير"
          icon={KeyRound}
          onClick={() => onNavigate("plans")}
        />
        <OverviewCard
          label="المستخدمين"
          value={totalUsers}
          sub="عبر جميع العملاء"
          icon={Users}
          onClick={() => onNavigate("users")}
        />
        <OverviewCard
          label="صحة النظام"
          value={healthStatus === "healthy" ? "سليم" : healthStatus === "degraded" ? "متراجع" : "غير معروف"}
          sub={healthStatus === "healthy" ? "جميع الخدمات تعمل" : "يوجد خلل"}
          icon={HeartPulse}
          status={healthStatus === "healthy" ? "ok" : "warning"}
          onClick={() => onNavigate("health")}
        />
      </div>

      <QuickActions onNavigate={onNavigate} />
    </div>
  )
}

function OverviewCard({
  label, value, sub, icon: Icon, onClick, status,
}: {
  label: string; value: string | number; sub: string; icon: React.ElementType; onClick: () => void; status?: "ok" | "warning"
}) {
  return (
    <button
      onClick={onClick}
      className="text-right rounded-xl border border-neutral-200 dark:border-neutral-700 bg-white dark:bg-neutral-900 p-4 hover:shadow-md transition-shadow"
    >
      <div className="flex items-center justify-between mb-3">
        <Icon className={cn("h-5 w-5", status === "warning" ? "text-amber-500" : "text-[var(--muhide-orange)]")} />
        {status === "warning" && <span className="h-2 w-2 rounded-full bg-amber-500 animate-pulse" />}
      </div>
      <p className="text-2xl font-bold">{value}</p>
      <p className="text-sm text-neutral-500 mt-1">{label}</p>
      <p className="text-xs text-neutral-400 mt-0.5">{sub}</p>
    </button>
  )
}

function QuickActions({ onNavigate }: { onNavigate: (tab: AdminTab) => void }) {
  const actions = [
    { label: "إدارة العملاء", desc: "عرض وإضافة وتعليق العملاء", tab: "tenants" as AdminTab, icon: Building2 },
    { label: "إدارة الباقات", desc: "إنشاء وتعديل خطط التسعير", tab: "plans" as AdminTab, icon: KeyRound },
    { label: "المستخدمين", desc: "إدارة مستخدمي المنصة", tab: "users" as AdminTab, icon: Users },
    { label: "الميزات التجريبية", desc: "تفعيل الميزات لكل عميل", tab: "flags" as AdminTab, icon: Flag },
    { label: "الوظائف الخلفية", desc: "مراقبة وإعادة تشغيل الوظائف", tab: "jobs" as AdminTab, icon: Briefcase },
    { label: "صحة النظام", desc: "مراقبة حالة الخدمات", tab: "health" as AdminTab, icon: HeartPulse },
  ]

  return (
    <div>
      <h2 className="text-lg font-semibold mb-3">إجراءات سريعة</h2>
      <div className="grid grid-cols-2 md:grid-cols-3 gap-3">
        {actions.map((a) => {
          const Icon = a.icon
          return (
            <button
              key={a.tab}
              onClick={() => onNavigate(a.tab)}
              className="text-right flex items-center gap-3 rounded-lg border border-neutral-200 dark:border-neutral-700 bg-white dark:bg-neutral-900 p-3 hover:bg-neutral-50 dark:hover:bg-neutral-800 transition"
            >
              <div className="rounded-lg p-2 bg-[var(--muhide-orange)]/10 text-[var(--muhide-orange)]">
                <Icon className="h-5 w-5" />
              </div>
              <div>
                <p className="font-medium text-sm">{a.label}</p>
                <p className="text-xs text-neutral-500">{a.desc}</p>
              </div>
            </button>
          )
        })}
      </div>
    </div>
  )
}
