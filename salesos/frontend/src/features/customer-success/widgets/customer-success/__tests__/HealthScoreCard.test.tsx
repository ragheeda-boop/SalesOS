import { render, screen } from '@testing-library/react'
import { HealthScoreCard } from '../HealthScoreCard'

const defaultProps = { score: 85, label: 'متوسط التبني', thresholds: { green: 80, yellow: 50 } }

function renderView(overrides?: Partial<Parameters<typeof HealthScoreCard>[0]>) {
  return render(<HealthScoreCard {...defaultProps} {...overrides} />)
}

describe('HealthScoreCard', () => {
  it('renders label', () => {
    renderView()
    expect(screen.getByText('متوسط التبني')).toBeInTheDocument()
  })

  it('renders score as percentage', () => {
    renderView()
    expect(screen.getByText('85%')).toBeInTheDocument()
  })

  it('shows جيد when score >= green threshold', () => {
    renderView()
    expect(screen.getByText('جيد')).toBeInTheDocument()
  })

  it('shows بحاجة للتحسين when score is yellow range', () => {
    renderView({ score: 65 })
    expect(screen.getByText('بحاجة للتحسين')).toBeInTheDocument()
  })

  it('shows حرج when score is below yellow threshold', () => {
    renderView({ score: 30 })
    expect(screen.getByText('حرج')).toBeInTheDocument()
  })

  it('formats score with toFixed(0)', () => {
    renderView({ score: 75.3 })
    expect(screen.getByText('75%')).toBeInTheDocument()
  })

  it('has green icon for high scores', () => {
    renderView()
    expect(screen.getByText('جيد')).toBeInTheDocument()
  })
})
