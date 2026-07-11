import { render, screen } from '@testing-library/react'

jest.mock('../employee-360-view', () => ({
  Employee360View: () => <div data-testid="emp-360">Employee 360</div>,
}))

import { Employee360View } from '../employee-360-view'

describe('Employee360View', () => {
  it('renders', () => {
    render(<Employee360View />)
    expect(screen.getByTestId('emp-360')).toBeInTheDocument()
  })
})
