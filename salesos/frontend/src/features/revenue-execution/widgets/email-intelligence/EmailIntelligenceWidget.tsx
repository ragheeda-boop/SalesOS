"use client"

import { useState } from "react"
import axios from "axios"
import { cn } from "@salesos/ui"

interface EmailAnalysis {
  sentiment: string
  topics: string[]
  action_items: string[]
  urgency: string
  key_entities: { type: string; value: string }[]
}

const SENTIMENT_CONFIG: Record<string, { label: string; color: string; bg: string }> = {
  positive: { label: "إيجابي", color: "text-success-600", bg: "bg-success-50" },
  neutral: { label: "محايد", color: "text-[var(--text-secondary)]", bg: "bg-[var(--bg-secondary)]" },
  negative: { label: "سلبي", color: "text-danger-600", bg: "bg-danger-50" },
}

const URGENCY_CONFIG: Record<string, { label: string; color: string; bg: string }> = {
  high: { label: "عاجل", color: "text-danger-600", bg: "bg-danger-50" },
  medium: { label: "متوسط", color: "text-warning-600", bg: "bg-warning-50" },
  low: { label: "منخفض", color: "text-success-600", bg: "bg-success-50" },
}

interface Props {
  opportunityId: string
  emails?: { id: string; subject: string; from_address: string; body: string; sent_at: string; direction: string }[]
}

interface EmailMessage {
  id: string
  subject: string
  from_address: string
  body: string
  sent_at: string
  direction: string
}

export function EmailIntelligenceWidget({ opportunityId, emails = [] }: Props) {
  const [analysis, setAnalysis] = useState<EmailAnalysis | null>(null)
  const [selectedEmail, setSelectedEmail] = useState<EmailMessage | null>(null)
  const [loading, setLoading] = useState(false)

  const analyzeEmail = async (email: EmailMessage) => {
    setSelectedEmail(email)
    setLoading(true)
    try {
      const res = await axios.post("/api/v1/emails/analyze", {
        opportunity_id: opportunityId,
        subject: email.subject,
        from_address: email.from_address,
        to_addresses: [],
        body: email.body,
        direction: email.direction,
        email_type: "general",
      })
      setAnalysis(res.data)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="space-y-4">
      {/* Email List */}
      <div className="space-y-2">
        {emails.length === 0 ? (
          <p className="text-sm text-[var(--text-muted)] text-center py-8">لا توجد رسائل بريد</p>
        ) : (
          emails.map((e) => (
            <button
              key={e.id}
              onClick={() => analyzeEmail(e)}
              className={cn(
                "w-full text-right rounded-xl border p-3 transition-colors",
                selectedEmail?.id === e.id
                  ? "border-[var(--muhide-orange)] bg-[var(--muhide-orange)]/5"
                  : "border-[var(--border-default)] bg-[var(--bg-primary)] hover:bg-[var(--bg-secondary)]"
              )}
            >
              <div className="flex items-center justify-between">
                <span className="text-sm font-medium text-[var(--text-primary)] truncate">{e.subject}</span>
                <span className={cn("text-xs px-1.5 py-0.5 rounded", e.direction === "inbound" ? "bg-info-50 text-info-600" : "bg-success-50 text-success-600")}>
                  {e.direction === "inbound" ? "وارد" : "صادر"}
                </span>
              </div>
              <p className="text-xs text-[var(--text-muted)] mt-1">{e.from_address} • {new Date(e.sent_at).toLocaleDateString("ar-SA")}</p>
            </button>
          ))
        )}
      </div>

      {/* Analysis Panel */}
      {analysis && (
        <div className="space-y-3 rounded-xl border border-[var(--border-default)] bg-[var(--bg-primary)] p-4">
          <h4 className="text-sm font-semibold text-[var(--text-primary)]">تحليل البريد</h4>

          {/* Sentiment & Urgency */}
          <div className="flex gap-2">
            <span className={cn("text-xs px-2 py-1 rounded-lg", SENTIMENT_CONFIG[analysis.sentiment]?.bg, SENTIMENT_CONFIG[analysis.sentiment]?.color)}>
              {SENTIMENT_CONFIG[analysis.sentiment]?.label || analysis.sentiment}
            </span>
            <span className={cn("text-xs px-2 py-1 rounded-lg", URGENCY_CONFIG[analysis.urgency]?.bg, URGENCY_CONFIG[analysis.urgency]?.color)}>
              {URGENCY_CONFIG[analysis.urgency]?.label || analysis.urgency}
            </span>
          </div>

          {/* Topics */}
          {analysis.topics.length > 0 && (
            <div>
              <p className="text-xs font-medium text-[var(--text-secondary)] mb-1">المواضيع</p>
              <div className="flex flex-wrap gap-1">
                {analysis.topics.map((t, i) => (
                  <span key={i} className="text-xs px-2 py-0.5 rounded-full bg-[var(--bg-secondary)] text-[var(--text-secondary)]">
                    {t}
                  </span>
                ))}
              </div>
            </div>
          )}

          {/* Action Items */}
          {analysis.action_items.length > 0 && (
            <div>
              <p className="text-xs font-medium text-[var(--text-secondary)] mb-1">إجراءات مطلوبة</p>
              <ul className="space-y-1">
                {analysis.action_items.map((a, i) => (
                  <li key={i} className="text-xs text-[var(--text-secondary)] flex items-start gap-2">
                    <span className="w-1.5 h-1.5 rounded-full bg-warning-500 mt-1.5 shrink-0" />
                    {a}
                  </li>
                ))}
              </ul>
            </div>
          )}
        </div>
      )}
    </div>
  )
}
