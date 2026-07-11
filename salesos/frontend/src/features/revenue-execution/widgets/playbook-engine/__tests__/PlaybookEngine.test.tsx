import { render, screen } from '@testing-library/react'
import { PlaybookView } from '../PlaybookView'
import { PlaybookWidget } from '../PlaybookContainer'
import { describeWidgetContract } from '@salesos/workspace/testing'
import type { Playbook } from '@/application/revenue-execution/playbook.dto'

const sample: Playbook = {
  id: 'pb-test', name: 'دليل الاختبار', description: 'وصف', industry: 'test',
  estimatedDuration: 'أسبوعين', successRate: 75,
  steps: [
    { id: 's1', order: 1, title: 'الخطوة 1', description: 'الوصف', duration: 'يوم' },
    { id: 's2', order: 2, title: 'الخطوة 2', description: 'الوصف', duration: 'يومان' },
  ],
}

function renderView(p: Playbook | null = sample, ind = 'test') { return render(<PlaybookView playbook={p} industry={ind} />) }

describeWidgetContract({
  name: 'PlaybookEngine', defaultData: sample,
  config: {
    metadata: { id: 'playbookEngine', title: 'محرك اللعب', permissions: ['playbook:read'], featureFlag: { enabled: true } },
    render: ({ data }) => <PlaybookView playbook={data} industry="test" />,
  },
})

describe('PlaybookView', () => {
  it('renders playbook name', () => {
    renderView(); expect(screen.getByText('دليل الاختبار')).toBeInTheDocument()
  })
  it('renders step titles', () => {
    renderView(); expect(screen.getByText('الخطوة 1')).toBeInTheDocument()
    expect(screen.getByText('الخطوة 2')).toBeInTheDocument()
  })
  it('renders success rate', () => {
    renderView(); expect(screen.getByText(/%75/)).toBeInTheDocument()
  })
  it('shows empty state', () => {
    renderView(null, 'unknown')
    expect(screen.getByText('لا يوجد دليل لعب متاح')).toBeInTheDocument()
  })
  it('has role="region"', () => {
    renderView(); expect(screen.getByRole('region', { name: 'محرك اللعب' })).toBeInTheDocument()
  })
})

describe('PlaybookWidget', () => { it('is a valid widget component', () => { expect(PlaybookWidget).toBeDefined() }) })
