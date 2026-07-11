"use client"

import { useState } from "react"
import { WorkflowBuilderWidget } from "../../widgets/workflow-builder/WorkflowBuilderWidget"
import { WorkflowTemplates } from "../../widgets/workflow-builder/WorkflowTemplates"
import { useWorkflows, useWorkflowExecutions } from "@/lib/workflowQueries"

type AutomationTab = "workflows" | "templates" | "history"

const TAB_LABELS: Record<AutomationTab, string> = {
  workflows: "سير العمل",
  templates: "القوالب",
  history: "سجل التنفيذ",
}

export function AutomationWorkspace() {
  const [activeTab, setActiveTab] = useState<AutomationTab>("workflows")

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-xl font-display text-[var(--text-primary)]">الأتمتة</h1>
        <div className="flex gap-2">
          {(Object.keys(TAB_LABELS) as AutomationTab[]).map((tab) => (
            <button
              key={tab}
              onClick={() => setActiveTab(tab)}
              className={`px-3 py-1.5 text-sm rounded-lg ${
                activeTab === tab
                  ? "bg-[var(--muhide-orange)] text-white"
                  : "text-[var(--text-muted)] hover:bg-[var(--bg-secondary)]"
              }`}
            >
              {TAB_LABELS[tab]}
            </button>
          ))}
        </div>
      </div>

      {activeTab === "workflows" && <WorkflowBuilderWidget />}
      {activeTab === "templates" && <WorkflowTemplates />}
      {activeTab === "history" && <WorkflowExecutionHistory />}
    </div>
  )
}

function WorkflowExecutionHistory() {
  const { data: workflows } = useWorkflows()
  const [selectedId, setSelectedId] = useState<string | null>(null)
  const { data: executions, isLoading } = useWorkflowExecutions(selectedId || "")

  return (
    <div className="space-y-4">
      <h2 className="text-lg font-display text-[var(--text-primary)]">سجل التنفيذ</h2>
      <div className="flex items-center gap-2">
        <select
          value={selectedId || ""}
          onChange={(e) => setSelectedId(e.target.value || null)}
          className="rounded-lg border border-[var(--border-default)] bg-[var(--bg-primary)] px-3 py-1.5 text-sm text-[var(--text-primary)]"
        >
          <option value="">اختر سير عمل</option>
          {workflows?.map((w: any) => (
            <option key={w.id} value={w.id}>{w.name}</option>
          ))}
        </select>
      </div>

      {!selectedId && (
        <div className="rounded-xl border border-dashed border-[var(--border-default)] p-8 text-center">
          <p className="text-sm text-[var(--text-muted)]">اختر سير عمل لعرض سجل التنفيذ</p>
        </div>
      )}

      {isLoading && <div className="animate-pulse h-24 bg-neutral-100 rounded-xl" />}

      {executions && executions.length === 0 && (
        <div className="rounded-xl border border-dashed border-[var(--border-default)] p-8 text-center">
          <p className="text-sm text-[var(--text-muted)]">لا توجد عمليات تنفيذ بعد</p>
        </div>
      )}

      {executions?.map((ex: any) => (
        <div key={ex.id} className="rounded-xl border border-[var(--border-default)] bg-[var(--bg-primary)] p-3 space-y-1">
          <div className="flex items-center justify-between">
            <span className={`text-xs font-medium ${
              ex.status === "success" ? "text-success-600" : ex.status === "failed" ? "text-danger-600" : "text-warning-600"
            }`}>
              {ex.status === "success" ? "نجاح" : ex.status === "failed" ? "فشل" : "قيد التنفيذ"}
            </span>
            <span className="text-xs text-[var(--text-muted)]">{new Date(ex.started_at).toLocaleString("ar-SA")}</span>
          </div>
          {ex.error_message && <p className="text-xs text-danger-600">{ex.error_message}</p>}
        </div>
      ))}
    </div>
  )
}
