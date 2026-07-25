import { render, screen } from '@testing-library/react'

jest.mock('@/lib/hooks/companyQueries', () => ({
  useCompany: jest.fn(),
}))

jest.mock('@/lib/hooks/company360Queries', () => ({
  useCompany360: jest.fn(),
}))

jest.mock('@salesos/ui', () => ({
  Avatar: ({ fallback }: { fallback?: string }) => <span data-testid="avatar">{fallback}</span>,
  cn: (...args: string[]) => args.filter(Boolean).join(' '),
  Tabs: ({ children }: { children: React.ReactNode }) => <div data-testid="tabs">{children}</div>,
  TabsList: ({ children }: { children: React.ReactNode }) => <div data-testid="tabs-list">{children}</div>,
  Tab: ({ children, value }: { children: React.ReactNode; value: string }) => (
    <button data-testid={`tab-${value}`}>{children}</button>
  ),
  TabsPanel: ({ children, value }: { children: React.ReactNode; value: string }) => (
    <div data-testid={`panel-${value}`}>{children}</div>
  ),
}))

jest.mock('@salesos/design-language', () => ({
  AI_ACTIONS: {
    explain: { labelAr: 'شرح', labelEn: 'Explain' },
    analyze: { labelAr: 'تحليل', labelEn: 'Analyze' },
    predict: { labelAr: 'تنبؤ', labelEn: 'Predict' },
    summarize: { labelAr: 'تلخيص', labelEn: 'Summarize' },
    recommend: { labelAr: 'توصية', labelEn: 'Recommend' },
  },
}))

jest.mock('@/features/company-intelligence/widgets/smart-timeline/SmartTimelineContainer', () => ({
  SmartTimelineWidget: () => <div data-testid="smart-timeline-widget">SmartTimelineWidget</div>,
}))

jest.mock('@/features/company-intelligence/widgets/signals-feed/SignalsFeedContainer', () => ({
  SignalsFeedWidget: () => <div data-testid="signals-feed-widget">SignalsFeedWidget</div>,
}))

jest.mock('@/features/company-intelligence/widgets/decision-makers/DecisionMakersContainer', () => ({
  DecisionMakersWidget: () => <div data-testid="decision-makers-widget">DecisionMakersWidget</div>,
}))

jest.mock('@/features/company-intelligence/widgets/relationship-graph/RelationshipGraphContainer', () => ({
  RelationshipGraphWidget: () => <div data-testid="relationship-graph-widget">RelationshipGraphWidget</div>,
}))

jest.mock('@/features/company-intelligence/widgets/ai-recommendation/AIRecommendationContainer', () => ({
  AIRecommendationWidget: () => <div data-testid="ai-recommendation-widget">AIRecommendationWidget</div>,
}))

jest.mock('@/features/company-intelligence/widgets/company-dna/CompanyDNAContainer', () => ({
  CompanyDNAWidget: () => <div data-testid="company-dna-widget">CompanyDNAWidget</div>,
}))

jest.mock('@/features/company-intelligence/widgets/government-intelligence/GovernmentIntelligenceContainer', () => ({
  GovernmentIntelligenceWidget: () => <div data-testid="government-intelligence-widget">GovernmentIntelligenceWidget</div>,
}))

jest.mock('@/features/company-intelligence/widgets/document-intelligence/DocumentIntelligenceContainer', () => ({
  DocumentIntelligenceWidget: () => <div data-testid="document-intelligence-widget">DocumentIntelligenceWidget</div>,
}))

jest.mock('@/features/company-intelligence/widgets/buying-journey/BuyingJourneyContainer', () => ({
  BuyingJourneyWidget: () => <div data-testid="buying-journey-widget">BuyingJourneyWidget</div>,
}))

jest.mock('@/features/company-intelligence/widgets/golden-record/GoldenRecordContainer', () => ({
  GoldenRecordWidget: () => <div data-testid="golden-record-widget">GoldenRecordWidget</div>,
}))

jest.mock('@/lib/i18n', () => ({
  useTranslation: () => ({
    t: (key: string) => key,
    locale: 'en' as const,
    setLocale: () => {},
    dir: 'ltr' as const,
  }),
}))

jest.mock('../timeline-widget', () => ({
  TimelineWidget: (props: Record<string, unknown>) => (
    <div data-testid="timeline-widget">TimelineWidget: {String(props.entityType)}</div>
  ),
}))

