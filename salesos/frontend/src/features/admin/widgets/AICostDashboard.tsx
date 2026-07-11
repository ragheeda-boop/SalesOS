"use client"

import { useState } from "react"
import { Card, Badge, Spinner } from "@salesos/ui"
import { DollarSign, TrendingUp, Cpu, BarChart3 } from "lucide-react"
import { useAdminAICostSummary, useAdminAIUsage, useAdminAICosts } from "@/lib/hooks/adminQueries"
import { AdminAICost } from "@/lib/api"

export function AICostDashboard() {
  const [days, setDays] = useState(30)
  const { data: summary, isLoading: summaryLoading } = useAdminAICostSummary(days)
  const { data: usage, isLoading: usageLoading } = useAdminAIUsage(days)
  const { data: costs, isLoading: costsLoading } = useAdminAICosts({ days })

  const loading = summaryLoading || usageLoading || costsLoading

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h2 className="text-xl font-bold">تكاليف الذكاء الاصطناعي</h2>
        <select
          value={days}
          onChange={(e) => setDays(Number(e.target.value))}
          className="border rounded px-3 py-2 text-sm dark:bg-neutral-800 dark:border-neutral-700"
        >
          <option value={7}>آخر 7 أيام</option>
          <option value={30}>آخر 30 يوم</option>
          <option value={90}>آخر 90 يوم</option>
        </select>
      </div>

      {loading ? (
        <div className="py-20 text-center text-neutral-500"><Spinner /> جاري التحميل...</div>
      ) : (
        <>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <MetricCard icon={DollarSign} label="إجمالي التكلفة" value={`$${summary?.total_cost?.toFixed(2) || "0.00"}`} color="red" />
            <MetricCard icon={Cpu} label="إجمالي التوكنات" value={summary?.total_tokens?.toLocaleString() || "0"} color="blue" />
            <MetricCard icon={TrendingUp} label="النماذج المستخدمة" value={summary?.by_model?.length || 0} color="purple" />
            <MetricCard icon={BarChart3} label="العمليات" value={summary?.by_operation?.length || 0} color="green" />
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <Card className="p-4">
              <h3 className="font-semibold mb-3">التكلفة حسب النموذج</h3>
              {summary?.by_model?.length ? (
                <div className="space-y-2">
                  {summary.by_model.map((m: { model: string; cost: number; tokens: number }) => {
                    const maxCost = Math.max(...summary.by_model.map((x: { cost: number }) => x.cost))
                    return (
                      <div key={m.model}>
                        <div className="flex justify-between text-sm mb-1">
                          <span>{m.model}</span>
                          <span className="font-mono">${m.cost.toFixed(4)}</span>
                        </div>
                        <div className="h-2 bg-neutral-100 dark:bg-neutral-800 rounded-full overflow-hidden">
                          <div className="h-full bg-[var(--muhide-orange)] rounded-full transition-all" style={{ width: `${(m.cost / maxCost) * 100}%` }} />
                        </div>
                      </div>
                    )
                  })}
                </div>
              ) : (
                <p className="text-sm text-neutral-500 text-center py-4">لا توجد بيانات</p>
              )}
            </Card>

            <Card className="p-4">
              <h3 className="font-semibold mb-3">التكلفة حسب النوع</h3>
              {summary?.by_operation?.length ? (
                <div className="space-y-2">
                  {summary.by_operation.map((o: { operation: string; cost: number; tokens: number }) => (
                    <div key={o.operation} className="flex items-center justify-between p-2 rounded-lg border dark:border-neutral-700">
                      <Badge>{o.operation}</Badge>
                      <div className="text-left">
                        <p className="text-sm font-mono">${o.cost.toFixed(4)}</p>
                        <p className="text-xs text-neutral-500">{o.tokens.toLocaleString()} توكن</p>
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <p className="text-sm text-neutral-500 text-center py-4">لا توجد بيانات</p>
              )}
            </Card>
          </div>

          <Card className="p-4">
            <h3 className="font-semibold mb-3">التكلفة حسب العميل</h3>
            {summary?.by_tenant?.length ? (
              <div className="overflow-x-auto">
                <table className="w-full text-sm">
                  <thead>
                    <tr className="border-b dark:border-neutral-700 text-right">
                      <th className="p-2 font-medium">العميل</th>
                      <th className="p-2 font-medium">التكلفة</th>
                      <th className="p-2 font-medium">التوكنات</th>
                    </tr>
                  </thead>
                  <tbody>
                    {summary.by_tenant.map((t: { tenant_id: string; cost: number; tokens: number }) => (
                      <tr key={t.tenant_id} className="border-b dark:border-neutral-800">
                        <td className="p-2 text-xs">{t.tenant_id === "system" ? "النظام" : t.tenant_id}</td>
                        <td className="p-2 font-mono">${t.cost.toFixed(4)}</td>
                        <td className="p-2 font-mono">{t.tokens.toLocaleString()}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            ) : (
              <p className="text-sm text-neutral-500 text-center py-4">لا توجد بيانات</p>
            )}
          </Card>

          <Card className="p-4">
            <h3 className="font-semibold mb-3">أحدث العمليات</h3>
            {costs?.length ? (
              <div className="overflow-x-auto">
                <table className="w-full text-sm">
                  <thead>
                    <tr className="border-b dark:border-neutral-700 text-right">
                      <th className="p-2 font-medium">النموذج</th>
                      <th className="p-2 font-medium">العملية</th>
                      <th className="p-2 font-medium">العميل</th>
                      <th className="p-2 font-medium">التكلفة</th>
                      <th className="p-2 font-medium">التاريخ</th>
                    </tr>
                  </thead>
                  <tbody>
                    {costs.map((c: AdminAICost) => (
                      <tr key={c.id} className="border-b dark:border-neutral-800">
                        <td className="p-2 text-xs">{c.model}</td>
                        <td className="p-2"><Badge>{c.operation}</Badge></td>
                        <td className="p-2 text-xs text-neutral-500">{c.tenant_name || "-"}</td>
                        <td className="p-2 font-mono text-xs">${c.cost.toFixed(4)}</td>
                        <td className="p-2 text-xs text-neutral-500">{new Date(c.created_at).toLocaleDateString("ar-SA")}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            ) : (
              <p className="text-sm text-neutral-500 text-center py-4">لا توجد عمليات</p>
            )}
          </Card>
        </>
      )}
    </div>
  )
}

function MetricCard({ icon: Icon, label, value, color }: { icon: React.ElementType; label: string; value: string | number; color: string }) {
  const colorMap: Record<string, string> = {
    red: "bg-danger-50 text-danger-600 dark:bg-danger-900/30",
    blue: "bg-info-50 text-info-600 dark:bg-info-900/30",
    purple: "bg-purple-50 text-purple-600 dark:bg-purple-900/30",
    green: "bg-success-50 text-success-600 dark:bg-success-900/30",
  }

  return (
    <div className="rounded-xl border border-neutral-200 dark:border-neutral-700 bg-white dark:bg-neutral-900 p-4">
      <div className="flex items-center gap-3">
        <div className={`rounded-lg p-2 ${colorMap[color] || colorMap.blue}`}>
          <Icon className="h-5 w-5" />
        </div>
        <div>
          <p className="text-xs text-neutral-500">{label}</p>
          <p className="text-lg font-bold">{value}</p>
        </div>
      </div>
    </div>
  )
}
