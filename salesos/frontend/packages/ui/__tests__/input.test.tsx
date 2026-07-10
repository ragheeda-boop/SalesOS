import { render, screen, fireEvent } from '@testing-library/react'
import { Input } from '../src/input'

describe('Input', () => {
  it('renders input element', () => {
    render(<Input placeholder="Enter name" />)
    expect(screen.getByPlaceholderText('Enter name')).toBeInTheDocument()
  })

  it('renders label with htmlFor', () => {
    render(<Input label="Name" id="name" />)
    const label = screen.getByText('Name')
    expect(label).toBeInTheDocument()
    expect(label).toHaveAttribute('for', 'name')
  })

  it('renders error message', () => {
    render(<Input error="This field is required" />)
    expect(screen.getByText('This field is required')).toBeInTheDocument()
  })

  it('forwards ref', () => {
    const ref = jest.fn()
    render(<Input ref={ref} />)
    expect(ref).toHaveBeenCalled()
  })

  it('handles value changes', () => {
    const handleChange = jest.fn()
    render(<Input onChange={handleChange} />)
    fireEvent.change(screen.getByRole('textbox'), { target: { value: 'new' } })
    expect(handleChange).toHaveBeenCalled()
  })
})
