'use client'

import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import api from '@/lib/api'
import { getTenantId } from '@/lib/hooks/useTenant'

interface AIAuditEntry {
  id: number
  user_id: string | null
  action: string
  resource_type: string
  resource_id: string | null
  model: string | null
  prompt_tokens: number | null
  completion_tokens: number | null
  total_tokens: number | null
  cost: number | null
  operation: string | null
  details: Record<string, unknown>
  created_at: string | null
}

interface AIAuditSummary {
  total_calls: number
  total_cost: number
  total_tokens: number
  by_model: { model: string; count: number }[]
  by_action: { action: string; count: number }[]
}

function formatCost(cost: number | null): string {
  if (cost === null || cost === undefined) return '-'
  return `$${cost.toFixed(6)}`
}

function formatTokens(tokens: number | null): string {
  if (tokens === null || tokens === undefined) return '-'
  return tokens.toLocaleString()
}

const ACTION_LABELS: Record<string, string> = {
  'ai:chat_completion': 'استكمال محادثة',
  'ai:embedding': 'تضمين',
  'ai:decision_evaluate': 'تقييم قرار',
  'ai:decision_explain': 'شرح قرار',
  'ai:recommendation': 'توصية',
  'ai:scoring': 'تقييم',
  'ai:agent_call': 'استدعاء وكيل',
  'ai:tool_call': 'استدعاء أداة',
  'ai:search': 'بحث',
}

function actionLabel(action: string): string {
  return ACTION_LABELS[action] || action.replace('ai:', '')
}

