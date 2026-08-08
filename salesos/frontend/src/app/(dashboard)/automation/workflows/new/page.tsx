"use client";

import { useState, useCallback, useRef } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import {
  useCreateWorkflow,
  type WorkflowStep,
  type StepType,
  type TriggerType,
} from "@/lib/workflowQueries";
import { cn } from "@salesos/ui";
import { Button, Badge, Input, Textarea, Select, useToast } from "@salesos/ui";
import {
  ArrowLeft,
  Plus,
  Trash2,
  Mail,
  Database,
  CheckSquare,
  Webhook,
  Brain,
  GitBranch,
  ArrowDown,
  Play,
  Save,
  X,
  Zap,
} from "lucide-react";

interface VisualStep {
  id: string;
  type: StepType;
  label: string;
  config: Record<string, unknown>;
  conditionExpression: string;
  x: number;
  y: number;
  connectedTo: string | null;
}

const STEP_TYPES: {
  value: StepType;
  label: string;
  icon: React.ReactNode;
  color: string;
}[] = [
  {
    value: "send_email",
    label: "إرسال بريد",
    icon: <Mail className="h-4 w-4" />,
    color: "#3B82F6",
  },
  {
    value: "update_crm",
    label: "تحديث سجل",
    icon: <Database className="h-4 w-4" />,
    color: "#10B981",
  },
  {
    value: "create_task",
    label: "إنشاء مهمة",
    icon: <CheckSquare className="h-4 w-4" />,
    color: "#F59E0B",
  },
  {
    value: "webhook",
    label: "Webhook",
    icon: <Webhook className="h-4 w-4" />,
    color: "#8B5CF6",
  },
  {
    value: "nba_recommend",
    label: "توصية ذكية",
    icon: <Brain className="h-4 w-4" />,
    color: "#EC4899",
  },
];

const TRIGGER_OPTIONS = [
  { label: "حدث", value: "event" },
  { label: "مجدول", value: "scheduled" },
  { label: "يدوي", value: "manual" },
];

const STATUS_OPTIONS = [
  { label: "مسودة", value: "draft" },
  { label: "نشط", value: "active" },
  { label: "متوقف", value: "inactive" },
];

function getStepInfo(type: StepType) {
  return STEP_TYPES.find((s) => s.value === type) || STEP_TYPES[0];
}

