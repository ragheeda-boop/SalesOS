import { render, screen } from '@testing-library/react'
import { AIRecommendationView } from '../AIRecommendationView'
import { AIRecommendationWidget } from '../AIRecommendationContainer'
import { describeWidgetContract } from '@salesos/workspace/testing'
import type { AIRecommendation } from '@/application/company-intelligence/company-intelligence.dto'

const sample: AIRecommendation = {
  action: 'schedule_demo', actionLabel: 'جدولة عرض توضيحي',
  reasoning: 'ارتفاع نية الشراء مع توفر جهات اتخاذ القرار',
  confidence: 0.85, expectedRevenue: 500000, expectedImpact: 'high',
  estimatedTime: 'أسبوعين',
  alternatives: [{ action: 'send_proposal', actionLabel: 'إرسال عرض', confidence: 0.7 }],
  risks: ['مورد بديل قيد التقييم'],
}

function renderView(override?: AIRecommendation | null) {
  return render(<AIRecommendationView recommendation={override !== undefined ? override : sample} />)
}

describeWidgetContract({
  name: 'AIRecommendation', defaultData: sample,
  config: {
    metadata: { id: 'aiRecommendation', title: 'توصيات AI', permissions: ['company:ai:recommendations'], featureFlag: { enabled: true } },
    render: ({ data }) => <AIRecommendationView recommendation={data} />,
  },
})

describe('AIRecommendationView', () => {
  it('renders action label', () => {
    renderView()
    expect(screen.getByText('جدولة عرض توضيحي')).toBeInTheDocument()
  })

  it('renders reasoning', () => {
    renderView()
    expect(screen.getByText(/ارتفاع نية الشراء/)).toBeInTheDocument()
  })

  it('renders confidence', () => {
    renderView()
    expect(screen.getByText(/%85/)).toBeInTheDocument()
  })

  it('renders expected revenue', () => {
    renderView()
    expect(screen.getByText(/\$500K/)).toBeInTheDocument()
  })

  it('renders risks', () => {
    renderView()
    expect(screen.getByText('مورد بديل قيد التقييم')).toBeInTheDocument()
  })

  it('renders alternatives', () => {
    renderView()
    expect(screen.getByText('إرسال عرض')).toBeInTheDocument()
  })

  it('shows empty state', () => {
    renderView(null)
    expect(screen.getByText('لا توجد توصيات متاحة')).toBeInTheDocument()
  })

  it('has role="region"', () => {
    renderView()
    expect(screen.getByRole('region', { name: 'توصيات AI' })).toBeInTheDocument()
  })
})

describe('AIRecommendationWidget', () => {
  it('is a valid widget component', () => {
    expect(AIRecommendationWidget).toBeDefined()
  })
})
