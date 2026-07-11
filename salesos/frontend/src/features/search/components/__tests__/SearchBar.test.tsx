import { render, screen, fireEvent } from '@testing-library/react'
import { SearchBar } from '../SearchBar'

describe('SearchBar', () => {
  it('renders input with placeholder', () => {
    render(<SearchBar value="" onChange={jest.fn()} onSubmit={jest.fn()} />)
    expect(screen.getByPlaceholderText('Search...')).toBeInTheDocument()
  })

  it('calls onChange when typing', () => {
    const onChange = jest.fn()
    render(<SearchBar value="" onChange={onChange} onSubmit={jest.fn()} />)
    fireEvent.change(screen.getByRole('textbox'), { target: { value: 'test' } })
    expect(onChange).toHaveBeenCalledWith('test')
  })

  it('calls onSubmit on Enter', () => {
    const onSubmit = jest.fn()
    render(<SearchBar value="test" onChange={jest.fn()} onSubmit={onSubmit} />)
    fireEvent.keyDown(screen.getByRole('textbox'), { key: 'Enter' })
    expect(onSubmit).toHaveBeenCalledWith('test')
  })
})
