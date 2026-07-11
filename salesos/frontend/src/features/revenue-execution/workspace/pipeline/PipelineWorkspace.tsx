"use client"

import { useState, useEffect } from "react"
import axios from "axios"
import { cn } from "@salesos/ui"

interface Opportunity {
  id: string
  name: string
  stage: string
  value: number
  currency: string
  probability: number
  health: string
  ownerId: string
}

interface HealthMapItem {
  opportunity_id: string
  name: string
  stage: string
  value: number
  health: string
  health_score: number
  owner: string
}

interface Forecast {
  best_case: number
  commit: number
  pipeline: number
  gap: number
  avg_probability: number
}

const STAGE_ORDER = ["prospecting", "qualification", "proposal", "negotiation", "closed_won", "closed_lost"]
const STAGE_LABELS: Record<string, string> = {
  prospecting: "استكشاف",
  qualification: "تأهيل",
  proposal: "عرض",
  negotiation: "تفاوض",
  closed_won: "فوز",
  closed_lost: "خسارة",
}

const HEALTH_COLORS: Record<string, string> = {
  healthy: "bg-success-500",
  at_risk: "bg-warning-500",
  critical: "bg-danger-500",
}

const HEALTH_BG: Record<string, string> = {
  healthy: "bg-success-50 border-success-200",
  at_risk: "bg-warning-50 border-warning-200",
  critical: "bg-danger-50 border-danger-200",
}

