"use client"

import { useState } from"react"
import { cn } from"@salesos/ui"
import {
 LayoutDashboard, Building2, KeyRound, Users, Flag, Briefcase, DollarSign, HeartPulse,
} from"lucide-react"
import { useAdminTenants, useAdminPlans, useAdminUsers, useAdminDetailedHealth } from"@/lib/hooks/adminQueries"
import { useTranslation } from"@/lib/i18n"
import { TenantList } from"./widgets/TenantList"
import { PlanManager } from"./widgets/PlanManager"
import { UserList } from"./widgets/UserList"
import { FeatureFlagManager } from"./widgets/FeatureFlagManager"
import { JobList } from"./widgets/JobList"
import { AICostDashboard } from"./widgets/AICostDashboard"
import { HealthDashboard } from"./widgets/HealthDashboard"

type AdminTab ="overview" |"tenants" |"plans" |"users" |"flags" |"jobs" |"ai-costs" |"health"

const TABS: { id: AdminTab; labelKey: string; icon: React.ElementType }[] = [
 { id:"overview", labelKey:"admin.tab.overview", icon: LayoutDashboard },
 { id:"tenants", labelKey:"admin.tab.tenants", icon: Building2 },
 { id:"plans", labelKey:"admin.tab.plans", icon: KeyRound },
 { id:"users", labelKey:"admin.tab.users", icon: Users },
 { id:"flags", labelKey:"admin.tab.flags", icon: Flag },
 { id:"jobs", labelKey:"admin.tab.jobs", icon: Briefcase },
 { id:"ai-costs", labelKey:"admin.tab.ai_costs", icon: DollarSign },
 { id:"health", labelKey:"admin.tab.health", icon: HeartPulse },
]

export function AdminWorkspace() {
 const { t } = useTranslation()
 const [activeTab, setActiveTab] = useState<AdminTab>("overview")

 const renderContent = () => {
 switch (activeTab) {
 case"overview": return <AdminOverview onNavigate={setActiveTab} />
 case"tenants": return <TenantList />
 case"plans": return <PlanManager />
 case"users": return <UserList />
 case"flags": return <FeatureFlagManager />
 case"jobs": return <JobList />
 case"ai-costs": return <AICostDashboard />
 case"health": return <HealthDashboard />
 }
 }

 return (
 <div className="flex flex-1 h-full overflow-hidden">
 <aside className="w-56 flex-shrink-0 border-l bg-[var(--bg-primary)] overflow-y-auto">
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
 ?"bg-[var(--muhide-orange)]/10 text-[var(--muhide-orange)] dark:bg-[var(--muhide-orange)]/20 font-medium"
 :"text-[var(--text-secondary)] hover:bg-[var(--bg-tertiary)] dark:hover:bg-[var(--bg-secondary)]"
 )}
 >
 <Icon className="h-5 w-5 shrink-0" />
 <span>{t(tab.labelKey)}</span>
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
 const { t } = useTranslation()
 const { data: tenants } = useAdminTenants()
 const { data: plans } = useAdminPlans()
 const { data: users } = useAdminUsers()
 const { data: health } = useAdminDetailedHealth()

 const totalTenants = tenants?.length || 0
 const activeTenants = tenants?.filter((t: { is_active: boolean }) => t.is_active).length || 0
 const totalUsers = users?.length || 0
 const totalPlans = plans?.length || 0
 const healthStatus = health?.overall_status ||"unknown"

 return (
 <div className="space-y-6">
 <h1 className="text-2xl font-bold">{t("admin.title")}</h1>
 <p className="text-[var(--text-muted)]">{t("admin.subtitle")}</p>

 <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
 <OverviewCard
 label={t("admin.total_tenants")}
 value={totalTenants}
 sub={t("admin.active_count", { count: activeTenants })}
 icon={Building2}
 onClick={() => onNavigate("tenants")}
 />
 <OverviewCard
 label={t("admin.plans")}
 value={totalPlans}
 sub={t("admin.pricing_plan")}
 icon={KeyRound}
 onClick={() => onNavigate("plans")}
 />
 <OverviewCard
 label={t("admin.users")}
 value={totalUsers}
 sub={t("admin.all_tenants")}
 icon={Users}
 onClick={() => onNavigate("users")}
 />
 <OverviewCard
 label={t("admin.system_health")}
 value={healthStatus ==="healthy" ? t("status.healthy") : healthStatus ==="degraded" ? t("admin.degraded") : t("admin.unknown")}
 sub={healthStatus ==="healthy" ? t("admin.all_services_ok") : t("admin.issue_detected")}
 icon={HeartPulse}
 status={healthStatus ==="healthy" ?"ok" :"warning"}
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
 label: string; value: string | number; sub: string; icon: React.ElementType; onClick: () => void; status?:"ok" |"warning"
}) {
 return (
 <button
 onClick={onClick}
 className="text-right rounded-xl border border-[var(--border-default)] bg-[var(--bg-primary)] p-4 hover:shadow-md transition-shadow"
 >
 <div className="flex items-center justify-between mb-3">
 <Icon className={cn("h-5 w-5", status ==="warning" ?"text-[var(--status-warning-text)]" :"text-[var(--muhide-orange)]")} />
          {status ==="warning" && <span className="h-2 w-2 rounded-full bg-amber-500 animate-pulse" />}
 </div>
 <p className="text-2xl font-bold">{value}</p>
 <p className="text-sm text-[var(--text-muted)] mt-1">{label}</p>
 <p className="text-xs text-[var(--text-disabled)] mt-0.5">{sub}</p>
 </button>
 )
}

function QuickActions({ onNavigate }: { onNavigate: (tab: AdminTab) => void }) {
 const { t } = useTranslation()
 const actions = [
 { labelKey:"admin.action.manage_tenants", descKey:"admin.action.manage_tenants_desc", tab:"tenants" as AdminTab, icon: Building2 },
 { labelKey:"admin.action.manage_plans", descKey:"admin.action.manage_plans_desc", tab:"plans" as AdminTab, icon: KeyRound },
 { labelKey:"admin.action.manage_users", descKey:"admin.action.manage_users_desc", tab:"users" as AdminTab, icon: Users },
 { labelKey:"admin.action.feature_flags", descKey:"admin.action.feature_flags_desc", tab:"flags" as AdminTab, icon: Flag },
 { labelKey:"admin.action.background_jobs", descKey:"admin.action.background_jobs_desc", tab:"jobs" as AdminTab, icon: Briefcase },
 { labelKey:"admin.action.system_health", descKey:"admin.action.system_health_desc", tab:"health" as AdminTab, icon: HeartPulse },
 ]

 return (
 <div>
 <h2 className="text-lg font-semibold mb-3">{t("admin.quick_actions")}</h2>
 <div className="grid grid-cols-2 md:grid-cols-3 gap-3">
 {actions.map((a) => {
 const Icon = a.icon
 return (
 <button
 key={a.tab}
 onClick={() => onNavigate(a.tab)}
 className="text-right flex items-center gap-3 rounded-lg border border-[var(--border-default)] bg-[var(--bg-primary)] p-3 hover:bg-[var(--bg-secondary)] dark:hover:bg-[var(--bg-secondary)] transition"
 >
 <div className="rounded-lg p-2 bg-[var(--muhide-orange)]/10 text-[var(--muhide-orange)]">
 <Icon className="h-5 w-5" />
 </div>
 <div>
 <p className="font-medium text-sm">{t(a.labelKey)}</p>
 <p className="text-xs text-[var(--text-muted)]">{t(a.descKey)}</p>
 </div>
 </button>
 )
 })}
 </div>
 </div>
 )
}
