import { render, screen } from '@testing-library/react'
import { MeetingView } from '../MeetingView'
import { MeetingIntelligenceWidget } from '../MeetingContainer'
import { describeWidgetContract } from '@salesos/workspace/testing'
import type { MeetingBrief } from '@/application/revenue-execution/meeting.dto'

const sample: MeetingBrief = {
  companyName: 'شركة الطاقة', meetingTitle: 'اجتماع المتابعة', date: '2026-07-15',
  attendees: [{ name: 'د. أحمد', role: 'CEO', influence: 'عالي' }],
  recentSignals: ['توظيف كبير'], risks: ['مخاطر'], opportunities: ['فرصة'],
  talkingPoints: ['نقطة نقاش 1'], recommendedAction: 'تقديم عرض',
}
function renderView(b: MeetingBrief | null = sample) { return render(<MeetingView brief={b} />) }

describeWidgetContract({
  name: 'MeetingIntelligence', defaultData: sample,
  config: { metadata: { id: 'meetingIntelligence', title: 'ذكاء الاجتماعات', permissions: ['meeting:read'], featureFlag: { enabled: true } }, render: ({ data }) => <MeetingView brief={data} /> },
})

describe('MeetingView', () => {
  it('renders meeting title', () => { renderView(); expect(screen.getByText('اجتماع المتابعة')).toBeInTheDocument() })
  it('renders company name', () => { renderView(); expect(screen.getByText(/شركة الطاقة/)).toBeInTheDocument() })
  it('renders attendees', () => { renderView(); expect(screen.getByText(/د. أحمد/)).toBeInTheDocument() })
  it('renders signals', () => { renderView(); expect(screen.getByText(/توظيف كبير/)).toBeInTheDocument() })
  it('renders risks section', () => { renderView(); expect(screen.getByText(/المخاطر/)).toBeInTheDocument() })
  it('renders talking points', () => { renderView(); expect(screen.getByText('نقطة نقاش 1')).toBeInTheDocument() })
  it('renders recommended action', () => { renderView(); expect(screen.getByText('تقديم عرض')).toBeInTheDocument() })
  it('shows empty state', () => { renderView(null); expect(screen.getByText('لا يوجد إيجاز اجتماع')).toBeInTheDocument() })
  it('has role="region"', () => { renderView(); expect(screen.getByRole('region', { name: 'ذكاء الاجتماعات' })).toBeInTheDocument() })
})
describe('MeetingIntelligenceWidget', () => { it('is a valid widget', () => { expect(MeetingIntelligenceWidget).toBeDefined() }) })
