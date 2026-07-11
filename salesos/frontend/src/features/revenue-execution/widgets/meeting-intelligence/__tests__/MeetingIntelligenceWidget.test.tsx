import { render, screen, fireEvent, waitFor } from '@testing-library/react'

jest.mock('axios', () => ({
  post: jest.fn().mockResolvedValue({
    data: {
      company_name: 'شركة', opportunity_name: 'صفقة', opportunity_stage: 'تفاوض', opportunity_value: 500000,
      recent_signals: ['توسع جديد'], key_contacts: ['أحمد'], talking_points: ['القيمة'], questions_to_ask: ['الميزانية'],
      ai_summary: 'ملخص ذكي',
    },
  }),
  get: jest.fn().mockResolvedValue({ data: [] }),
}))

import { MeetingIntelligenceWidget } from '../MeetingIntelligenceWidget'

describe('MeetingIntelligenceWidget', () => {
  it('renders brief tab by default', async () => {
    render(<MeetingIntelligenceWidget opportunityId="o-1" />)
    expect(await screen.findByText('تحضير الاجتماع')).toBeInTheDocument()
  })

  it('shows AI summary', async () => {
    render(<MeetingIntelligenceWidget opportunityId="o-1" />)
    expect(await screen.findByText('ملخص ذكي')).toBeInTheDocument()
  })

  it('shows company name', async () => {
    render(<MeetingIntelligenceWidget opportunityId="o-1" />)
    expect(await screen.findByText('شركة')).toBeInTheDocument()
  })

  it('switches to meetings tab', async () => {
    render(<MeetingIntelligenceWidget opportunityId="o-1" />)
    expect(await screen.findByText('تحضير الاجتماع')).toBeInTheDocument()

    fireEvent.click(screen.getByText('الاجتماعات السابقة'))
    expect(screen.getByText('لا توجد اجتماعات سابقة')).toBeInTheDocument()
  })
})
