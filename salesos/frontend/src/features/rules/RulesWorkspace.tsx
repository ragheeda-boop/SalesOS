"use client"

import { useState } from "react"
import { useTranslation } from "@/lib/i18n"
import {
  useRules,
  useCreateRule,
  useUpdateRule,
  useDeleteRule,
  useToggleRule,
  type Rule,
  type RuleCondition,
  type RuleAction,
} from "@/lib/hooks/ruleQueries"

const DOMAIN_LABELS: Record<string, string> = {
  company: "rules.domain.company",
  opportunity: "rules.domain.opportunity",
  scoring: "rules.domain.scoring",
  workflow: "rules.domain.workflow",
}

type RulesTab = "all" | "company" | "opportunity" | "scoring" | "workflow"

const TABS: { key: RulesTab; labelKey: string }[] = [
  { key: "all", labelKey: "status.all" },
  { key: "company", labelKey: "rules.domain.company" },
  { key: "opportunity", labelKey: "rules.domain.opportunity" },
  { key: "scoring", labelKey: "rules.domain.scoring" },
  { key: "workflow", labelKey: "rules.domain.workflow" },
]

const TRIGGER_TYPES = [
  { value: "field_change", labelAr: "تغيير حقل", labelEn: "Field Change" },
  { value: "new_record", labelAr: "سجل جديد", labelEn: "New Record" },
  { value: "status_change", labelAr: "تغيير الحالة", labelEn: "Status Change" },
  { value: "value_threshold", labelAr: "عتبة قيمة", labelEn: "Value Threshold" },
  { value: "time_based", labelAr: "مبني على الوقت", labelEn: "Time Based" },
]

const ACTION_TYPES = [
  { value: "send_notification", labelAr: "إرسال إشعار", labelEn: "Send Notification" },
  { value: "create_task", labelAr: "إنشاء مهمة", labelEn: "Create Task" },
  { value: "update_field", labelAr: "تحديث حقل", labelEn: "Update Field" },
  { value: "send_email", labelAr: "إرسال بريد", labelEn: "Send Email" },
  { value: "assign_to", labelAr: "تعيين إلى", labelEn: "Assign To" },
]

const EMPTY_FORM: RuleFormData = {
  name: "",
  description: "",
  enabled: true,
  domain: "company",
  priority: 0,
  conditions: [],
  actions: [],
}

interface RuleFormData {
  name: string
  description: string
  enabled: boolean
  domain: string
  priority: number
  conditions: RuleCondition[]
  actions: RuleAction[]
}

export function RulesWorkspace() {
  const { t } = useTranslation()
  const [activeTab, setActiveTab] = useState<RulesTab>("all")
  const [mode, setMode] = useState<"list" | "create" | "edit">("list")
  const [editingRule, setEditingRule] = useState<Rule | null>(null)
  const [deletingId, setDeletingId] = useState<string | null>(null)

  const domainFilter = activeTab === "all" ? undefined : activeTab
  const { data: rules = [], isLoading } = useRules(domainFilter)
  const createRule = useCreateRule()
  const updateRule = useUpdateRule()
  const deleteRule = useDeleteRule()
  const toggleRule = useToggleRule()

  const isMutating = createRule.isPending || updateRule.isPending || deleteRule.isPending

  function handleCreate(input: RuleFormData) {
    createRule.mutate(input, {
      onSuccess: () => setMode("list"),
    })
  }

  function handleEdit(input: RuleFormData) {
    if (!editingRule) return
    updateRule.mutate(
      { id: editingRule.id, input },
      { onSuccess: () => { setMode("list"); setEditingRule(null) } },
    )
  }

  function handleDelete(id: string) {
    deleteRule.mutate(id, { onSuccess: () => setDeletingId(null) })
  }

  function handleStartEdit(rule: Rule) {
    setEditingRule(rule)
    setMode("edit")
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-xl font-display text-[var(--text-primary)]">{t("rules.title")}</h1>
        {mode === "list" && (
          <div className="flex gap-2">
            {TABS.map((tab) => (
              <button
                key={tab.key}
                onClick={() => setActiveTab(tab.key)}
                className={`px-3 py-1.5 text-sm rounded-lg transition-colors ${
                  activeTab === tab.key
                    ? "bg-[var(--muhide-orange)] text-white"
                    : "text-[var(--text-muted)] hover:bg-[var(--bg-secondary)]"
                }`}
              >
                {t(tab.labelKey)}
              </button>
            ))}
            <button
              onClick={() => { setEditingRule(null); setMode("create") }}
              className="px-3 py-1.5 text-sm rounded-lg bg-[var(--muhide-orange)] text-white font-medium"
            >
              + {t("rules.create")}
            </button>
          </div>
        )}
      </div>

      {mode !== "list" && (
        <RulesForm
          initialData={mode === "edit" && editingRule ? {
            name: editingRule.name,
            description: editingRule.description,
            enabled: editingRule.enabled,
            domain: editingRule.domain,
            priority: editingRule.priority,
            conditions: editingRule.conditions,
            actions: editingRule.actions,
          } : EMPTY_FORM}
          isEdit={mode === "edit"}
          isSaving={isMutating}
          onSave={mode === "edit" ? handleEdit : handleCreate}
          onCancel={() => { setMode("list"); setEditingRule(null) }}
        />
      )}

      {mode === "list" && isLoading && (
        <div className="rounded-xl border border-dashed border-[var(--border-default)] p-12 text-center">
          <p className="text-sm text-[var(--text-muted)]">{t("common.loading")}</p>
        </div>
      )}

      {mode === "list" && !isLoading && rules.length === 0 && (
        <div className="rounded-xl border border-dashed border-[var(--border-default)] p-12 text-center">
          <p className="text-sm text-[var(--text-muted)]">{t("rules.no_rules")}</p>
        </div>
      )}

      {mode === "list" && !isLoading && rules.length > 0 && (
        <div className="space-y-3">
          {rules.map((rule) => (
            <RuleCard
              key={rule.id}
              rule={rule}
              isDeleting={deletingId === rule.id}
              onToggle={() => toggleRule.mutate(rule.id)}
              onEdit={() => handleStartEdit(rule)}
              onDelete={() => setDeletingId(rule.id)}
              onConfirmDelete={() => handleDelete(rule.id)}
              onCancelDelete={() => setDeletingId(null)}
            />
          ))}
        </div>
      )}
    </div>
  )
}

