'use client'

import { createDashboardWidget } from '../../sdk'
import { AIBriefView } from './AIBriefView'
import type { AIBriefData } from '@/application/dashboard/dashboard.dto'

export const AIBriefWidget = createDashboardWidget<AIBriefData>('aiBrief', {
  metadata: {
    title: 'الملخص اليومي',
    description: 'ملخص يومي من الذكاء الاصطناعي لأهم الأحداث',
    permissions: ['ai:read'],
    featureFlag: { enabled: true, tier: 'enabled' },
  },
  render: ({ data, refresh }) => (
    <AIBriefView
      summary={data.summary ?? ''}
      highlights={data.highlights ?? []}
      generatedAt={data.generatedAt}
      onRefresh={refresh}
    />
  ),
})
