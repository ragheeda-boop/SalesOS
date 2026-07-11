import { render, screen, fireEvent } from '@testing-library/react'
import { SearchInput } from '../components/SearchInput'

describe('SearchInput', () => {
  it('renders with placeholder', () => {
    render(<SearchInput value="" onChange={() => {}} onSearch={() => {}} placeholder="ابحث" />)
    expect(screen.getByRole('searchbox')).toHaveAttribute('placeholder', 'ابحث')
  })

  it('calls onChange when user types', () => {
    const onChange = jest.fn()
    render(<SearchInput value="" onChange={onChange} onSearch={() => {}} />)
    fireEvent.change(screen.getByRole('searchbox'), { target: { value: 'test' } })
    expect(onChange).toHaveBeenCalledWith('test')
  })

  it('calls onSearch on Enter', () => {
    const onSearch = jest.fn()
    render(<SearchInput value="test" onChange={() => {}} onSearch={onSearch} />)
    fireEvent.keyDown(screen.getByRole('searchbox'), { key: 'Enter' })
    expect(onSearch).toHaveBeenCalledWith('test')
  })

  it('shows clear button when value exists', () => {
    render(<SearchInput value="test" onChange={() => {}} onSearch={() => {}} />)
    expect(screen.getByLabelText('مسح البحث')).toBeInTheDocument()
  })

  it('calls onChange with empty on clear', () => {
    const onChange = jest.fn()
    render(<SearchInput value="test" onChange={onChange} onSearch={() => {}} />)
    fireEvent.click(screen.getByLabelText('مسح البحث'))
    expect(onChange).toHaveBeenCalledWith('')
  })

  it('does not show clear button when value is empty', () => {
    render(<SearchInput value="" onChange={() => {}} onSearch={() => {}} />)
    expect(screen.queryByLabelText('مسح البحث')).not.toBeInTheDocument()
  })

  it('calls onChange on Escape', () => {
    const onChange = jest.fn()
    render(<SearchInput value="test" onChange={onChange} onSearch={() => {}} />)
    fireEvent.keyDown(screen.getByRole('searchbox'), { key: 'Escape' })
    expect(onChange).toHaveBeenCalledWith('')
  })

  it('has role="searchbox"', () => {
    render(<SearchInput value="" onChange={() => {}} onSearch={() => {}} />)
    expect(screen.getByRole('searchbox')).toBeInTheDocument()
  })
})