function RuleCard({
  rule,
  isDeleting,
  onToggle,
  onEdit,
  onDelete,
  onConfirmDelete,
  onCancelDelete,
}: {
  rule: Rule
  isDeleting: boolean
  onToggle: () => void
  onEdit: () => void
  onDelete: () => void
  onConfirmDelete: () => void
  onCancelDelete: () => void
}) {
  const { t } = useTranslation()

  return (
    <div className="rounded-xl border border-[var(--border-default)] bg-[var(--bg-primary)] p-4 space-y-2">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <button
            onClick={onToggle}
            className={`w-9 h-5 rounded-full relative transition-colors ${
              rule.enabled ? "bg-[var(--muhide-orange)]" : "bg-neutral-300"
            }`}
            aria-label={rule.enabled ? t("workflows.deactivate") : t("workflows.activate")}
          >
            <span
              className={`absolute top-0.5 w-4 h-4 rounded-full bg-white shadow transition-transform ${
                rule.enabled ? "end-0.5" : "start-0.5"
              }`}
            />
          </button>
          <h3 className="font-medium text-[var(--text-primary)]">{rule.name}</h3>
        </div>
        <div className="flex items-center gap-2 text-xs">
          <span className="rounded-full bg-[var(--bg-secondary)] px-2 py-0.5 text-[var(--text-muted)]">
            {t(DOMAIN_LABELS[rule.domain] || rule.domain)}
          </span>
          <span className="text-[var(--text-muted)]">
            {rule.conditions.length} {t("rules.conditions_count")}
          </span>
          <span className="text-[var(--text-muted)]">
            {rule.actions.length} {t("rules.actions_count")}
          </span>
        </div>
      </div>
      {rule.description && (
        <p className="text-sm text-[var(--text-muted)]">{rule.description}</p>
      )}
      {rule.conditions.length > 0 && (
        <div className="flex flex-wrap gap-1.5">
          {rule.conditions.map((c, i) => (
            <span key={i} className="text-xs bg-[var(--bg-secondary)] text-[var(--text-muted)] rounded px-2 py-0.5">
              {c.field} {c.operator} {c.value}
            </span>
          ))}
        </div>
      )}
      <div className="flex items-center justify-between text-xs text-[var(--text-muted)]">
        <span>{t("labels.priority")}: {rule.priority}</span>
        <span>{t("labels.updated")}: {new Date(rule.updated_at).toLocaleDateString("ar-SA")}</span>
      </div>
      <div className="flex justify-end gap-1 pt-1">
        <button
          onClick={onEdit}
          className="px-2 py-1 text-xs rounded-lg text-[var(--text-muted)] hover:bg-[var(--bg-secondary)]"
        >
          {t("common.edit")}
        </button>
        {isDeleting ? (
          <>
            <button
              onClick={onConfirmDelete}
              className="px-2 py-1 text-xs rounded-lg text-red-600 hover:bg-red-50"
            >
              {t("common.confirm")}
            </button>
            <button
              onClick={onCancelDelete}
              className="px-2 py-1 text-xs rounded-lg text-[var(--text-muted)] hover:bg-[var(--bg-secondary)]"
            >
              {t("common.cancel")}
            </button>
          </>
        ) : (
          <button
            onClick={onDelete}
            className="px-2 py-1 text-xs rounded-lg text-red-500 hover:bg-red-50"
          >
            {t("common.delete")}
          </button>
        )}
      </div>
    </div>
  )
}

