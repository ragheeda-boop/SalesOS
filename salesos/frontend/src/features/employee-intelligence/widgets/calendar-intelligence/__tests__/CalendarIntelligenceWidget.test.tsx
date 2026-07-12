import { render, screen } from '@testing-library/react'
import { CalendarIntelligenceView } from '../CalendarIntelligenceWidget'
import type { CalendarIntelligence } from '@/lib/api'

const baseData: CalendarIntelligence = {
  today_count: 3,
  week_count: 8,
  month_count: 20,
  total_hours: 12.5,
  avg_duration_minutes: 45,
  unique_companies_met: 5,
  upcoming: [
    { id: 'ev1', title: 'Review with CEO', start_time: new Date(Date.now() + 3600000).toISOString() },
    { id: 'ev2', title: 'Pipeline Review', start_time: new Date(Date.now() + 7200000).toISOString() },
  ],
}

describe('CalendarIntelligenceView', () => {
  it('renders today count', () => {
    render(<CalendarIntelligenceView data={baseData} />)
    expect(screen.getByText('3')).toBeInTheDocument()
  })

  it('renders week count', () => {
    render(<CalendarIntelligenceView data={baseData} />)
    expect(screen.getByText('8')).toBeInTheDocument()
  })

  it('renders month count', () => {
    render(<CalendarIntelligenceView data={baseData} />)
    expect(screen.getByText('20')).toBeInTheDocument()
  })

  it('renders total hours', () => {
    render(<CalendarIntelligenceView data={baseData} />)
    expect(screen.getByText(/ساعة/)).toBeInTheDocument()
  })

  it('renders unique companies met', () => {
    render(<CalendarIntelligenceView data={baseData} />)
    expect(screen.getByText('5')).toBeInTheDocument()
  })

  it('renders upcoming meetings', () => {
    render(<CalendarIntelligenceView data={baseData} />)
    expect(screen.getByText('Review with CEO')).toBeInTheDocument()
  })

  it('renders empty state', () => {
    const empty: CalendarIntelligence = { today_count: 0, week_count: 0, month_count: 0, total_hours: 0, avg_duration_minutes: 0, unique_companies_met: 0, upcoming: [] }
    render(<CalendarIntelligenceView data={empty} />)
    expect(screen.getByText('لا توجد اجتماعات مجدولة')).toBeInTheDocument()
  })
})
