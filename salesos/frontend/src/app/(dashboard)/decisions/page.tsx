"use client"

import { useState, useEffect } from "react"
import axios from "axios"
import { useTranslation } from "@/lib/i18n"
import { cn } from "@salesos/ui"
import { Check, X, ChevronRight } from "lucide-react"

interface DecisionItem {
  id: string
  entity_type: string
  entity_id: string
  action: string
  priority: "high" | "medium" | "low"
  score: number
  reasoning: string
  created_at: string
  status: "pending" | "accepted" | "executed" | "dismissed"
}

export default function DecisionCenterPage() {
  const { t } = useTranslation()
  const [decisions, setDecisions] = useState<DecisionItem[]>([])
  const [selected, setSelected] = useState<DecisionItem | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    axios.get("/api/v1/decision/history?limit=50")
      .then(res => { setDecisions(res.data.items || []); setLoading(false) })
      .catch(() => { setError(t("error.server_error")); setLoading(false) })
  }, [t])

  const handleAccept = async (id: string) => {
    await axios.post(`/api/v1/decisions/${id}/accept`)
    setDecisions(prev => prev.map(d => d.id === id ? { ...d, status: "accepted" as const } : d))
  }

  const handleDismiss = async (id: string) => {
    await axios.post(`/api/v1/decisions/${id}/feedback`, { accepted: false })
    setDecisions(prev => prev.map(d => d.id === id ? { ...d, status: "dismissed" as const } : d))
  }

  if (loading) return <div className="p-8 text-center text-neutral-500">{t("common.loading")}</div>
  if (error) return <div className="p-8 text-center text-red-500">{error}</div>

  return (
    <div className="p-6 space-y-6">
      <h1 className="text-2xl font-bold">{t("decisions.title")}</h1>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2 space-y-3">
          {decisions.length === 0 && (
            <p className="text-neutral-500 p-8 text-center">{t("common.no_results")}</p>
          )}
          {decisions.map(d => (
            <div
              key={d.id}
              onClick={() => setSelected(d)}
              className={cn(
                "rounded-lg border p-4 cursor-pointer hover:border-[var(--muhide-orange)] transition bg-white dark:bg-neutral-900",
                selected?.id === d.id && "border-[var(--muhide-orange)] ring-1 ring-[var(--muhide-orange)]"
              )}
            >
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <span className={cn(
                    "px-2 py-0.5 rounded text-xs font-medium",
                    d.priority === "high" && "bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-400",
                    d.priority === "medium" && "bg-yellow-100 text-yellow-700 dark:bg-yellow-900/30 dark:text-yellow-400",
                    d.priority === "low" && "bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400"
                  )}>
                    {d.priority}
                  </span>
                  <span className="font-medium">{d.action}</span>
                </div>
                <ChevronRight className="h-4 w-4 text-neutral-400" />
              </div>
            </div>
          ))}
        </div>

        {selected && (
          <div className="rounded-lg border p-4 bg-white dark:bg-neutral-900 space-y-3">
            <h3 className="font-bold text-lg">{selected.action}</h3>
            <p className="text-sm text-neutral-600 dark:text-neutral-400">{selected.reasoning}</p>
            <div className="flex items-center justify-between text-sm">
              <span className="text-neutral-500">{t("decisions.score")}: {selected.score}</span>
              <span className={cn(
                "px-2 py-0.5 rounded text-xs",
                selected.status === "accepted" && "bg-green-100 text-green-700",
                selected.status === "dismissed" && "bg-red-100 text-red-700",
                selected.status === "pending" && "bg-blue-100 text-blue-700"
              )}>
                {selected.status}
              </span>
            </div>
            {selected.status === "pending" && (
              <div className="flex gap-2 pt-2">
                <button onClick={() => handleAccept(selected.id)} className="flex items-center gap-1 px-3 py-1.5 bg-green-600 text-white rounded-lg text-sm hover:bg-green-700">
                  <Check className="h-4 w-4" /> {t("decisions.accept")}
                </button>
                <button onClick={() => handleDismiss(selected.id)} className="flex items-center gap-1 px-3 py-1.5 bg-red-600 text-white rounded-lg text-sm hover:bg-red-700">
                  <X className="h-4 w-4" /> {t("decisions.dismiss")}
                </button>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  )
}
