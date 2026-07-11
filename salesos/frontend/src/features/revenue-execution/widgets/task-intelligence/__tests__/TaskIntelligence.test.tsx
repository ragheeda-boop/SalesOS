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

describe('TaskView interactions', () => {
  it('calls onComplete when clicking circle button', () => {
    const onComplete = jest.fn()
    render(<TaskView tasks={sample} onComplete={onComplete} />)
    const circles = screen.getAllByRole('button')
    fireEvent.click(circles[0])
    expect(onComplete).toHaveBeenCalledWith('t1')
  })

  it('switches to completed filter showing no tasks', () => {
    renderView()
    fireEvent.click(screen.getByText('مكتملة'))
    expect(screen.getByText('لا توجد مهام')).toBeInTheDocument()
  })

  it('switches to all filter showing all tasks', () => {
    renderView()
    fireEvent.click(screen.getByText('الكل'))
    expect(screen.getByText('متابعة شركة الطاقة')).toBeInTheDocument()
    expect(screen.getByText('تجهيز عرض STC')).toBeInTheDocument()
  })

  it('switches back to active filter after viewing all', () => {
    renderView()
    fireEvent.click(screen.getByText('الكل'))
    fireEvent.click(screen.getByText('نشطة'))
    expect(screen.getByText('2 نشطة')).toBeInTheDocument()
  })

  it('shows active count reflecting completed tasks', () => {
    const withCompleted: RevenueTask[] = [
      ...sample,
      { id: 't3', title: 'مهمة مكتملة', priority: 'medium', source: 'manual', completed: true, createdAt: '2026-07-10' },
    ]
    render(<TaskView tasks={withCompleted} />)
    expect(screen.getByText('2 نشطة')).toBeInTheDocument()
  })

  it('renders AI source icon for nba-sourced tasks', () => {
    renderView(); expect(screen.getAllByText('AI').length).toBeGreaterThanOrEqual(1)
  })

  it('renders due date when present', () => {
    renderView(); expect(document.body.textContent).toContain('١٤')
  })
})
describe('TaskIntelligenceWidget', () => { it('is a valid widget', () => { expect(TaskIntelligenceWidget).toBeDefined() }) })
