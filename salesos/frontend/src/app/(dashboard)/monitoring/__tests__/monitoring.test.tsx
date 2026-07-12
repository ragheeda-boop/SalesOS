import { render, screen, waitFor, act } from '@testing-library/react'
import '@testing-library/jest-dom'

jest.mock('@/lib/api')
jest.mock('@salesos/ui', () => {
  const actual = jest.requireActual('@salesos/ui')
  return {
    ...actual,
    Spinner: () => <span data-testid="spinner" />,
    Badge: ({ children, variant }: { children: React.ReactNode; variant?: string }) => (
      <span data-testid="badge" data-variant={variant}>{children}</span>
    ),
    cn: (...args: (string | undefined | false)[]) => args.filter(Boolean).join(' '),
    Card: ({ children, className }: { children: React.ReactNode; className?: string }) => (
      <div data-testid="card" className={className}>{children}</div>
    ),
  }
})
jest.mock('lucide-react', () => ({
  AlertTriangle: () => <span data-testid="icon-alert" />,
  Activity: () => <span data-testid="icon-activity" />,
  Clock: () => <span data-testid="icon-clock" />,
  MemoryStick: () => <span data-testid="icon-memory" />,
  Gauge: () => <span data-testid="icon-gauge" />,
  RefreshCw: () => <span data-testid="icon-refresh" />,
  CheckCircle: () => <span data-testid="icon-check" />,
  XCircle: () => <span data-testid="icon-x" />,
}))

import api from '@/lib/api'
import MonitoringPage from '../page'

const mockedApi = api as jest.Mocked<typeof api>

const mockMetrics = {
  api_calls: { total: 1234, p50_ms: 45, p95_ms: 120, p99_ms: 250 },
  errors: {
    total: 12,
    by_context: { auth: 5, api: 7 },
    recent: [
      { message: 'Timeout error', time: '2026-07-12T10:00:00Z' },
      { message: 'DB connection failed', time: '2026-07-12T09:30:00Z' },
    ],
  },
  page_loads: { total: 5000, avg_load_ms: 180, avg_dom_interactive_ms: 90 },
  web_vitals: { lcp: 1200, fid: 50, cls: 0.05 },
  system_health: {
    database: 'connected',
    redis: 'connected',
    neo4j: 'disconnected',
  },
  memory: { current_mb: 256 },
}

beforeEach(() => {
  jest.useFakeTimers()
  mockedApi.get.mockResolvedValue({ data: mockMetrics })
})

afterEach(() => {
  jest.useRealTimers()
  jest.clearAllMocks()
})

describe('MonitoringPage', () => {
  it('renders loading spinner initially', async () => {
    mockedApi.get.mockReturnValue(new Promise(() => {}))
    render(<MonitoringPage />)
    expect(screen.getByTestId('spinner')).toBeInTheDocument()
    expect(screen.getByText(/جاري التحميل/)).toBeInTheDocument()
  })

  it('renders metrics after fetch', async () => {
    render(<MonitoringPage />)
    await waitFor(() => {
      expect(screen.getByText('مراقبة النظام')).toBeInTheDocument()
    })
    expect(screen.getByText('1234')).toBeInTheDocument()
    expect(screen.getByText('12')).toBeInTheDocument()
    expect(screen.getByText('180ms')).toBeInTheDocument()
    expect(screen.getByText('256MB')).toBeInTheDocument()
  })

  it('shows connected database badge', async () => {
    render(<MonitoringPage />)
    await waitFor(() => {
      const badge = screen.getByTestId('badge')
      expect(badge).toHaveAttribute('data-variant', 'success')
      expect(badge).toHaveTextContent('متصل')
    })
  })

  it('shows disconnected badge when database is down', async () => {
    mockedApi.get.mockResolvedValue({
      data: { ...mockMetrics, system_health: { ...mockMetrics.system_health, database: 'disconnected' } },
    })
    render(<MonitoringPage />)
    await waitFor(() => {
      const badge = screen.getByTestId('badge')
      expect(badge).toHaveAttribute('data-variant', 'danger')
      expect(badge).toHaveTextContent('منفصل')
    })
  })

  it('renders recent errors', async () => {
    render(<MonitoringPage />)
    await waitFor(() => {
      expect(screen.getByText('Timeout error')).toBeInTheDocument()
      expect(screen.getByText('DB connection failed')).toBeInTheDocument()
    })
  })

  it('hides errors section when no recent errors', async () => {
    mockedApi.get.mockResolvedValue({
      data: { ...mockMetrics, errors: { ...mockMetrics.errors, recent: [] } },
    })
    render(<MonitoringPage />)
    await waitFor(() => {
      expect(screen.getByText('مراقبة النظام')).toBeInTheDocument()
    })
    expect(screen.queryByText('Timeout error')).not.toBeInTheDocument()
  })

  it('renders all system health services', async () => {
    render(<MonitoringPage />)
    await waitFor(() => {
      expect(screen.getByText('database')).toBeInTheDocument()
      expect(screen.getByText('redis')).toBeInTheDocument()
      expect(screen.getByText('neo4j')).toBeInTheDocument()
      expect(screen.getAllByText('connected').length).toBeGreaterThanOrEqual(2)
      expect(screen.getByText('disconnected')).toBeInTheDocument()
    })
  })

  it('sets up 30s polling interval', async () => {
    render(<MonitoringPage />)
    await waitFor(() => {
      expect(mockedApi.get).toHaveBeenCalledTimes(1)
    })
    act(() => {
      jest.advanceTimersByTime(30_000)
    })
    await waitFor(() => {
      expect(mockedApi.get).toHaveBeenCalledTimes(2)
    })
    act(() => {
      jest.advanceTimersByTime(30_000)
    })
    await waitFor(() => {
      expect(mockedApi.get).toHaveBeenCalledTimes(3)
    })
  })
})
