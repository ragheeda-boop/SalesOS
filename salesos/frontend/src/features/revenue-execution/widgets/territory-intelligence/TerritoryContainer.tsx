'use client'

import { createWidget } from '@salesos/workspace'
import type { TerritoryData } from './types'
import { TerritoryView } from './TerritoryView'

const sample: TerritoryData = {
  territories: [
    { id: 't1', name: 'الرياض', deals: 8, value: 3500000, quota: 4000000, attainment: 88 },
    { id: 't2', name: 'جدة', deals: 5, value: 2100000, quota: 3000000, attainment: 70 },
    { id: 't3', name: 'الدمام', deals: 3, value: 1200000, quota: 2000000, attainment: 60 },
    { id: 't4', name: 'تبوك', deals: 1, value: 400000, quota: 1000000, attainment: 40 },
  ],
  coverage: [{ region: 'الرياض', covered: true, salesReps: 3, opportunityValue: 3500000 }],
  gaps: [{ region: 'القصيم', potentialValue: 1800000, reason: 'لا يوجد مندوب' }, { region: 'عسير', potentialValue: 1200000, reason: 'تغطية ضعيفة' }],
}

export const TerritoryIntelligenceWidget = createWidget({
  metadata: { id: 'territoryIntelligence', title: 'ذكاء المناطق', category: 'intelligence', priority: 'high', permissions: ['territory:read'], featureFlag: { enabled: true }, minHeight: '360px' },
  useData: () => ({ data: sample, status: 'ready' as const, lastUpdated: null, error: null, refetch: () => {} }),
  render: ({ data }) => <TerritoryView data={data} />,
})
