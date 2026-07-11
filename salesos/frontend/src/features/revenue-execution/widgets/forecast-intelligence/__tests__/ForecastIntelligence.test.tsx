import { render, screen } from '@testing-library/react'
import { ForecastView } from '../ForecastView'
import { ForecastIntelligenceWidget } from '../ForecastContainer'
import { describeWidgetContract } from '@salesos/workspace/testing'
import type { ForecastData } from '../types'

const sample: ForecastData = {
  currentQuarter: { target: 10000000, actual: 4200000, projected: 7800000, confidence: 0.78 },
  monthlyTrend: [], risks: [{ label: 'تباطؤ', impact: 500000, probability: 0.35 }],
}

function renderView(d: ForecastData = sample) { return render(<ForecastView data={d} />) }

describeWidgetContract({ name: 'ForecastIntelligence', defaultData: sample, config: { metadata: { id: 'forecastIntelligence', title: 'التوقعات', permissions: ['forecast:read'], featureFlag: { enabled: true } }, render: ({ data }) => <ForecastView data={data} /> } })

describe('ForecastView', () => {
  it('renders target', () => { renderView(); expect(screen.getByText(/\$10\.0M/)).toBeInTheDocument() })
  it('renders actual', () => { renderView(); expect(screen.getByText(/\$4\.2M/)).toBeInTheDocument() })
  it('renders projected', () => { renderView(); expect(screen.getByText(/\$7\.8M/)).toBeInTheDocument() })
  it('renders risks', () => { renderView(); expect(screen.getByText('تباطؤ')).toBeInTheDocument() })
  it('has role="region"', () => { renderView(); expect(screen.getByRole('region', { name: 'التوقعات' })).toBeInTheDocument() })
})
describe('ForecastIntelligenceWidget', () => { it('is a valid widget', () => { expect(ForecastIntelligenceWidget).toBeDefined() }) })
