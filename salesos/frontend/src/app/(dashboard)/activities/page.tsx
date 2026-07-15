"use client"

import { useState, useMemo } from "react"
import { useGlobalActivities } from "@/lib/hooks/activityQueries"
import { Card, CardContent, CardHeader, Badge, Button, Spinner, Input } from "@salesos/ui"
import {
  Activity, Mail, Phone, Calendar, CheckSquare, FileText, MessageSquare,
  Edit3, Plus, Clock, User, Search, Filter, TrendingUp, AlertTriangle,
} from "lucide-react"

const ACTION_CONFIG: Record<string, { icon: typeof Mail; color: string; label: string }> = {
  email_sent: { icon: Mail, color: "text-info-600 bg-info-100 dark:text-info-400 dark:bg-info-900/50", label: "إرسال بريد" },
  email_received: { icon: Mail, color: "text-info-600 bg-info-100 dark:text-info-400 dark:bg-info-900/50", label: "استلام بريد" },
  meeting_created: { icon: Calendar, color: "text-purple-600 bg-purple-100 dark:text-purple-400 dark:bg-purple-900/50", label: "اجتماع جديد" },
  meeting_completed: { icon: Calendar, color: "text-success-600 bg-success-100 dark:text-success-400 dark:bg-success-900/50", label: "اجتماع منتهي" },
  call: { icon: Phone, color: "text-success-600 bg-success-100 dark:text-success-400 dark:bg-success-900/50", label: "مكالمة" },
  task_created: { icon: CheckSquare, color: "text-warning-600 bg-warning-100 dark:text-warning-400 dark:bg-warning-900/50", label: "مهمة جديدة" },
  task_completed: { icon: CheckSquare, color: "text-success-600 bg-success-100 dark:text-success-400 dark:bg-success-900/50", label: "إنجاز مهمة" },
  contract_signed: { icon: FileText, color: "text-danger-600 bg-danger-100 dark:text-danger-400 dark:bg-danger-900/50", label: "توقيع عقد" },
  contract_created: { icon: FileText, color: "text-danger-600 bg-danger-100 dark:text-danger-400 dark:bg-danger-900/50", label: "عقد جديد" },
  note_added: { icon: MessageSquare, color: "text-neutral-600 bg-neutral-100 dark:text-neutral-400 dark:bg-neutral-800", label: "ملاحظة" },
  note_updated: { icon: Edit3, color: "text-neutral-600 bg-neutral-100 dark:text-neutral-400 dark:bg-neutral-800", label: "تحديث ملاحظة" },
  company_created: { icon: Plus, color: "text-info-600 bg-info-100 dark:text-info-400 dark:bg-info-900/50", label: "شركة جديدة" },
  opportunity_created: { icon: Plus, color: "text-warning-600 bg-warning-100 dark:text-warning-400 dark:bg-warning-900/50", label: "فرصة جديدة" },
  opportunity_won: { icon: CheckSquare, color: "text-success-600 bg-success-100 dark:text-success-400 dark:bg-success-900/50", label: "ربح فرصة" },
  opportunity_lost: { icon: Clock, color: "text-danger-600 bg-danger-100 dark:text-danger-400 dark:bg-danger-900/50", label: "خسارة فرصة" },
}

const ACTION_FILTERS = [
  { label: "الكل", value: "" },
  { label: "بريد", value: "email" },
  { label: "اجتماعات", value: "meeting" },
  { label: "مكالمات", value: "call" },
  { label: "مهام", value: "task" },
  { label: "عقود", value: "contract" },
  { label: "ملاحظات", value: "note" },
  { label: "فرص", value: "opportunity" },
]

function formatRelativeTime(timestamp: string): string {
  const diff = Date.now() - new Date(timestamp).getTime()
  const mins = Math.floor(diff / 60000)
  if (mins < 1) return "الآن"
  if (mins < 60) return `منذ ${mins} دقيقة`
  const hours = Math.floor(mins / 60)
  if (hours < 24) return `منذ ${hours} ساعة`
  const days = Math.floor(hours / 24)
  if (days < 30) return `منذ ${days} يوم`
  return new Intl.DateTimeFormat("ar-SA", { day: "numeric", month: "short" }).format(new Date(timestamp))
}

function groupByDate<T extends { timestamp: string }>(items: T[]) {
  const groups: Record<string, T[]> = {}
  for (const item of items) {
    const date = new Date(item.timestamp).toLocaleDateString("ar-SA", { weekday: "long", year: "numeric", month: "long", day: "numeric" })
    if (!groups[date]) groups[date] = []
    groups[date].push(item)
  }
  return groups
}

