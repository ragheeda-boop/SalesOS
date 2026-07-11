import { render, screen } from '@testing-library/react'
import { RevenueHealthView } from '../RevenueHealthView'
import { RevenueHealthWidget } from '../RevenueHealthContainer'
import { describeWidgetContract } from '@salesos/workspace/testing'
import type { RevenueHealthData } from '../types'

const sample: RevenueHealthData = { totalPortfolio: 85, activeAccounts: 62, atRisk: 8, growthAccounts: 15, healthDistribution: [{ label: 'ممتاز', count: 25, value: 40, color: 'bg-green-500' }] }
function renderView(d: RevenueHealthData = sample) { return render(<RevenueHealthView data={d} />) }

describeWidgetContract({ name: 'RevenueHealth', defaultData: sample, config: { metadata: { id: 'revenueHealth', title: 'صحة الإيرادات', permissions: ['revenue:health:read'], featureFlag: { enabled: true } }, render: ({ data }) => <RevenueHealthView data={data} /> } })

describe('RevenueHealthView', () => {
  it('renders portfolio count', () => { renderView(); expect(screen.getByText('85')).toBeInTheDocument() })
  it('renders active count', () => { renderView(); expect(screen.getByText('62')).toBeInTheDocument() })
  it('renders at-risk count', () => { renderView(); expect(screen.getByText('8')).toBeInTheDocument() })
  it('renders health labels', () => { renderView(); expect(screen.getByText('ممتاز')).toBeInTheDocument() })
  it('has role="region"', () => { renderView(); expect(screen.getByRole('region', { name: 'صحة الإيرادات' })).toBeInTheDocument() })
})
describe('RevenueHealthWidget', () => { it('is a valid widget', () => { expect(RevenueHealthWidget).toBeDefined() }) })
