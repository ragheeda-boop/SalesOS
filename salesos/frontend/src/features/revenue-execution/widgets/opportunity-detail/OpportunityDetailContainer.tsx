'use client'

import { createWidget } from '@salesos/workspace'

export const OpportunityDetailWidget = createWidget({
  metadata: {
    id: 'opportunityDetail',
    title: 'تفاصيل الفرصة',
    category: 'intelligence',
    priority: 'high',
    permissions: ['opportunity:read'],
    featureFlag: { enabled: true },
    minHeight: '320px',
  },
  useData: () => ({
    data: null, status: 'ready' as const, lastUpdated: null, error: null, refetch: () => {},
  }),
  render: () => null,
})
