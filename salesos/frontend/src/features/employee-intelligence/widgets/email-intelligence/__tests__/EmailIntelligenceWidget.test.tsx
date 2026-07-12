import { render, screen } from '@testing-library/react'
import { EmailIntelligenceView } from '../EmailIntelligenceWidget'
import type { EmailIntelligence } from '@/lib/api'

const baseData: EmailIntelligence = {
  sent: 45,
  received: 120,
  replies: 30,
  avg_response_hours: 2.5,
  top_contacts: [
    { name: 'Ahmed Ali', email: 'ahmed@example.com', count: 15 },
    { name: 'Sara K.', email: 'sara@example.com', count: 8 },
  ],
  top_companies: [
    { name: 'Acme Corp', count: 25 },
    { name: 'Globex', count: 12 },
  ],
}

describe('EmailIntelligenceView', () => {
  it('renders sent count', () => {
    render(<EmailIntelligenceView data={baseData} />)
    expect(screen.getByText('45')).toBeInTheDocument()
  })

  it('renders received count', () => {
    render(<EmailIntelligenceView data={baseData} />)
    expect(screen.getByText('120')).toBeInTheDocument()
  })

  it('renders average response time', () => {
    render(<EmailIntelligenceView data={baseData} />)
    expect(screen.getByText(/ساعة/)).toBeInTheDocument()
  })

  it('renders top contacts', () => {
    render(<EmailIntelligenceView data={baseData} />)
    expect(screen.getByText('Ahmed Ali')).toBeInTheDocument()
  })

  it('renders top companies', () => {
    render(<EmailIntelligenceView data={baseData} />)
    expect(screen.getByText('Acme Corp')).toBeInTheDocument()
  })

  it('renders empty state when no data', () => {
    const empty: EmailIntelligence = { sent: 0, received: 0, replies: 0, avg_response_hours: 0, top_contacts: [], top_companies: [] }
    render(<EmailIntelligenceView data={empty} />)
    expect(screen.getByText('لا توجد بيانات بريد')).toBeInTheDocument()
  })
})
