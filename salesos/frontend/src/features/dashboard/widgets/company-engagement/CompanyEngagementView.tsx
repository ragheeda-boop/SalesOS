'use client'

import type { CompanyEngagementDTO } from '@/lib/api/types'

interface CompanyEngagementViewProps {
 engagement: CompanyEngagementDTO | null
 isLoading: boolean
 error: Error | null
 onRefresh: () => void
}

export function CompanyEngagementView({
 engagement,
 isLoading,
 error,
 onRefresh,
}: CompanyEngagementViewProps) {
 if (isLoading) {
 return (
 <div className="flex items-center justify-center h-full" role="status">
 <div className="flex flex-col items-center gap-3 text-muted">
 <div className="w-8 h-8 border-2 border-primary border-t-transparent rounded-full animate-spin" />
 <span>جاري تحميل بيانات التفاعل...</span>
 </div>
 </div>
 )
 }

 if (error) {
 return (
 <div className="flex items-center justify-center h-full text-destructive" role="alert">
 <div className="flex flex-col items-center gap-3">
 <span>تعذر تحميل بيانات التفاعل</span>
 <button onClick={onRefresh} className="text-sm underline">إعادة المحاولة</button>
 </div>
 </div>
 )
 }

 if (!engagement) {
 return (
 <div className="flex items-center justify-center h-full text-muted">
 لا توجد بيانات تفاعل
 </div>
 )
 }

 const health = engagement.score?.relationship_health ?? 0
 const healthPct = Math.round(health * 100)
 const healthColor =
 healthPct >= 70 ? 'text-green-400' :
 healthPct >= 40 ? 'text-[var(--status-warning-text)]' :
 'text-red-400'

 return (
 <div className="p-4 h-full flex flex-col gap-4" dir="rtl">
 <div className="flex items-center justify-between">
 <div>
 <div className="text-sm text-muted">صحة العلاقة</div>
 <div className={`text-3xl font-bold ${healthColor} tabular-nums`}>
 {healthPct}%
 </div>
 </div>
 <div className="text-right">
 <div className="text-xs text-muted">آخر تواصل</div>
 <div className="text-sm">
 {engagement.last_activity ?? '-'}
 </div>
 </div>
 </div>

 <div className="grid grid-cols-2 gap-2">
 <MiniStat label="بريد" value={engagement.email_count} />
 <MiniStat label="اجتماعات" value={engagement.meeting_count} />
 <MiniStat label="آخر بريد" value={engagement.last_email ?? '-'} />
 <MiniStat label="آخر اجتماع" value={engagement.last_meeting ?? '-'} />
 </div>

 {engagement.followup_status && (
 <div className="text-xs text-muted text-center">
 حالة المتابعة: {engagement.followup_status}
 </div>
 )}
 </div>
 )
}

function MiniStat({ label, value }: { label: string; value: string | number }) {
 return (
 <div className="bg-surface-elevated rounded p-2 text-center">
 <div className="text-lg font-bold tabular-nums">{value}</div>
 <div className="text-[10px] text-muted">{label}</div>
 </div>
 )
}
