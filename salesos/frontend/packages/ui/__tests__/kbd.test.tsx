import { render, screen } from '@testing-library/react'
import { Kbd } from '../src/kbd'

describe('Kbd', () => {
  it('renders children', () => {
    render(<Kbd>Ctrl+K</Kbd>)
    expect(screen.getByText('Ctrl+K')).toBeInTheDocument()
  })

  it('renders as kbd element', () => {
    const { container } = render(<Kbd>Esc</Kbd>)
    expect(container.querySelector('kbd')).toBeInTheDocument()
  })
})
