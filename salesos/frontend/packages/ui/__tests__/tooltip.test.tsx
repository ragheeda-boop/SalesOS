import { render, screen } from '@testing-library/react'
import { Tooltip } from '../src/tooltip'

describe('Tooltip', () => {
  it('renders children', () => {
    render(<Tooltip content="Tooltip text"><button>Hover me</button></Tooltip>)
    expect(screen.getByText('Hover me')).toBeInTheDocument()
  })
})
