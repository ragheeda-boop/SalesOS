"use client"

import { useState, useEffect, useCallback } from "react"
import api from "@/lib/api"
import { Card, Badge, cn, Spinner } from "@salesos/ui"
import { AlertTriangle, Activity, Clock, MemoryStick, Gauge, RefreshCw, CheckCircle, XCircle } from "lucide-react"

interface AggregatedMetrics {
  api_calls: { total: number; p50_ms: number; p95_ms: number; p99_ms: number }
  errors: { total: number; by_context: Record<string, number>; recent: { message: string; time: string }[] }
  page_loads: { total: number; avg_load_ms: number; avg_dom_interactive_ms: number }
  web_vitals: { lcp: number | null; fid: number | null; cls: number | null }
  system_health: Record<string, string>
  memory: { current_mb: number | null }
}

export default function MonitoringPage() {
  const [metrics, setMetrics] = useState<AggregatedMetrics | null>(null)
  const [loading, setLoading] = useState(true)
  const [refreshing, setRefreshing] = useState(false)

  const fetchMetrics = useCallback(async () => {
    try {
      const res = await api.get("/api/v1/monitoring/metrics")
      setMetrics(res.data)
    } catch {}
    setLoading(false)
    setRefreshing(false)
  }, [])

  useEffect(() => {
    fetchMetrics()
    const interval = setInterval(fetchMetrics, 30_000)
    return () => clearInterval(interval)
  }, [fetchMetrics])

  const handleRefresh = () => {
    setRefreshing(true)
    fetchMetrics()
  }

  if (loading) {
    return <div className="py-20 text-center text-neutral-500"><Spinner /> جاري التحميل...</div>
  }

  return (
    <div className="p-6 space-y-6" dir="rtl">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold">مراقبة النظام</h1>
        <div className="flex items-center gap-2">
          <Badge variant={metrics?.system_health?.database === 'connected' ? 'success' : 'danger'}>
            {metrics?.system_health?.database === 'connected' ? 'متصل' : 'منفصل'}
          </Badge>
          <button onClick={handleRefresh} className="rounded-lg p-1.5 hover:bg-neutral-100 dark:hover:bg-neutral-800">
            <RefreshCw className={cn("h-5 w-5", refreshing && "animate-spin")} />
          </button>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard icon={Activity} label="طلبات API" value={metrics?.api_calls?.total || 0} color="blue" />
        <StatCard icon={AlertTriangle} label="الأخطاء" value={metrics?.errors?.total || 0} color="red" />
        <StatCard icon={Clock} label="متوسط زمن التحميل" value={`${metrics?.page_loads?.avg_load_ms || 0}ms`} color="green" />
        <StatCard icon={MemoryStick} label="الذاكرة" value={metrics?.memory?.current_mb ? `${metrics.memory.current_mb}MB` : '-'} color="purple" />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <Card className="p-4">
          <h3 className="font-semibold mb-3 flex items-center gap-2">
            <Gauge className="h-4 w-4" />
            زمن استجابة API
          </h3>
          <div className="space-y-3">
            <LatencyBar label="p50" value={metrics?.api_calls?.p50_ms || 0} max={1000} color="bg-success-500" />
            <LatencyBar label="p95" value={metrics?.api_calls?.p95_ms || 0} max={1000} color="bg-warning-500" />
            <LatencyBar label="p99" value={metrics?.api_calls?.p99_ms || 0} max={1000} color="bg-danger-500" />
          </div>
        </Card>

        <Card className="p-4">
          <h3 className="font-semibold mb-3 flex items-center gap-2">
            <Clock className="h-4 w-4" />
            مقاييس تحميل الصفحة
          </h3>
          <div className="space-y-3">
            <LatencyBar label="DOM Interactive" value={metrics?.page_loads?.avg_dom_interactive_ms || 0} max={5000} color="bg-info-500" />
            <LatencyBar label="LCP" value={metrics?.web_vitals?.lcp || 0} max={4000} color="bg-warning-500" />
            <LatencyBar label="FID" value={metrics?.web_vitals?.fid || 0} max={300} color="bg-info-500" />
            <LatencyBar label="CLS" value={(metrics?.web_vitals?.cls || 0) * 100} max={25} color="bg-purple-500" unit="%" />
          </div>
        </Card>
      </div>

      {metrics?.errors?.recent && metrics.errors.recent.length > 0 && (
        <Card className="p-4">
          <h3 className="font-semibold mb-3 flex items-center gap-2">
            <AlertTriangle className="h-4 w-4 text-danger-500" />
            آخر الأخطاء
          </h3>
          <div className="space-y-2">
            {metrics.errors.recent.slice(0, 10).map((err, i) => (
              <div key={i} className="flex items-start gap-2 text-sm p-2 bg-danger-50 dark:bg-danger-900/20 rounded-lg">
                <XCircle className="h-4 w-4 text-danger-500 mt-0.5 shrink-0" />
                <div className="flex-1 min-w-0">
                  <p className="text-danger-700 dark:text-danger-300 truncate">{err.message}</p>
                  <p className="text-xs text-neutral-500">{new Date(err.time).toLocaleString('ar-SA')}</p>
                </div>
              </div>
            ))}
          </div>
        </Card>
      )}

      <Card className="p-4">
        <h3 className="font-semibold mb-3 flex items-center gap-2">
          <Activity className="h-4 w-4" />
          حالة النظام
        </h3>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
          {Object.entries(metrics?.system_health || {}).map(([service, status]) => (
            <div key={service} className="flex items-center gap-2 text-sm">
              {status === 'connected' || status === 'active' ? (
                <CheckCircle className="h-4 w-4 text-success-500" />
              ) : (
                <XCircle className="h-4 w-4 text-danger-500" />
              )}
              <span className="text-neutral-600 dark:text-neutral-400">{service}</span>
              <span className={cn("font-mono text-xs", status === 'connected' || status === 'active' ? "text-success-600" : "text-danger-600")}>
                {status}
              </span>
            </div>
          ))}
        </div>
      </Card>
    </div>
  )
}

