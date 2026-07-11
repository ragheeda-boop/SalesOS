'use client'

import { createWidget } from '@salesos/workspace'
import type { SecurityData } from './types'
import { SecurityView } from './SecurityView'

const sample: SecurityData = { ssoEnabled: true, rbacEnabled: true, auditEnabled: true, mfaEnabled: false, activeUsers: 24, roles: 6, auditEvents: 15200, pendingActions: 2, recentAudit: [{ action: 'تسجيل دخول', user: 'ahmed@salesos', timestamp: '2026-07-10T08:00:00Z', status: 'success' }, { action: 'تحديث صلاحية', user: 'admin', timestamp: '2026-07-09T14:00:00Z', status: 'success' }] }

export const EnterpriseSecurityWidget = createWidget({
  metadata: { id: 'enterpriseSecurity', title: 'الأمان', category: 'enterprise', priority: 'critical', permissions: ['enterprise:security:read'], featureFlag: { enabled: true, tier: 'enterprise' }, minHeight: '360px' },
  useData: () => ({ data: sample, status: 'ready' as const, lastUpdated: null, error: null, refetch: () => {} }),
  render: ({ data }) => <SecurityView data={data} />,
})
