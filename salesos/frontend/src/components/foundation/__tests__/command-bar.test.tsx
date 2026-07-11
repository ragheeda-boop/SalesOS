import { render, screen, fireEvent } from '@testing-library/react'
import { CommandBar } from '../command-bar'

const groups = [
  {
    id: 'nav',
    label: 'Navigation',
    items: [
      { id: 'go-home', label: 'Go Home', onSelect: jest.fn() },
      { id: 'go-settings', label: 'Go Settings', onSelect: jest.fn() },
    ],
  },
]

describe('CommandBar', () => {
  beforeEach(() => {
    jest.clearAllMocks()
  })

  it('does not render when closed', () => {
    render(<CommandBar open={false} onClose={jest.fn()} />)
    expect(screen.queryByRole('dialog')).not.toBeInTheDocument()
  })

  it('renders when open', () => {
    render(<CommandBar open={true} onClose={jest.fn()} />)
    expect(screen.getByRole('dialog')).toBeInTheDocument()
  })

  it('renders groups and items', () => {
    render(<CommandBar open={true} onClose={jest.fn()} groups={groups} />)
    expect(screen.getByText('Go Home')).toBeInTheDocument()
    expect(screen.getByText('Go Settings')).toBeInTheDocument()
    expect(screen.getByText('Navigation')).toBeInTheDocument()
  })

  it('calls onClose on Escape', () => {
    const onClose = jest.fn()
    render(<CommandBar open={true} onClose={onClose} groups={groups} />)

    fireEvent.keyDown(screen.getByRole('dialog'), { key: 'Escape' })
    expect(onClose).toHaveBeenCalled()
  })

  it('selects item on Enter', () => {
    const onClose = jest.fn()
    render(<CommandBar open={true} onClose={onClose} groups={groups} />)

    fireEvent.keyDown(screen.getByPlaceholderText(/Search commands/), { key: 'ArrowDown' })
    fireEvent.keyDown(screen.getByPlaceholderText(/Search commands/), { key: 'Enter' })

    expect(groups[0].items[0].onSelect).toHaveBeenCalled()
  })

  it('displays loading state', () => {
    render(<CommandBar open={true} onClose={jest.fn()} loading={true} />)
    expect(screen.getByText('Searching...')).toBeInTheDocument()
  })

  it('displays error state', () => {
    render(<CommandBar open={true} onClose={jest.fn()} error="Something went wrong" />)
    expect(screen.getByText('Something went wrong')).toBeInTheDocument()
  })

  it('displays empty message when no results', () => {
    render(<CommandBar open={true} onClose={jest.fn()} emptyMessage="No results" />)
    expect(screen.getByText('No results')).toBeInTheDocument()
  })

  it('renders recent queries', () => {
    render(<CommandBar open={true} onClose={jest.fn()} recentQueries={['query1', 'query2']} />)
    expect(screen.getByText('query1')).toBeInTheDocument()
    expect(screen.getByText('query2')).toBeInTheDocument()
  })

  it('renders suggestions', () => {
    const onClick = jest.fn()
    render(<CommandBar open={true} onClose={jest.fn()} suggestions={[{ label: 'Suggestion 1', onClick }]} />)
    expect(screen.getByText('Suggestion 1')).toBeInTheDocument()
  })

  it('closes on backdrop click', () => {
    const onClose = jest.fn()
    render(<CommandBar open={true} onClose={onClose} />)
    fireEvent.click(screen.getByRole('dialog').querySelector('.fixed.inset-0')!)
    expect(onClose).toHaveBeenCalled()
  })
})