export function AIAuditLogWidget() {
  const [page, setPage] = useState(1)
  const [filterAction, setFilterAction] = useState('')
  const [filterModel, setFilterModel] = useState('')

  const tenantId = getTenantId()

  const { data: summary } = useQuery<AIAuditSummary>({
    queryKey: ['admin', 'ai-audit', 'summary', tenantId],
    queryFn: async () => {
      const res = await api.get('/api/v1/admin/ai/audit/summary', {
        headers: { 'X-Tenant-Id': tenantId },
      })
      return res.data
    },
    refetchInterval: 60_000,
  })

  const { data: logs, isLoading } = useQuery<{ total: number; results: AIAuditEntry[] }>({
    queryKey: ['admin', 'ai-audit', 'logs', tenantId, page, filterAction, filterModel],
    queryFn: async () => {
      const params: Record<string, string | number> = { page, size: 20 }
      if (filterAction) params.action = filterAction
      if (filterModel) params.model = filterModel
      const res = await api.get('/api/v1/admin/ai/audit/logs', {
        params,
        headers: { 'X-Tenant-Id': tenantId },
      })
      return res.data
    },
    refetchInterval: 30_000,
  })

  const totalPages = logs ? Math.ceil(logs.total / 20) : 0

  return (
    <div className="space-y-6" dir="rtl">
      <div>
        <h2 className="text-xl font-bold">سجل تدقيق الذكاء الاصطناعي</h2>
        <p className="text-sm text-[var(--text-muted)] mt-1">
          تتبع جميع استدعاءات الذكاء الاصطناعي والتكاليف والرموز المميزة
        </p>
      </div>

      {summary && (
        <div className="grid grid-cols-3 gap-4">
          <div className="rounded-xl border border-[var(--border-default)] bg-[var(--bg-primary)] p-4">
            <p className="text-sm text-[var(--text-muted)]">إجمالي الاستدعاءات</p>
            <p className="text-2xl font-bold mt-1">{summary.total_calls.toLocaleString()}</p>
          </div>
          <div className="rounded-xl border border-[var(--border-default)] bg-[var(--bg-primary)] p-4">
            <p className="text-sm text-[var(--text-muted)]">إجمالي التكلفة</p>
            <p className="text-2xl font-bold mt-1">${summary.total_cost.toFixed(4)}</p>
          </div>
          <div className="rounded-xl border border-[var(--border-default)] bg-[var(--bg-primary)] p-4">
            <p className="text-sm text-[var(--text-muted)]">إجمالي الرموز</p>
            <p className="text-2xl font-bold mt-1">{summary.total_tokens.toLocaleString()}</p>
          </div>
        </div>
      )}

      <div className="grid grid-cols-2 gap-6">
        {summary && summary.by_model.length > 0 && (
          <div className="rounded-xl border border-[var(--border-default)] bg-[var(--bg-primary)] p-4">
            <h3 className="font-semibold mb-3">حسب النموذج</h3>
            <div className="space-y-2">
              {summary.by_model.slice(0, 8).map((m) => (
                <div key={m.model} className="flex justify-between text-sm">
                  <span className="text-[var(--text-secondary)]">{m.model}</span>
                  <span className="font-medium">{m.count.toLocaleString()}</span>
                </div>
              ))}
            </div>
          </div>
        )}
        {summary && summary.by_action.length > 0 && (
          <div className="rounded-xl border border-[var(--border-default)] bg-[var(--bg-primary)] p-4">
            <h3 className="font-semibold mb-3">حسب العملية</h3>
            <div className="space-y-2">
              {summary.by_action.slice(0, 8).map((a) => (
                <div key={a.action} className="flex justify-between text-sm">
                  <span className="text-[var(--text-secondary)]">{actionLabel(a.action)}</span>
                  <span className="font-medium">{a.count.toLocaleString()}</span>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>

      <div className="flex gap-3">
        <select
          value={filterAction}
          onChange={(e) => { setFilterAction(e.target.value); setPage(1) }}
          className="rounded-lg border border-[var(--border-default)] bg-[var(--bg-primary)] px-3 py-2 text-sm"
        >
          <option value="">جميع العمليات</option>
          {Object.entries(ACTION_LABELS).map(([key, label]) => (
            <option key={key} value={key}>{label}</option>
          ))}
        </select>
        <input
          type="text"
          placeholder="فلترة حسب النموذج..."
          value={filterModel}
          onChange={(e) => { setFilterModel(e.target.value); setPage(1) }}
          className="rounded-lg border border-[var(--border-default)] bg-[var(--bg-primary)] px-3 py-2 text-sm flex-1"
        />
      </div>

      <div className="rounded-xl border border-[var(--border-default)] overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="bg-[var(--bg-tertiary)] border-b border-[var(--border-default)]">
                <th className="text-right p-3 font-medium">العملية</th>
                <th className="text-right p-3 font-medium">النموذج</th>
                <th className="text-right p-3 font-medium">الرموز</th>
                <th className="text-right p-3 font-medium">التكلفة</th>
                <th className="text-right p-3 font-medium">المستخدم</th>
                <th className="text-right p-3 font-medium">التاريخ</th>
              </tr>
            </thead>
            <tbody>
              {isLoading ? (
                <tr>
                  <td colSpan={6} className="p-6 text-center text-[var(--text-muted)]">
                    جاري التحميل...
                  </td>
                </tr>
              ) : !logs?.results.length ? (
                <tr>
                  <td colSpan={6} className="p-6 text-center text-[var(--text-muted)]">
                    لا توجد سجلات
                  </td>
                </tr>
              ) : (
                logs.results.map((entry) => (
                  <tr key={entry.id} className="border-b border-[var(--border-default)] hover:bg-[var(--bg-tertiary)]">
                    <td className="p-3">{actionLabel(entry.action)}</td>
                    <td className="p-3 text-[var(--text-muted)]">{entry.model || '-'}</td>
                    <td className="p-3">{formatTokens(entry.total_tokens)}</td>
                    <td className="p-3">{formatCost(entry.cost)}</td>
                    <td className="p-3 text-[var(--text-muted)]">{entry.user_id ? entry.user_id.slice(0, 8) + '...' : '-'}</td>
                    <td className="p-3 text-[var(--text-muted)]">
                      {entry.created_at ? new Date(entry.created_at).toLocaleString('ar-SA') : '-'}
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>

      {totalPages > 1 && (
        <div className="flex justify-center gap-2">
          <button
            onClick={() => setPage((p) => Math.max(1, p - 1))}
            disabled={page <= 1}
            className="rounded-lg px-3 py-1.5 text-sm border border-[var(--border-default)] disabled:opacity-40"
          >
            السابق
          </button>
          <span className="px-3 py-1.5 text-sm text-[var(--text-muted)]">
            {page} / {totalPages}
          </span>
          <button
            onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
            disabled={page >= totalPages}
            className="rounded-lg px-3 py-1.5 text-sm border border-[var(--border-default)] disabled:opacity-40"
          >
            التالي
          </button>
        </div>
      )}
    </div>
  )
}
