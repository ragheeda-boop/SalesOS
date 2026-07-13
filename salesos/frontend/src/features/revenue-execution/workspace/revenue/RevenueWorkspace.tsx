"use client"

import { useState, useEffect } from "react"
import axios from "axios"
import { cn } from "@salesos/ui"
import { NBAWidget } from "../../widgets/nba-widget/NBAWidget"
import { PipelineWorkspace } from "../pipeline/PipelineWorkspace"
import { MeetingIntelligenceWidget } from "../../widgets/meeting-intelligence/MeetingIntelligenceWidget"
import { EmailIntelligenceWidget } from "../../widgets/email-intelligence/EmailIntelligenceWidget"

interface DashboardData {
  pipeline_summary: {
    total_value: number
    active_count: number
    health_map: Record<string, number>
  }
  active_opportunities: {
    id: string
    name: string
    stage: string
    value: number
    probability: number
    health: string
  }[]
  total_value: number
  opportunity_count: number
  recent_signals: {
    id: string
    title: string
    signal_type: string
    company_name: string
    created_at: string
  }[]
}

const HEALTH_COLORS: Record<string, string> = {
  healthy: "bg-success-500",
  at_risk: "bg-warning-500",
  critical: "bg-danger-500",
}

const STAGE_LABELS: Record<string, string> = {
  prospecting: "استكشاف",
  qualification: "تأهيل",
  proposal: "عرض",
  negotiation: "تفاوض",
  closed_won: "فوز",
  closed_lost: "خسارة",
}

export function RevenueWorkspace() {
  const [data, setData] = useState<DashboardData | null>(null)
  const [selectedOppId, setSelectedOppId] = useState<string | null>(null)
  const [activeView, setActiveView] = useState<"overview" | "pipeline" | "opportunity">("overview")
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    const load = async () => {
      try {
        const res = await axios.get("/api/v1/revenue/dashboard")
        setData(res.data)
      } finally {
        setLoading(false)
      }
    }
    load()
  }, [])

  if (loading || !data) {
    return <div className="animate-pulse h-96 bg-neutral-100 rounded-xl" />
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <h1 className="text-xl font-display text-[var(--text-primary)]">منصة الإيرادات</h1>
        <div className="flex gap-2">
          {(["overview", "pipeline", "opportunity"] as const).map((v) => (
            <button
              key={v}
              onClick={() => setActiveView(v)}
              className={cn(
                "px-3 py-1.5 text-sm rounded-lg",
                activeView === v
                  ? "bg-[var(--muhide-orange)] text-white"
                  : "text-[var(--text-muted)] hover:bg-[var(--bg-secondary)]"
              )}
            >
              {v === "overview" ? "نظرة عامة" : v === "pipeline" ? "الـ Pipeline" : "الفرصة"}
            </button>
          ))}
        </div>
      </div>

      {/* Overview View */}
      {activeView === "overview" && (
        <>
          {/* KPI Row */}
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
            <div className="rounded-xl border border-[var(--border-default)] bg-[var(--bg-primary)] p-4">
              <p className="text-xs text-[var(--text-muted)]">قيمة Pipeline</p>
              <p className="text-lg font-display text-[var(--text-primary)]">{data.total_value.toLocaleString()} SAR</p>
            </div>
            <div className="rounded-xl border border-[var(--border-default)] bg-[var(--bg-primary)] p-4">
              <p className="text-xs text-[var(--text-muted)]">الفرص النشطة</p>
              <p className="text-lg font-display text-[var(--text-primary)]">{data.opportunity_count}</p>
            </div>
            <div className="rounded-xl border border-[var(--border-default)] bg-[var(--bg-primary)] p-4">
              <p className="text-xs text-[var(--text-muted)]">الصحيحة</p>
              <p className="text-lg font-display text-success-600">{data.pipeline_summary?.health_map?.healthy || 0}</p>
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            {/* NBA Widget */}
            {selectedOppId && (
              <div className="col-span-1">
                <h3 className="text-sm font-semibold text-[var(--text-primary)] mb-3">التوصية القادمة</h3>
                <NBAWidget opportunityId={selectedOppId} />
              </div>
            )}

            {/* Active Opportunities */}
            <div className={cn("space-y-2", selectedOppId ? "col-span-1" : "col-span-2")}>
              <h3 className="text-sm font-semibold text-[var(--text-primary)] mb-3">الفرص النشطة</h3>
              <div className="space-y-2">
                {data.active_opportunities.map((opp) => (
                  <button
                    key={opp.id}
                    onClick={() => { setSelectedOppId(opp.id); setActiveView("opportunity") }}
                    className={cn(
                      "w-full text-right rounded-xl border p-3 transition-colors",
                      selectedOppId === opp.id
                        ? "border-[var(--muhide-orange)] bg-[var(--muhide-orange)]/5"
                        : "border-[var(--border-default)] bg-[var(--bg-primary)] hover:bg-[var(--bg-secondary)]"
                    )}
                  >
                    <div className="flex items-center justify-between">
                      <span className="text-sm font-medium text-[var(--text-primary)] truncate">{opp.name}</span>
                      <span className="w-2 h-2 rounded-full shrink-0" style={{ backgroundColor: HEALTH_COLORS[opp.health] || "#9CA3AF" }} />
                    </div>
                    <div className="flex items-center justify-between mt-1">
                      <span className="text-xs text-[var(--text-muted)]">{STAGE_LABELS[opp.stage] || opp.stage}</span>
                      <span className="text-xs text-[var(--text-muted)]">{opp.value.toLocaleString()} SAR</span>
                    </div>
                  </button>
                ))}
              </div>
            </div>

            {/* Recent Signals */}
            <div className="space-y-2">
              <h3 className="text-sm font-semibold text-[var(--text-primary)] mb-3">إشارات حديثة</h3>
              <div className="space-y-2">
                {data.recent_signals.map((s) => (
                  <div key={s.id} className="rounded-xl border border-[var(--border-default)] bg-[var(--bg-primary)] p-3">
                    <p className="text-xs font-medium text-[var(--text-primary)]">{s.title}</p>
                    <div className="flex items-center justify-between mt-1">
                      <span className="text-xs text-[var(--text-muted)]">{s.company_name}</span>
                      <span className="text-xs text-[var(--text-muted)]">{s.signal_type}</span>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </>
      )}

      {/* Pipeline View */}
      {activeView === "pipeline" && <PipelineWorkspace />}

      {/* Opportunity Detail View */}
      {activeView === "opportunity" && selectedOppId && (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <MeetingIntelligenceWidget opportunityId={selectedOppId} />
          <EmailIntelligenceWidget opportunityId={selectedOppId} />
        </div>
      )}
    </div>
  )
}
