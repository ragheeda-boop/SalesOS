"use client"

import { useState } from"react"
import Link from"next/link"
import { useTranslation } from"@/lib/i18n"
import { Bot, History, Trash2, MessageSquare, GitBranch, BarChart3 } from"lucide-react"
import { CopilotPanel } from"@/components/copilot-panel"
import { ExperimentalAiBadge } from"@/components/ai/ExperimentalAiBadge"
import { useAiCopilotEnabled } from"@/lib/hooks/useAiCopilotEnabled"

export default function CopilotPage() {
 const { t, dir } = useTranslation()
 const [showHistory, setShowHistory] = useState(false)
 const { enabled: aiCopilotEnabled, ready } = useAiCopilotEnabled()

 if (ready && !aiCopilotEnabled) {
 return (
 <div className="flex flex-col items-center justify-center gap-3 py-24 text-center" dir={dir}>
 <Bot className="h-10 w-10 text-[var(--text-disabled)]" />
 <h1 className="text-xl font-bold text-[var(--text-primary)]">
 {t("copilot.title")}
 </h1>
 <ExperimentalAiBadge />
 <p className="max-w-md text-sm text-[var(--text-muted)]">{t("copilot.disabled_ga")}</p>
 </div>
 )
 }

 return (
 <div className="flex h-[calc(100vh-7rem)] gap-4" dir={dir}>
 <div className="flex-1 flex flex-col">
 <div className="flex items-center justify-between mb-4">
 <div className="flex items-center gap-3">
 <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-[var(--muhide-orange)]/10">
 <Bot className="h-5 w-5 text-[var(--muhide-orange)]" />
 </div>
 <div>
 <div className="flex items-center gap-2">
 <h1 className="text-xl font-bold text-[var(--text-primary)]">
 {t("copilot.title")}
 </h1>
 <ExperimentalAiBadge />
 </div>
 <p className="text-sm text-[var(--text-muted)]">{t("copilot.subtitle")}</p>
 </div>
 </div>
 <div className="flex items-center gap-2">
 <Link
 href="/copilot/telemetry"
 className="flex items-center gap-2 rounded-lg border border-[var(--border-default)] px-3 py-2 text-sm text-[var(--text-secondary)] hover:bg-[var(--bg-secondary)] dark:hover:bg-[var(--bg-secondary)]"
 >
 <BarChart3 className="h-4 w-4" />
 {t("copilot.telemetry")}
 </Link>
 <button
 onClick={() => setShowHistory(!showHistory)}
 className="flex items-center gap-2 rounded-lg border border-[var(--border-default)] px-3 py-2 text-sm text-[var(--text-secondary)] hover:bg-[var(--bg-secondary)] dark:hover:bg-[var(--bg-secondary)]"
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
 <div className="w-72 shrink-0 rounded-2xl border border-[var(--border-default)] bg-[var(--bg-primary)] p-4 flex flex-col">
 <div className="flex items-center justify-between mb-3">
 <h3 className="font-semibold text-sm text-[var(--text-primary)]">
 {t("copilot.branch_history")}
 </h3>
 <button className="text-[var(--text-disabled)] hover:text-danger-500" title={t("copilot.clear_all")} aria-label={t("copilot.clear_all")}>
 <Trash2 className="h-4 w-4" />
 </button>
 </div>
 <div className="flex-1 space-y-2">
 <div className="flex items-center gap-2 rounded-lg p-2 text-sm text-[var(--text-secondary)] hover:bg-[var(--bg-secondary)] dark:hover:bg-[var(--bg-secondary)] cursor-pointer">
 <MessageSquare className="h-4 w-4 shrink-0" />
 <span className="truncate">{t("copilot.sample_q3_analysis")}</span>
 </div>
 <div className="flex items-center gap-2 rounded-lg p-2 text-sm text-[var(--text-secondary)] hover:bg-[var(--bg-secondary)] dark:hover:bg-[var(--bg-secondary)] cursor-pointer">
 <MessageSquare className="h-4 w-4 shrink-0" />
 <span className="truncate">{t("copilot.sample_deal_compare")}</span>
 </div>
 </div>
 <div className="mt-3 pt-3 border-t border-[var(--border-subtle)]">
 <h4 className="text-xs font-medium text-[var(--text-muted)] mb-2 flex items-center gap-1.5">
 <GitBranch className="h-3 w-3" />
 {t("copilot.branches_sidebar")}
 </h4>
 <p className="text-[11px] text-[var(--text-disabled)]">
 {t("copilot.no_branches")}
 </p>
 </div>
 <p className="mt-2 text-center text-xs text-[var(--text-disabled)]">
 {t("copilot.history_note")}
 </p>
 </div>
 )}
 </div>
 )
}
