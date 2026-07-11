import { render, screen, fireEvent } from '@testing-library/react'
import { SearchHistory } from '../components/SearchHistory'
import type { SearchHistoryEntry } from '@salesos/search'

const entries: SearchHistoryEntry[] = [
  { id: '1', text: 'شركات الطاقة', timestamp: Date.now() - 1000, resultCount: 15 },
  { id: '2', text: 'مستشفيات الرياض', timestamp: Date.now() - 2000 },
]

describe('SearchHistory', () => {
  it('renders entries', () => {
    render(<SearchHistory entries={entries} onClick={() => {}} />)
    expect(screen.getByText('شركات الطاقة')).toBeInTheDocument()
    expect(screen.getByText('مستشفيات الرياض')).toBeInTheDocument()
  })

  it('shows result count when available', () => {
    render(<SearchHistory entries={entries} onClick={() => {}} />)
    expect(screen.getByText('15 نتيجة')).toBeInTheDocument()
  })

  it('calls onClick when entry clicked', () => {
    const onClick = jest.fn()
    render(<SearchHistory entries={entries} onClick={onClick} />)
    fireEvent.click(screen.getByText('شركات الطاقة'))
    expect(onClick).toHaveBeenCalledWith(entries[0])
  })

  it('calls onClear when clear clicked', () => {
    const onClear = jest.fn()
    render(<SearchHistory entries={entries} onClick={() => {}} onClear={onClear} />)
    fireEvent.click(screen.getByLabelText('مسح سجل البحث'))
    expect(onClear).toHaveBeenCalled()
  })

  it('returns null for empty entries', () => {
    const { container } = render(<SearchHistory entries={[]} onClick={() => {}} />)
    expect(container.innerHTML).toBe('')
  })
})
