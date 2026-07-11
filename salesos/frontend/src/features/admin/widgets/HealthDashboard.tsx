"use client"

import { Card, Badge, Spinner } from "@salesos/ui"
import { HeartPulse, CheckCircle, XCircle, Activity, Clock, Database, Cpu } from "lucide-react"
import { useAdminDetailedHealth, useAdminHealthHistory } from "@/lib/hooks/adminQueries"
import { AdminHealthComponent, AdminHealthHistoryEntry } from "@/lib/api"

export function HealthDashboard() {
  const { data: health, isLoading: healthLoading } = useAdminDetailedHealth()
  const { data: history, isLoading: historyLoading } = useAdminHealthHistory()

  const loading = healthLoading || historyLoading

  if (loading) {
    return <div className="py-20 text-center text-neutral-500"><Spinner /> جاري التحميل...</div>
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h2 className="text-xl font-bold">صحة النظام</h2>
        {health && (
          <div className="flex items-center gap-2">
            <span className={`h-3 w-3 rounded-full ${health.overall_status === "healthy" ? "bg-success-500" : "bg-danger-500"}`} />
            <span className="font-medium">{health.overall_status === "healthy" ? "النظام سليم" : "يوجد خلل"}</span>
          </div>
        )}
      </div>

      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <div className="rounded-xl border border-neutral-200 dark:border-neutral-700 bg-white dark:bg-neutral-900 p-4">
          <div className="flex items-center gap-2 mb-2">
            <HeartPulse className="h-5 w-5 text-success-500" />
          </div>
          <p className="text-2xl font-bold">{Math.floor((health?.uptime_seconds || 0) / 86400)}d</p>
          <p className="text-xs text-neutral-500">مدة التشغيل</p>
        </div>
        <div className="rounded-xl border border-neutral-200 dark:border-neutral-700 bg-white dark:bg-neutral-900 p-4">
          <div className="flex items-center gap-2 mb-2">
            <Cpu className="h-5 w-5 text-[var(--muhide-orange)]" />
          </div>
          <p className="text-2xl font-bold">{health?.components?.length || 0}</p>
          <p className="text-xs text-neutral-500">مكونات النظام</p>
        </div>
        <div className="rounded-xl border border-neutral-200 dark:border-neutral-700 bg-white dark:bg-neutral-900 p-4">
          <div className="flex items-center gap-2 mb-2">
            <CheckCircle className="h-5 w-5 text-success-500" />
          </div>
          <p className="text-2xl font-bold">{health?.components?.filter((c: AdminHealthComponent) => c.status === "healthy").length || 0}</p>
          <p className="text-xs text-neutral-500">سليمة</p>
        </div>
        <div className="rounded-xl border border-neutral-200 dark:border-neutral-700 bg-white dark:bg-neutral-900 p-4">
          <div className="flex items-center gap-2 mb-2">
            <Activity className="h-5 w-5 text-neutral-400" />
          </div>
          <p className="text-2xl font-bold">{history?.length || 0}</p>
          <p className="text-xs text-neutral-500">فحوصات سابقة</p>
        </div>
      </div>

      <Card className="p-4">
        <h3 className="font-semibold mb-3">حالة المكونات</h3>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
          {health?.components?.map((comp: AdminHealthComponent) => (
            <div key={comp.component} className="flex items-start gap-3 p-3 rounded-lg border dark:border-neutral-700">
              <div className="mt-0.5">
                {comp.status === "healthy" ? (
                  <CheckCircle className="h-5 w-5 text-success-500" />
                ) : (
                  <XCircle className="h-5 w-5 text-danger-500" />
                )}
              </div>
              <div className="flex-1">
                <div className="flex items-center justify-between">
                  <p className="font-medium text-sm">{comp.component}</p>
                  <Badge variant={comp.status === "healthy" ? "success" : "danger"}>{comp.status}</Badge>
                </div>
                {comp.latency_ms != null && (
                  <p className="text-xs text-neutral-500 mt-1">الاستجابة: {comp.latency_ms}ms</p>
                )}
                {comp.details && (
                  <p className="text-xs text-neutral-400 mt-0.5">{comp.details}</p>
                )}
              </div>
            </div>
          ))}
        </div>
      </Card>

      <Card className="p-4">
        <h3 className="font-semibold mb-3 flex items-center gap-2">
          <Clock className="h-4 w-4" />
          تاريخ الصحة (آخر 24 ساعة)
        </h3>
        {history?.length ? (
          <div className="space-y-2">
            {history.map((entry: AdminHealthHistoryEntry, i: number) => (
              <div key={i} className="flex items-center gap-3 p-2 rounded-lg border dark:border-neutral-700 text-sm">
                <span className={`h-2 w-2 rounded-full shrink-0 ${entry.overall_status === "healthy" ? "bg-success-500" : "bg-danger-500"}`} />
                <span className="text-xs text-neutral-500 font-mono w-32">
                  {new Date(entry.timestamp).toLocaleTimeString("ar-SA")}
                </span>
                <Badge variant={entry.overall_status === "healthy" ? "success" : "danger"}>{entry.overall_status}</Badge>
                <div className="flex gap-1 flex-wrap">
                  {Object.entries(entry.components).map(([name, status]) => (
                    <span key={name} className={`text-xs px-1.5 py-0.5 rounded ${
                      status === "healthy" ? "bg-success-50 text-success-700 dark:bg-success-900/20" : "bg-danger-50 text-danger-700 dark:bg-danger-900/20"
                    }`}>
                      {name}: {status}
                    </span>
                  ))}
                </div>
              </div>
            ))}
          </div>
        ) : (
          <p className="text-sm text-neutral-500 text-center py-4">لا توجد بيانات تاريخية</p>
        )}
      </Card>
    </div>
  )
}
