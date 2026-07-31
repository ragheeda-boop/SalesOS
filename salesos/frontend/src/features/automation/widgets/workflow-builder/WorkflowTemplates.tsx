"use client";

import { useCreateWorkflow, type WorkflowStep } from "@/lib/workflowQueries";
import { useTranslation } from "@/lib/i18n";

interface Template {
  id: string;
  nameKey: string;
  descriptionKey: string;
  trigger_type: "event" | "scheduled" | "manual";
  steps: WorkflowStep[];
  triggerReasonKey?: string;
  emailSubjectKey?: string;
  emailBodyKey?: string;
  taskTitleKey?: string;
}

const TEMPLATES: Template[] = [
  {
    id: "lead-followup",
    nameKey: "automation.tmpl.lead_followup.name",
    descriptionKey: "automation.tmpl.lead_followup.description",
    trigger_type: "event",
    steps: [
      {
        id: "lf-1",
        type: "send_email" as const,
        config: {
          send_email: {
            to: "{{lead.email}}",
            subject: "شكراً لتواصلك",
            body: "نحن سعداء بتواصلك...",
          },
        },
        order: 0,
      },
      {
        id: "lf-2",
        type: "create_task" as const,
        config: {
          create_task: {
            title: "متابعة العميل {{lead.name}}",
            priority: "high",
            assignee: "{{owner}}",
          },
        },
        order: 1,
      },
    ],
  },
  {
    id: "deal-review",
    nameKey: "automation.tmpl.deal_review.name",
    descriptionKey: "automation.tmpl.deal_review.description",
    trigger_type: "scheduled",
    steps: [
      {
        id: "dr-1",
        type: "send_email" as const,
        config: {
          send_email: {
            to: "team@example.com",
            subject: "مراجعة الصفقات",
            body: "يرجى مراجعة الصفقات الكبيرة...",
          },
        },
        order: 0,
      },
      {
        id: "dr-2",
        type: "update_crm" as const,
        config: {
          update_crm: { field: "review_status", value: "pending_review" },
        },
        order: 1,
      },
    ],
  },
  {
    id: "meeting-prep",
    nameKey: "automation.tmpl.meeting_prep.name",
    descriptionKey: "automation.tmpl.meeting_prep.description",
    trigger_type: "event",
    steps: [
      {
        id: "mp-1",
        type: "nba_recommend" as const,
        config: {
          nba_recommend: {
            action_type: "meeting_prep",
            reason: "اجتماع مرتقب",
          },
        },
        order: 0,
      },
      {
        id: "mp-2",
        type: "send_email" as const,
        config: {
          send_email: {
            to: "{{owner.email}}",
            subject: "تحضير الاجتماع",
            body: "إليك ملخص التحضير...",
          },
        },
        order: 1,
      },
    ],
  },
  {
    id: "lost-deal",
    nameKey: "automation.tmpl.lost_deal.name",
    descriptionKey: "automation.tmpl.lost_deal.description",
    trigger_type: "event",
    steps: [
      {
        id: "ld-1",
        type: "create_task" as const,
        config: {
          create_task: {
            title: "تحليل خسارة {{deal.name}}",
            priority: "medium",
            assignee: "{{owner}}",
          },
        },
        order: 0,
      },
      {
        id: "ld-2",
        type: "send_email" as const,
        config: {
          send_email: {
            to: "{{owner.email}}",
            subject: "تحليل الصفقة الخاسرة",
            body: "يرجى توثيق أسباب الخسارة...",
          },
        },
        order: 1,
      },
    ],
  },
];

export function WorkflowTemplates() {
  const { t } = useTranslation();
  const createWorkflow = useCreateWorkflow();

  const handleUseTemplate = async (tmpl: Template) => {
    await createWorkflow.mutateAsync({
      name: t(tmpl.nameKey),
      description: t(tmpl.descriptionKey),
      trigger_type: tmpl.trigger_type,
      trigger_config: {},
      steps: tmpl.steps.map((s) => ({
        ...s,
        config: s.config,
        condition_expression: undefined,
      })),
      status: "draft",
    });
  };

  const triggerLabel = (type: string) => {
    if (type === "scheduled") return t("automation.scheduled");
    if (type === "event") return t("automation.event");
    return t("automation.manual");
  };

  return (
    <div className="space-y-4">
      <h2 className="text-lg font-display text-[var(--text-primary)]">
        {t("automation.templates")}
      </h2>
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {TEMPLATES.map((tmpl) => (
          <div
            key={tmpl.id}
            className="rounded-xl border border-[var(--border-default)] bg-[var(--bg-primary)] p-4 space-y-3"
          >
            <h3 className="text-sm font-medium text-[var(--text-primary)]">
              {t(tmpl.nameKey)}
            </h3>
            <p className="text-xs text-[var(--text-secondary)]">
              {t(tmpl.descriptionKey)}
            </p>
            <div className="flex items-center gap-2 text-xs text-[var(--text-muted)]">
              <span>
                {t("automation.steps_count", { count: tmpl.steps.length })}
              </span>
              <span>•</span>
              <span>{triggerLabel(tmpl.trigger_type)}</span>
            </div>
            <button
              onClick={() => handleUseTemplate(tmpl)}
              disabled={createWorkflow.isPending}
              className="rounded-lg bg-[var(--muhide-orange)] px-3 py-1.5 text-xs text-white hover:opacity-90 disabled:opacity-50"
            >
              {createWorkflow.isPending
                ? t("common.loading")
                : t("automation.use_template")}
            </button>
          </div>
        ))}
      </div>
    </div>
  );
}