import { useCompany } from '@/lib/hooks/companyQueries'
import { useCompany360 } from '@/lib/hooks/company360Queries'
import { CompanyWorkspace } from '../company-workspace'

const mockUseCompany = useCompany as jest.Mock
const mockUseCompany360 = useCompany360 as jest.Mock

function makeCompany(overrides: Record<string, unknown> = {}) {
  return {
    name_ar: 'شركة أرامكو',
    name_en: 'Saudi Aramco',
    cr_number: '1234567890',
    city: 'الرياض',
    status: 'active',
    region: 'المنطقة الوسطى',
    confidence_score: 85,
    ...overrides,
  }
}

describe('CompanyWorkspace', () => {
  beforeEach(() => jest.clearAllMocks())

  it('shows loading state', () => {
    mockUseCompany.mockReturnValue({ data: undefined, isLoading: true, isError: false })
    mockUseCompany360.mockReturnValue({ data: undefined })
    const { container } = render(<CompanyWorkspace companyId="c1" />)
    expect(container.querySelectorAll('.animate-pulse').length).toBeGreaterThan(0)
  })

  it('shows error state', () => {
    mockUseCompany.mockReturnValue({ data: undefined, isLoading: false, isError: true })
    mockUseCompany360.mockReturnValue({ data: undefined })
    render(<CompanyWorkspace companyId="c1" />)
    expect(screen.getByText('company.load_error')).toBeInTheDocument()
  })

  it('renders company name', () => {
    mockUseCompany.mockReturnValue({ data: makeCompany(), isLoading: false, isError: false })
    mockUseCompany360.mockReturnValue({ data: {} })
    render(<CompanyWorkspace companyId="c1" />)
    expect(screen.getByText('شركة أرامكو')).toBeInTheDocument()
  })

  it('renders English name when different from Arabic', () => {
    mockUseCompany.mockReturnValue({ data: makeCompany(), isLoading: false, isError: false })
    mockUseCompany360.mockReturnValue({ data: {} })
    render(<CompanyWorkspace companyId="c1" />)
    expect(screen.getByText('Saudi Aramco')).toBeInTheDocument()
  })

  it('hides English name when same as Arabic', () => {
    mockUseCompany.mockReturnValue({ data: makeCompany({ name_en: 'شركة أرامكو' }), isLoading: false, isError: false })
    mockUseCompany360.mockReturnValue({ data: {} })
    render(<CompanyWorkspace companyId="c1" />)
    expect(screen.queryByText('Saudi Aramco')).not.toBeInTheDocument()
  })

  it('renders CR number', () => {
    mockUseCompany.mockReturnValue({ data: makeCompany(), isLoading: false, isError: false })
    mockUseCompany360.mockReturnValue({ data: {} })
    render(<CompanyWorkspace companyId="c1" />)
    expect(screen.getByText('1234567890')).toBeInTheDocument()
  })

  it('renders city', () => {
    mockUseCompany.mockReturnValue({ data: makeCompany(), isLoading: false, isError: false })
    mockUseCompany360.mockReturnValue({ data: {} })
    render(<CompanyWorkspace companyId="c1" />)
    expect(screen.getByText('الرياض')).toBeInTheDocument()
  })

  it('does not render city when missing', () => {
    mockUseCompany.mockReturnValue({ data: makeCompany({ city: '' }), isLoading: false, isError: false })
    mockUseCompany360.mockReturnValue({ data: {} })
    const { container } = render(<CompanyWorkspace companyId="c1" />)
    expect(container.querySelector('.lucide-map-pin')).not.toBeInTheDocument()
  })

  it('renders status badge', () => {
    mockUseCompany.mockReturnValue({ data: makeCompany(), isLoading: false, isError: false })
    mockUseCompany360.mockReturnValue({ data: {} })
    render(<CompanyWorkspace companyId="c1" />)
    expect(screen.getByText('active')).toBeInTheDocument()
  })

  it('renders AI action buttons', () => {
    mockUseCompany.mockReturnValue({ data: makeCompany(), isLoading: false, isError: false })
    mockUseCompany360.mockReturnValue({ data: {} })
    render(<CompanyWorkspace companyId="c1" />)
    expect(screen.getByText('شرح')).toBeInTheDocument()
    expect(screen.getByText('تحليل')).toBeInTheDocument()
    expect(screen.getByText('تنبؤ')).toBeInTheDocument()
    expect(screen.getByText('تلخيص')).toBeInTheDocument()
    expect(screen.getByText('توصية')).toBeInTheDocument()
  })

  it('renders tabs with correct labels', () => {
    mockUseCompany.mockReturnValue({ data: makeCompany(), isLoading: false, isError: false })
    mockUseCompany360.mockReturnValue({ data: {} })
    render(<CompanyWorkspace companyId="c1" />)
    expect(screen.getByText('tabs.overview')).toBeInTheDocument()
    expect(screen.getByText('tabs.intelligence')).toBeInTheDocument()
    expect(screen.getByText('tabs.decision_makers')).toBeInTheDocument()
    expect(screen.getByText('tabs.government_data')).toBeInTheDocument()
    expect(screen.getByText('tabs.documents')).toBeInTheDocument()
    expect(screen.getByText('tabs.timeline')).toBeInTheDocument()
  })

  it('shows overview panel by default', () => {
    mockUseCompany.mockReturnValue({ data: makeCompany(), isLoading: false, isError: false })
    mockUseCompany360.mockReturnValue({ data: {} })
    render(<CompanyWorkspace companyId="c1" />)
    expect(screen.getByTestId('panel-overview')).toBeInTheDocument()
    expect(screen.getAllByTestId('company-dna-widget').length).toBeGreaterThanOrEqual(1)
    expect(screen.getAllByTestId('ai-recommendation-widget').length).toBeGreaterThanOrEqual(1)
  })

  it('renders health score ring', () => {
    mockUseCompany.mockReturnValue({ data: makeCompany(), isLoading: false, isError: false })
    mockUseCompany360.mockReturnValue({ data: { health_score: 75 } })
    render(<CompanyWorkspace companyId="c1" />)
    expect(screen.getByText('75')).toBeInTheDocument()
  })

  it('uses confidence_score as fallback for health', () => {
    mockUseCompany.mockReturnValue({ data: makeCompany({ confidence_score: 90 }), isLoading: false, isError: false })
    mockUseCompany360.mockReturnValue({ data: {} })
    render(<CompanyWorkspace companyId="c1" />)
    expect(screen.getByText('90')).toBeInTheDocument()
  })

  it('renders region when available', () => {
    mockUseCompany.mockReturnValue({ data: makeCompany(), isLoading: false, isError: false })
    mockUseCompany360.mockReturnValue({ data: {} })
    render(<CompanyWorkspace companyId="c1" />)
    expect(screen.getByText('المنطقة الوسطى')).toBeInTheDocument()
  })

  it('shows metrics when overview data is available', () => {
    mockUseCompany.mockReturnValue({ data: makeCompany(), isLoading: false, isError: false })
    mockUseCompany360.mockReturnValue({
      data: {
        overview: { total_revenue: 5000000, active_contracts: 12 },
        assigned_employees: [{ full_name: 'أحمد' }],
        opportunities: [{ name: 'صفقة 1' }],
      },
    })
    render(<CompanyWorkspace companyId="c1" />)
    expect(screen.getAllByText('company.assigned_team').length).toBeGreaterThanOrEqual(1)
    expect(screen.getAllByText('company.opportunities').length).toBeGreaterThanOrEqual(1)
  })

  it('does not render metrics when no overview data', () => {
    mockUseCompany.mockReturnValue({ data: makeCompany(), isLoading: false, isError: false })
    mockUseCompany360.mockReturnValue({ data: {} })
    render(<CompanyWorkspace companyId="c1" />)
    expect(screen.queryByText('company.assigned_team')).not.toBeInTheDocument()
  })

  it('renders assigned team members', () => {
    mockUseCompany.mockReturnValue({ data: makeCompany(), isLoading: false, isError: false })
    mockUseCompany360.mockReturnValue({
      data: {
        assigned_employees: [
          { full_name: 'أحمد السبيعي', role: 'مدير مبيعات' },
          { full_name: 'سارة المطيري', role: 'محللة' },
        ],
      },
    })
    render(<CompanyWorkspace companyId="c1" />)
    expect(screen.getAllByText('company.assigned_team').length).toBeGreaterThanOrEqual(1)
    expect(screen.getByText('أحمد السبيعي')).toBeInTheDocument()
    expect(screen.getByText('سارة المطيري')).toBeInTheDocument()
  })
})
