import { render, screen } from '@testing-library/react'
import { MarketplaceView } from '../MarketplaceView'
import { MarketplaceWidget } from '../MarketplaceContainer'
import { describeWidgetContract } from '@salesos/workspace/testing'
import type { PluginData } from '../types'

const sample: PluginData = { plugins: [{ id: 'p1', name: 'Slack', description: 'التكامل', installed: true, version: '1.0', icon: '', category: 'تواصل' }], installed: 1, available: 1 }
function renderView(d: PluginData = sample) { return render(<MarketplaceView data={d} />) }

describeWidgetContract({ name: 'Marketplace', defaultData: sample, config: { metadata: { id: 'marketplace', title: 'المتجر', permissions: ['enterprise:marketplace:read'], featureFlag: { enabled: true } }, render: ({ data }) => <MarketplaceView data={data} /> } })

describe('MarketplaceView', () => {
  it('renders plugin name', () => { renderView(); expect(screen.getByText('Slack')).toBeInTheDocument() })
  it('renders version', () => { renderView(); expect(screen.getByText('v1.0')).toBeInTheDocument() })
  it('shows install count', () => { renderView(); const s = screen.getAllByText(/1\/1/); expect(s.length).toBeGreaterThanOrEqual(1) })
  it('has role="region"', () => { renderView(); expect(screen.getByRole('region', { name: 'المتجر' })).toBeInTheDocument() })
})
describe('MarketplaceWidget', () => { it('is a valid widget', () => { expect(MarketplaceWidget).toBeDefined() }) })
