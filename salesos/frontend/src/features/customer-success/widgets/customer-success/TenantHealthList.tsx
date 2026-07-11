"use client"

import { cn } from "@salesos/ui"
import { AlertTriangle, CheckCircle, Clock } from "lucide-react"

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

const STATUS_MAP: Record<string, { label: string; icon: typeof CheckCircle; color: string }> = {
  healthy: { label: "سليم", icon: CheckCircle, color: "text-green-600 bg-green-50" },
  warning: { label: "تحذير", icon: Clock, color: "text-yellow-600 bg-yellow-50" },
  critical: { label: "حرج", icon: AlertTriangle, color: "text-red-600 bg-red-50" },
}

export function TenantHealthList({ tenants }: TenantHealthListProps) {
  if (!tenants || tenants.length === 0) {
    return (
      <div className="flex items-center justify-center h-32 text-sm text-[var(--text-muted)]">
        لا توجد بيانات عملاء
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
              tenant.color === "green" ? "border-green-200 bg-green-50/50" :
              tenant.color === "yellow" ? "border-yellow-200 bg-yellow-50/50" :
              "border-red-200 bg-red-50/50"
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
                tenant.color === "green" ? "text-green-600" :
                tenant.color === "yellow" ? "text-yellow-600" : "text-red-600"
              )}>
                {tenant.score.toFixed(0)}%
              </span>
            </div>
            <div className="flex items-center gap-3 mt-2 text-xs text-[var(--text-muted)]">
              <span>{tenant.user_count} مستخدم</span>
              {tenant.renewal_risk && (
                <span className="flex items-center gap-1 text-red-600">
                  <AlertTriangle className="h-3 w-3" />
                  خطر تجديد
                </span>
              )}
            </div>
          </div>
        )
      })}
    </div>
  )
}
