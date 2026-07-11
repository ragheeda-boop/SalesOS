import { render, screen } from '@testing-library/react'
import { AIAnswer } from '../AIAnswer'

describe('AIAnswer', () => {
  it('renders answer text', () => {
    render(<AIAnswer answer="This is the AI answer" />)
    expect(screen.getByText('This is the AI answer')).toBeInTheDocument()
  })

  it('renders with confidence', () => {
    render(<AIAnswer answer="Answer" confidence={0.85} />)
    expect(screen.getByText('Answer')).toBeInTheDocument()
  })
})
