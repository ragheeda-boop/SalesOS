"use client"

import { useState } from "react"
import { useWorkflows, useCreateWorkflow, useUpdateWorkflow, useDeleteWorkflow, useExecuteWorkflow, useWorkflowExecutions, type Workflow, type WorkflowStep, type StepType, type TriggerType } from "@/lib/workflowQueries"

const TRIGGER_LABELS: Record<TriggerType, string> = {
  event: "حدث",
  scheduled: "مجدول",
  manual: "يدوي",
}

const STATUS_LABELS: Record<string, { label: string; color: string }> = {
  active: { label: "نشط", color: "bg-success-500" },
  draft: { label: "مسودة", color: "bg-warning-500" },
  inactive: { label: "متوقف", color: "bg-neutral-400" },
}

const STEP_TYPE_OPTIONS: { value: StepType; label: string }[] = [
  { value: "send_email", label: "إرسال بريد" },
  { value: "update_crm", label: "تحديث CRM" },
  { value: "create_task", label: "إنشاء مهمة" },
  { value: "webhook", label: "Webhook" },
  { value: "nba_recommend", label: "توصية NBA" },
]

function emptyStep(order: number): WorkflowStep {
  return { id: crypto.randomUUID?.() || `${Date.now()}`, type: "send_email", config: {}, order }
}

