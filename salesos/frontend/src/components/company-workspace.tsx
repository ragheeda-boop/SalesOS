"use client"

import { useState, useMemo } from 'react'
import { useCompany } from '@/lib/hooks/companyQueries'
import { useCompany360 } from '@/lib/hooks/company360Queries'
import { useLocalization, useRuntime } from '@salesos/hooks'
import { WorkspaceRenderer, generateWorkspace, type WorkspaceRole, type CapabilityDefinition } from '@salesos/workspace'
import { Badge, cn } from '@salesos/ui'
import { Building2, MapPin, FileText } from 'lucide-react'
import { AI_ACTIONS, type AIAction } from '@salesos/design-language'

interface CompanyWorkspaceProps {
  companyId: string
  preset?: WorkspaceRole
}

export function CompanyWorkspace({ companyId, preset = 'sales' }: CompanyWorkspaceProps) {
  const { data: company, isLoading, isError } = useCompany(companyId)
  const { data: company360 } = useCompany360(companyId)
  const { t, locale } = useLocalization()
  const [activePreset, setActivePreset] = useState<WorkspaceRole>(preset)

  const capability: CapabilityDefinition = {
    entityType: 'company',
    labelAr: 'شركة',
    labelEn: 'Company',
    icon: 'Building2',
    color: 'blue',
    widgets: ['overview', 'revenue', 'timeline', 'signals', 'buying-committee', 'contacts', 'branches', 'licenses', 'documents', 'tasks', 'ai-insights'],
    tabs: ['branches', 'licenses', 'contacts', 'documents', 'meetings', 'emails', 'tasks', 'settings'],
    actions: ['edit', 'enrich', 'merge', 'export'],
    timeline: true,
    ai: true,
    signals: true,
    graph: true,
  }

  const schema = useMemo(() => {
    return generateWorkspace({
      entityType: 'company',
      entityId: companyId,
      title: company?.name_ar || company?.name_en || 'جاري التحميل...',
      preset: activePreset,
      capability,
      density: 'normal',
      context: {
        company: company || null,
        overview: company360?.overview || null,
        organization: company360?.organization || null,
        signals: company360?.signals || null,
        region: company?.region,
        city: company?.city,
        status: company?.status,
      },
    })
  }, [companyId, company, company360, activePreset])

  const presets: { id: WorkspaceRole; label: string }[] = [
    { id: 'sales', label: 'مبيعات' },
    { id: 'marketing', label: 'تسويق' },
    { id: 'executive', label: 'تنفيذي' },
    { id: 'legal', label: 'قانوني' },
    { id: 'operations', label: 'عمليات' },
    { id: 'customer-success', label: 'نجاح العملاء' },
  ]

  return (
    <div className="space-y-4">
      <div className="rounded-xl border bg-white shadow-muhide-1 dark:border-neutral-700 dark:bg-neutral-900">
        <div className="flex flex-wrap items-center justify-between gap-4 px-6 py-4">
          <div className="flex items-center gap-4">
            <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-info-100 text-info-700 dark:bg-info-900 dark:text-info-300">
              <Building2 className="h-6 w-6" />
            </div>
            <div>
              {company && (
                <>
                  <h1 className="text-xl font-bold text-neutral-900 dark:text-neutral-100">
                    {company.name_ar || company.name_en}
                  </h1>
                  <div className="mt-1 flex flex-wrap items-center gap-3 text-sm text-neutral-500 dark:text-neutral-400">
                    {company.name_en && company.name_ar !== company.name_en && (
                      <span>{company.name_en}</span>
                    )}
                    <span className="flex items-center gap-1">
                      <FileText className="h-3.5 w-3.5" /> {company.cr_number}
                    </span>
                    <span className="flex items-center gap-1">
                      <MapPin className="h-3.5 w-3.5" /> {company.city || '-'}
                    </span>
                    <Badge variant="primary">{company.status}</Badge>
                  </div>
                </>
              )}
            </div>
          </div>
          <div className="flex items-center gap-2">
            <div className="flex gap-1 rounded-lg border border-neutral-200 p-0.5 dark:border-neutral-700">
              {presets.map((p) => (
                <button
                  key={p.id}
                  onClick={() => setActivePreset(p.id)}
                  className={cn(
                    'rounded-md px-2.5 py-1 text-xs transition',
                    activePreset === p.id
                      ? 'bg-[var(--muhide-orange)] text-white'
                      : 'text-neutral-500 hover:text-neutral-700 dark:text-neutral-400 dark:hover:text-neutral-200'
                  )}
                >
                  {p.label}
                </button>
              ))}
            </div>
          </div>
        </div>
        <div className="flex items-center gap-1 border-t border-neutral-100 px-6 py-2 dark:border-neutral-800">
          <span className="text-[10px] font-medium text-neutral-400">AI:</span>
          {(['explain', 'analyze', 'predict', 'summarize', 'recommend'] as AIAction[]).map((actionId) => {
            const action = AI_ACTIONS[actionId]
            return (
              <button
                key={actionId}
                className="flex items-center gap-1 rounded-lg px-2 py-1 text-[10px] text-purple-600 hover:bg-purple-50 dark:text-purple-400 dark:hover:bg-purple-900/50"
              >
                {action.labelAr}
              </button>
            )
          })}
        </div>
      </div>

      <WorkspaceRenderer
        schema={schema}
        loading={isLoading}
        error={isError ? 'فشل تحميل بيانات الشركة' : undefined}
        entityType="company"
        entityId={companyId}
      />
    </div>
  )
}
