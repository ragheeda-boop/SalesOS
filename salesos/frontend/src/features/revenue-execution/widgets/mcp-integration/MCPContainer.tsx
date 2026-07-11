'use client'

import { createWidget } from '@salesos/workspace'
import type { MCPData } from './types'
import { MCPView } from './MCPView'

const sample: MCPData = { connections: [{ id: 'm1', name: 'Odoo ERP', type: 'ERP', status: 'connected', lastSync: '2026-07-10', entities: 12500 }, { id: 'm2', name: 'Neo4j Graph', type: 'قاعدة بيانات', status: 'connected', entities: 45000 }, { id: 'm3', name: 'Government API', type: 'API', status: 'disconnected', entities: 0 }], totalConnections: 3, activeConnections: 2, syncedEntities: 57500 }

export const MCPIntegrationWidget = createWidget({
  metadata: { id: 'mcpIntegration', title: 'اتصالات MCP', category: 'enterprise', priority: 'medium', permissions: ['enterprise:mcp:read'], featureFlag: { enabled: true }, minHeight: '360px' },
  useData: () => ({ data: sample, status: 'ready' as const, lastUpdated: null, error: null, refetch: () => {} }),
  render: ({ data }) => <MCPView data={data} />,
})
