"use client";

import { useState } from "react";
import { WorkflowBuilderWidget } from "../../widgets/workflow-builder/WorkflowBuilderWidget";
import { WorkflowTemplates } from "../../widgets/workflow-builder/WorkflowTemplates";
import { useWorkflows, useWorkflowExecutions } from "@/lib/workflowQueries";
import { useTranslation } from "@/lib/i18n";
import type { Workflow, WorkflowExecution } from "@/lib/workflowQueries";
import { safeArray } from "@/lib/utils";

type AutomationTab = "workflows" | "templates" | "history";

const TAB_KEYS: Record<AutomationTab, string> = {
  workflows: "automation.workflows",
  templates: "automation.templates",
  history: "automation.execution_history",
};

export function AutomationWorkspace() {
  const { t } = useTranslation();
  const [activeTab, setActiveTab] = useState<AutomationTab>("workflows");

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-xl font-display text-[var(--text-primary)]">
          {t("automation.title")}
        </h1>
        <div className="flex gap-2">
          {(Object.keys(TAB_KEYS) as AutomationTab[]).map((tab) => (
            <button
              key={tab}
              onClick={() => setActiveTab(tab)}
              className={`px-3 py-1.5 text-sm rounded-lg ${
                activeTab === tab
                  ? "bg-[var(--muhide-orange)] text-white"
                  : "text-[var(--text-muted)] hover:bg-[var(--bg-secondary)]"
              }`}
            >
              {t(TAB_KEYS[tab])}
            </button>
          ))}
        </div>
      </div>

      {activeTab === "workflows" && <WorkflowBuilderWidget />}
      {activeTab === "templates" && <WorkflowTemplates />}
      {activeTab === "history" && <WorkflowExecutionHistory />}
    </div>
  );
}

function WorkflowExecutionHistory() {
  const { t } = useTranslation();
  const { data: workflows } = useWorkflows();
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const { data: executions, isLoading } = useWorkflowExecutions(
    selectedId || "",
  );

  return (
    <div className="space-y-4">
      <h2 className="text-lg font-display text-[var(--text-primary)]">
        {t("automation.execution_history")}
      </h2>
      <div className="flex items-center gap-2">
        <select
          value={selectedId || ""}
          onChange={(e) => setSelectedId(e.target.value || null)}
          className="rounded-lg border border-[var(--border-default)] bg-[var(--bg-primary)] px-3 py-1.5 text-sm text-[var(--text-primary)]"
        >
          <option value="">{t("automation.select_workflow")}</option>
          {safeArray<Workflow>(workflows).map((w) => (
            <option key={w.id} value={w.id}>
              {w.name}
            </option>
          ))}
        </select>
      </div>

      {!selectedId && (
        <div className="rounded-xl border border-dashed border-[var(--border-default)] p-8 text-center">
          <p className="text-sm text-[var(--text-muted)]">
            {t("automation.select_workflow_hint")}
          </p>
        </div>
      )}

      {isLoading && (
        <div className="animate-pulse h-24 bg-[var(--bg-tertiary)] rounded-xl" />
      )}

      {safeArray(executions).length === 0 && (
        <div className="rounded-xl border border-dashed border-[var(--border-default)] p-8 text-center">
          <p className="text-sm text-[var(--text-muted)]">
            {t("automation.no_executions")}
          </p>
        </div>
      )}

      {safeArray<WorkflowExecution>(executions).map((ex) => (
        <div
          key={ex.id}
          className="rounded-xl border border-[var(--border-default)] bg-[var(--bg-primary)] p-3 space-y-1"
        >
          <div className="flex items-center justify-between">
            <span
              className={`text-xs font-medium ${
                ex.status === "success"
                  ? "text-success-600"
                  : ex.status === "failed"
                    ? "text-danger-600"
                    : "text-warning-600"
              }`}
            >
              {ex.status === "success"
                ? t("automation.success")
                : ex.status === "failed"
                  ? t("automation.failed")
                  : t("automation.in_progress")}
            </span>
            <span className="text-xs text-[var(--text-muted)]">
              {new Date(ex.started_at).toLocaleString("ar-SA")}
            </span>
          </div>
          {ex.error_message && (
            <p className="text-xs text-danger-600">{ex.error_message}</p>
          )}
        </div>
      ))}
    </div>
  );
}
