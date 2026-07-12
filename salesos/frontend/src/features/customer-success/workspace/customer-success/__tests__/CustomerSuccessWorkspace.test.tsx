import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import '@testing-library/jest-dom'

jest.mock('@/lib/telemetryQueries', () => ({
  useTelemetryOverview: jest.fn(),
}))

jest.mock('../../../widgets/customer-success/HealthScoreCard', () => ({
  HealthScoreCard: ({ score, label }: { score: number; label: string }) => (
    <div data-testid="health-score-card">{label}: {score}%</div>
  ),
}))
jest.mock('../../../widgets/customer-success/AdoptionChart', () => ({
  AdoptionChart: ({ data }: { data: unknown }) => (
    <div data-testid="adoption-chart">AdoptionChart</div>
  ),
}))
jest.mock('../../../widgets/customer-success/ActiveUsersWidget', () => ({
  ActiveUsersWidget: ({ dau, wau, mau }: { dau: number; wau: number; mau: number }) => (
    <div data-testid="active-users-widget">DAU: {dau} WAU: {wau} MAU: {mau}</div>
  ),
}))
jest.mock('../../../widgets/customer-success/SearchSuccessWidget', () => ({
  SearchSuccessWidget: ({ total_searches, success_rate }: { total_searches: number; success_rate: number }) => (
    <div data-testid="search-success-widget">Searches: {total_searches} Rate: {success_rate}</div>
  ),
}))
jest.mock('../../../widgets/customer-success/NBAAcceptanceWidget', () => ({
  NBAAcceptanceWidget: ({ nba_views, acceptance_rate }: { nba_views: number; acceptance_rate: number }) => (
    <div data-testid="nba-acceptance-widget">Views: {nba_views} Rate: {acceptance_rate}</div>
  ),
}))
jest.mock('../../../widgets/customer-success/TenantHealthList', () => ({
  TenantHealthList: ({ tenants }: { tenants: Array<{ tenant_name: string }> }) => (
    <div data-testid="tenant-health-list">{tenants.map(t => t.tenant_name).join(', ')}</div>
  ),
}))

import { useTelemetryOverview } from '@/lib/telemetryQueries'
import { CustomerSuccessWorkspace } from '../CustomerSuccessWorkspace'

const mockedUseTelemetryOverview = useTelemetryOverview as jest.MockedFunction<typeof useTelemetryOverview>

const mockData = {
  avg_adoption_pct: 75,
  feature_adoption: [
    { feature: 'search', label: 'Search', user_count: 80, total_users: 100, adoption_pct: 80 },
    { feature: 'nba', label: 'NBA', user_count: 50, total_users: 100, adoption_pct: 50 },
  ],
  search_success: { total_searches: 1000, searches_with_action: 600, success_rate: 0.6 },
  nba_acceptance: { nba_views: 200, nba_accepts: 80, nba_rejects: 20, acceptance_rate: 0.4 },
  active_users: { dau: 25, wau: 120, mau: 450 },
}

beforeEach(() => {
  jest.clearAllMocks()
})

describe('CustomerSuccessWorkspace', () => {
  it('shows loading skeleton when loading', () => {
    mockedUseTelemetryOverview.mockReturnValue({ data: null, isLoading: true } as any)
    const { container } = render(<CustomerSuccessWorkspace />)
    expect(container.querySelector('.animate-pulse')).toBeInTheDocument()
  })

  it('renders workspace header', () => {
    mockedUseTelemetryOverview.mockReturnValue({ data: mockData, isLoading: false } as any)
    render(<CustomerSuccessWorkspace />)
    expect(screen.getByText('نجاح العملاء')).toBeInTheDocument()
  })

  it('renders overview widgets with telemetry data', () => {
    mockedUseTelemetryOverview.mockReturnValue({ data: mockData, isLoading: false } as any)
    render(<CustomerSuccessWorkspace />)
    expect(screen.getByTestId('health-score-card')).toHaveTextContent('75%')
    expect(screen.getByTestId('active-users-widget')).toHaveTextContent('DAU: 25')
    expect(screen.getByTestId('search-success-widget')).toHaveTextContent('Searches: 1000')
    expect(screen.getByTestId('nba-acceptance-widget')).toHaveTextContent('Views: 200')
    expect(screen.getByTestId('adoption-chart')).toBeInTheDocument()
  })

  it('switches to tenants tab', () => {
    mockedUseTelemetryOverview.mockReturnValue({ data: mockData, isLoading: false } as any)
    render(<CustomerSuccessWorkspace />)
    fireEvent.click(screen.getByText('العملاء'))
    expect(screen.getByText('قائمة العملاء')).toBeInTheDocument()
    expect(screen.queryByTestId('adoption-chart')).not.toBeInTheDocument()
  })

  it('switches back to overview tab', () => {
    mockedUseTelemetryOverview.mockReturnValue({ data: mockData, isLoading: false } as any)
    render(<CustomerSuccessWorkspace />)
    fireEvent.click(screen.getByText('العملاء'))
    fireEvent.click(screen.getByText('نظرة عامة'))
    expect(screen.getByTestId('adoption-chart')).toBeInTheDocument()
    expect(screen.queryByText('قائمة العملاء')).not.toBeInTheDocument()
  })

  it('renders overview tab buttons with correct styles', () => {
    mockedUseTelemetryOverview.mockReturnValue({ data: mockData, isLoading: false } as any)
    render(<CustomerSuccessWorkspace />)
    const overviewBtn = screen.getByText('نظرة عامة')
    const tenantsBtn = screen.getByText('العملاء')
    expect(overviewBtn).toBeInTheDocument()
    expect(tenantsBtn).toBeInTheDocument()
  })

  it('shows tenant health list in overview', () => {
    mockedUseTelemetryOverview.mockReturnValue({ data: mockData, isLoading: false } as any)
    render(<CustomerSuccessWorkspace />)
    const lists = screen.getAllByTestId('tenant-health-list')
    expect(lists.length).toBeGreaterThanOrEqual(1)
  })
})
