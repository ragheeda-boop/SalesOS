import { render, screen } from '@testing-library/react'
import { EmailView } from '../EmailView'
import { EmailIntelligenceWidget } from '../EmailContainer'
import { describeWidgetContract } from '@salesos/workspace/testing'
import type { EmailSummary } from '@/application/revenue-execution/email.dto'

const sample: EmailSummary[] = [
  { threadId: 'e1', subject: 'متابعة العرض', summary: 'طلب معلومات إضافية', sender: 'أحمد', date: '2026-07-10', priority: 'high', suggestedReply: 'شكراً للتواصل', actionItems: ['ترتيب عرض'] },
]

function renderView(e = sample) { return render(<EmailView emails={e} />) }

describeWidgetContract({
  name: 'EmailIntelligence', defaultData: sample,
  config: { metadata: { id: 'emailIntelligence', title: 'ذكاء البريد', permissions: ['email:read'], featureFlag: { enabled: true } }, render: ({ data }) => <EmailView emails={data} /> },
})

describe('EmailView', () => {
  it('renders subject', () => { renderView(); expect(screen.getByText('متابعة العرض')).toBeInTheDocument() })
  it('renders summary', () => { renderView(); expect(screen.getByText('طلب معلومات إضافية')).toBeInTheDocument() })
  it('renders suggested reply', () => { renderView(); expect(screen.getByText('شكراً للتواصل')).toBeInTheDocument() })
  it('renders action items', () => { renderView(); expect(screen.getByText('ترتيب عرض')).toBeInTheDocument() })
  it('shows empty state', () => { renderView([]); expect(screen.getByText('لا توجد رسائل بريد')).toBeInTheDocument() })
  it('has role="region"', () => { renderView(); expect(screen.getByRole('region', { name: 'ذكاء البريد' })).toBeInTheDocument() })
})
describe('EmailIntelligenceWidget', () => { it('is a valid widget', () => { expect(EmailIntelligenceWidget).toBeDefined() }) })
