import { render, screen, fireEvent } from '@testing-library/react'
import { Select } from '../src/select'

describe('Select', () => {
  const options = [
    { label: 'Option 1', value: '1' },
    { label: 'Option 2', value: '2' },
  ]

  it('renders trigger with placeholder', () => {
    render(<Select options={options} placeholder="Choose..." />)
    expect(screen.getByText('Choose...')).toBeInTheDocument()
  })

  it('applies error styling', () => {
    const { container } = render(<Select options={options} error="Required" />)
    expect(container.querySelector('.border-danger-500')).toBeInTheDocument()
  })

  it('renders error message', () => {
    render(<Select options={options} error="Required" />)
    expect(screen.getByText('Required')).toBeInTheDocument()
  })
})
