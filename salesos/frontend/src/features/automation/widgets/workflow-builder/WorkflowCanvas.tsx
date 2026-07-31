"use client";

import type { WorkflowStep, StepType } from "@/lib/workflowQueries";

const STEP_COLORS: Record<StepType, string> = {
  send_email: "#3B82F6",
  update_crm: "#10B981",
  create_task: "#F59E0B",
  webhook: "#8B5CF6",
  nba_recommend: "#EC4899",
  if_else: "#6366F1",
  for_each: "#14B8A6",
  parallel: "#F97316",
  set_variable: "#6B7280",
  log_message: "#9CA3AF",
};

const STEP_LABELS: Record<StepType, string> = {
  send_email: "بريد",
  update_crm: "CRM",
  create_task: "مهمة",
  webhook: "Webhook",
  nba_recommend: "NBA",
  if_else: "شرط",
  for_each: "تكرار",
  parallel: "متوازي",
  set_variable: "متغير",
  log_message: "سجل",
};

interface WorkflowCanvasProps {
  steps: WorkflowStep[];
  onAddStep: () => void;
  onRemoveStep: (index: number) => void;
  onUpdateStep: (index: number, step: Partial<WorkflowStep>) => void;
}

export function WorkflowCanvas({
  steps,
  onAddStep,
  onRemoveStep,
  onUpdateStep,
}: WorkflowCanvasProps) {
  if (steps.length === 0) {
    return (
      <div className="flex items-center justify-center h-40 border border-dashed border-[var(--border-default)] rounded-xl">
        <button
          onClick={onAddStep}
          className="text-sm text-[var(--muhide-orange)] hover:underline"
        >
          + إضافة الخطوة الأولى
        </button>
      </div>
    );
  }

  return (
    <div className="overflow-x-auto pb-4" dir="rtl">
      <div className="flex items-start gap-0 min-w-max">
        {steps.map((step, i) => (
          <div key={step.id || i} className="flex items-center">
            <WorkflowNode
              step={step}
              index={i}
              isLast={i === steps.length - 1}
              onRemove={onRemoveStep}
              onUpdate={onUpdateStep}
            />
            {i < steps.length - 1 && (
              <div className="flex flex-col items-center mx-1 shrink-0">
                <svg width="32" height="40" viewBox="0 0 32 40">
                  <line
                    x1="16"
                    y1="0"
                    x2="16"
                    y2="28"
                    stroke="#D1D5DB"
                    strokeWidth="2"
                  />
                  <polygon points="8,30 16,40 24,30" fill="#D1D5DB" />
                </svg>
              </div>
            )}
          </div>
        ))}
        <button
          onClick={onAddStep}
          className="shrink-0 flex items-center justify-center w-10 h-10 rounded-full border-2 border-dashed border-[var(--border-default)] text-[var(--text-muted)] hover:border-[var(--muhide-orange)] hover:text-[var(--muhide-orange)] transition-colors ml-2 mt-6"
        >
          +
        </button>
      </div>
    </div>
  );
}

function WorkflowNode({
  step,
  index,
  isLast: _isLast,
  onRemove,
  onUpdate: _onUpdate,
}: {
  step: WorkflowStep;
  index: number;
  isLast: boolean;
  onRemove: (index: number) => void;
  onUpdate: (index: number, step: Partial<WorkflowStep>) => void;
}) {
  const color = STEP_COLORS[step.type as StepType] || "#6B7280";
  const label = STEP_LABELS[step.type as StepType] || step.type;

  return (
    <div
      className="shrink-0 rounded-xl border-2 bg-[var(--bg-primary)] p-3 w-36 transition-shadow hover:shadow-md cursor-pointer"
      style={{ borderColor: color }}
    >
      <div className="flex items-center justify-between mb-2">
        <span className="text-[10px] font-semibold text-[var(--text-muted)]">
          {index + 1}
        </span>
        <button
          onClick={(e) => {
            e.stopPropagation();
            onRemove(index);
          }}
          className="text-[10px] text-danger-500 hover:text-danger-700"
        >
          ✕
        </button>
      </div>

      <div
        className="text-xs font-bold mb-1 px-1.5 py-0.5 rounded text-white inline-block"
        style={{ backgroundColor: color }}
      >
        {label}
      </div>

      {step.condition_expression && (
        <div className="mt-2 pt-2 border-t border-[var(--border-default)]">
          <span className="text-[10px] text-[var(--text-muted)] block truncate">
            {step.condition_expression}
          </span>
        </div>
      )}

      {step.config && Object.keys(step.config).length > 0 && (
        <div className="mt-1 space-y-0.5">
          {Object.entries(step.config)
            .slice(0, 2)
            .map(([k, v]) => (
              <div
                key={k}
                className="text-[10px] text-[var(--text-secondary)] truncate"
              >
                {k}: {String(v).slice(0, 20)}
              </div>
            ))}
        </div>
      )}
    </div>
  );
}
