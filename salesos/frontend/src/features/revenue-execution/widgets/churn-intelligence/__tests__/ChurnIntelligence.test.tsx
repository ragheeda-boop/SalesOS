import { render, screen } from '@testing-library/react'
import { ChurnView } from '../ChurnView'
import { ChurnIntelligenceWidget } from '../ChurnContainer'
import { describeWidgetContract } from '@salesos/workspace/testing'
import type { ChurnData } from '../types'

const sample: ChurnData = { atRiskAccounts: [{ companyName: 'شركة البترول', riskScore: 0.85, revenue: 1200000, reason: 'لا نشاط', daysSinceActivity: 45 }], totalAtRisk: 1, totalRevenue: 1200000, avgRiskScore: 0.85 }
function renderView(d: ChurnData = sample) { return render(<ChurnView data={d} />) }

describeWidgetContract({ name: 'ChurnIntelligence', defaultData: sample, config: { metadata: { id: 'churnIntelligence', title: 'مخاطر التوقف', permissions: ['churn:read'], featureFlag: { enabled: true } }, render: ({ data }) => <ChurnView data={data} /> } })

describe('ChurnView', () => {
  it('renders company name', () => { renderView(); expect(screen.getByText('شركة البترول')).toBeInTheDocument() })
  it('renders at-risk count', () => { renderView(); const c = screen.getAllByText('1'); expect(c.length).toBeGreaterThanOrEqual(1) })
  it('renders total revenue', () => { renderView(); const v = screen.getAllByText(/\$1\.2M/); expect(v.length).toBeGreaterThanOrEqual(1) })
  it('renders reason', () => { renderView(); expect(screen.getByText('لا نشاط')).toBeInTheDocument() })
  it('renders days inactive', () => { renderView(); expect(screen.getByText(/45 يوم/)).toBeInTheDocument() })
  it('has role="region"', () => { renderView(); expect(screen.getByRole('region', { name: 'مخاطر التوقف' })).toBeInTheDocument() })
})
describe('ChurnIntelligenceWidget', () => { it('is a valid widget', () => { expect(ChurnIntelligenceWidget).toBeDefined() }) })
