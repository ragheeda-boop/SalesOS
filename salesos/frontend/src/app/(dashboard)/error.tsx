"use client"

import { useEffect } from "react"
import { useTranslation } from "@/lib/i18n"

export default function DashboardError({
  error,
  reset,
}: {
  error: Error & { digest?: string }
  reset: () => void
}) {
  const { t } = useTranslation()

  useEffect(() => {
    console.error("Dashboard error:", error)
  }, [error])

  return (
    <div className="flex flex-col items-center justify-center min-h-[400px] p-8">
      <h2 className="text-xl font-bold text-neutral-900 dark:text-neutral-100">
        {t("error.default_title")}
      </h2>
      <p className="mt-2 text-neutral-500">{t("error.default_message")}</p>
      <button
        onClick={reset}
        className="mt-4 px-4 py-2 bg-[var(--muhide-orange)] text-white rounded-lg hover:opacity-90"
      >
        {t("error.retry")}
      </button>
    </div>
  )
}
