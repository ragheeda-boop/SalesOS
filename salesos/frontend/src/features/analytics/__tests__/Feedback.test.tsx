import { render, screen, fireEvent } from '@testing-library/react'
import { FeedbackWidget } from '../FeedbackWidget'

describe('FeedbackWidget', () => {
  it('renders feedback button', () => {
    render(<FeedbackWidget />)
    expect(screen.getByText('تقييم سريع')).toBeInTheDocument()
  })

  it('opens feedback form on click', () => {
    render(<FeedbackWidget />)
    fireEvent.click(screen.getByText('تقييم سريع'))
    expect(screen.getByText(/ما رأيك في SalesOS/)).toBeInTheDocument()
  })

  it('shows NPS options', () => {
    render(<FeedbackWidget />)
    fireEvent.click(screen.getByText('تقييم سريع'))
    expect(screen.getByText('0')).toBeInTheDocument()
    expect(screen.getByText('10')).toBeInTheDocument()
  })

  it('submits feedback and shows thank you', () => {
    render(<FeedbackWidget />)
    fireEvent.click(screen.getByText('تقييم سريع'))
    fireEvent.click(screen.getByText('9'))
    fireEvent.click(screen.getByText('إرسال'))
    expect(screen.getByText('شكرًا لتقييمك!')).toBeInTheDocument()
  })
})
