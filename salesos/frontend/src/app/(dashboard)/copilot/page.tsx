"use client"

import { useState } from "react"
import { useTranslation } from "@/lib/i18n"
import { Bot, History, Trash2, MessageSquare } from "lucide-react"
import { CopilotPanel } from "@/components/copilot-panel"

export default function CopilotPage() {
  const { t, dir } = useTranslation()
  const [showHistory, setShowHistory] = useState(false)

  return (
    <div className="flex h-[calc(100vh-7rem)] gap-4" dir={dir}>
      <div className="flex-1 flex flex-col">
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center gap-3">
            <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-[var(--muhide-orange)]/10">
              <Bot className="h-5 w-5 text-[var(--muhide-orange)]" />
            </div>
            <div>
              <h1 className="text-xl font-bold text-neutral-900 dark:text-neutral-100">
                {t("copilot.title")}
              </h1>
              <p className="text-sm text-neutral-500">{t("copilot.subtitle")}</p>
            </div>
          </div>
          <div className="flex items-center gap-2">
            <button
              onClick={() => setShowHistory(!showHistory)}
              className="flex items-center gap-2 rounded-lg border border-neutral-200 px-3 py-2 text-sm text-neutral-600 hover:bg-neutral-50 dark:border-neutral-700 dark:text-neutral-400 dark:hover:bg-neutral-800"
            >
              <History className="h-4 w-4" />
              {t("copilot.history")}
            </button>
          </div>
        </div>

        <div className="flex-1">
          <CopilotPanel open={true} onClose={() => {}} embedded />
        </div>
      </div>

      {showHistory && (
        <div className="w-72 shrink-0 rounded-2xl border border-neutral-200 bg-white p-4 dark:border-neutral-700 dark:bg-neutral-900">
          <div className="flex items-center justify-between mb-3">
            <h3 className="font-semibold text-sm text-neutral-900 dark:text-neutral-100">
              {t("copilot.recent_conversations")}
            </h3>
            <button className="text-neutral-400 hover:text-danger-500" title={t("copilot.clear_all")}>
              <Trash2 className="h-4 w-4" />
            </button>
          </div>
          <div className="space-y-2">
            <div className="flex items-center gap-2 rounded-lg p-2 text-sm text-neutral-600 hover:bg-neutral-50 dark:text-neutral-400 dark:hover:bg-neutral-800 cursor-pointer">
              <MessageSquare className="h-4 w-4 shrink-0" />
              <span className="truncate">تحليل أداء الشركات في الربع الثالث</span>
            </div>
            <div className="flex items-center gap-2 rounded-lg p-2 text-sm text-neutral-600 hover:bg-neutral-50 dark:text-neutral-400 dark:hover:bg-neutral-800 cursor-pointer">
              <MessageSquare className="h-4 w-4 shrink-0" />
              <span className="truncate">مقارنة بين فرصتين في مرحلة التفاوض</span>
            </div>
          </div>
          <p className="mt-3 text-center text-xs text-neutral-400">
            {t("copilot.history_note")}
          </p>
        </div>
      )}
    </div>
  )
}
