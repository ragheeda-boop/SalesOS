import { render, screen, fireEvent } from '@testing-library/react'
import { DatePicker } from '../src/date-picker'

describe('DatePicker', () => {
  it('renders with label', () => {
    render(<DatePicker label="Start date" />)
    expect(screen.getByText('Start date')).toBeInTheDocument()
  })

  it('shows placeholder when no value', () => {
    render(<DatePicker placeholder="Pick a date" />)
    expect(screen.getByText('Pick a date')).toBeInTheDocument()
  })

  it('opens calendar on click', () => {
    render(<DatePicker />)
    fireEvent.click(screen.getByRole('button'))
    expect(screen.getByRole('dialog')).toBeInTheDocument()
  })

  it('shows error state', () => {
    render(<DatePicker error="Invalid date" />)
    expect(screen.getByText('Invalid date')).toBeInTheDocument()
  })

  it('disables when disabled prop is true', () => {
    render(<DatePicker disabled />)
    expect(screen.getByRole('button')).toBeDisabled()
  })

  it('displays selected date', () => {
    render(<DatePicker value={new Date(2026, 6, 15)} />)
    expect(screen.getByText(/Jul 15, 2026|15 Jul 2026/)).toBeInTheDocument()
  })
})