export function WorkflowBuilderWidget() {
  const { data: workflows, isLoading, error } = useWorkflows()
  const createWorkflow = useCreateWorkflow()
  const updateWorkflow = useUpdateWorkflow()
  const deleteWorkflow = useDeleteWorkflow()
  const executeWorkflow = useExecuteWorkflow()

  const [editing, setEditing] = useState<Partial<Workflow> | null>(null)
  const [showForm, setShowForm] = useState(false)
  const [executingId, setExecutingId] = useState<string | null>(null)
  const [confirmExecute, setConfirmExecute] = useState<string | null>(null)

  const handleCreate = () => {
    setEditing({ name: "", description: "", trigger_type: "manual", trigger_config: {}, steps: [emptyStep(0)], status: "draft" })
    setShowForm(true)
  }

  const handleEdit = (w: Workflow) => {
    setEditing({ ...w })
    setShowForm(true)
  }

  const handleSave = async () => {
    if (!editing) return
    if (editing.id) {
      await updateWorkflow.mutateAsync(editing as any)
    } else {
      await createWorkflow.mutateAsync(editing)
    }
    setShowForm(false)
    setEditing(null)
  }

  const handleDelete = async (id: string) => {
    if (confirm("هل أنت متأكد من حذف سير العمل هذا؟")) {
      await deleteWorkflow.mutateAsync(id)
    }
  }

  const handleExecute = async (id: string) => {
    setExecutingId(id)
    try {
      await executeWorkflow.mutateAsync(id)
    } finally {
      setExecutingId(null)
      setConfirmExecute(null)
    }
  }

  const addStep = () => {
    if (!editing) return
    const steps = [...(editing.steps || [])]
    steps.push(emptyStep(steps.length))
    setEditing({ ...editing, steps })
  }

  const removeStep = (index: number) => {
    if (!editing) return
    const steps = editing.steps?.filter((_, i) => i !== index).map((s, i) => ({ ...s, order: i })) || []
    setEditing({ ...editing, steps })
  }

  const updateStep = (index: number, step: Partial<WorkflowStep>) => {
    if (!editing?.steps) return
    const steps = editing.steps.map((s, i) => i === index ? { ...s, ...step } : s)
    setEditing({ ...editing, steps })
  }

  if (isLoading) {
    return <div className="animate-pulse space-y-3 p-4"><div className="h-8 w-48 bg-neutral-200 rounded" /><div className="h-20 bg-neutral-100 rounded" /><div className="h-20 bg-neutral-100 rounded" /></div>
  }

  if (error) {
    return <div className="rounded-xl border border-danger-200 bg-danger-50 p-4 text-center text-danger-700">فشل تحميل سير العمل</div>
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h2 className="text-lg font-display text-[var(--text-primary)]">سير العمل</h2>
        <button onClick={handleCreate} className="rounded-lg bg-[var(--muhide-orange)] px-3 py-1.5 text-sm text-white hover:opacity-90">إنشاء سير عمل</button>
      </div>

      {(!workflows || workflows.length === 0) && !showForm && (
        <div className="rounded-xl border border-dashed border-[var(--border-default)] p-8 text-center">
          <p className="text-sm text-[var(--text-muted)]">لا توجد سير عمل بعد</p>
          <button onClick={handleCreate} className="mt-2 text-sm text-[var(--muhide-orange)] hover:underline">إنشاء أول سير عمل</button>
        </div>
      )}

      {workflows?.map((w) => (
        <div key={w.id} className="rounded-xl border border-[var(--border-default)] bg-[var(--bg-primary)] p-4 space-y-2">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <span className="text-sm font-medium text-[var(--text-primary)]">{w.name}</span>
              <span className={`inline-block w-2 h-2 rounded-full ${STATUS_LABELS[w.status]?.color}`} />
              <span className="text-xs text-[var(--text-muted)]">{STATUS_LABELS[w.status]?.label}</span>
            </div>
            <div className="flex items-center gap-1">
              <button onClick={() => handleEdit(w)} className="rounded px-2 py-1 text-xs text-[var(--text-muted)] hover:bg-[var(--bg-secondary)]">تعديل</button>
              <button onClick={() => handleDelete(w.id)} className="rounded px-2 py-1 text-xs text-danger-600 hover:bg-danger-50">حذف</button>
            </div>
          </div>
          {w.description && <p className="text-xs text-[var(--text-secondary)]">{w.description}</p>}
          <div className="flex items-center gap-3 text-xs text-[var(--text-muted)]">
            <span>{TRIGGER_LABELS[w.trigger_type]}</span>
            <span>{w.steps.length} خطوة</span>
            <span>{new Date(w.updated_at).toLocaleDateString("ar-SA")}</span>
          </div>
          <div className="flex gap-2 pt-1">
            {confirmExecute === w.id ? (
              <div className="flex items-center gap-2">
                <span className="text-xs text-warning-600">تأكيد التنفيذ؟</span>
                <button onClick={() => handleExecute(w.id)} disabled={executingId === w.id} className="rounded bg-success-600 px-2 py-1 text-xs text-white hover:bg-success-700 disabled:opacity-50">
                  {executingId === w.id ? "جاري..." : "نعم"}
                </button>
                <button onClick={() => setConfirmExecute(null)} className="rounded bg-neutral-200 px-2 py-1 text-xs">إلغاء</button>
              </div>
            ) : (
              <button onClick={() => setConfirmExecute(w.id)} className="rounded bg-[var(--muhide-orange)] px-2 py-1 text-xs text-white hover:opacity-90">تنفيذ</button>
            )}
          </div>
        </div>
      ))}

      {showForm && editing && (
        <div className="fixed inset-0 z-50 flex items-start justify-center overflow-auto bg-black/40 pt-10">
          <div className="w-full max-w-2xl rounded-xl bg-[var(--bg-primary)] p-6 shadow-xl space-y-4 m-4">
            <div className="flex items-center justify-between">
              <h3 className="text-lg font-display text-[var(--text-primary)]">{editing.id ? "تعديل سير عمل" : "إنشاء سير عمل"}</h3>
              <button onClick={() => { setShowForm(false); setEditing(null) }} className="text-[var(--text-muted)] hover:text-[var(--text-primary)]">✕</button>
            </div>

            <div className="space-y-3">
              <div>
                <label className="block text-xs text-[var(--text-muted)] mb-1">الاسم</label>
                <input value={editing.name || ""} onChange={(e) => setEditing({ ...editing, name: e.target.value })} className="w-full rounded-lg border border-[var(--border-default)] bg-[var(--bg-primary)] px-3 py-2 text-sm text-[var(--text-primary)]" />
              </div>
              <div>
                <label className="block text-xs text-[var(--text-muted)] mb-1">الوصف</label>
                <textarea value={editing.description || ""} onChange={(e) => setEditing({ ...editing, description: e.target.value })} rows={2} className="w-full rounded-lg border border-[var(--border-default)] bg-[var(--bg-primary)] px-3 py-2 text-sm text-[var(--text-primary)]" />
              </div>
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs text-[var(--text-muted)] mb-1">نوع المشغل</label>
                  <select value={editing.trigger_type} onChange={(e) => setEditing({ ...editing, trigger_type: e.target.value as TriggerType })} className="w-full rounded-lg border border-[var(--border-default)] bg-[var(--bg-primary)] px-3 py-2 text-sm text-[var(--text-primary)]">
                    {Object.entries(TRIGGER_LABELS).map(([k, v]) => <option key={k} value={k}>{v}</option>)}
                  </select>
                </div>
                <div>
                  <label className="block text-xs text-[var(--text-muted)] mb-1">الحالة</label>
                  <select value={editing.status} onChange={(e) => setEditing({ ...editing, status: e.target.value as Workflow["status"] })} className="w-full rounded-lg border border-[var(--border-default)] bg-[var(--bg-primary)] px-3 py-2 text-sm text-[var(--text-primary)]">
                    <option value="draft">مسودة</option>
                    <option value="active">نشط</option>
                    <option value="inactive">متوقف</option>
                  </select>
                </div>
              </div>

              <div>
                <div className="flex items-center justify-between mb-2">
                  <label className="text-xs text-[var(--text-muted)]">الخطوات</label>
                  <button onClick={addStep} className="text-xs text-[var(--muhide-orange)] hover:underline">+ إضافة خطوة</button>
                </div>
                <div className="space-y-2">
                  {editing.steps?.map((step, i) => (
                    <div key={step.id} className="rounded-lg border border-[var(--border-default)] bg-[var(--bg-secondary)] p-3 space-y-2">
                      <div className="flex items-center justify-between">
                        <span className="text-xs font-medium text-[var(--text-muted)]">الخطوة {i + 1}</span>
                        <button onClick={() => removeStep(i)} className="text-xs text-danger-600 hover:underline">حذف</button>
                      </div>
                      <div className="grid grid-cols-2 gap-2">
                        <div>
                          <label className="block text-xs text-[var(--text-muted)] mb-1">النوع</label>
                          <select value={step.type} onChange={(e) => updateStep(i, { type: e.target.value as StepType })} className="w-full rounded-lg border border-[var(--border-default)] bg-[var(--bg-primary)] px-2 py-1 text-xs text-[var(--text-primary)]">
                            {STEP_TYPE_OPTIONS.map((o) => <option key={o.value} value={o.value}>{o.label}</option>)}
                          </select>
                        </div>
                        <div>
                          <label className="block text-xs text-[var(--text-muted)] mb-1">شرط (اختياري)</label>
                          <input value={step.condition_expression || ""} onChange={(e) => updateStep(i, { condition_expression: e.target.value })} placeholder="مثال: deal.value > 10000" className="w-full rounded-lg border border-[var(--border-default)] bg-[var(--bg-primary)] px-2 py-1 text-xs text-[var(--text-primary)]" />
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </div>

            <div className="flex justify-end gap-2 pt-2">
              <button onClick={() => { setShowForm(false); setEditing(null) }} className="rounded-lg border border-[var(--border-default)] px-3 py-1.5 text-sm text-[var(--text-muted)]">إلغاء</button>
              <button onClick={handleSave} disabled={createWorkflow.isPending || updateWorkflow.isPending} className="rounded-lg bg-[var(--muhide-orange)] px-3 py-1.5 text-sm text-white hover:opacity-90 disabled:opacity-50">
                {createWorkflow.isPending ? "جاري الحفظ..." : "حفظ"}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
