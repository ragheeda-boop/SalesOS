"use client"

import { useState } from"react"
import { useCompany360 } from"@/lib/hooks/company360Queries"
import { useDecisionRecommendations, useDecisionScores } from"@/lib/decisionQueries"
import { Card, CardContent, CardHeader, cn, Badge, Skeleton, EmptyState } from"@salesos/ui"
import {
 Sparkles, TrendingUp, AlertTriangle, CheckCircle, ChevronDown, ChevronUp,
 Lightbulb, Target, Zap, Shield, BarChart3
} from"lucide-react"

interface DecisionPlatformPanelProps {
 companyId: string
 company360?: ReturnType<typeof useCompany360>["data"] | null
}

function ConfidenceBadge({ value }: { value: number }) {
 const color = value >= 0.7 ?"success" : value >= 0.4 ?"warning" :"danger"
 return (
 <span className={cn(
"inline-flex items-center gap-1 rounded-full px-2 py-0.5 text-[10px] font-medium",
 color ==="success" &&"bg-[var(--color-success-bg)] text-[var(--color-success)]",
 color ==="warning" &&"bg-[var(--color-warning-bg)] text-[var(--color-warning)]",
 color ==="danger" &&"bg-[var(--color-danger-bg)] text-[var(--color-danger)]",
 )}>
 <CheckCircle className="h-2.5 w-2.5" />
 {Math.round(value * 100)}%
 </span>
 )
}

function ScoreGauge({ label, value, max }: { label: string; value: number; max: number }) {
 const pct = Math.min((value / max) * 100, 100)
 const color = pct >= 70 ?"stroke-[var(--color-success)]" : pct >= 40 ?"stroke-[var(--color-warning)]" :"stroke-[var(--color-danger)]"
 return (
 <div className="flex flex-col items-center gap-1">
 <svg width="48" height="48" viewBox="0 0 48 48">
 <circle cx="24" cy="24" r="18" fill="none" stroke="currentColor" className="text-[var(--text-disabled)]" strokeWidth="4" />
 <circle cx="24" cy="24" r="18" fill="none" className={color} strokeWidth="4" strokeDasharray={`${(pct / 100) * 113} 113`} strokeLinecap="round" transform="rotate(-90 24 24)" />
 </svg>
 <span className="text-lg font-bold text-[var(--text-primary)]">{value}</span>
 <span className="text-[9px] text-[var(--text-muted)]">{label}</span>
 </div>
 )
}