function StepConfigPanel({
  step,
  onUpdate,
  onClose,
}: {
  step: VisualStep;
  onUpdate: (updates: Partial<VisualStep>) => void;
  onClose: () => void;
}) {
  const info = getStepInfo(step.type);

  return (
    <div className="w-80 border-l border-[var(--border-default)] bg-[var(--bg-primary)] p-4 space-y-4 overflow-y-auto">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <span style={{ color: info.color }}>{info.icon}</span>
          <h3 className="text-sm font-semibold text-[var(--text-primary)]">إعدادات الخطوة</h3>
        </div>
        <button
          onClick={onClose}
          className="text-[var(--text-muted)] hover:text-[var(--text-primary)]"
        >
          <X className="h-4 w-4" />
        </button>
      </div>

      <div className="space-y-3">
        <div>
          <label className="mb-1 block text-xs font-medium text-[var(--text-muted)]">
            نوع الخطوة
          </label>
          <select
            value={step.type}
            onChange={(e) => onUpdate({ type: e.target.value as StepType })}
            className="w-full rounded-lg border border-[var(--border-default)] bg-[var(--bg-primary)] px-3 py-2 text-sm text-[var(--text-primary)]"
          >
            {STEP_TYPES.map((t) => (
              <option key={t.value} value={t.value}>
                {t.label}
              </option>
            ))}
          </select>
        </div>

        <div>
          <label className="mb-1 block text-xs font-medium text-[var(--text-muted)]">التسمية</label>
          <Input
            value={step.label}
            onChange={(e) => onUpdate({ label: e.target.value })}
            placeholder="اسم الخطوة"
          />
        </div>

        {step.type === "send_email" && (
          <>
            <div>
              <label className="mb-1 block text-xs font-medium text-[var(--text-muted)]">إلى</label>
              <Input
                value={(step.config.to as string) || ""}
                onChange={(e) => onUpdate({ config: { ...step.config, to: e.target.value } })}
                placeholder="example@email.com"
              />
            </div>
            <div>
              <label className="mb-1 block text-xs font-medium text-[var(--text-muted)]">
                الموضوع
              </label>
              <Input
                value={(step.config.subject as string) || ""}
                onChange={(e) =>
                  onUpdate({
                    config: { ...step.config, subject: e.target.value },
                  })
                }
                placeholder="موضوع البريد"
              />
            </div>
            <div>
              <label className="mb-1 block text-xs font-medium text-[var(--text-muted)]">
                المحتوى
              </label>
              <Textarea
                value={(step.config.body as string) || ""}
                onChange={(e) => onUpdate({ config: { ...step.config, body: e.target.value } })}
                placeholder="محتوى البريد..."
                rows={3}
              />
            </div>
          </>
        )}

        {step.type === "update_crm" && (
          <>
            <div>
              <label className="mb-1 block text-xs font-medium text-[var(--text-muted)]">
                الحقل
              </label>
              <Input
                value={(step.config.field as string) || ""}
                onChange={(e) =>
                  onUpdate({
                    config: { ...step.config, field: e.target.value },
                  })
                }
                placeholder="deal.stage"
              />
            </div>
            <div>
              <label className="mb-1 block text-xs font-medium text-[var(--text-muted)]">
                القيمة الجديدة
              </label>
              <Input
                value={(step.config.value as string) || ""}
                onChange={(e) =>
                  onUpdate({
                    config: { ...step.config, value: e.target.value },
                  })
                }
                placeholder="proposal"
              />
            </div>
          </>
        )}

        {step.type === "create_task" && (
          <>
            <div>
              <label className="mb-1 block text-xs font-medium text-[var(--text-muted)]">
                عنوان المهمة
              </label>
              <Input
                value={(step.config.title as string) || ""}
                onChange={(e) =>
                  onUpdate({
                    config: { ...step.config, title: e.target.value },
                  })
                }
                placeholder="عنوان المهمة"
              />
            </div>
            <div className="grid grid-cols-2 gap-2">
              <div>
                <label className="mb-1 block text-xs font-medium text-[var(--text-muted)]">
                  الأولوية
                </label>
                <select
                  value={(step.config.priority as string) || "medium"}
                  onChange={(e) =>
                    onUpdate({
                      config: { ...step.config, priority: e.target.value },
                    })
                  }
                  className="w-full rounded-lg border border-[var(--border-default)] bg-[var(--bg-primary)] px-2 py-1.5 text-xs text-[var(--text-primary)]"
                >
                  <option value="low">منخفضة</option>
                  <option value="medium">متوسطة</option>
                  <option value="high">عالية</option>
                </select>
              </div>
              <div>
                <label className="mb-1 block text-xs font-medium text-[var(--text-muted)]">
                  المسؤول
                </label>
                <Input
                  value={(step.config.assignee as string) || ""}
                  onChange={(e) =>
                    onUpdate({
                      config: { ...step.config, assignee: e.target.value },
                    })
                  }
                  placeholder="{{owner}}"
                />
              </div>
            </div>
          </>
        )}

        {step.type === "webhook" && (
          <>
            <div>
              <label className="mb-1 block text-xs font-medium text-[var(--text-muted)]">
                الرابط
              </label>
              <Input
                value={(step.config.url as string) || ""}
                onChange={(e) => onUpdate({ config: { ...step.config, url: e.target.value } })}
                placeholder="https://api.example.com/webhook"
              />
            </div>
            <div>
              <label className="mb-1 block text-xs font-medium text-[var(--text-muted)]">
                الطريقة
              </label>
              <select
                value={(step.config.method as string) || "POST"}
                onChange={(e) =>
                  onUpdate({
                    config: { ...step.config, method: e.target.value },
                  })
                }
                className="w-full rounded-lg border border-[var(--border-default)] bg-[var(--bg-primary)] px-2 py-1.5 text-xs text-[var(--text-primary)]"
              >
                <option value="POST">POST</option>
                <option value="GET">GET</option>
                <option value="PUT">PUT</option>
                <option value="PATCH">PATCH</option>
              </select>
            </div>
          </>
        )}

        {step.type === "nba_recommend" && (
          <>
            <div>
              <label className="mb-1 block text-xs font-medium text-[var(--text-muted)]">
                نوع الإجراء
              </label>
              <Input
                value={(step.config.action_type as string) || ""}
                onChange={(e) =>
                  onUpdate({
                    config: { ...step.config, action_type: e.target.value },
                  })
                }
                placeholder="follow_up_call"
              />
            </div>
            <div>
              <label className="mb-1 block text-xs font-medium text-[var(--text-muted)]">
                السبب
              </label>
              <Textarea
                value={(step.config.reason as string) || ""}
                onChange={(e) =>
                  onUpdate({
                    config: { ...step.config, reason: e.target.value },
                  })
                }
                placeholder="سبب التوصية..."
                rows={2}
              />
            </div>
          </>
        )}

        <div>
          <label className="mb-1 block text-xs font-medium text-[var(--text-muted)]">
            شرط (اختياري)
          </label>
          <Input
            value={step.conditionExpression}
            onChange={(e) => onUpdate({ conditionExpression: e.target.value })}
            placeholder="deal.value > 10000"
          />
        </div>
      </div>
    </div>
  );
}

