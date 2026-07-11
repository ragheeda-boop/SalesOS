import { render, screen, fireEvent } from '@testing-library/react'
import { CommandBarInput } from '../CommandBarInput'

describe('CommandBarInput', () => {
  it('renders input with searchbox role', () => {
    render(<CommandBarInput value="" onChange={jest.fn()} onSearch={jest.fn()} onKeyDown={jest.fn()} inputRef={{ current: null }} />)
    expect(screen.getByRole('searchbox')).toBeInTheDocument()
  })

  it('calls onChange', () => {
    const onChange = jest.fn()
    render(<CommandBarInput value="" onChange={onChange} onSearch={jest.fn()} onKeyDown={jest.fn()} inputRef={{ current: null }} />)
    fireEvent.change(screen.getByRole('searchbox'), { target: { value: 'x' } })
    expect(onChange).toHaveBeenCalledWith('x')
  })
})
