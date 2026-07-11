"use client"

import { useState, useEffect } from "react"
import axios from "axios"
import { cn } from "@salesos/ui"

interface Brief {
  company_name: string
  opportunity_name: string
  opportunity_stage: string
  opportunity_value: number
  recent_signals: string[]
  key_contacts: string[]
  talking_points: string[]
  questions_to_ask: string[]
  ai_summary?: string
}

interface MeetingSummary {
  key_topics: string[]
  action_items: string[]
  sentiment: string
  ai_summary?: string
}

const SENTIMENT_MAP: Record<string, { label: string; color: string }> = {
  positive: { label: "إيجابي", color: "text-success-600" },
  neutral: { label: "محايد", color: "text-[var(--text-secondary)]" },
  negative: { label: "سلبي", color: "text-danger-600" },
}

interface Props {
  opportunityId: string
}

export function MeetingIntelligenceWidget({ opportunityId }: Props) {
  const [brief, setBrief] = useState<Brief | null>(null)
  const [meetings, setMeetings] = useState<any[]>([])
  const [activeTab, setActiveTab] = useState<"brief" | "meetings">("brief")
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    const load = async () => {
      try {
        const [briefRes, meetingsRes] = await Promise.all([
          axios.post(`/api/v1/meetings/${opportunityId}/brief`),
          axios.get(`/api/v1/meetings/${opportunityId}`),
        ])
        setBrief(briefRes.data)
        setMeetings(meetingsRes.data || [])
      } finally {
        setLoading(false)
      }
    }
    load()
  }, [opportunityId])

  if (loading) return <div className="animate-pulse h-64 bg-neutral-100 rounded-xl" />

  return (
    <div className="space-y-4">
      {/* Tab Switch */}
      <div className="flex gap-2">
        <button
          onClick={() => setActiveTab("brief")}
          className={cn("px-3 py-1.5 text-sm rounded-lg", activeTab === "brief" ? "bg-[var(--muhide-orange)] text-white" : "text-[var(--text-muted)] hover:bg-[var(--bg-secondary)]")}
        >
          تحضير الاجتماع
        </button>
        <button
          onClick={() => setActiveTab("meetings")}
          className={cn("px-3 py-1.5 text-sm rounded-lg", activeTab === "meetings" ? "bg-[var(--muhide-orange)] text-white" : "text-[var(--text-muted)] hover:bg-[var(--bg-secondary)]")}
        >
          الاجتماعات السابقة
        </button>
      </div>

      {activeTab === "brief" && brief && (
        <div className="space-y-4">
          {/* AI Summary */}
          {brief.ai_summary && (
            <div className="rounded-xl border border-[var(--muhide-orange)]/20 bg-[var(--muhide-orange)]/5 p-4">
              <h4 className="text-sm font-semibold text-[var(--muhide-orange)] mb-2">ملخص ذكي</h4>
              <p className="text-sm text-[var(--text-primary)] leading-relaxed">{brief.ai_summary}</p>
            </div>
          )}

          {/* Company & Opportunity */}
          <div className="rounded-xl border border-[var(--border-default)] bg-[var(--bg-primary)] p-4 space-y-2">
            <h4 className="text-sm font-semibold text-[var(--text-primary)]">{brief.company_name}</h4>
            <div className="grid grid-cols-2 gap-2 text-xs">
              <span className="text-[var(--text-muted)]">الفرصة: <span className="text-[var(--text-primary)]">{brief.opportunity_name}</span></span>
              <span className="text-[var(--text-muted)]">المرحلة: <span className="text-[var(--text-primary)]">{brief.opportunity_stage}</span></span>
              <span className="text-[var(--text-muted)]">القيمة: <span className="text-[var(--text-primary)]">{brief.opportunity_value.toLocaleString()} SAR</span></span>
            </div>
          </div>

          {/* Recent Signals */}
          {brief.recent_signals.length > 0 && (
            <div className="rounded-xl border border-[var(--border-default)] bg-[var(--bg-primary)] p-4">
              <h4 className="text-sm font-semibold text-[var(--text-primary)] mb-2">إشارات حديثة</h4>
              <ul className="space-y-1">
                {brief.recent_signals.map((s, i) => (
                  <li key={i} className="text-xs text-[var(--text-secondary)] flex items-start gap-2">
                    <span className="w-1.5 h-1.5 rounded-full bg-[var(--muhide-orange)] mt-1.5 shrink-0" />
                    {s}
                  </li>
                ))}
              </ul>
            </div>
          )}

          {/* Talking Points */}
          {brief.talking_points.length > 0 && (
            <div className="rounded-xl border border-[var(--border-default)] bg-[var(--bg-primary)] p-4">
              <h4 className="text-sm font-semibold text-[var(--text-primary)] mb-2">نقاط الحديث</h4>
              <ul className="space-y-1">
                {brief.talking_points.map((p, i) => (
                  <li key={i} className="text-xs text-[var(--text-secondary)] flex items-start gap-2">
                    <span className="w-1.5 h-1.5 rounded-full bg-success-500 mt-1.5 shrink-0" />
                    {p}
                  </li>
                ))}
              </ul>
            </div>
          )}

          {/* Questions to Ask */}
          {brief.questions_to_ask.length > 0 && (
            <div className="rounded-xl border border-[var(--border-default)] bg-[var(--bg-primary)] p-4">
              <h4 className="text-sm font-semibold text-[var(--text-primary)] mb-2">أسئلة مقترحة</h4>
              <ul className="space-y-1">
                {brief.questions_to_ask.map((q, i) => (
                  <li key={i} className="text-xs text-[var(--text-secondary)] flex items-start gap-2">
                    <span className="w-1.5 h-1.5 rounded-full bg-[var(--info)] mt-1.5 shrink-0" />
                    {q}
                  </li>
                ))}
              </ul>
            </div>
          )}

          {/* Key Contacts */}
          {brief.key_contacts.length > 0 && (
            <div className="rounded-xl border border-[var(--border-default)] bg-[var(--bg-primary)] p-4">
              <h4 className="text-sm font-semibold text-[var(--text-primary)] mb-2">جهات الاتصال الرئيسية</h4>
              <ul className="space-y-1">
                {brief.key_contacts.map((c, i) => (
                  <li key={i} className="text-xs text-[var(--text-secondary)]">{c}</li>
                ))}
              </ul>
            </div>
          )}
        </div>
      )}

      {activeTab === "meetings" && (
        <div className="space-y-3">
          {meetings.length === 0 ? (
            <p className="text-sm text-[var(--text-muted)] text-center py-8">لا توجد اجتماعات سابقة</p>
          ) : (
            meetings.map((m) => (
              <div key={m.id} className="rounded-xl border border-[var(--border-default)] bg-[var(--bg-primary)] p-4">
                <div className="flex items-center justify-between">
                  <h4 className="text-sm font-medium text-[var(--text-primary)]">{m.title}</h4>
                  <span className={cn("text-xs", m.status === "completed" ? "text-success-600" : "text-warning-600")}>
                    {m.status === "completed" ? "مكتمل" : "مجدول"}
                  </span>
                </div>
                <p className="text-xs text-[var(--text-muted)] mt-1">
                  {new Date(m.meeting_date).toLocaleDateString("ar-SA")} • {m.duration_minutes} دقيقة
                </p>
                {m.notes && (
                  <p className="text-xs text-[var(--text-secondary)] mt-2 line-clamp-2">{m.notes}</p>
                )}
              </div>
            ))
          )}
        </div>
      )}
    </div>
  )
}
