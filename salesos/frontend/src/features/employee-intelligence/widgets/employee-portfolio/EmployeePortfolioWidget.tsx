'use client'

import { createWorkspaceWidget } from '@salesos/workspace'
import { useWorkspaceContext } from '../../workspace/EmployeeWorkspace'
import type { EmployeePortfolio } from '@/lib/api'
import { Building2, Users, TrendingUp, FileText, DollarSign, Briefcase } from 'lucide-react'

export function EmployeePortfolioView({ portfolio }: { portfolio: EmployeePortfolio }) {
  const totalPipeline = portfolio.pipeline.reduce((s, p) => s + p.value, 0)

  return (
    <div className="space-y-4">
      <div className="grid grid-cols-2 gap-3">
        <div className="rounded-lg bg-[var(--bg-secondary)] p-3">
          <div className="flex items-center gap-1.5 text-xs text-[var(--text-muted)] mb-1">
            <Building2 className="h-3 w-3" /> شركات
          </div>
          <p className="text-lg font-semibold text-[var(--text-primary)]">{portfolio.companies.length}</p>
        </div>
        <div className="rounded-lg bg-[var(--bg-secondary)] p-3">
          <div className="flex items-center gap-1.5 text-xs text-[var(--text-muted)] mb-1">
            <Users className="h-3 w-3" /> جهات اتصال
          </div>
          <p className="text-lg font-semibold text-[var(--text-primary)]">{portfolio.contacts.length}</p>
        </div>
        <div className="rounded-lg bg-[var(--bg-secondary)] p-3">
          <div className="flex items-center gap-1.5 text-xs text-[var(--text-muted)] mb-1">
            <TrendingUp className="h-3 w-3" /> خط التصفية
          </div>
          <p className="text-lg font-semibold text-[var(--text-primary)]">{totalPipeline.toLocaleString()}</p>
        </div>
        <div className="rounded-lg bg-[var(--bg-secondary)] p-3">
          <div className="flex items-center gap-1.5 text-xs text-[var(--text-muted)] mb-1">
            <DollarSign className="h-3 w-3" /> الإيرادات
          </div>
          <p className="text-lg font-semibold text-[var(--text-primary)]">{portfolio.revenue.toLocaleString()}</p>
        </div>
      </div>

      {portfolio.pipeline.length > 0 && (
        <div>
          <p className="text-xs font-medium text-[var(--text-muted)] mb-2">الصفقات النشطة</p>
          <div className="space-y-1.5">
            {portfolio.pipeline.slice(0, 5).map((item) => (
              <div key={item.id} className="flex items-center justify-between text-xs py-1.5 px-2 rounded-lg hover:bg-[var(--bg-secondary)]">
                <div className="flex items-center gap-2 min-w-0">
                  <span className="w-1.5 h-1.5 rounded-full bg-[var(--muhide-orange)] shrink-0" />
                  <span className="truncate text-[var(--text-secondary)]">{item.name}</span>
                </div>
                <div className="flex items-center gap-2 shrink-0">
                  <span className="text-[var(--text-secondary)]">{item.value.toLocaleString()}</span>
                  <span className="px-1.5 py-0.5 rounded text-[9px] bg-[var(--bg-secondary)] text-[var(--text-muted)]">{item.status}</span>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {portfolio.contracts.length > 0 && (
        <div>
          <p className="text-xs font-medium text-[var(--text-muted)] mb-2 flex items-center gap-1">
            <FileText className="h-3 w-3" /> العقود
          </p>
          <div className="space-y-1.5">
            {portfolio.contracts.map((c) => (
              <div key={c.id} className="flex items-center justify-between text-xs py-1">
                <span className="text-[var(--text-secondary)]">{c.name}</span>
                <span className="text-[var(--text-muted)]">{c.value.toLocaleString()}</span>
              </div>
            ))}
          </div>
        </div>
      )}

      {!portfolio.companies.length && !portfolio.pipeline.length && (
        <div className="flex flex-col items-center justify-center py-6 text-center">
          <Briefcase className="h-8 w-8 text-[var(--text-muted)] opacity-30 mb-1" />
          <p className="text-xs text-[var(--text-muted)]">لا توجد بيانات محفظة</p>
        </div>
      )}
    </div>
  )
}

export const EmployeePortfolioWidget = createWorkspaceWidget(
  { id: 'employeePortfolio', minHeight: '340px' },
  useWorkspaceContext,
  (widgets) => widgets.portfolio,
  {
    metadata: { title: 'محفظة الأعمال' },
    render: ({ data }) => <EmployeePortfolioView portfolio={data} />,
  },
)
