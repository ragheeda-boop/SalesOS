import { render, screen } from '@testing-library/react'
import { Metric } from '../metric'

describe('Metric', () => {
  it('renders label and value', () => {
    render(<Metric label="Revenue" value="$1M" />)
    expect(screen.getByText('Revenue')).toBeInTheDocument()
    expect(screen.getByText('$1M')).toBeInTheDocument()
  })

  it('renders trend indicator', () => {
    render(<Metric label="Growth" value="12%" trend="up" trendValue="+2%" />)
    expect(screen.getByText('+2%')).toBeInTheDocument()
  })

  it('has sr-only trend label for accessibility', () => {
    const { container } = render(<Metric label="Test" value="5" trend="down" />)
    const srOnly = container.querySelector('.sr-only')
    expect(srOnly).toHaveTextContent('Decreased')
  })

  it('renders loading skeleton with aria-busy', () => {
    const { container } = render(<Metric label="Revenue" value="$1M" loading />)
    expect(container.firstChild).toHaveAttribute('aria-busy', 'true')
    expect(container.firstChild).toHaveAttribute('role', 'status')
  })

  it('applies brand color', () => {
    const { container } = render(<Metric label="Revenue" value="$1M" color="brand" />)
    expect(container.querySelector('.text-\\[var\\(--muhide-orange\\)\\]')).toBeInTheDocument()
  })
})
