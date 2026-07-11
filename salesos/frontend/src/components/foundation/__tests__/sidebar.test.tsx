import { render, screen, fireEvent } from '@testing-library/react'
import { Sidebar } from '../sidebar'
import { AppShell } from '../app-shell'

const sections = [
  {
    id: 'main',
    label: 'Main',
    items: [
      { id: 'dashboard', label: 'Dashboard', icon: <span>D</span>, href: '/dashboard', active: true },
      { id: 'companies', label: 'Companies', icon: <span>C</span>, href: '/companies' },
    ],
  },
]

describe('Sidebar', () => {
  it('renders sections and items', () => {
    render(
      <AppShell>
        <Sidebar sections={sections} />
      </AppShell>,
    )
    expect(screen.getByText('Dashboard')).toBeInTheDocument()
    expect(screen.getByText('Companies')).toBeInTheDocument()
  })

  it('shows active state', () => {
    render(
      <AppShell>
        <Sidebar sections={sections} />
      </AppShell>,
    )
    const dashboardLink = screen.getByText('Dashboard').closest('a')!
    expect(dashboardLink).toHaveAttribute('aria-current', 'page')
  })

  it('shows section label', () => {
    render(
      <AppShell>
        <Sidebar sections={sections} />
      </AppShell>,
    )
    expect(screen.getByText('Main')).toBeInTheDocument()
  })

  it('renders company section', () => {
    render(
      <AppShell>
        <Sidebar sections={sections} companySection={{ id: 'company', label: 'شركتي', items: [{ id: 'my-co', label: 'شركتي', icon: <span>M</span> }] }} />
      </AppShell>,
    )
    expect(screen.getByText('شركتي')).toBeInTheDocument()
  })

  it('toggles collapse', () => {
    render(
      <AppShell>
        <Sidebar sections={sections} />
      </AppShell>,
    )
    const toggle = screen.getByLabelText('Collapse sidebar')
    fireEvent.click(toggle)
    expect(screen.getByLabelText('Expand sidebar')).toBeInTheDocument()
  })
})
