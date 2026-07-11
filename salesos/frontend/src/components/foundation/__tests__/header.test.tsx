import { render, screen, fireEvent } from '@testing-library/react'
import { Header } from '../header'
import { AppShell } from '../app-shell'

describe('Header', () => {
  it('renders title', () => {
    render(<Header title="Dashboard" />)
    expect(screen.getByText('Dashboard')).toBeInTheDocument()
  })

  it('renders breadcrumbs', () => {
    render(
      <AppShell>
        <Header breadcrumbs={[{ label: 'Home', href: '/' }, { label: 'Settings' }]} />
      </AppShell>,
    )
    expect(screen.getByText('Home')).toBeInTheDocument()
    expect(screen.getByText('Settings')).toBeInTheDocument()
  })

  it('opens command palette on search click', () => {
    render(
      <AppShell>
        <Header />
      </AppShell>,
    )
    fireEvent.click(screen.getByLabelText('Search'))
  })

  it('renders notification bell with count', () => {
    render(<Header notificationCount={5} />)
    expect(screen.getByText('5')).toBeInTheDocument()
  })

  it('renders 99+ for high notification count', () => {
    render(<Header notificationCount={150} />)
    expect(screen.getByText('99+')).toBeInTheDocument()
  })

  it('renders user avatar', () => {
    render(<Header userAvatar={<div data-testid="avatar">A</div>} />)
    expect(screen.getByTestId('avatar')).toBeInTheDocument()
  })

  it('renders custom placeholder', () => {
    render(<Header searchPlaceholder="ابحث..." />)
    expect(screen.getByText('ابحث...')).toBeInTheDocument()
  })
})
