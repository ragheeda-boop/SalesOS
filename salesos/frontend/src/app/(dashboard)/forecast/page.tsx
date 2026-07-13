"use client"

import { useState, useEffect } from "react"
import axios from "axios"
import { cn } from "@salesos/ui"
import { useTranslation } from "@/lib/i18n"

interface ForecastData {
  total_expected: number
  weighted: number
  confidence: number
  risk: number
  horizon: string
  scenarios?: {
    pessimistic: number
    baseline: number
    optimistic: number
  }
}

function ForecastCard({ label, value, variant = "neutral" }: {
  label: string
  value: string | number
  variant?: "green" | "red" | "neutral"
}) {
  return (
    <div className={cn(
      "rounded-xl border p-4 bg-white dark:bg-neutral-900",
      variant === "green" && "border-green-200 dark:border-green-800",
      variant === "red" && "border-red-200 dark:border-red-800",
      variant === "neutral" && "border-neutral-200 dark:border-neutral-700"
    )}>
      <p className="text-sm text-neutral-500">{label}</p>
      <p className={cn(
        "text-2xl font-bold mt-1",
        variant === "green" && "text-green-600",
        variant === "red" && "text-red-600"
      )}>{value}</p>
    </div>
  )
}

export default function ForecastPage() {
  const { t } = useTranslation()
  const [forecast, setForecast] = useState<ForecastData | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    axios.get("/api/v1/forecast")
      .then(res => { setForecast(res.data); setLoading(false) })
      .catch(() => { setError(t("error.server_error")); setLoading(false) })
  }, [t])

  if (loading) return <div className="p-8 text-center text-neutral-500">{t("common.loading")}</div>
  if (error) return <div className="p-8 text-center text-red-500">{error}</div>
  if (!forecast) return <div className="p-8 text-center text-neutral-500">{t("common.no_results")}</div>

  return (
    <div className="p-6 space-y-6">
      <h1 className="text-2xl font-bold">{t("forecast.title")}</h1>
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <ForecastCard label={t("forecast.total_expected")} value={forecast.total_expected} />
        <ForecastCard label={t("forecast.weighted")} value={forecast.weighted} />
        <ForecastCard label={t("forecast.confidence")} value={`${forecast.confidence}%`} />
      </div>
      {forecast.scenarios && (
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <ForecastCard label={t("forecast.pessimistic")} value={forecast.scenarios.pessimistic} variant="red" />
          <ForecastCard label={t("forecast.baseline")} value={forecast.scenarios.baseline} variant="neutral" />
          <ForecastCard label={t("forecast.optimistic")} value={forecast.scenarios.optimistic} variant="green" />
        </div>
      )}
    </div>
  )
}