export default function ActivitiesPage() {
  const [actionFilter, setActionFilter] = useState("")
  const [searchQuery, setSearchQuery] = useState("")

  const filters = useMemo(() => {
    const f: Record<string, string> = {}
    if (actionFilter) f.action = actionFilter
    return f
  }, [actionFilter])

  const { data, isLoading, isError, error, refetch } = useGlobalActivities(filters)
  const activities = data?.items || []
  const total = data?.total || 0

  const filteredActivities = useMemo(() => {
    if (!searchQuery) return activities
    const q = searchQuery.toLowerCase()
    return activities.filter(
      (a) =>
        a.actor.toLowerCase().includes(q) ||
        a.action.toLowerCase().includes(q) ||
        a.entity_type.toLowerCase().includes(q)
    )
  }, [activities, searchQuery])

  const grouped = useMemo(() => groupByDate(filteredActivities), [filteredActivities])

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-neutral-900 dark:text-neutral-100">النشاطات</h1>
          <p className="mt-1 text-sm text-neutral-500 dark:text-neutral-400">
            سجل شامل لجميع النشاطات في المنصة
          </p>
        </div>
        {total > 0 && (
          <Badge variant="primary">{total} نشاط</Badge>
        )}
      </div>

      {/* Filters */}
      <div className="flex flex-wrap items-center gap-3">
        <Input
          placeholder="بحث في النشاطات..."
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
          leftIcon={<Search className="h-4 w-4" />}
          className="max-w-xs"
        />
        <div className="flex gap-1 overflow-x-auto rounded-lg border border-neutral-200 px-1 py-0.5 dark:border-neutral-700">
          {ACTION_FILTERS.map((f) => (
            <button
              key={f.value}
              onClick={() => setActionFilter(f.value)}
              className={`whitespace-nowrap rounded-md px-2.5 py-1 text-xs transition ${
                actionFilter === f.value
                  ? "bg-[var(--muhide-orange)] text-white"
                  : "text-neutral-500 hover:text-neutral-700 dark:text-neutral-400 dark:hover:text-neutral-200"
              }`}
            >
              {f.label}
            </button>
          ))}
        </div>
      </div>

      {/* Activity Feed */}
      <Card>
        <CardContent className="p-0">
          {isLoading ? (
            <div className="flex items-center justify-center py-16">
              <Spinner className="h-6 w-6" />
            </div>
          ) : isError ? (
            <div className="flex flex-col items-center justify-center py-16 text-center">
              <AlertTriangle className="mb-3 h-10 w-10 text-danger-500" />
              <p className="text-lg font-semibold text-neutral-900 dark:text-neutral-100">فشل تحميل النشاطات</p>
              <p className="mt-1 text-sm text-neutral-500">{(error as Error)?.message || "تأكد من اتصال الخادم"}</p>
              <Button variant="outline" size="sm" className="mt-4" onClick={() => refetch()}>إعادة المحاولة</Button>
            </div>
          ) : filteredActivities.length === 0 ? (
            <div className="flex flex-col items-center justify-center py-16 text-center">
              <Activity className="mb-3 h-10 w-10 text-neutral-300" />
              <p className="text-lg font-semibold text-neutral-900 dark:text-neutral-100">
                {searchQuery || actionFilter ? "لا توجد نتائج" : "لا توجد نشاطات"}
              </p>
              <p className="mt-1 text-sm text-neutral-500">
                {searchQuery || actionFilter ? "جرب تغيير معايير البحث" : "ستظهر النشاطات هنا عندما تبدأ العمل"}
              </p>
            </div>
          ) : (
            <div className="divide-y divide-neutral-100 dark:divide-neutral-800">
              {Object.entries(grouped).map(([date, items]) => (
                <div key={date}>
                  <div className="sticky top-0 z-10 bg-neutral-50 px-4 py-2 text-xs font-medium text-neutral-500 dark:bg-neutral-900 dark:text-neutral-400">
                    {date}
                  </div>
                  <div className="divide-y divide-neutral-50 dark:divide-neutral-800/50">
                    {items.map((activity) => {
                      const config = ACTION_CONFIG[activity.action] || { icon: Clock, color: "text-neutral-600 bg-neutral-100", label: activity.action }
                      const Icon = config.icon
                      return (
                        <div key={activity.id} className="flex items-start gap-3 px-4 py-3 transition hover:bg-neutral-50 dark:hover:bg-neutral-800/30">
                          <div className={`flex h-8 w-8 shrink-0 items-center justify-center rounded-full ${config.color}`}>
                            <Icon className="h-4 w-4" />
                          </div>
                          <div className="min-w-0 flex-1">
                            <div className="flex items-center gap-2">
                              <span className="text-sm font-medium text-neutral-900 dark:text-neutral-100">{config.label}</span>
                              <Badge variant="default" className="text-[9px]">{activity.entity_type}</Badge>
                            </div>
                            <div className="mt-0.5 flex items-center gap-2 text-xs text-neutral-500 dark:text-neutral-400">
                              <span className="inline-flex items-center gap-1">
                                <User className="h-3 w-3" />
                                {activity.actor}
                              </span>
                              <span>·</span>
                              <span className="inline-flex items-center gap-1">
                                <Clock className="h-3 w-3" />
                                {formatRelativeTime(activity.timestamp)}
                              </span>
                            </div>
                          </div>
                        </div>
                      )
                    })}
                  </div>
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  )
}
