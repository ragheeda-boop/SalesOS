import { render, screen } from '@testing-library/react'

jest.mock('@/lib/hooks/activityQueries', () => ({
  useEntityActivity: jest.fn(),
}))

import { useEntityActivity } from '@/lib/hooks/activityQueries'
import { TimelineWidget } from '../timeline-widget'

const mockUseEntityActivity = useEntityActivity as jest.Mock

function makeActivity(overrides: Record<string, string> = {}) {
  return {
    id: 'act-1',
    action: 'email_sent',
    actor: 'أحمد',
    timestamp: new Date().toISOString(),
    ...overrides,
  }
}

describe('TimelineWidget', () => {
  beforeEach(() => jest.clearAllMocks())

  it('shows loading skeletons', () => {
    mockUseEntityActivity.mockReturnValue({ data: undefined, isLoading: true })
    render(<TimelineWidget entityType="company" entityId="c1" />)
    expect(screen.getAllByRole('generic').length).toBeGreaterThan(0)
  })

  it('shows empty message when no activities', () => {
    mockUseEntityActivity.mockReturnValue({ data: { items: [], total: 0 }, isLoading: false })
    render(<TimelineWidget entityType="company" entityId="c1" />)
    expect(screen.getByText('لا توجد نشاطات حتى الآن')).toBeInTheDocument()
  })

  it('renders activity count in header', () => {
    mockUseEntityActivity.mockReturnValue({
      data: { items: [makeActivity()], total: 5 },
      isLoading: false,
    })
    render(<TimelineWidget entityType="company" entityId="c1" />)
    expect(screen.getByText('5 نشاط')).toBeInTheDocument()
  })

  it('renders custom title', () => {
    mockUseEntityActivity.mockReturnValue({ data: { items: [], total: 0 }, isLoading: false })
    render(<TimelineWidget entityType="company" entityId="c1" title="نشاطات مخصصة" />)
    expect(screen.getByText('نشاطات مخصصة')).toBeInTheDocument()
  })

  it('renders default title when not provided', () => {
    mockUseEntityActivity.mockReturnValue({ data: { items: [], total: 0 }, isLoading: false })
    render(<TimelineWidget entityType="company" entityId="c1" />)
    expect(screen.getByText('النشاطات')).toBeInTheDocument()
  })

  it('renders known action labels', () => {
    mockUseEntityActivity.mockReturnValue({
      data: {
        items: [
          makeActivity({ action: 'email_sent', actor: 'سارة' }),
          makeActivity({ id: 'act-2', action: 'call', actor: 'محمد' }),
          makeActivity({ id: 'act-3', action: 'meeting_completed', actor: 'خالد' }),
        ],
        total: 3,
      },
      isLoading: false,
    })
    render(<TimelineWidget entityType="company" entityId="c1" />)
    expect(screen.getByText('إرسال بريد إلكتروني')).toBeInTheDocument()
    expect(screen.getByText('مكالمة هاتفية')).toBeInTheDocument()
    expect(screen.getByText('اجتماع منتهي')).toBeInTheDocument()
  })

  it('renders actor names', () => {
    mockUseEntityActivity.mockReturnValue({
      data: { items: [makeActivity({ actor: 'فاطمة' })], total: 1 },
      isLoading: false,
    })
    render(<TimelineWidget entityType="company" entityId="c1" />)
    expect(screen.getByText('فاطمة')).toBeInTheDocument()
  })

  it('falls back to raw action string for unknown actions', () => {
    mockUseEntityActivity.mockReturnValue({
      data: { items: [makeActivity({ action: 'custom_action' })], total: 1 },
      isLoading: false,
    })
    render(<TimelineWidget entityType="company" entityId="c1" />)
    expect(screen.getByText('custom_action')).toBeInTheDocument()
  })

  it('renders connector lines between items', () => {
    mockUseEntityActivity.mockReturnValue({
      data: {
        items: [
          makeActivity(),
          makeActivity({ id: 'act-2' }),
        ],
        total: 2,
      },
      isLoading: false,
    })
    const { container } = render(<TimelineWidget entityType="company" entityId="c1" />)
    const lines = container.querySelectorAll('.absolute.right-\\[15px\\]')
    expect(lines.length).toBe(1)
  })

  it('does not render connector for last item', () => {
    mockUseEntityActivity.mockReturnValue({
      data: {
        items: [
          makeActivity(),
          makeActivity({ id: 'act-2' }),
        ],
        total: 2,
      },
      isLoading: false,
    })
    const { container } = render(<TimelineWidget entityType="company" entityId="c1" />)
    const items = container.querySelectorAll('.relative.flex.gap-3')
    const lastItem = items[items.length - 1]
    expect(lastItem.querySelector('.absolute')).toBeNull()
  })

  it('applies className prop', () => {
    mockUseEntityActivity.mockReturnValue({ data: { items: [], total: 0 }, isLoading: false })
    const { container } = render(<TimelineWidget entityType="company" entityId="c1" className="my-custom" />)
    expect(container.firstChild).toHaveClass('my-custom')
  })
})
