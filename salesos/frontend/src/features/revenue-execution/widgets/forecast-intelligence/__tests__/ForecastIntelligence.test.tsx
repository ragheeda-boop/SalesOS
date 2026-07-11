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
  it('renders risk probability', () => { renderView(); expect(screen.getByText(/%35/)).toBeInTheDocument() })
  it('renders progress percentage', () => { renderView(); expect(screen.getByText(/%42/)).toBeInTheDocument() })
  it('renders projected percentage of target', () => { renderView(); expect(screen.getByText(/%78/)).toBeInTheDocument() })
  it('has role="region"', () => { renderView(); expect(screen.getByRole('region', { name: 'التوقعات' })).toBeInTheDocument() })
})

describe('ForecastView edge cases', () => {
  it('renders 0% progress when target is 0', () => {
    const zeroTarget: ForecastData = { currentQuarter: { target: 0, actual: 500000, projected: 500000, confidence: 0 }, monthlyTrend: [], risks: [] }
    renderView(zeroTarget)
    expect(screen.getByText(/%0/)).toBeInTheDocument()
  })

  it('renders $0 for all metrics when all zero', () => {
    const allZero: ForecastData = { currentQuarter: { target: 0, actual: 0, projected: 0, confidence: 0 }, monthlyTrend: [], risks: [] }
    renderView(allZero)
    expect(screen.getByText(/\$0K/)).toBeInTheDocument()
  })

  it('renders K format for values under 1M', () => {
    const small: ForecastData = { currentQuarter: { target: 500000, actual: 250000, projected: 350000, confidence: 0.5 }, monthlyTrend: [], risks: [] }
    renderView(small)
    expect(screen.getByText(/\$500K/)).toBeInTheDocument()
    expect(screen.getByText(/\$250K/)).toBeInTheDocument()
    expect(screen.getByText(/\$350K/)).toBeInTheDocument()
  })

  it('does not render risks section when empty', () => {
    const noRisks: ForecastData = { ...sample, risks: [] }
    renderView(noRisks)
    expect(screen.queryByText('المخاطر')).not.toBeInTheDocument()
  })

  it('renders multiple risks', () => {
    const multiRisks: ForecastData = {
      ...sample,
      risks: [
        { label: 'تباطؤ السوق', impact: 500000, probability: 0.35 },
        { label: 'منافس جديد', impact: 300000, probability: 0.25 },
      ],
    }
    renderView(multiRisks)
    expect(screen.getByText('تباطؤ السوق')).toBeInTheDocument()
    expect(screen.getByText('منافس جديد')).toBeInTheDocument()
    expect(screen.getByText(/%35/)).toBeInTheDocument()
    expect(screen.getByText(/%25/)).toBeInTheDocument()
  })
})
describe('ForecastIntelligenceWidget', () => { it('is a valid widget', () => { expect(ForecastIntelligenceWidget).toBeDefined() }) })
