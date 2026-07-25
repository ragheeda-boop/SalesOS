'use client'

import type { CalendarMetricsDTO } from '@/lib/api/types'

interface CalendarIntelligenceViewProps {
 metrics: CalendarMetricsDTO | null
 isLoading: boolean
 error: Error | null
 onRefresh: () => void
}

export function CalendarIntelligenceView({
 metrics,
 isLoading,
 error,
 onRefresh,
}: CalendarIntelligenceViewProps) {
 if (isLoading) {
 return (
 <div className="flex items-center justify-center h-full" role="status">
 <div className="flex flex-col items-center gap-3 text-muted">
 <div className="w-8 h-8 border-2 border-primary border-t-transparent rounded-full animate-spin" />
 <span>جاري تحميل تحليلات التقويم...</span>
 </div>
 </div>
 )
 }

 if (error) {
 return (
 <div className="flex items-center justify-center h-full text-destructive" role="alert">
 <div className="flex flex-col items-center gap-3">
 <span>تعذر تحميل تحليلات التقويم</span>
 <button onClick={onRefresh} className="text-sm underline">إعادة المحاولة</button>
 </div>
 </div>
 )
 }

 if (!metrics) {
 return (
 <div className="flex items-center justify-center h-full text-muted">
 لا توجد بيانات تقويم
 </div>
 )
 }

 return (
 <div className="p-4 h-full flex flex-col gap-4" dir="rtl">
 <div className="grid grid-cols-2 gap-3">
 <StatCard label="اجتماعات" value={metrics.meeting_count} color="text-blue-400" />
 <StatCard label="إجمالي الساعات" value={`${metrics.total_hours}h`} color="text-green-400" />
 <StatCard label="متوسط المدة" value={`${metrics.avg_duration_minutes}د`} color="text-[var(--status-warning-text)]" />
 <StatCard label="إجمالي الأحداث" value={metrics.total_events} color="text-[var(--chart-purple)]" />
 </div>

 {metrics.upcoming && metrics.upcoming.length > 0 && (
 <div className="flex-1 min-h-0">
 <h4 className="text-xs font-semibold text-muted mb-2">المواعيد القادمة</h4>
 <div className="space-y-2">
 {metrics.upcoming.slice(0, 5).map((ev, i) => (
 <div key={i} className="flex justify-between items-center text-sm bg-surface-elevated rounded p-2">
 <div className="flex flex-col min-w-0">
 <span className="truncate">{ev.title}</span>
 <span className="text-xs text-muted">{ev.start_time}</span>
 </div>
 {ev.company_id && (
 <span className="text-xs bg-primary/10 text-primary rounded px-2 py-0.5 shrink-0">
 {ev.company_id.slice(0, 8)}
 </span>
 )}
 </div>
 ))}
 </div>
 </div>
 )}
 </div>
 )
}

function StatCard({ label, value, color }: { label: string; value: string | number; color: string }) {
 return (
 <div className="bg-surface-elevated rounded-lg p-3 text-center">
 <div className={`text-2xl font-bold ${color} tabular-nums`}>{value}</div>
 <div className="text-xs text-muted mt-1">{label}</div>
 </div>
 )
}
