import { render, screen } from '@testing-library/react'
import { AIAnswerCard } from '../AIAnswer'

describe('AIAnswerCard', () => {
  it('renders answer summary', () => {
    const answer = { summary: 'AI response', confidence: 0.85, explanation: '', recommendations: [], risks: [], sources: [] }
    render(<AIAnswerCard answer={answer as any} />)
    expect(screen.getByText('AI response')).toBeInTheDocument()
  })

  it('shows confidence percentage', () => {
    const answer = { summary: 'Test', confidence: 0.85, explanation: '', recommendations: [], risks: [], sources: [] }
    render(<AIAnswerCard answer={answer as any} />)
    expect(screen.getByText('%85 ثقة')).toBeInTheDocument()
  })
})