function CanvasStep({
  step,
  isSelected,
  isStart,
  onSelect,
  onDelete,
  index: _index,
}: {
  step: VisualStep;
  isSelected: boolean;
  isStart: boolean;
  onSelect: () => void;
  onDelete: () => void;
  index: number;
}) {
  const info = getStepInfo(step.type);

  return (
    <div
      className={cn(
        "absolute rounded-xl border-2 bg-[var(--bg-primary)] p-3 shadow-sm cursor-pointer transition-all",
        isSelected
          ? "border-[var(--muhide-orange)] shadow-md"
          : "border-[var(--border-default)] hover:border-[var(--text-muted)]"
      )}
      style={{ left: step.x, top: step.y, width: 220 }}
      onClick={(e) => {
        e.stopPropagation();
        onSelect();
      }}
    >
      <div className="flex items-center justify-between mb-2">
        <div className="flex items-center gap-2">
          <div
            className="rounded-lg p-1.5"
            style={{ backgroundColor: `${info.color}20`, color: info.color }}
          >
            {info.icon}
          </div>
          <div>
            <p className="text-xs font-medium text-[var(--text-primary)]">{step.label}</p>
            <p className="text-[10px] text-[var(--text-muted)]">{info.label}</p>
          </div>
        </div>
        <button
          onClick={(e) => {
            e.stopPropagation();
            onDelete();
          }}
          className="rounded p-1 text-[var(--text-muted)] hover:bg-danger-50 hover:text-danger-600 opacity-0 group-hover:opacity-100 transition-opacity"
        >
          <Trash2 className="h-3 w-3" />
        </button>
      </div>

      {step.conditionExpression && (
        <div className="flex items-center gap-1 mt-1">
          <GitBranch className="h-3 w-3 text-warning-500" />
          <span className="text-[10px] text-warning-600 truncate">{step.conditionExpression}</span>
        </div>
      )}

      {isStart && (
        <div className="absolute -top-3 left-1/2 -translate-x-1/2">
          <Badge variant="success" className="text-[9px] px-1.5 py-0">
            بداية
          </Badge>
        </div>
      )}

      <div className="absolute left-1/2 -translate-x-1/2 -bottom-5 text-[var(--text-muted)]">
        <ArrowDown className="h-4 w-4" />
      </div>
    </div>
  );
}

function WorkflowCanvas({
  steps,
  selectedStepId,
  onSelectStep,
  onDeleteStep,
}: {
  steps: VisualStep[];
  selectedStepId: string | null;
  onSelectStep: (id: string) => void;
  onDeleteStep: (id: string) => void;
}) {
  const canvasRef = useRef<HTMLDivElement>(null);

  const sortedSteps = [...steps].sort((a, b) => {
    if (!a.connectedTo && !b.connectedTo) return 0;
    if (!a.connectedTo) return -1;
    if (!b.connectedTo) return 1;
    const aIdx = steps.findIndex((s) => s.id === a.connectedTo);
    const bIdx = steps.findIndex((s) => s.id === b.connectedTo);
    return aIdx - bIdx;
  });

  return (
    <div
      ref={canvasRef}
      className="relative flex-1 overflow-auto bg-[var(--bg-secondary)] rounded-xl border border-[var(--border-default)] min-h-[500px]"
      style={{
        backgroundImage: "radial-gradient(circle, var(--border-default) 1px, transparent 1px)",
        backgroundSize: "20px 20px",
      }}
      onClick={() => onSelectStep("")}
    >
      {steps.length === 0 && (
        <div className="absolute inset-0 flex items-center justify-center">
          <div className="text-center space-y-3">
            <div className="rounded-full bg-[var(--bg-primary)] p-4 mx-auto w-fit border border-[var(--border-default)]">
              <Zap className="h-8 w-8 text-[var(--text-muted)]" />
            </div>
            <p className="text-sm text-[var(--text-muted)]">أضف خطوة للبدء</p>
          </div>
        </div>
      )}

      {sortedSteps.map((step, i) => (
        <CanvasStep
          key={step.id}
          step={{ ...step, y: 80 + i * 160 }}
          isSelected={selectedStepId === step.id}
          isStart={i === 0}
          onSelect={() => onSelectStep(step.id)}
          onDelete={() => onDeleteStep(step.id)}
          index={i}
        />
      ))}

      {/* Connection lines (simplified vertical arrows between steps) */}
      {sortedSteps.length > 1 && (
        <svg
          className="absolute inset-0 pointer-events-none"
          style={{ width: "100%", height: "100%" }}
        >
          {sortedSteps.slice(0, -1).map((step, i) => {
            const y1 = 80 + i * 160 + 60;
            const y2 = 80 + (i + 1) * 160;
            return (
              <line
                key={`line-${i}`}
                x1={350}
                y1={y1}
                x2={350}
                y2={y2}
                stroke="var(--border-default)"
                strokeWidth={2}
                strokeDasharray="4 4"
              />
            );
          })}
        </svg>
      )}
    </div>
  );
}

