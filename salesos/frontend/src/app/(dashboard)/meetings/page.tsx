"use client"

import { useState, useEffect } from "react"
import axios from "axios"
import { useTranslation } from "@/lib/i18n"
import { cn } from "@salesos/ui"
import { Calendar, Users, AlertTriangle, Lightbulb, Target, ChevronDown, Mail } from "lucide-react"

interface Opportunity {
  id: string
  name: string
  company_name?: string
  stage?: string
  value?: number
}

interface Meeting {
  id: string
  title: string
  date: string
  duration_minutes?: number
  status: string
  notes?: string
}

interface MeetingBrief {
  company_name?: string
  meeting_title?: string
  date?: string
  attendees?: { name: string; role: string; influence: string }[]
  recent_signals?: string[]
  risks?: string[]
  opportunities?: string[]
  talking_points?: string[]
  recommended_action?: string
}

export default function MeetingsPage() {
  const { t } = useTranslation()
  const [opportunities, setOpportunities] = useState<Opportunity[]>([])
  const [selected, setSelected] = useState<string | null>(null)
  const [brief, setBrief] = useState<MeetingBrief | null>(null)
  const [meetings, setMeetings] = useState<Meeting[]>([])
  const [loading, setLoading] = useState(true)
  const [briefLoading, setBriefLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [showDropdown, setShowDropdown] = useState(false)

  useEffect(() => {
    axios.get("/api/v1/opportunities?limit=100")
      .then(res => { setOpportunities(res.data.records || res.data || []); setLoading(false) })
      .catch(() => { setError(t("error.server_error")); setLoading(false) })
  }, [t])

  const loadMeetingData = async (oppId: string) => {
    setBriefLoading(true)
    try {
      const [briefRes, meetingsRes] = await Promise.allSettled([
        axios.post(`/api/v1/meetings/${oppId}/brief`),
        axios.get(`/api/v1/meetings/${oppId}`),
      ])
      if (briefRes.status === "fulfilled") setBrief(briefRes.value.data)
      if (meetingsRes.status === "fulfilled") setMeetings(meetingsRes.value.data.records || meetingsRes.value.data || [])
    } catch { /* graceful */}
    setBriefLoading(false)
  }

  const handleSelect = (id: string) => {
    setSelected(id)
    setShowDropdown(false)
    loadMeetingData(id)
  }

  const selectedOpp = opportunities.find(o => o.id === selected)

  if (loading) return <div className="p-8 text-center text-neutral-500">{t("common.loading")}</div>
  if (error) return <div className="p-8 text-center text-red-500">{error}</div>

  return (
    <div className="p-6 space-y-6">
      <h1 className="text-2xl font-bold">{t("meetings.title")}</h1>

      <div className="relative">
        <button
          onClick={() => setShowDropdown(!showDropdown)}
          className="flex items-center gap-2 w-full max-w-md px-4 py-2.5 border rounded-lg bg-white dark:bg-neutral-900 text-sm hover:border-[var(--muhide-orange)] transition"
        >
          {selectedOpp ? (
            <span>{selectedOpp.name} {selectedOpp.company_name && `— ${selectedOpp.company_name}`}</span>
          ) : (
            <span className="text-neutral-400">{t("meetings.select_opportunity")}</span>
          )}
          <ChevronDown className="h-4 w-4 ms-auto text-neutral-400" />
        </button>
        {showDropdown && (
          <div className="absolute z-10 mt-1 w-full max-w-md max-h-60 overflow-y-auto border rounded-lg bg-white dark:bg-neutral-900 shadow-lg">
            {opportunities.length === 0 && (
              <p className="p-3 text-sm text-neutral-500">{t("common.no_results")}</p>
            )}
            {opportunities.map(o => (
              <button
                key={o.id}
                onClick={() => handleSelect(o.id)}
                className="w-full text-left px-4 py-2.5 text-sm hover:bg-[var(--muhide-orange)]/5 transition"
              >
                <span className="font-medium">{o.name}</span>
                {o.company_name && <span className="text-neutral-400 ms-2">— {o.company_name}</span>}
              </button>
            ))}
          </div>
        )}
      </div>

      {selected && briefLoading && (
        <div className="p-8 text-center text-neutral-500">{t("common.loading")}</div>
      )}

      {selected && !briefLoading && (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          <div className="lg:col-span-2 space-y-4">
            {brief && (
              <div className="rounded-lg border p-4 bg-white dark:bg-neutral-900 space-y-4">
                <h2 className="text-lg font-bold flex items-center gap-2">
                  <Target className="h-5 w-5 text-[var(--muhide-orange)]" />
                  {t("meetings.brief")}
                </h2>

                {brief.recommended_action && (
                  <div className="p-3 bg-[var(--muhide-orange)]/10 rounded-lg border border-[var(--muhide-orange)]/20">
                    <p className="text-sm font-medium text-[var(--muhide-orange)]">{t("meetings.recommended_action")}</p>
                    <p className="text-sm mt-1">{brief.recommended_action}</p>
                  </div>
                )}

                {brief.talking_points && brief.talking_points.length > 0 && (
                  <div>
                    <h4 className="text-sm font-medium flex items-center gap-1"><Lightbulb className="h-4 w-4" /> {t("meetings.talking_points")}</h4>
                    <ul className="mt-1 space-y-1">
                      {brief.talking_points.map((p, i) => (
                        <li key={i} className="text-sm text-neutral-600 dark:text-neutral-400 flex items-start gap-2">
                          <span className="text-[var(--muhide-orange)] mt-1">•</span> {p}
                        </li>
                      ))}
                    </ul>
                  </div>
                )}

                {brief.risks && brief.risks.length > 0 && (
                  <div className="p-3 bg-red-50 dark:bg-red-900/20 rounded-lg border border-red-200 dark:border-red-800">
                    <h4 className="text-sm font-medium text-red-700 dark:text-red-400 flex items-center gap-1">
                      <AlertTriangle className="h-4 w-4" /> {t("meetings.risks")}
                    </h4>
                    <ul className="mt-1 space-y-1">
                      {brief.risks.map((r, i) => (
                        <li key={i} className="text-sm text-red-600 dark:text-red-300">• {r}</li>
                      ))}
                    </ul>
                  </div>
                )}
              </div>
            )}

            {meetings.length > 0 && (
              <div className="rounded-lg border p-4 bg-white dark:bg-neutral-900">
                <h3 className="font-bold mb-3">{t("meetings.past_meetings")}</h3>
                <div className="space-y-2">
                  {meetings.map(m => (
                    <div key={m.id} className="flex items-center justify-between p-3 rounded-lg bg-neutral-50 dark:bg-neutral-800">
                      <div>
                        <p className="font-medium text-sm">{m.title}</p>
                        <p className="text-xs text-neutral-500">{m.date}{m.duration_minutes && ` · ${m.duration_minutes}min`}</p>
                      </div>
                      <span className={cn(
                        "px-2 py-0.5 rounded text-xs font-medium",
                        m.status === "completed" && "bg-green-100 text-green-700",
                        m.status === "scheduled" && "bg-blue-100 text-blue-700"
                      )}>{m.status}</span>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {!brief && !briefLoading && meetings.length === 0 && (
              <p className="text-neutral-500 p-8 text-center">{t("common.no_results")}</p>
            )}
          </div>

          {brief?.attendees && brief.attendees.length > 0 && (
            <div className="rounded-lg border p-4 bg-white dark:bg-neutral-900 h-fit">
              <h3 className="font-bold mb-3 flex items-center gap-2">
                <Users className="h-4 w-4" /> {t("meetings.attendees")}
              </h3>
              <div className="space-y-2">
                {brief.attendees.map((a, i) => (
                  <div key={i} className="flex items-center justify-between p-2 rounded bg-neutral-50 dark:bg-neutral-800">
                    <div>
                      <p className="text-sm font-medium">{a.name}</p>
                      <p className="text-xs text-neutral-500">{a.role}</p>
                    </div>
                    <span className="text-xs px-2 py-0.5 rounded bg-[var(--muhide-orange)]/10 text-[var(--muhide-orange)]">{a.influence}</span>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}

      {!selected && !loading && (
        <div className="flex flex-col items-center justify-center min-h-[300px] text-neutral-500">
          <Calendar className="h-12 w-12 mb-4 text-neutral-300" />
          <p>{t("meetings.select_prompt")}</p>
        </div>
      )}
    </div>
  )
}
