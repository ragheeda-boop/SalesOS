import { render, screen } from '@testing-library/react'
import { MCPView } from '../MCPView'
import { MCPIntegrationWidget } from '../MCPContainer'
import { describeWidgetContract } from '@salesos/workspace/testing'
import type { MCPData } from '../types'

const sample: MCPData = { connections: [{ id: 'm1', name: 'Odoo', type: 'ERP', status: 'connected', entities: 100 }], totalConnections: 1, activeConnections: 1, syncedEntities: 100 }
function renderView(d: MCPData = sample) { return render(<MCPView data={d} />) }

describeWidgetContract({ name: 'MCPIntegration', defaultData: sample, config: { metadata: { id: 'mcpIntegration', title: 'اتصالات MCP', permissions: ['enterprise:mcp:read'], featureFlag: { enabled: true } }, render: ({ data }) => <MCPView data={data} /> } })

describe('MCPView', () => {
  it('renders connection name', () => { renderView(); expect(screen.getByText('Odoo')).toBeInTheDocument() })
  it('renders connection count', () => { renderView(); const c = screen.getAllByText('1'); expect(c.length).toBeGreaterThanOrEqual(1) })
  it('renders entity count', () => { renderView(); expect(screen.getByText('100')).toBeInTheDocument() })
  it('has role="region"', () => { renderView(); expect(screen.getByRole('region', { name: 'اتصالات MCP' })).toBeInTheDocument() })
})
describe('MCPIntegrationWidget', () => { it('is a valid widget', () => { expect(MCPIntegrationWidget).toBeDefined() }) })
