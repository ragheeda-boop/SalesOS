"use client"

import { useCreateWorkflow, type WorkflowStep } from "@/lib/workflowQueries"

const TEMPLATES = [
  {
    id: "lead-followup",
    name: "متابعة العميل المحتمل",
    description: "إرسال بريد متابعة وإنشاء مهمة بعد تسجيل عميل محتمل جديد",
    trigger_type: "event" as const,
    steps: [
      { type: "send_email" as const, config: { send_email: { to: "{{lead.email}}", subject: "شكراً لتواصلك", body: "نحن سعداء بتواصلك..." } }, order: 0 },
      { type: "create_task" as const, config: { create_task: { title: "متابعة العميل {{lead.name}}", priority: "high", assignee: "{{owner}}" } }, order: 1 },
    ],
  },
  {
    id: "deal-review",
    name: "مراجعة الصفقة",
    description: "جدولة اجتماع مراجعة أسبوعي للصفقات الكبيرة",
    trigger_type: "scheduled" as const,
    steps: [
      { type: "send_email" as const, config: { send_email: { to: "team@example.com", subject: "مراجعة الصفقات", body: "يرجى مراجعة الصفقات الكبيرة..." } }, order: 0 },
      { type: "update_crm" as const, config: { update_crm: { field: "review_status", value: "pending_review" } }, order: 1 },
    ],
  },
  {
    id: "meeting-prep",
    name: "تحضير الاجتماع",
    description: "إرسال ملخص تحضيري قبل الاجتماع ب 24 ساعة",
    trigger_type: "event" as const,
    steps: [
      { type: "nba_recommend" as const, config: { nba_recommend: { action_type: "meeting_prep", reason: "اجتماع مرتقب" } }, order: 0 },
      { type: "send_email" as const, config: { send_email: { to: "{{owner.email}}", subject: "تحضير الاجتماع", body: "إليك ملخص التحضير..." } }, order: 1 },
    ],
  },
  {
    id: "lost-deal",
    name: "تحليل الصفقة الخاسرة",
    description: "تحليل أسباب خسارة الصفقة وجدولة متابعة",
    trigger_type: "event" as const,
    steps: [
      { type: "create_task" as const, config: { create_task: { title: "تحليل خسارة {{deal.name}}", priority: "medium", assignee: "{{owner}}" } }, order: 0 },
      { type: "send_email" as const, config: { send_email: { to: "{{owner.email}}", subject: "تحليل الصفقة الخاسرة", body: "يرجى توثيق أسباب الخسارة..." } }, order: 1 },
    ],
  },
]

export function WorkflowTemplates() {
  const createWorkflow = useCreateWorkflow()

  const handleUseTemplate = async (tmpl: typeof TEMPLATES[number]) => {
    await createWorkflow.mutateAsync({
      name: tmpl.name,
      description: tmpl.description,
      trigger_type: tmpl.trigger_type,
      trigger_config: {},
      steps: tmpl.steps.map((s, i) => ({ id: crypto.randomUUID?.() || `${Date.now()}-${i}`, ...s, config: s.config, condition_expression: undefined })),
      status: "draft",
    })
  }

  return (
    <div className="space-y-4">
      <h2 className="text-lg font-display text-[var(--text-primary)]">القوالب</h2>
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {TEMPLATES.map((tmpl) => (
          <div key={tmpl.id} className="rounded-xl border border-[var(--border-default)] bg-[var(--bg-primary)] p-4 space-y-3">
            <h3 className="text-sm font-medium text-[var(--text-primary)]">{tmpl.name}</h3>
            <p className="text-xs text-[var(--text-secondary)]">{tmpl.description}</p>
            <div className="flex items-center gap-2 text-xs text-[var(--text-muted)]">
              <span>{tmpl.steps.length} خطوات</span>
              <span>•</span>
              <span>{tmpl.trigger_type === "scheduled" ? "مجدول" : tmpl.trigger_type === "event" ? "حدث" : "يدوي"}</span>
            </div>
            <button
              onClick={() => handleUseTemplate(tmpl)}
              disabled={createWorkflow.isPending}
              className="rounded-lg bg-[var(--muhide-orange)] px-3 py-1.5 text-xs text-white hover:opacity-90 disabled:opacity-50"
            >
              {createWorkflow.isPending ? "جاري..." : "استخدام القالب"}
            </button>
          </div>
        ))}
      </div>
    </div>
  )
}
