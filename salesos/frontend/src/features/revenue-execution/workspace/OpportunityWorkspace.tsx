"use client"

import { useCallback } from "react"
import axios from "axios"
import { NBAWidget } from "../widgets/nba-widget/NBAWidget"

interface Opportunity {
  id: string
  companyId: string
  name: string
  stage: string
  value: number
  currency: string
  probability: number
  health: string
  expectedCloseDate?: string
  ownerId: string
  status: string
  description: string
  createdAt: string
  updatedAt: string
}

interface OpportunityWorkspaceProps {
  opportunityId: string
}

export function OpportunityWorkspace({ opportunityId }: OpportunityWorkspaceProps) {
  // In a full implementation, this would use createWorkspaceProvider
  // from @salesos/workspace. For now, inline data fetching.

  const [opportunity, setOpportunity] = useState<Opportunity | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    const load = async () => {
      try {
        const { data } = await axios.get(`/api/v1/opportunities/${opportunityId}`)
        setOpportunity(data)
      } finally {
        setLoading(false)
      }
    }
    load()
  }, [opportunityId])

  if (loading) return <div className="animate-pulse h-96 bg-neutral-100 rounded-xl" />

  if (!opportunity) return (
    <div className="flex items-center justify-center h-96 text-[var(--text-muted)]">
      لم يتم العثور على الفرصة
    </div>
  )

  const stageLabels: Record<string, string> = {
    prospecting: "استكشاف",
    qualification: "تأهيل",
    proposal: "عرض",
    negotiation: "تفاوض",
    closed_won: "فوز",
    closed_lost: "خسارة",
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-xl font-display text-[var(--text-primary)]">{opportunity.name}</h1>
          <div className="flex items-center gap-3 mt-1">
            <span className="text-sm px-2 py-0.5 rounded-full bg-[var(--bg-secondary)] text-[var(--text-secondary)]">
              {stageLabels[opportunity.stage] || opportunity.stage}
            </span>
            <span className="text-sm font-medium text-[var(--text-primary)]">
              {opportunity.value.toLocaleString()} {opportunity.currency}
            </span>
            <span className={cn(
              "text-xs px-2 py-0.5 rounded-full",
              opportunity.health === 'healthy' && "bg-success-100 text-success-700",
              opportunity.health === 'at_risk' && "bg-warning-100 text-warning-700",
              opportunity.health === 'critical' && "bg-danger-100 text-danger-700",
            )}>
              {opportunity.health === 'healthy' ? 'سليم' : opportunity.health === 'at_risk' ? 'في خطر' : 'حرج'}
            </span>
          </div>
        </div>
      </div>

      {/* Two-column layout */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left: NBA + Timeline */}
        <div className="lg:col-span-2 space-y-6">
          {/* NBA Widget */}
          <section aria-label="Next Best Action">
            <NBAWidget opportunityId={opportunityId} />
          </section>

          {/* Timeline (placeholder — would use Activity Runtime) */}
          <section className="rounded-xl border border-[var(--border-default)] bg-[var(--bg-primary)] p-4">
            <h3 className="text-sm font-semibold text-[var(--text-primary)] mb-3">النشاطات</h3>
            <p className="text-sm text-[var(--text-muted)]">سيتم عرض النشاطات قريبًا</p>
          </section>
        </div>

        {/* Right: Company Snapshot + Deal Health */}
        <div className="space-y-6">
          {/* Company Snapshot */}
          <section className="rounded-xl border border-[var(--border-default)] bg-[var(--bg-primary)] p-4">
            <h3 className="text-sm font-semibold text-[var(--text-primary)] mb-3">الشركة</h3>
            <p className="text-sm text-[var(--text-muted)]">معلومات الشركة من Company Intelligence</p>
          </section>

          {/* Deal Health */}
          <section className="rounded-xl border border-[var(--border-default)] bg-[var(--bg-primary)] p-4">
            <h3 className="text-sm font-semibold text-[var(--text-primary)] mb-3">صحة الفرصة</h3>
            <p className="text-sm text-[var(--text-muted)]">مؤشرات الصحة قريبًا</p>
          </section>
        </div>
      </div>
    </div>
  )
}

import { useState, useEffect } from "react"
import { cn } from "@salesos/ui"
