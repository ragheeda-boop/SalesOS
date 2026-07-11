import { render, screen, fireEvent } from '@testing-library/react'
import { CommandBarInput } from '../CommandBarInput'

describe('CommandBarInput', () => {
  it('renders input', () => {
    render(<CommandBarInput value="" onChange={jest.fn()} />)
    expect(screen.getByRole('textbox')).toBeInTheDocument()
  })

  it('calls onChange', () => {
    const onChange = jest.fn()
    render(<CommandBarInput value="" onChange={onChange} />)
    fireEvent.change(screen.getByRole('textbox'), { target: { value: 'x' } })
    expect(onChange).toHaveBeenCalledWith('x')
  })
})
