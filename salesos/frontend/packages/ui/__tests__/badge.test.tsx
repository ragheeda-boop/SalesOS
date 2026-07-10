import { render, screen, fireEvent } from '@testing-library/react'
import { Badge } from '../src/badge'

describe('Badge (UI Kit)', () => {
  it('renders children', () => {
    render(<Badge>New</Badge>)
    expect(screen.getByText('New')).toBeInTheDocument()
  })

  it('renders with variant', () => {
    const { container } = render(<Badge variant="success">Success</Badge>)
    expect(container.firstChild).toBeInTheDocument()
  })
})
