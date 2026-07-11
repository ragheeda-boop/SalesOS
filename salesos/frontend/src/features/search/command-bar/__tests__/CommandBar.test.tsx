import { render, screen, fireEvent } from '@testing-library/react'
import { CommandBar } from '../CommandBar'

describe('CommandBar', () => {
  it('renders with placeholder', () => {
    render(<CommandBar />)
    expect(screen.getByPlaceholderText('Type a command...')).toBeInTheDocument()
  })

  it('calls onSearch when typing', () => {
    const onSearch = jest.fn()
    render(<CommandBar onSearch={onSearch} />)
    fireEvent.change(screen.getByRole('textbox'), { target: { value: 'test' } })
    expect(onSearch).toHaveBeenCalledWith('test')
  })
})
