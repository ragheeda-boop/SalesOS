'use client'

import { createWidget } from '@salesos/workspace'
import type { APIData } from './types'
import { APIView } from './APIView'

const sample: APIData = { endpoints: [{ method: 'GET', path: '/api/v1/companies', description: 'قائمة الشركات', calls: 45200, avgLatency: 45 }, { method: 'POST', path: '/api/v1/search', description: 'بحث شامل', calls: 12800, avgLatency: 180 }, { method: 'GET', path: '/api/v1/opportunities', description: 'الفرص', calls: 8900, avgLatency: 32 }], totalEndpoints: 24, totalCalls: 186000, avgLatency: 85, errorRate: 2.3 }

export const APIPlatformWidget = createWidget({
  metadata: { id: 'apiPlatform', title: 'منصة API', category: 'enterprise', priority: 'medium', permissions: ['enterprise:api:read'], featureFlag: { enabled: true, tier: 'enterprise' }, minHeight: '360px' },
  useData: () => ({ data: sample, status: 'ready' as const, lastUpdated: null, error: null, refetch: () => {} }),
  render: ({ data }) => <APIView data={data} />,
})
