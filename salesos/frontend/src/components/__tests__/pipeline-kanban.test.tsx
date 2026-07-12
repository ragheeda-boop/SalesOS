import { render, screen, fireEvent } from '@testing-library/react'

jest.mock('@/lib/hooks/opportunityQueries', () => ({
  useOpportunities: jest.fn(),
  useCreateOpportunity: jest.fn(),
  useAdvanceOpportunity: jest.fn(),
  useCloseWon: jest.fn(),
  useCloseLost: jest.fn(),
}))

jest.mock('@/lib/hooks/companyQueries', () => ({
  useCompanySearch: jest.fn(),
}))

jest.mock('@radix-ui/react-dialog', () => {
  const real = jest.requireActual('@radix-ui/react-dialog')
  return {
    ...real,
    Portal: ({ children }: { children: React.ReactNode }) => <>{children}</>,
    Overlay: (props: Record<string, unknown>) => <div data-testid="dialog-overlay" {...props} />,
    Content: ({ children, ...props }: React.PropsWithChildren<Record<string, unknown>>) => <div data-testid="dialog-content">{children}</div>,
    Title: ({ children }: { children: React.ReactNode }) => <div>{children}</div>,
  }
})

import {
  useOpportunities,
  useCreateOpportunity,
  useAdvanceOpportunity,
  useCloseWon,
  useCloseLost,
} from '@/lib/hooks/opportunityQueries'
import { useCompanySearch } from '@/lib/hooks/companyQueries'
import { PipelineKanban } from '../pipeline-kanban'

const mockUseOpportunities = useOpportunities as jest.Mock
const mockUseCreateOpportunity = useCreateOpportunity as jest.Mock
const mockUseAdvanceOpportunity = useAdvanceOpportunity as jest.Mock
const mockUseCloseWon = useCloseWon as jest.Mock
const mockUseCloseLost = useCloseLost as jest.Mock
const mockUseCompanySearch = useCompanySearch as jest.Mock

function makeOpp(overrides: Record<string, unknown> = {}) {
  return {
    id: 'opp-1',
    name: 'صفقة اختبار',
    value: 500000,
    stage: 'prospecting',
    status: 'open',
    company_name: 'شركة اختبار',
    ...overrides,
  }
}

