import { render, screen, fireEvent } from '@testing-library/react'
import { QuickOverlay } from '../QuickOverlay'

describe('QuickOverlay', () => {
  it('renders when open', () => {
    render(<QuickOverlay open={true} onClose={jest.fn()} />)
    expect(screen.getByRole('dialog')).toBeInTheDocument()
  })

  it('does not render when closed', () => {
    render(<QuickOverlay open={false} onClose={jest.fn()} />)
    expect(screen.queryByRole('dialog')).not.toBeInTheDocument()
  })

  it('calls onClose on Escape', () => {
    const onClose = jest.fn()
    render(<QuickOverlay open={true} onClose={onClose} />)
    fireEvent.keyDown(document, { key: 'Escape' })
    expect(onClose).toHaveBeenCalled()
  })
})
