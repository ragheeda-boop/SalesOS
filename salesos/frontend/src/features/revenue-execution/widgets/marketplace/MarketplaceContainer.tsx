'use client'

import { createWidget } from '@salesos/workspace'
import type { PluginData } from './types'
import { MarketplaceView } from './MarketplaceView'

const sample: PluginData = { plugins: [{ id: 'p1', name: 'Power BI Connector', description: 'ربط Power BI مع SalesOS', installed: true, version: '2.1.0', icon: 'chart', category: 'تحليلات' }, { id: 'p2', name: 'Slack Integration', description: 'إشعارات الفرق عبر Slack', installed: false, version: '1.5.0', icon: 'message', category: 'تواصل' }, { id: 'p3', name: 'Odoo Sync', description: 'مزامنة مع Odoo ERP', installed: false, version: '1.0.0', icon: 'database', category: 'ERP' }], installed: 1, available: 3 }

export const MarketplaceWidget = createWidget({
  metadata: { id: 'marketplace', title: 'المتجر', category: 'enterprise', priority: 'medium', permissions: ['enterprise:marketplace:read'], featureFlag: { enabled: true }, minHeight: '360px' },
  useData: () => ({ data: sample, status: 'ready' as const, lastUpdated: null, error: null, refetch: () => {} }),
  render: ({ data }) => <MarketplaceView data={data} />,
})
