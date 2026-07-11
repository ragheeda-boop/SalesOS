import { render, screen, fireEvent } from '@testing-library/react'
import { NBAView } from '../NBAView'
import { NextBestActionWidget } from '../NBAContainer'
import { describeWidgetContract } from '@salesos/workspace/testing'
import type { NextBestAction } from '@/application/revenue-execution/nba.dto'

const sampleAction: NextBestAction = {
  actionId: 'nba_1',
  actionLabel: 'ترتيب اجتماع',
  actionType: 'meeting',
  reasoning: 'ارتفاع نية الشراء مع توفر جهات اتخاذ القرار',
  confidence: 0.85,
  priority: 'high',
  score: 0.82,
  expectedRevenue: 500000,
  expectedImpact: 'high',
  estimatedTime: 'أسبوعين',
  contextSummary: 'شركة في قطاع الطاقة بحجم enterprise',
  triggerEvent: 'إعلان توسع في الرياض',
  risks: ['مورد بديل قيد التقييم'],
  alternatives: [{ actionLabel: 'إرسال عرض', confidence: 0.7 }],
  playbookId: 'playbook-energy',
  createsOpportunity: true,
  scoreBreakdown: { buyingIntent: 0.82, relationshipStrength: 0.70, signalRecency: 0.60, aiConfidence: 0.85, decisionMakerAccess: 0.50, revenuePotential: 0.12 },
}

function renderView(action = sampleAction) {
  return render(<NBAView action={action} />)
}

describeWidgetContract({
  name: 'NextBestAction',
  defaultData: sampleAction,
  config: {
    metadata: {
      id: 'nextBestAction',
      title: 'أفضل إجراء تالي',
      permissions: ['company:nba:read'],
      featureFlag: { enabled: true },
    },
    render: ({ data }) => <NBAView action={data} />,
  },
})

describe('NBAView', () => {
  it('renders action label', () => {
    renderView()
    expect(screen.getByText('ترتيب اجتماع')).toBeInTheDocument()
  })

  it('renders reasoning', () => {
    renderView()
    expect(screen.getByText(/ارتفاع نية الشراء/)).toBeInTheDocument()
  })

  it('renders priority', () => {
    renderView()
    expect(screen.getByText(/عالي/)).toBeInTheDocument()
  })

  it('renders confidence', () => {
    renderView()
    const pcts = screen.getAllByText(/%85/)
    expect(pcts.length).toBeGreaterThanOrEqual(1)
  })

  it('renders revenue', () => {
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

  it('renders context', () => {
    renderView()
    expect(screen.getByText(/قطاع الطاقة/)).toBeInTheDocument()
  })

  it('renders trigger event', () => {
    renderView()
    expect(screen.getByText(/إعلان توسع/)).toBeInTheDocument()
  })

  it('shows execute button when createsOpportunity', () => {
    const onExecute = jest.fn()
    render(<NBAView action={sampleAction} onExecute={onExecute} />)
    const btn = screen.getByText('تنفيذ — إنشاء فرصة')
    expect(btn).toBeInTheDocument()
    fireEvent.click(btn)
    expect(onExecute).toHaveBeenCalledWith(sampleAction)
  })

  it('hides execute button when no onExecute', () => {
    renderView()
    expect(screen.queryByText('تنفيذ')).not.toBeInTheDocument()
  })

  it('shows score breakdown', () => {
    renderView()
    expect(screen.getByText(/%82/)).toBeInTheDocument()
  })

  it('shows empty state when no action', () => {
    renderView(null)
    expect(screen.getByText('جاري تحليل أفضل إجراء تالي')).toBeInTheDocument()
  })

  it('has role="region"', () => {
    renderView()
    expect(screen.getByRole('region', { name: 'أفضل إجراء تالي' })).toBeInTheDocument()
  })

  it('has dark mode variant classes', () => {
    renderView()
    const container = document.querySelector('[class*="dark:"]')
    expect(container).toBeInTheDocument()
  })
})

describe('NextBestActionWidget (SDK integration)', () => {
  it('is a valid widget component', () => {
    expect(NextBestActionWidget).toBeDefined()
  })
})
