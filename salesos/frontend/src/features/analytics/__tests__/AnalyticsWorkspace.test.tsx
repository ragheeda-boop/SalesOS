import { render, screen } from '@testing-library/react'
import { AnalyticsWorkspace } from '../AnalyticsWorkspace'

jest.mock('@/lib/i18n', () => ({
  useTranslation: () => ({
    t: (key: string) => {
      const map: Record<string, string> = {
        'analytics.title': 'Analytics',
        'analytics.subtitle': 'Key performance indicators and advanced analytics dashboards',
        'analytics.revenue': 'Revenue',
        'analytics.pipeline': 'Pipeline',
        'analytics.conversion': 'Conversion Rate',
        'analytics.forecast_accuracy': 'Forecast Accuracy',
        'analytics.revenue_trend': 'Revenue Trend',
        'analytics.pipeline_stages': 'Pipeline Stages',
        'analytics.forecast_vs_actual': 'Forecast vs Actual',
        'analytics.export_csv': 'Export CSV',
        'analytics.export_pdf': 'Export PDF',
      }
      return map[key] || key
    },
    dir: 'ltr',
  }),
}))

describe('AnalyticsWorkspace', () => {
  it('renders title', () => {
    render(<AnalyticsWorkspace />)
    expect(screen.getByText('Analytics')).toBeInTheDocument()
  })

  it('renders KPI cards', () => {
    render(<AnalyticsWorkspace />)
    expect(screen.getByText('$12.5M')).toBeInTheDocument()
    expect(screen.getByText('$42.0M')).toBeInTheDocument()
    expect(screen.getByText('33%')).toBeInTheDocument()
    expect(screen.getByText('87%')).toBeInTheDocument()
  })

  it('renders export buttons', () => {
    render(<AnalyticsWorkspace />)
    expect(screen.getByText('Export CSV')).toBeInTheDocument()
    expect(screen.getByText('Export PDF')).toBeInTheDocument()
  })

  it('renders chart sections', () => {
    render(<AnalyticsWorkspace />)
    expect(screen.getByText('Revenue Trend')).toBeInTheDocument()
    expect(screen.getByText('Pipeline Stages')).toBeInTheDocument()
    expect(screen.getByText('Forecast vs Actual')).toBeInTheDocument()
  })

  it('has accessible region', () => {
    render(<AnalyticsWorkspace />)
    expect(screen.getByRole('region', { name: 'Analytics' })).toBeInTheDocument()
  })
})
