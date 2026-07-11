import { render, screen, fireEvent } from '@testing-library/react'
import { RelationshipGraphView } from '../RelationshipGraphView'
import { RelationshipGraphWidget } from '../RelationshipGraphContainer'
import { describeWidgetContract } from '@salesos/workspace/testing'
import type { RelationshipNode, RelationshipEdge } from '@/application/company-intelligence/company-intelligence.dto'

const nodes: RelationshipNode[] = [
  { id: 'n1', type: 'person', label: 'د. أحمد السلمي', strength: 0.9 },
  { id: 'n2', type: 'company', label: 'أرامكو', strength: 0.8 },
  { id: 'n3', type: 'person', label: 'نورة القحطاني', strength: 0.7 },
]
const edges: RelationshipEdge[] = [
  { source: 'n1', target: 'n2', type: 'works_at', label: 'يعمل في', direction: 'outbound' },
  { source: 'n2', target: 'n3', type: 'partner', label: 'شريك', direction: 'bidirectional' },
]

function renderView(n = nodes, e = edges) {
  return render(<RelationshipGraphView nodes={n} edges={e} />)
}

describeWidgetContract({
  name: 'RelationshipGraph', defaultData: { nodes, edges },
  config: {
    metadata: { id: 'relationshipGraph', title: 'العلاقات', permissions: ['company:graph:read'], featureFlag: { enabled: true } },
    render: ({ data }) => <RelationshipGraphView nodes={data.nodes} edges={data.edges} />,
  },
})

describe('RelationshipGraphView', () => {
  it('renders nodes', () => {
    renderView()
    expect(screen.getByText('د. أحمد السلمي')).toBeInTheDocument()
    expect(screen.getByText('أرامكو')).toBeInTheDocument()
  })

  it('shows edges on node click', () => {
    renderView()
    fireEvent.click(screen.getByText('د. أحمد السلمي'))
    expect(screen.getByText('يعمل في')).toBeInTheDocument()
  })

  it('shows empty state', () => {
    renderView([], [])
    expect(screen.getByText('لا توجد علاقات')).toBeInTheDocument()
  })

  it('has role="region"', () => {
    renderView()
    expect(screen.getByRole('region', { name: 'العلاقات' })).toBeInTheDocument()
  })
})

describe('RelationshipGraphWidget', () => {
  it('is a valid widget component', () => {
    expect(RelationshipGraphWidget).toBeDefined()
  })
})
