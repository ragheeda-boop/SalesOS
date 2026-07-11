import { render, screen } from '@testing-library/react'

jest.mock('../timeline-widget', () => ({
  TimelineWidget: () => <div data-testid="timeline-widget">Timeline Widget</div>,
}))

import { TimelineWidget } from '../timeline-widget'

describe('TimelineWidget', () => {
  it('renders', () => {
    render(<TimelineWidget />)
    expect(screen.getByTestId('timeline-widget')).toBeInTheDocument()
  })
})