export function PipelineWorkspace() {
  const [opportunities, setOpportunities] = useState<Opportunity[]>([])
  const [healthMap, setHealthMap] = useState<HealthMapItem[]>([])
  const [forecast, setForecast] = useState<Forecast | null>(null)
  const [loading, setLoading] = useState(true)
  const [view, setView] = useState<'kanban' | 'list'>('kanban')

  useEffect(() => {
    const load = async () => {
      try {
        const [oppsRes, healthRes, forecastRes] = await Promise.all([
          axios.get('/api/v1/opportunities', { params: { limit: 200 } }),
          axios.get('/api/v1/pipeline/health'),
          axios.get('/api/v1/pipeline/forecast'),
        ])
        setOpportunities(oppsRes.data || [])
        setHealthMap(healthRes.data || [])
        setForecast(forecastRes.data)
      } finally {
        setLoading(false)
      }
    }
    load()
  }, [])

  if (loading) {
    return <div className="animate-pulse h-96 bg-neutral-100 rounded-xl" />
  }

  const groupedByStage: Record<string, Opportunity[]> = {}
  STAGE_ORDER.forEach((s) => { groupedByStage[s] = [] })
  opportunities.forEach((o) => {
    if (groupedByStage[o.stage]) groupedByStage[o.stage].push(o)
  })

  const stageTotals = STAGE_ORDER.map((stage) => {
    const items = groupedByStage[stage] || []
    return {
      stage,
      label: STAGE_LABELS[stage] || stage,
      count: items.length,
      value: items.reduce((sum, o) => sum + o.value, 0),
    }
  })

  const healthyCount = healthMap.filter((h) => h.health === 'healthy').length
  const atRiskCount = healthMap.filter((h) => h.health === 'at_risk').length
  const criticalCount = healthMap.filter((h) => h.health === 'critical').length

  return (
    <div className="space-y-6">
      {/* Header + Forecast */}
      <div className="flex items-center justify-between">
        <h1 className="text-xl font-display text-[var(--text-primary)]">Pipeline</h1>
        <div className="flex items-center gap-2">
          <button
            onClick={() => setView('kanban')}
            className={cn("px-3 py-1.5 text-sm rounded-lg", view === 'kanban' ? "bg-[var(--muhide-orange)] text-white" : "text-[var(--text-muted)] hover:bg-[var(--bg-secondary)]")}
          >
            كانبان
          </button>
          <button
            onClick={() => setView('list')}
            className={cn("px-3 py-1.5 text-sm rounded-lg", view === 'list' ? "bg-[var(--muhide-orange)] text-white" : "text-[var(--text-muted)] hover:bg-[var(--bg-secondary)]")}
          >
            جدول
          </button>
        </div>
      </div>

      {/* Forecast Cards */}
      {forecast && (
        <div className="grid grid-cols-4 gap-4">
          <div className="rounded-xl border border-[var(--border-default)] bg-[var(--bg-primary)] p-4">
            <p className="text-xs text-[var(--text-muted)]">أفضل سيناريو</p>
            <p className="text-lg font-display text-success-600">{forecast.best_case.toLocaleString()} SAR</p>
          </div>
          <div className="rounded-xl border border-[var(--border-default)] bg-[var(--bg-primary)] p-4">
            <p className="text-xs text-[var(--text-muted)]">ملتزم به</p>
            <p className="text-lg font-display text-[var(--muhide-orange)]">{forecast.commit.toLocaleString()} SAR</p>
          </div>
          <div className="rounded-xl border border-[var(--border-default)] bg-[var(--bg-primary)] p-4">
            <p className="text-xs text-[var(--text-muted)]"> Pipeline</p>
            <p className="text-lg font-display text-[var(--text-primary)]">{forecast.pipeline.toLocaleString()} SAR</p>
          </div>
          <div className="rounded-xl border border-[var(--border-default)] bg-[var(--bg-primary)] p-4">
            <p className="text-xs text-[var(--text-muted)]">احتمال متوسط</p>
            <p className="text-lg font-display text-[var(--text-primary)]">{Math.round(forecast.avg_probability * 100)}%</p>
          </div>
        </div>
      )}

      {/* Health Map */}
      <div className="flex items-center gap-4">
        <div className="flex items-center gap-1.5">
          <span className="w-2.5 h-2.5 rounded-full bg-success-500" />
          <span className="text-xs text-[var(--text-secondary)]">{healthyCount} سليم</span>
        </div>
        <div className="flex items-center gap-1.5">
          <span className="w-2.5 h-2.5 rounded-full bg-warning-500" />
          <span className="text-xs text-[var(--text-secondary)]">{atRiskCount} في خطر</span>
        </div>
        <div className="flex items-center gap-1.5">
          <span className="w-2.5 h-2.5 rounded-full bg-danger-500" />
          <span className="text-xs text-[var(--text-secondary)]">{criticalCount} حرج</span>
        </div>
      </div>

      {/* Kanban / List View */}
      {view === 'kanban' ? (
        <div className="grid grid-cols-4 gap-4">
          {stageTotals.filter(s => !s.stage.includes('closed')).map((stage) => (
            <div key={stage.stage} className="rounded-xl border border-[var(--border-default)] bg-[var(--bg-secondary)] p-3">
              <div className="flex items-center justify-between mb-3">
                <h3 className="text-sm font-semibold text-[var(--text-primary)]">{stage.label}</h3>
                <span className="text-xs text-[var(--text-muted)]">{stage.count} | {stage.value.toLocaleString()}</span>
              </div>
              <div className="space-y-2">
                {(groupedByStage[stage.stage] || []).slice(0, 10).map((opp) => (
                  <div key={opp.id} className={cn(
                    "rounded-lg border p-3 bg-[var(--bg-primary)] cursor-pointer hover:shadow-sm transition-shadow",
                    HEALTH_BG[opp.health] || "border-[var(--border-default)]"
                  )}>
                    <p className="text-sm font-medium text-[var(--text-primary)] truncate">{opp.name}</p>
                    <div className="flex items-center justify-between mt-1">
                      <span className="text-xs text-[var(--text-muted)]">{opp.value.toLocaleString()} SAR</span>
                      <span className={cn("w-2 h-2 rounded-full", HEALTH_COLORS[opp.health] || "bg-neutral-300")} />
                    </div>
                  </div>
                ))}
                {(groupedByStage[stage.stage] || []).length > 10 && (
                  <p className="text-xs text-center text-[var(--text-muted)]">+{groupedByStage[stage.stage].length - 10} أخرى</p>
                )}
              </div>
            </div>
          ))}
        </div>
      ) : (
        <div className="rounded-xl border border-[var(--border-default)] bg-[var(--bg-primary)] overflow-hidden">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-[var(--border-default)] bg-[var(--bg-secondary)]">
                <th className="text-right px-4 py-3 font-medium text-[var(--text-secondary)]">الاسم</th>
                <th className="text-right px-4 py-3 font-medium text-[var(--text-secondary)]">المرحلة</th>
                <th className="text-right px-4 py-3 font-medium text-[var(--text-secondary)]">القيمة</th>
                <th className="text-right px-4 py-3 font-medium text-[var(--text-secondary)]">الاحتمال</th>
                <th className="text-right px-4 py-3 font-medium text-[var(--text-secondary)]">الصحة</th>
              </tr>
            </thead>
            <tbody>
              {opportunities.filter(o => o.status !== 'closed').map((opp) => (
                <tr key={opp.id} className="border-b border-[var(--border-default)] hover:bg-[var(--bg-secondary)]">
                  <td className="px-4 py-3 text-[var(--text-primary)]">{opp.name}</td>
                  <td className="px-4 py-3 text-[var(--text-secondary)]">{STAGE_LABELS[opp.stage] || opp.stage}</td>
                  <td className="px-4 py-3 text-[var(--text-primary)]">{opp.value.toLocaleString()} {opp.currency}</td>
                  <td className="px-4 py-3">{Math.round(opp.probability * 100)}%</td>
                  <td className="px-4 py-3">
                    <span className={cn("w-2 h-2 rounded-full inline-block", HEALTH_COLORS[opp.health] || "bg-neutral-300")} />
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  )
}
