import { render, screen, fireEvent } from '@testing-library/react'
import { TaskView } from '../TaskView'
import { TaskIntelligenceWidget } from '../TaskContainer'
import { describeWidgetContract } from '@salesos/workspace/testing'
import type { RevenueTask } from '@/application/revenue-execution/task.dto'

const sample: RevenueTask[] = [
  { id: 't1', title: 'متابعة شركة الطاقة', priority: 'critical', source: 'nba', companyName: 'شركة الطاقة', dueDate: '2026-07-15', completed: false, createdAt: '2026-07-10' },
  { id: 't2', title: 'تجهيز عرض STC', priority: 'high', source: 'meeting', companyName: 'STC', completed: false, createdAt: '2026-07-09' },
]

function renderView(t: RevenueTask[] = sample) { return render(<TaskView tasks={t} />) }

describeWidgetContract({
  name: 'TaskIntelligence', defaultData: sample,
  config: { metadata: { id: 'taskIntelligence', title: 'المهام', permissions: ['task:read'], featureFlag: { enabled: true } }, render: ({ data }) => <TaskView tasks={data} /> },
})

describe('TaskView', () => {
  it('renders task titles', () => {
    renderView(); expect(screen.getByText('متابعة شركة الطاقة')).toBeInTheDocument()
    expect(screen.getByText('تجهيز عرض STC')).toBeInTheDocument()
  })
  it('renders priority labels', () => { renderView(); const p = screen.getAllByText('حرج'); expect(p.length).toBeGreaterThanOrEqual(1) })
  it('renders company names', () => { renderView(); const c = screen.getAllByText(/شركة الطاقة/); expect(c.length).toBeGreaterThanOrEqual(1) })
  it('shows active count', () => { renderView(); expect(screen.getByText('2 نشطة')).toBeInTheDocument() })
  it('shows filter buttons', () => { renderView(); expect(screen.getByText('نشطة')).toBeInTheDocument() })
  it('shows empty state', () => { renderView([]); expect(screen.getByText('لا توجد مهام')).toBeInTheDocument() })
  it('has role="region"', () => { renderView(); expect(screen.getByRole('region', { name: 'المهام' })).toBeInTheDocument() })
})
describe('TaskIntelligenceWidget', () => { it('is a valid widget', () => { expect(TaskIntelligenceWidget).toBeDefined() }) })
