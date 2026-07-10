import { render, screen } from '@testing-library/react'
import { Stack } from '../stack'

describe('Stack', () => {
  it('renders children', () => {
    render(<Stack><span>Item</span></Stack>)
    expect(screen.getByText('Item')).toBeInTheDocument()
  })

  it('defaults to row direction', () => {
    const { container } = render(<Stack><span>A</span><span>B</span></Stack>)
    expect(container.firstChild).toHaveClass('flex', 'flex-row')
  })

  it('applies column direction', () => {
    const { container } = render(<Stack direction="column"><span>A</span></Stack>)
    expect(container.firstChild).toHaveClass('flex-col')
  })

  it('applies gap', () => {
    const { container } = render(<Stack gap={4}><span>A</span></Stack>)
    expect(container.firstChild).toHaveClass('gap-4')
  })

  it('applies align', () => {
    const { container } = render(<Stack align="center"><span>A</span></Stack>)
    expect(container.firstChild).toHaveClass('items-center')
  })

  it('applies justify', () => {
    const { container } = render(<Stack justify="between"><span>A</span></Stack>)
    expect(container.firstChild).toHaveClass('justify-between')
  })

  it('renders as custom element', () => {
    const { container } = render(<Stack as="nav"><span>A</span></Stack>)
    expect(container.querySelector('nav')).toBeInTheDocument()
  })
})
