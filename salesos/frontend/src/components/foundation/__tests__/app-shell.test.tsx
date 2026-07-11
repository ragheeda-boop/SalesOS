import { render, screen, fireEvent } from '@testing-library/react'
import { AppShell, useAppShell } from '../app-shell'

function TestConsumer() {
  const { sidebarCollapsed, setSidebarCollapsed, commandOpen, setCommandOpen } = useAppShell()
  return (
    <div>
      <span data-testid="sidebar-collapsed">{String(sidebarCollapsed)}</span>
      <span data-testid="command-open">{String(commandOpen)}</span>
      <button onClick={() => setSidebarCollapsed(true)}>Collapse</button>
      <button onClick={() => setCommandOpen(true)}>Open Cmd</button>
    </div>
  )
}

describe('AppShell', () => {
  it('renders children', () => {
    render(
      <AppShell>
        <div>Content</div>
      </AppShell>,
    )
    expect(screen.getByText('Content')).toBeInTheDocument()
  })

  it('provides default context values', () => {
    render(
      <AppShell>
        <TestConsumer />
      </AppShell>,
    )
    expect(screen.getByTestId('sidebar-collapsed')).toHaveTextContent('false')
    expect(screen.getByTestId('command-open')).toHaveTextContent('false')
  })

  it('respects defaultSidebarCollapsed', () => {
    render(
      <AppShell defaultSidebarCollapsed={true}>
        <TestConsumer />
      </AppShell>,
    )
    expect(screen.getByTestId('sidebar-collapsed')).toHaveTextContent('true')
  })

  it('allows updating context', () => {
    render(
      <AppShell>
        <TestConsumer />
      </AppShell>,
    )
    fireEvent.click(screen.getByText('Collapse'))
    expect(screen.getByTestId('sidebar-collapsed')).toHaveTextContent('true')
  })

  it('has aria-label on shell div', () => {
    const { container } = render(
      <AppShell>
        <div />
      </AppShell>,
    )
    const shell = container.querySelector('[aria-label="Application shell"]')
    expect(shell).toBeInTheDocument()
  })

  it('toggles command palette on Ctrl+K', () => {
    render(
      <AppShell>
        <TestConsumer />
      </AppShell>,
    )
    fireEvent.keyDown(document, { key: 'k', ctrlKey: true })
    expect(screen.getByTestId('command-open')).toHaveTextContent('true')
  })

  it('closes command palette on Escape', () => {
    render(
      <AppShell>
        <TestConsumer />
      </AppShell>,
    )
    fireEvent.click(screen.getByText('Open Cmd'))
    expect(screen.getByTestId('command-open')).toHaveTextContent('true')

    fireEvent.keyDown(document, { key: 'Escape' })
    expect(screen.getByTestId('command-open')).toHaveTextContent('false')
  })
})