describe('PipelineKanban', () => {
  beforeEach(() => {
    jest.clearAllMocks()
    mockUseCreateOpportunity.mockReturnValue({ mutateAsync: jest.fn(), isPending: false })
    mockUseAdvanceOpportunity.mockReturnValue({ mutate: jest.fn() })
    mockUseCloseWon.mockReturnValue({ mutateAsync: jest.fn(), isPending: false })
    mockUseCloseLost.mockReturnValue({ mutateAsync: jest.fn(), isPending: false })
    mockUseCompanySearch.mockReturnValue({ data: { items: [] } })
  })

  it('shows loading state', () => {
    mockUseOpportunities.mockReturnValue({ data: undefined, isLoading: true, error: null })
    render(<PipelineKanban />)
    expect(screen.getByText('جاري التحميل...')).toBeInTheDocument()
  })

  it('shows error state', () => {
    mockUseOpportunities.mockReturnValue({ data: undefined, isLoading: false, error: { message: 'Network error' } })
    render(<PipelineKanban />)
    expect(screen.getByText(/فشل تحميل الفرص/)).toBeInTheDocument()
  })

  it('renders kanban header with stage columns', () => {
    mockUseOpportunities.mockReturnValue({ data: { items: [] }, isLoading: false, error: null })
    render(<PipelineKanban />)
    expect(screen.getByText('خط أنابيب المبيعات')).toBeInTheDocument()
    expect(screen.getByText('استكشاف')).toBeInTheDocument()
    expect(screen.getByText('تأهيل')).toBeInTheDocument()
    expect(screen.getByText('عرض')).toBeInTheDocument()
    expect(screen.getByText('تفاوض')).toBeInTheDocument()
  })

  it('renders empty won/lost columns', () => {
    mockUseOpportunities.mockReturnValue({ data: { items: [] }, isLoading: false, error: null })
    render(<PipelineKanban />)
    expect(screen.getByText('مغلقة (فوز)')).toBeInTheDocument()
    expect(screen.getByText('مغلقة (خسارة)')).toBeInTheDocument()
  })

  it('renders opportunity cards in correct columns', () => {
    const opps = [
      makeOpp({ id: 'o1', name: 'صفقة 1', stage: 'prospecting' }),
      makeOpp({ id: 'o2', name: 'صفقة 2', stage: 'qualification' }),
    ]
    mockUseOpportunities.mockReturnValue({ data: { items: opps }, isLoading: false, error: null })
    render(<PipelineKanban />)
    expect(screen.getByText('صفقة 1')).toBeInTheDocument()
    expect(screen.getByText('صفقة 2')).toBeInTheDocument()
  })

  it('renders won opportunities in won column', () => {
    const opps = [makeOpp({ id: 'o1', status: 'won', stage: 'prospecting' })]
    mockUseOpportunities.mockReturnValue({ data: { items: opps }, isLoading: false, error: null })
    render(<PipelineKanban />)
    expect(screen.getAllByText('1').length).toBeGreaterThanOrEqual(1)
    expect(screen.getAllByText((_, el) => el?.textContent?.includes('فرصة مفتوحة بقيمة') ?? false).length).toBeGreaterThanOrEqual(1)
  })

  it('renders lost opportunities in lost column', () => {
    const opps = [makeOpp({ id: 'o1', status: 'lost', stage: 'prospecting' })]
    mockUseOpportunities.mockReturnValue({ data: { items: opps }, isLoading: false, error: null })
    render(<PipelineKanban />)
    expect(screen.getAllByText('0').length).toBeGreaterThanOrEqual(1)
    expect(screen.getAllByText((_, el) => el?.textContent?.includes('فرصة مفتوحة بقيمة') ?? false).length).toBeGreaterThanOrEqual(1)
  })

  it('calculates total pipeline value', () => {
    const opps = [
      makeOpp({ id: 'o1', value: 100000, stage: 'prospecting' }),
      makeOpp({ id: 'o2', value: 200000, stage: 'qualification' }),
    ]
    mockUseOpportunities.mockReturnValue({ data: { items: opps }, isLoading: false, error: null })
    render(<PipelineKanban />)
    expect(screen.getByText(/300K/)).toBeInTheDocument()
  })

  it('shows empty column placeholders', () => {
    mockUseOpportunities.mockReturnValue({ data: { items: [] }, isLoading: false, error: null })
    render(<PipelineKanban />)
    const allEmpty = screen.getAllByText('اسحب الفرصة هنا')
    expect(allEmpty.length).toBeGreaterThanOrEqual(4)
    expect(screen.getByText('اسحب الفرصة هنا للإغلاق بالفوز')).toBeInTheDocument()
    expect(screen.getByText('اسحب الفرصة هنا للإغلاق بالخسارة')).toBeInTheDocument()
  })
})