function RulesForm({
  initialData,
  isEdit,
  isSaving,
  onSave,
  onCancel,
}: {
  initialData: RuleFormData
  isEdit: boolean
  isSaving: boolean
  onSave: (data: RuleFormData) => void
  onCancel: () => void
}) {
  const { t, locale } = useTranslation()
  const isAr = locale === "ar"
  const [form, setForm] = useState<RuleFormData>(initialData)
  const [conditionField, setConditionField] = useState("")
  const [conditionOperator, setConditionOperator] = useState("equals")
  const [conditionValue, setConditionValue] = useState("")
  const [actionType, setActionType] = useState(ACTION_TYPES[0].value)
  const [actionTarget, setActionTarget] = useState("")

  function addCondition() {
    if (!conditionField.trim()) return
    setForm((prev) => ({
      ...prev,
      conditions: [...prev.conditions, { field: conditionField.trim(), operator: conditionOperator, value: conditionValue.trim() }],
    }))
    setConditionField("")
    setConditionValue("")
  }

  function removeCondition(index: number) {
    setForm((prev) => ({
      ...prev,
      conditions: prev.conditions.filter((_, i) => i !== index),
    }))
  }

  function addAction() {
    setForm((prev) => ({
      ...prev,
      actions: [...prev.actions, { type: actionType, params: { target: actionTarget.trim() } }],
    }))
    setActionTarget("")
  }

  function removeAction(index: number) {
    setForm((prev) => ({
      ...prev,
      actions: prev.actions.filter((_, i) => i !== index),
    }))
  }

  return (
    <div className="rounded-xl border border-[var(--border-default)] bg-[var(--bg-primary)] p-6 space-y-5">
      <h2 className="text-lg font-display text-[var(--text-primary)]">
        {isEdit ? t("common.edit") : t("rules.create")}
      </h2>

      <div className="grid grid-cols-2 gap-4">
        <div className="space-y-1.5">
          <label className="text-sm text-[var(--text-muted)]">{t("labels.name")}</label>
          <input
            value={form.name}
            onChange={(e) => setForm((p) => ({ ...p, name: e.target.value }))}
            className="w-full rounded-lg border border-[var(--border-default)] bg-[var(--bg-primary)] px-3 py-1.5 text-sm"
            placeholder={t("rules.name_placeholder")}
          />
        </div>
        <div className="space-y-1.5">
          <label className="text-sm text-[var(--text-muted)]">{t("labels.domain")}</label>
          <select
            value={form.domain}
            onChange={(e) => setForm((p) => ({ ...p, domain: e.target.value }))}
            className="w-full rounded-lg border border-[var(--border-default)] bg-[var(--bg-primary)] px-3 py-1.5 text-sm"
          >
            <option value="company">{t("rules.domain.company")}</option>
            <option value="opportunity">{t("rules.domain.opportunity")}</option>
            <option value="scoring">{t("rules.domain.scoring")}</option>
            <option value="workflow">{t("rules.domain.workflow")}</option>
          </select>
        </div>
        <div className="space-y-1.5">
          <label className="text-sm text-[var(--text-muted)]">{t("labels.priority")}</label>
          <input
            type="number"
            value={form.priority}
            onChange={(e) => setForm((p) => ({ ...p, priority: Number(e.target.value) }))}
            className="w-full rounded-lg border border-[var(--border-default)] bg-[var(--bg-primary)] px-3 py-1.5 text-sm"
            min={0}
            max={100}
          />
        </div>
        <div className="col-span-2 space-y-1.5">
          <label className="text-sm text-[var(--text-muted)]">{t("labels.description")}</label>
          <textarea
            value={form.description}
            onChange={(e) => setForm((p) => ({ ...p, description: e.target.value }))}
            className="w-full rounded-lg border border-[var(--border-default)] bg-[var(--bg-primary)] px-3 py-1.5 text-sm"
            rows={2}
          />
        </div>
      </div>

      <div className="space-y-3">
        <h3 className="text-sm font-medium text-[var(--text-primary)]">{t("workflows.triggers")}</h3>
        <div className="flex gap-2">
          <input
            value={conditionField}
            onChange={(e) => setConditionField(e.target.value)}
            className="flex-1 rounded-lg border border-[var(--border-default)] bg-[var(--bg-primary)] px-3 py-1.5 text-sm"
            placeholder={isAr ? "اسم الحقل" : "Field name"}
          />
          <select
            value={conditionOperator}
            onChange={(e) => setConditionOperator(e.target.value)}
            className="rounded-lg border border-[var(--border-default)] bg-[var(--bg-primary)] px-3 py-1.5 text-sm"
          >
            <option value="equals">{isAr ? "يساوي" : "Equals"}</option>
            <option value="not_equals">{isAr ? "لا يساوي" : "Not Equals"}</option>
            <option value="gt">{isAr ? "أكبر من" : "Greater Than"}</option>
            <option value="lt">{isAr ? "أقل من" : "Less Than"}</option>
            <option value="contains">{isAr ? "يحتوي" : "Contains"}</option>
          </select>
          <input
            value={conditionValue}
            onChange={(e) => setConditionValue(e.target.value)}
            className="flex-1 rounded-lg border border-[var(--border-default)] bg-[var(--bg-primary)] px-3 py-1.5 text-sm"
            placeholder={isAr ? "القيمة" : "Value"}
          />
          <button
            type="button"
            onClick={addCondition}
            className="px-3 py-1.5 text-sm rounded-lg bg-[var(--bg-secondary)] text-[var(--text-muted)] hover:bg-[var(--bg-tertiary)]"
          >
            + {t("common.create")}
          </button>
        </div>
        {form.conditions.length > 0 && (
          <div className="flex flex-wrap gap-1.5">
            {form.conditions.map((c, i) => (
              <span key={i} className="inline-flex items-center gap-1 text-xs bg-[var(--bg-secondary)] text-[var(--text-muted)] rounded px-2 py-0.5">
                {c.field} {c.operator} {c.value}
                <button onClick={() => removeCondition(i)} className="ml-1 text-red-400 hover:text-red-600">×</button>
              </span>
            ))}
          </div>
        )}
      </div>

      <div className="space-y-3">
        <h3 className="text-sm font-medium text-[var(--text-primary)]">{t("workflows.actions")}</h3>
        <div className="flex gap-2">
          <select
            value={actionType}
            onChange={(e) => setActionType(e.target.value)}
            className="rounded-lg border border-[var(--border-default)] bg-[var(--bg-primary)] px-3 py-1.5 text-sm"
          >
            {ACTION_TYPES.map((a) => (
              <option key={a.value} value={a.value}>{isAr ? a.labelAr : a.labelEn}</option>
            ))}
          </select>
          <input
            value={actionTarget}
            onChange={(e) => setActionTarget(e.target.value)}
            className="flex-1 rounded-lg border border-[var(--border-default)] bg-[var(--bg-primary)] px-3 py-1.5 text-sm"
            placeholder={isAr ? "الهدف" : "Target"}
          />
          <button
            type="button"
            onClick={addAction}
            className="px-3 py-1.5 text-sm rounded-lg bg-[var(--bg-secondary)] text-[var(--text-muted)] hover:bg-[var(--bg-tertiary)]"
          >
            + {t("common.create")}
          </button>
        </div>
        {form.actions.length > 0 && (
          <div className="flex flex-wrap gap-1.5">
            {form.actions.map((a, i) => (
              <span key={i} className="inline-flex items-center gap-1 text-xs bg-[var(--bg-secondary)] text-[var(--text-muted)] rounded px-2 py-0.5">
                {a.type}: {String(a.params.target || "")}
                <button onClick={() => removeAction(i)} className="ml-1 text-red-400 hover:text-red-600">×</button>
              </span>
            ))}
          </div>
        )}
      </div>

      <div className="flex justify-end gap-2 pt-2">
        <button
          onClick={onCancel}
          className="px-4 py-1.5 text-sm rounded-lg border border-[var(--border-default)] text-[var(--text-muted)]"
        >
          {t("common.cancel")}
        </button>
        <button
          onClick={() => onSave(form)}
          disabled={!form.name.trim() || isSaving}
          className="px-4 py-1.5 text-sm rounded-lg bg-[var(--muhide-orange)] text-white disabled:opacity-50"
        >
          {isSaving ? t("common.loading") : t("common.save")}
        </button>
      </div>
    </div>
  )
}
