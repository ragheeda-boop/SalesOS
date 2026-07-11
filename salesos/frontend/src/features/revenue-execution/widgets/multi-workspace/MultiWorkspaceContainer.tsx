'use client'

import { createWidget } from '@salesos/workspace'
import type { WorkspaceData } from './types'
import { MultiWorkspaceView } from './MultiWorkspaceView'

const sample: WorkspaceData = { workspaces: [{ id: 'w1', name: 'لوحة القيادة', type: 'dashboard', active: true, lastAccessed: '2026-07-10' }, { id: 'w2', name: 'شركة الطاقة', type: 'company', active: false, lastAccessed: '2026-07-09' }, { id: 'w3', name: 'الفرص', type: 'crm', active: false, lastAccessed: '2026-07-08' }], total: 3, active: 1 }

export const MultiWorkspaceWidget = createWidget({
  metadata: { id: 'multiWorkspace', title: 'مساحات العمل', category: 'enterprise', priority: 'high', permissions: ['workspace:read'], featureFlag: { enabled: true }, minHeight: '320px' },
  useData: () => ({ data: sample, status: 'ready' as const, lastUpdated: null, error: null, refetch: () => {} }),
  render: ({ data }) => <MultiWorkspaceView data={data} />,
})