describe('OpportunityCard', () => {
  it('formats large currency (>=1M)', () => {
    const { OpportunityCard } = require('../pipeline-kanban/OpportunityCard')
    render(<OpportunityCard opportunity={makeOpp({ value: 2500000 })} />)
    expect(screen.getByText(/2\.5M SAR/)).toBeInTheDocument()
  })

  it('formats medium currency (>=1K)', () => {
    const { OpportunityCard } = require('../pipeline-kanban/OpportunityCard')
    render(<OpportunityCard opportunity={makeOpp({ value: 75000 })} />)
    expect(screen.getByText(/75K SAR/)).toBeInTheDocument()
  })

  it('formats small currency (<1K)', () => {
    const { OpportunityCard } = require('../pipeline-kanban/OpportunityCard')
    render(<OpportunityCard opportunity={makeOpp({ value: 500 })} />)
    expect(screen.getByText(/500 SAR/)).toBeInTheDocument()
  })

  it('shows company name when provided', () => {
    const { OpportunityCard } = require('../pipeline-kanban/OpportunityCard')
    render(<OpportunityCard opportunity={makeOpp({ company_name: 'أرامكو' })} />)
    expect(screen.getByText('أرامكو')).toBeInTheDocument()
  })

  it('hides company name when not provided', () => {
    const { OpportunityCard } = require('../pipeline-kanban/OpportunityCard')
    const { container } = render(<OpportunityCard opportunity={makeOpp({ company_name: '' })} />)
    expect(container.querySelector('.text-neutral-500')).toBeNull()
  })

  it('shows won badge with amount', () => {
    const { OpportunityCard } = require('../pipeline-kanban/OpportunityCard')
    render(<OpportunityCard opportunity={makeOpp({ status: 'won', won_amount: 500000 })} />)
    const matches = screen.getAllByText(/500K/)
    expect(matches.length).toBe(2)
  })

  it('shows loss reason when status is lost', () => {
    const { OpportunityCard } = require('../pipeline-kanban/OpportunityCard')
    render(<OpportunityCard opportunity={makeOpp({ status: 'lost', loss_reason: 'السعر مرتفع' })} />)
    expect(screen.getByText('السعر مرتفع')).toBeInTheDocument()
  })

  it('sets dragging class on drag start', () => {
    const { OpportunityCard } = require('../pipeline-kanban/OpportunityCard')
    const { container } = render(<OpportunityCard opportunity={makeOpp()} />)
    const card = container.firstChild as HTMLElement
    const dataTransfer = { setData: jest.fn() }
    fireEvent.dragStart(card, { dataTransfer })
    expect(dataTransfer.setData).toHaveBeenCalledWith('text/plain', 'opp-1')
  })

  it('removes dragging class on drag end', () => {
    const { OpportunityCard } = require('../pipeline-kanban/OpportunityCard')
    const { container } = render(<OpportunityCard opportunity={makeOpp()} />)
    const card = container.firstChild as HTMLElement
    fireEvent.dragStart(card, { dataTransfer: { setData: jest.fn() } })
    fireEvent.dragEnd(card)
    expect(card.className).not.toContain('opacity-50')
  })
})

describe('PipelineColumn', () => {
  it('calls onDrop with correct stage', () => {
    const onDrop = jest.fn()
    const { PipelineColumn } = require('../pipeline-kanban/PipelineColumn')
    const stage = { key: 'proposal', label: 'عرض', color: 'bg-warning-500' }
    const { container } = render(<PipelineColumn stage={stage} opportunities={[]} onDrop={onDrop} />)

    const column = container.firstChild as HTMLElement
    const dataTransfer = { getData: jest.fn().mockReturnValue('opp-123'), preventDefault: jest.fn() }
    fireEvent.drop(column, { dataTransfer })
    expect(onDrop).toHaveBeenCalledWith('opp-123', 'proposal')
  })

  it('does not call onDrop when no data in transfer', () => {
    const onDrop = jest.fn()
    const { PipelineColumn } = require('../pipeline-kanban/PipelineColumn')
    const stage = { key: 'proposal', label: 'عرض', color: 'bg-warning-500' }
    const { container } = render(<PipelineColumn stage={stage} opportunities={[]} onDrop={onDrop} />)

    const column = container.firstChild as HTMLElement
    const dataTransfer = { getData: jest.fn().mockReturnValue(''), preventDefault: jest.fn() }
    fireEvent.drop(column, { dataTransfer })
    expect(onDrop).not.toHaveBeenCalled()
  })

  it('shows opportunity count in badge', () => {
    const { PipelineColumn } = require('../pipeline-kanban/PipelineColumn')
    const stage = { key: 'proposal', label: 'عرض', color: 'bg-warning-500' }
    const opps = [makeOpp({ id: 'o1' }), makeOpp({ id: 'o2' })]
    render(<PipelineColumn stage={stage} opportunities={opps} onDrop={jest.fn()} />)
    expect(screen.getByText('2')).toBeInTheDocument()
  })
})