function StatCard({ icon: Icon, label, value, color }: { icon: React.ComponentType<{ className?: string }>; label: string; value: string | number; color: string }) {
  const colorMap: Record<string, string> = {
    blue: "bg-info-50 text-info-600 dark:bg-info-900/30 dark:text-info-400",
    green: "bg-success-50 text-success-600 dark:bg-success-900/30 dark:text-success-400",
    red: "bg-danger-50 text-danger-600 dark:bg-danger-900/30 dark:text-danger-400",
    purple: "bg-purple-50 text-purple-600 dark:bg-purple-900/30 dark:text-purple-400",
  }
  return (
    <Card className="p-4">
      <div className="flex items-center gap-3">
        <div className={cn("rounded-lg p-2", colorMap[color] || colorMap.blue)}>
          <Icon className="h-5 w-5" />
        </div>
        <div>
          <p className="text-xs text-neutral-500 dark:text-neutral-400">{label}</p>
          <p className="text-xl font-bold">{value}</p>
        </div>
      </div>
    </Card>
  )
}

function LatencyBar({ label, value, max, color = "bg-info-500", unit = "ms" }: { label: string; value: number; max: number; color?: string; unit?: string }) {
  const pct = Math.min(100, (value / max) * 100)
  return (
    <div className="flex items-center gap-3">
      <span className="w-28 text-sm text-neutral-600 dark:text-neutral-400">{label}</span>
      <div className="flex-1 h-4 bg-neutral-100 dark:bg-neutral-800 rounded-full overflow-hidden">
        <div className={cn("h-full rounded-full transition-all", color)} style={{ width: `${pct}%` }} />
      </div>
      <span className="text-sm font-mono w-20 text-left">{value}{unit}</span>
    </div>
  )
}