export function DecisionPlatformPanel({ companyId, company360: externalCompany360 }: DecisionPlatformPanelProps) {
 const { data: fetchedCompany360, isLoading: loading360 } = useCompany360(companyId)
 const company360 = externalCompany360 ?? fetchedCompany360
 const { data: recommendations, isLoading: loadingRecs, isError: recsError } = useDecisionRecommendations(companyId,"company")
 const { data: scores, isLoading: loadingScores } = useDecisionScores(companyId,"company")

 const [expandedRec, setExpandedRec] = useState<string | null>(null)

 const isLoading = loading360 || loadingRecs || loadingScores

 const dealScore = scores?.find((s: { name?: string }) => s.name ==="deal_score")?.value || company360?.health_score || 0
 const nextBestActions = recommendations?.slice(0, 5) || []
 const riskFlags = scores?.filter((s: { name?: string; value: number }) => s.name?.includes("risk") && s.value > 0.3) || []

 if (isLoading) {
 return (
 <Card>
 <CardHeader>
 <div className="flex items-center gap-2">
          <Sparkles className="h-5 w-5 text-[var(--chart-purple)]" />
          <span className="text-sm font-semibold text-[var(--text-primary)]">منصة القرارات</span>
        </div>
      </CardHeader>
      <CardContent>
        <div className="space-y-4">
          <Skeleton variant="card" />
          <Skeleton variant="card" />
          <Skeleton variant="card" />
        </div>
      </CardContent>
    </Card>
    )
  }

  if (recsError && !nextBestActions.length && !riskFlags.length) {
    return (
    <Card>
      <CardHeader>
        <div className="flex items-center gap-2">
          <Sparkles className="h-5 w-5 text-[var(--chart-purple)]" />
          <span className="text-sm font-semibold text-[var(--text-primary)]">منصة القرارات</span>
        </div>
      </CardHeader>
      <CardContent>
        <EmptyState icon={<Sparkles className="h-10 w-10" />} title="لا توجد توصيات" description="تعذر تحميل توصيات منصة القرارات" />
      </CardContent>
    </Card>
    )
  }

  if (!nextBestActions.length && !riskFlags.length && !dealScore) {
    return (
    <Card>
      <CardHeader>
        <div className="flex items-center gap-2">
          <Sparkles className="h-5 w-5 text-[var(--chart-purple)]" />
          <span className="text-sm font-semibold text-[var(--text-primary)]">منصة القرارات</span>
 </div>
 </CardHeader>
 <CardContent>
 <EmptyState icon={<Sparkles className="h-10 w-10" />} title="لا توجد توصيات" description="لم يتم العثور على توصيات أو تقييمات لهذه الشركة" />
 </CardContent>
 </Card>
 )
 }

 return (
 <Card>
 <CardHeader>
        <div className="flex items-center gap-2">
          <Sparkles className="h-5 w-5 text-[var(--chart-purple)]" />
          <span className="text-sm font-semibold text-[var(--text-primary)]">منصة القرارات</span>
        </div>
      </CardHeader>
      <CardContent>
        <div className="space-y-5">
          {dealScore > 0 && (
            <div className="flex items-center justify-center gap-8 rounded-lg bg-[var(--bg-secondary)] p-4/50">
              <ScoreGauge label="درجة الصفقة" value={dealScore} max={100} />
              <div className="flex flex-col gap-2">
                <div className="flex items-center gap-2">
                  <Target className="h-4 w-4 text-[var(--chart-purple)]" />
 <span className="text-xs text-[var(--text-secondary)]">
 {dealScore >= 70 ?"جاهزة للإغلاق" : dealScore >= 40 ?"في طور التقييم" :"تحتاج متابعة"}
 </span>
 </div>
 {scores?.slice(0, 3).map((s: { name?: string; value: number; label?: string }) => (
 <div key={s.name || s.label} className="flex items-center gap-2">
 <BarChart3 className="h-3 w-3 text-[var(--text-disabled)]" />
 <span className="text-[10px] text-[var(--text-muted)]">{s.label || s.name}: {Math.round(s.value * 100)}%</span>
 </div>
 ))}
 </div>
 </div>
 )}

 {nextBestActions.length > 0 && (
 <div>
 <h4 className="mb-2 flex items-center gap-1.5 text-xs font-semibold text-[var(--text-secondary)]">
                <Lightbulb className="h-3.5 w-3.5 text-[var(--chart-purple)]" />
 الإجراءات التالية
 </h4>
 <div className="space-y-2">
 {nextBestActions.map((rec: { id?: string; action?: string; title?: string; description?: string; reasoning?: string; confidence?: number; impact?: string; priority?: string }, i: number) => {
 const id = rec.id || String(i)
 const isExpanded = expandedRec === id
 return (
 <div key={id} className="rounded-lg border border-[var(--border-default)]">
 <button
 onClick={() => setExpandedRec(isExpanded ? null : id)}
 className="flex w-full items-center gap-3 px-3 py-2.5 text-left transition-colors hover:bg-[var(--bg-secondary)] dark:hover:bg-[var(--bg-secondary)]/50"
 >
                    <div className="flex h-7 w-7 shrink-0 items-center justify-center rounded-full bg-[var(--chart-purple-bg)] text-[var(--text-secondary)] dark:bg-[var(--bg-primary)]/30 dark:text-[var(--chart-purple)]">
 <Zap className="h-3.5 w-3.5" />
 </div>
 <div className="min-w-0 flex-1">
 <p className="text-sm font-medium text-[var(--text-primary)]">
 {rec.title || rec.action}
 </p>
 <p className="mt-0.5 text-[10px] text-[var(--text-muted)]">{rec.description || rec.reasoning}</p>
 </div>
 <div className="flex shrink-0 items-center gap-2">
 {rec.confidence !== undefined && <ConfidenceBadge value={rec.confidence} />}
 {isExpanded ? <ChevronUp className="h-4 w-4 text-[var(--text-disabled)]" /> : <ChevronDown className="h-4 w-4 text-[var(--text-disabled)]" />}
 </div>
 </button>
 {isExpanded && rec.description && (
 <div className="border-t border-[var(--border-subtle)] px-3 py-2">
 <p className="text-xs text-[var(--text-secondary)]">{rec.description}</p>
 {(() => {
 const recAny = rec as Record<string, unknown>
 const risks = Array.isArray(recAny.risks) ? recAny.risks as string[] : null
 if (!risks) return null
 return (
 <div className="mt-2 flex flex-wrap gap-1">
 {risks.map((risk: string, ri: number) => (
 <span key={ri} className="inline-flex items-center gap-1 rounded-full bg-[var(--color-danger-bg)] px-1.5 py-0.5 text-[9px] text-[var(--color-danger)]">
 <AlertTriangle className="h-2.5 w-2.5" />
 {risk}
 </span>
 ))}
 </div>
 )
 })()}
 {rec.impact && (
 <div className="mt-2 flex items-center gap-1">
 <TrendingUp className="h-3 w-3 text-[var(--color-success)]" />
 <span className="text-[10px] text-[var(--color-success)]">الأثر: {rec.impact}</span>
 </div>
 )}
 </div>
 )}
 </div>
 )
 })}
 </div>
 </div>
 )}

 {riskFlags.length > 0 && (
 <div>
 <h4 className="mb-2 flex items-center gap-1.5 text-xs font-semibold text-[var(--color-danger)]">
 <Shield className="h-3.5 w-3.5" />
 مؤشرات الخطر
 </h4>
 <div className="space-y-1.5">
 {riskFlags.map((flag: { name?: string; value: number; label?: string; description?: string }, i: number) => (
 <div key={i} className="flex items-center gap-2 rounded-lg bg-[var(--color-danger-bg)]/50 px-3 py-2">
 <AlertTriangle className="h-3.5 w-3.5 shrink-0 text-[var(--color-danger)]" />
 <span className="text-xs text-[var(--color-danger)]">{flag.label || flag.name}</span>
 </div>
 ))}
 </div>
 </div>
 )}
 </div>
 </CardContent>
 </Card>
 )
}