export default function NewWorkflowPage() {
  const { toast } = useToast();
  const router = useRouter();
  const createWorkflow = useCreateWorkflow();

  const [workflowName, setWorkflowName] = useState("");
  const [workflowDesc, setWorkflowDesc] = useState("");
  const [triggerType, setTriggerType] = useState<TriggerType>("manual");
  const [status, setStatus] = useState<"draft" | "active" | "inactive">("draft");
  const [steps, setSteps] = useState<VisualStep[]>([]);
  const [selectedStepId, setSelectedStepId] = useState<string | null>(null);
  const [showConfig, setShowConfig] = useState(false);

  const selectedStep = steps.find((s) => s.id === selectedStepId);

  const deleteStep = useCallback(
    (id: string) => {
      setSteps((prev) => prev.filter((s) => s.id !== id).map((s, i) => ({ ...s, order: i })));
      if (selectedStepId === id) {
        setSelectedStepId(null);
        setShowConfig(false);
      }
    },
    [selectedStepId]
  );

  const updateStep = useCallback((id: string, updates: Partial<VisualStep>) => {
    setSteps((prev) => prev.map((s) => (s.id === id ? { ...s, ...updates } : s)));
  }, []);

  const handleSave = useCallback(async () => {
    if (!workflowName.trim()) {
      toast({ variant: "error", title: "أدخل اسم سير العمل" });
      return;
    }

    const apiSteps: WorkflowStep[] = steps.map((s, i) => ({
      id: s.id,
      type: s.type,
      config: s.config as WorkflowStep["config"],
      condition_expression: s.conditionExpression || undefined,
      order: i,
    }));

    try {
      await createWorkflow.mutateAsync({
        name: workflowName,
        description: workflowDesc,
        trigger_type: triggerType,
        trigger_config: {},
        steps: apiSteps,
        status,
      });
      toast({ variant: "success", title: "تم إنشاء سير العمل بنجاح" });
      router.push("/automation");
    } catch {
      toast({ variant: "error", title: "فشل إنشاء سير العمل" });
    }
  }, [workflowName, workflowDesc, triggerType, status, steps, createWorkflow, toast, router]);

  const handleTestRun = useCallback(() => {
    if (steps.length === 0) {
      toast({ variant: "error", title: "أضف خطوات أولاً" });
      return;
    }
    toast({ variant: "success", title: "جاري اختبار سير العمل..." });
  }, [steps, toast]);

  return (
    <div className="flex h-[calc(100vh-4rem)] flex-col">
      {/* Top bar */}
      <div className="flex items-center justify-between border-b border-[var(--border-default)] bg-[var(--bg-primary)] px-4 py-3">
        <div className="flex items-center gap-3">
          <Link
            href="/automation"
            className="rounded-lg p-1.5 hover:bg-[var(--bg-secondary)] transition-colors text-[var(--text-muted)]"
          >
            <ArrowLeft className="h-4 w-4" />
          </Link>
          <div>
            <h1 className="text-lg font-bold text-[var(--text-primary)]">مُنشئ سير العمل</h1>
            <p className="text-xs text-[var(--text-muted)]">صمم خطوات سير العمل بصرياً</p>
          </div>
        </div>
        <div className="flex items-center gap-2">
          <Button
            variant="outline"
            size="sm"
            onClick={handleTestRun}
            leftIcon={<Play className="h-3.5 w-3.5" />}
          >
            اختبار
          </Button>
          <Button
            size="sm"
            onClick={handleSave}
            disabled={createWorkflow.isPending}
            leftIcon={<Save className="h-3.5 w-3.5" />}
          >
            {createWorkflow.isPending ? "جاري الحفظ..." : "حفظ"}
          </Button>
        </div>
      </div>

      <div className="flex flex-1 overflow-hidden">
        {/* Left sidebar — workflow settings */}
        <div className="w-64 border-l border-[var(--border-default)] bg-[var(--bg-primary)] p-4 space-y-4 overflow-y-auto">
          <div className="space-y-3">
            <h3 className="text-xs font-semibold uppercase tracking-wider text-[var(--text-muted)]">
              إعدادات سير العمل
            </h3>

            <div>
              <label className="mb-1 block text-xs font-medium text-[var(--text-muted)]">
                الاسم *
              </label>
              <Input
                value={workflowName}
                onChange={(e) => setWorkflowName(e.target.value)}
                placeholder="اسم سير العمل"
              />
            </div>

            <div>
              <label className="mb-1 block text-xs font-medium text-[var(--text-muted)]">
                الوصف
              </label>
              <Textarea
                value={workflowDesc}
                onChange={(e) => setWorkflowDesc(e.target.value)}
                placeholder="وصف مختصر..."
                rows={2}
              />
            </div>

            <div>
              <label className="mb-1 block text-xs font-medium text-[var(--text-muted)]">
                نوع المشغل
              </label>
              <Select
                options={TRIGGER_OPTIONS}
                value={triggerType}
                onChange={(v) => setTriggerType(v as TriggerType)}
              />
            </div>

            <div>
              <label className="mb-1 block text-xs font-medium text-[var(--text-muted)]">
                الحالة
              </label>
              <Select
                options={STATUS_OPTIONS}
                value={status}
                onChange={(v) => setStatus(v as typeof status)}
              />
            </div>
          </div>

          <div className="border-t border-[var(--border-default)] pt-3">
            <h3 className="text-xs font-semibold uppercase tracking-wider text-[var(--text-muted)] mb-2">
              إضافة خطوة
            </h3>
            <div className="space-y-1.5">
              {STEP_TYPES.map((st) => (
                <button
                  key={st.value}
                  onClick={() => {
                    const lastStep = steps[steps.length - 1];
                    const newStep: VisualStep = {
                      id: crypto.randomUUID?.() || `step-${Date.now()}`,
                      type: st.value,
                      label: st.label,
                      config: {},
                      conditionExpression: "",
                      x: 240,
                      y: 80 + steps.length * 160,
                      connectedTo: lastStep?.id || null,
                    };
                    setSteps((prev) => [...prev, newStep]);
                    setSelectedStepId(newStep.id);
                    setShowConfig(true);
                  }}
                  className="flex w-full items-center gap-2 rounded-lg px-2.5 py-2 text-right text-xs text-[var(--text-primary)] hover:bg-[var(--bg-secondary)] transition-colors"
                >
                  <span style={{ color: st.color }}>{st.icon}</span>
                  <span>{st.label}</span>
                  <Plus className="mr-auto h-3 w-3 text-[var(--text-muted)]" />
                </button>
              ))}
            </div>
          </div>

          {steps.length > 0 && (
            <div className="border-t border-[var(--border-default)] pt-3">
              <h3 className="text-xs font-semibold uppercase tracking-wider text-[var(--text-muted)] mb-2">
                الخطوات ({steps.length})
              </h3>
              <div className="space-y-1">
                {steps.map((s, i) => {
                  const info = getStepInfo(s.type);
                  return (
                    <button
                      key={s.id}
                      onClick={() => {
                        setSelectedStepId(s.id);
                        setShowConfig(true);
                      }}
                      className={cn(
                        "flex w-full items-center gap-2 rounded-lg px-2 py-1.5 text-right text-xs transition-colors",
                        selectedStepId === s.id
                          ? "bg-[var(--muhide-orange)]/10 text-[var(--muhide-orange)]"
                          : "text-[var(--text-primary)] hover:bg-[var(--bg-secondary)]"
                      )}
                    >
                      <span className="text-[10px] text-[var(--text-muted)] w-4">{i + 1}</span>
                      <span style={{ color: info.color }}>{info.icon}</span>
                      <span className="truncate">{s.label}</span>
                    </button>
                  );
                })}
              </div>
            </div>
          )}
        </div>

        {/* Canvas */}
        <WorkflowCanvas
          steps={steps}
          selectedStepId={selectedStepId}
          onSelectStep={(id) => {
            setSelectedStepId(id);
            setShowConfig(!!id);
          }}
          onDeleteStep={deleteStep}
        />

        {/* Right config panel */}
        {showConfig && selectedStep && (
          <StepConfigPanel
            step={selectedStep}
            onUpdate={(updates) => updateStep(selectedStep.id, updates)}
            onClose={() => {
              setSelectedStepId(null);
              setShowConfig(false);
            }}
          />
        )}
      </div>
    </div>
  );
}
