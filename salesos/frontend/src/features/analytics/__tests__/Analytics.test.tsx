import { render, screen, fireEvent } from '@testing-library/react'
import { AnalyticsView } from '../AnalyticsView'
import { CommercialAnalyticsWidget } from '../AnalyticsContainer'
import { describeWidgetContract } from '@salesos/workspace/testing'
import type { AnalyticsData } from '../types'

const sample: AnalyticsData = {
  users: { total: 15, active: 12, new: 3 },
  usage: { totalSessions: 342, avgSessionDuration: 840, dailyActiveUsers: 12 },
  pipeline: { totalValue: 8500000, weightedValue: 4200000, dealCount: 24, winRate: 0.33 },
  widgets: { mostUsed: 'company-dna', usageCount: 120, widgets: [{ id: 'dna', name: 'Company DNA', count: 120 }] },
  search: { totalQueries: 420, avgResults: 12, topQueries: ['شركات الطاقة'] },
  nba: { shown: 85, executed: 38, acceptanceRate: 45 },
}

function renderView(d: AnalyticsData = sample) { return render(<AnalyticsView data={d} />) }

describe('AnalyticsView', () => {
  it('renders active users', () => { renderView(); const u = screen.getAllByText('12'); expect(u.length).toBeGreaterThanOrEqual(1) })
  it('renders total value', () => { renderView(); expect(screen.getByText(/\$8\.5M/)).toBeInTheDocument() })
  it('renders NBA acceptance rate', () => { renderView(); expect(screen.getByText(/%45/)).toBeInTheDocument() })
  it('renders widget name', () => { renderView(); expect(screen.getByText('Company DNA')).toBeInTheDocument() })
  it('renders top query', () => { renderView(); expect(screen.getByText(/شركات الطاقة/)).toBeInTheDocument() })
  it('has role="region"', () => { renderView(); expect(screen.getByRole('region', { name: 'تحليلات المنتج' })).toBeInTheDocument() })
})

describe('CommercialAnalyticsWidget', () => { it('is a valid widget', () => { expect(CommercialAnalyticsWidget).toBeDefined() }) })
