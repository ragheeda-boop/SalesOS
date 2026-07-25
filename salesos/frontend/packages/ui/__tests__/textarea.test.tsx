import { render, screen, fireEvent } from '@testing-library/react'
import { Textarea } from '../src/textarea'

describe('Textarea', () => {
  it('renders with label', () => {
    render(<Textarea label="Description" />)
    expect(screen.getByText('Description')).toBeInTheDocument()
  })

  it('calls onChange on input', () => {
    const handleChange = jest.fn()
    render(<Textarea onChange={handleChange} />)
    fireEvent.change(screen.getByRole('textbox'), { target: { value: 'hello' } })
    expect(handleChange).toHaveBeenCalled()
  })

  it('shows error state', () => {
    render(<Textarea label="Bio" error errorMessage="Too long" />)
    expect(screen.getByText('Too long')).toBeInTheDocument()
    expect(screen.getByRole('textbox')).toHaveAttribute('aria-invalid', 'true')
  })

  it('shows character count with maxLength', () => {
    render(<Textarea value="Hi" maxLength={10} onChange={() => {}} />)
    expect(screen.getByText('2/10')).toBeInTheDocument()
  })

  it('disables when disabled prop is true', () => {
    render(<Textarea disabled />)
    expect(screen.getByRole('textbox')).toBeDisabled()
  })

  it('renders required indicator', () => {
    render(<Textarea label="Details" required />)
    expect(screen.getByText('*')).toBeInTheDocument()
  })
})
