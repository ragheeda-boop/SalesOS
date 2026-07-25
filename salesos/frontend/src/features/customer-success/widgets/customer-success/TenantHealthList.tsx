"use client"

import { cn } from"@salesos/ui"
import { AlertTriangle, CheckCircle, Clock } from"lucide-react"
import { useTranslation } from"@/lib/i18n"

interface TenantHealthItem {
 tenant_id: string
 tenant_name: string
 score: number
 status: string
 color: string
 components: Record<string, { weight: number; value: number; contribution: number }>
 user_count: number
 last_active: string | null
 renewal_risk: boolean
 days_in_low_health: number
}

interface TenantHealthListProps {
 tenants: TenantHealthItem[]
}

export function TenantHealthList({ tenants }: TenantHealthListProps) {
 const { t } = useTranslation()

 const STATUS_MAP: Record<string, { labelKey: string; icon: typeof CheckCircle; color: string }> = {
 healthy: { labelKey:"cs.healthy", icon: CheckCircle, color:"text-[var(--status-success-text)] bg-[var(--status-success-bg)]" },
 warning: { labelKey:"cs.warning", icon: Clock, color:"text-yellow-600 bg-yellow-50" },
 critical: { labelKey:"cs.critical", icon: AlertTriangle, color:"text-[var(--status-danger-text)] bg-[var(--status-danger-bg)]" },
 }

 if (!tenants || tenants.length === 0) {
 return (
 <div className="flex items-center justify-center h-32 text-sm text-[var(--text-muted)]">
 {t("cs.no_tenant_data")}
 </div>
 )
 }

 return (
 <div className="space-y-3">
 {tenants.map((tenant) => {
 const statusInfo = STATUS_MAP[tenant.status] || STATUS_MAP.critical
 const Icon = statusInfo.icon

 return (
 <div
 key={tenant.tenant_id}
 className={cn(
"rounded-lg border p-3 transition-colors",
 tenant.color ==="green" ?"border-[var(--status-success-border)] bg-[var(--status-success-bg)]/50" :
 tenant.color ==="yellow" ?"border-yellow-200 bg-yellow-50/50" :
"border-[var(--status-danger-border)] bg-[var(--status-danger-bg)]/50"
 )}
 >
 <div className="flex items-center justify-between">
 <div className="flex items-center gap-2">
 <div className={cn("rounded-full p-1.5", statusInfo.color)}>
 <Icon className="h-4 w-4" />
 </div>
 <span className="text-sm font-medium text-[var(--text-primary)]">{tenant.tenant_name}</span>
 </div>
 <span className={cn(
"text-lg font-bold",
 tenant.color ==="green" ?"text-[var(--status-success-text)]" :
 tenant.color ==="yellow" ?"text-yellow-600" :"text-[var(--status-danger-text)]"
 )}>
 {tenant.score.toFixed(0)}%
 </span>
 </div>
 <div className="flex items-center gap-3 mt-2 text-xs text-[var(--text-muted)]">
 <span>{t("cs.users_count", { count: tenant.user_count })}</span>
 {tenant.renewal_risk && (
 <span className="flex items-center gap-1 text-[var(--status-danger-text)]">
 <AlertTriangle className="h-3 w-3" />
 {t("cs.renewal_risk")}
 </span>
 )}
 </div>
 </div>
 )
 })}
 </div>
 )
}
