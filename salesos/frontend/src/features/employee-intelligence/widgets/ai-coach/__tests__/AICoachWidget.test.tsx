import { render, screen } from '@testing-library/react'
import { AICoachView } from '../AICoachWidget'
import type { AICoachAction } from '@/lib/api'

jest.mock('../../../../revenue-execution/_providers/DecisionProvider', () => ({
  useDecision: () => ({
    evaluate: jest.fn().mockResolvedValue({}),
    isEvaluating: false,
  }),
  DecisionProvider: ({ children }: { children: React.ReactNode }) => <>{children}</>,
}))

const actions: AICoachAction[] = [
  { type: 'pipeline_empty', title: 'أنشئ صفقة جديدة', description: 'خط التصفية فارغ', priority: 'high', target_type: 'opportunity' },
  { type: 'win_rate_low', title: 'حسّن نسبة الفوز', description: 'نسبة الفوز منخفضة', priority: 'medium' },
  { type: 'on_track', title: 'أداء ممتاز', description: 'كل شيء على ما يرام', priority: 'low' },
]

describe('AICoachView', () => {
  it('renders action titles', () => {
    render(<AICoachView actions={actions} />)
    expect(screen.getByText('أنشئ صفقة جديدة')).toBeInTheDocument()
    expect(screen.getByText('حسّن نسبة الفوز')).toBeInTheDocument()
    expect(screen.getByText('أداء ممتاز')).toBeInTheDocument()
  })

  it('renders action descriptions', () => {
    render(<AICoachView actions={actions} />)
    expect(screen.getByText('خط التصفية فارغ')).toBeInTheDocument()
    expect(screen.getByText('نسبة الفوز منخفضة')).toBeInTheDocument()
  })

  it('renders empty state when no actions', () => {
    render(<AICoachView actions={[]} />)
    expect(screen.getByText('لا توجد إجراءات حالياً')).toBeInTheDocument()
  })
})
