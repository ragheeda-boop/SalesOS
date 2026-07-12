import { render, screen } from '@testing-library/react'
import { ActivityIntelligenceView } from '../ActivityIntelligenceWidget'
import type { ActivityIntelligence } from '@/lib/api'

const baseData: ActivityIntelligence = {
  meetings: 8,
  emails: 45,
  calls: 12,
  tasks: 6,
  notes: 3,
  documents: 5,
  total: 79,
  recent: [
    { id: 'a1', description: 'Call with Acme Corp', action: 'call', timestamp: new Date().toISOString() },
    { id: 'a2', description: 'Email to Ahmed', action: 'email', timestamp: new Date().toISOString() },
  ],
}

describe('ActivityIntelligenceView', () => {
  it('renders meeting count', () => {
    render(<ActivityIntelligenceView data={baseData} />)
    expect(screen.getByText('8')).toBeInTheDocument()
  })

  it('renders total activities', () => {
    render(<ActivityIntelligenceView data={baseData} />)
    expect(screen.getByText('79')).toBeInTheDocument()
  })

  it('renders recent activities', () => {
    render(<ActivityIntelligenceView data={baseData} />)
    expect(screen.getByText('Call with Acme Corp')).toBeInTheDocument()
    expect(screen.getByText('Email to Ahmed')).toBeInTheDocument()
  })

  it('renders empty state when no activities', () => {
    const empty: ActivityIntelligence = { meetings: 0, emails: 0, calls: 0, tasks: 0, notes: 0, documents: 0, total: 0, recent: [] }
    render(<ActivityIntelligenceView data={empty} />)
    expect(screen.getByText('لا توجد نشاطات حديثة')).toBeInTheDocument()
  })
})
