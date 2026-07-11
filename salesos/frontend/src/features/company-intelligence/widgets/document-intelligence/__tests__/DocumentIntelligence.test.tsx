import { render, screen } from '@testing-library/react'
import { DocumentIntelligenceView } from '../DocumentIntelligenceView'
import { DocumentIntelligenceWidget } from '../DocumentIntelligenceContainer'
import { describeWidgetContract } from '@salesos/workspace/testing'
import type { DocumentItem } from '@/application/company-intelligence/company-intelligence.dto'

const sample: DocumentItem[] = [
  { id: 'd1', title: 'عقد توريد 2026', type: 'contract', date: '2026-07-01', aiSummary: 'عقد توريد مواد بـ 2 مليون ريال', confidence: 0.92 },
  { id: 'd2', title: 'تقرير الأداء الربعي', type: 'report', date: '2026-06-15', confidence: 0.85 },
]

function renderView(docs = sample) {
  return render(<DocumentIntelligenceView documents={docs} />)
}

describeWidgetContract({
  name: 'DocumentIntelligence', defaultData: sample,
  config: {
    metadata: { id: 'documentIntelligence', title: 'المستندات', permissions: ['company:documents:read'], featureFlag: { enabled: true } },
    render: ({ data }) => <DocumentIntelligenceView documents={data} />,
  },
})

describe('DocumentIntelligenceView', () => {
  it('renders document titles', () => {
    renderView()
    expect(screen.getByText('عقد توريد 2026')).toBeInTheDocument()
    expect(screen.getByText('تقرير الأداء الربعي')).toBeInTheDocument()
  })

  it('renders AI summary', () => {
    renderView()
    expect(screen.getByText(/عقد توريد مواد/)).toBeInTheDocument()
  })

  it('shows empty state', () => {
    renderView([])
    expect(screen.getByText('لا توجد مستندات')).toBeInTheDocument()
  })

  it('has role="region"', () => {
    renderView()
    expect(screen.getByRole('region', { name: 'المستندات' })).toBeInTheDocument()
  })
})

describe('DocumentIntelligenceWidget', () => {
  it('is a valid widget component', () => {
    expect(DocumentIntelligenceWidget).toBeDefined()
  })
})
