import { render, screen } from '@testing-library/react'
import { ExpansionView } from '../ExpansionView'
import { ExpansionIntelligenceWidget } from '../ExpansionContainer'
import { describeWidgetContract } from '@salesos/workspace/testing'
import type { ExpansionData } from '../types'

const sample: ExpansionData = { opportunities: [{ companyName: 'أرامكو', product: 'طاقة', value: 2500000, confidence: 0.82, reason: 'طلب عالي' }], totalValue: 2500000, avgConfidence: 0.82 }
function renderView(d: ExpansionData = sample) { return render(<ExpansionView data={d} />) }

describeWidgetContract({ name: 'ExpansionIntelligence', defaultData: sample, config: { metadata: { id: 'expansionIntelligence', title: 'فرص التوسع', permissions: ['expansion:read'], featureFlag: { enabled: true } }, render: ({ data }) => <ExpansionView data={data} /> } })

describe('ExpansionView', () => {
  it('renders company name', () => { renderView(); expect(screen.getByText('أرامكو')).toBeInTheDocument() })
  it('renders product', () => { renderView(); expect(screen.getByText('طاقة')).toBeInTheDocument() })
  it('renders total value', () => { renderView(); const v = screen.getAllByText(/\$2\.5M/); expect(v.length).toBeGreaterThanOrEqual(1) })
  it('renders reason', () => { renderView(); expect(screen.getByText('طلب عالي')).toBeInTheDocument() })
  it('has role="region"', () => { renderView(); expect(screen.getByRole('region', { name: 'فرص التوسع' })).toBeInTheDocument() })
})
describe('ExpansionIntelligenceWidget', () => { it('is a valid widget', () => { expect(ExpansionIntelligenceWidget).toBeDefined() }) })
