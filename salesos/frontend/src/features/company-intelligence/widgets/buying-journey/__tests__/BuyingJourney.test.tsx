import { render, screen } from '@testing-library/react'
import { BuyingJourneyView } from '../BuyingJourneyView'
import { BuyingJourneyWidget } from '../BuyingJourneyContainer'
import { describeWidgetContract } from '@salesos/workspace/testing'
import type { BuyingJourney } from '@/application/company-intelligence/company-intelligence.dto'

const sample: BuyingJourney = {
  currentStage: 'evaluation', progress: 45, timeInStage: '14 يوم',
  recommendedAction: 'تقديم عرض توضيحي', stageDescription: 'العميل يقيم الموردين المحتملين',
}

function renderView(journey = sample) {
  return render(<BuyingJourneyView journey={journey} />)
}

describeWidgetContract({
  name: 'BuyingJourney', defaultData: sample,
  config: {
    metadata: { id: 'buyingJourney', title: 'رحلة الشراء', permissions: ['company:buying-journey:read'], featureFlag: { enabled: true } },
    render: ({ data }) => <BuyingJourneyView journey={data} />,
  },
})

describe('BuyingJourneyView', () => {
  it('renders recommended action', () => {
    renderView()
    expect(screen.getByText('تقديم عرض توضيحي')).toBeInTheDocument()
  })

  it('renders stage description', () => {
    renderView()
    expect(screen.getByText(/العميل يقيم الموردين/)).toBeInTheDocument()
  })

  it('renders progress', () => {
    renderView()
    expect(screen.getByText(/%45 مكتمل/)).toBeInTheDocument()
  })

  it('shows empty state', () => {
    renderView(null)
    expect(screen.getByText('رحلة الشراء غير متاحة')).toBeInTheDocument()
  })

  it('has role="region"', () => {
    renderView()
    expect(screen.getByRole('region', { name: 'رحلة الشراء' })).toBeInTheDocument()
  })
})

describe('BuyingJourneyWidget', () => {
  it('is a valid widget component', () => {
    expect(BuyingJourneyWidget).toBeDefined()
  })
})
