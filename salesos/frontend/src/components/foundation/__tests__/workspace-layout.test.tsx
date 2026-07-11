import { render, screen } from '@testing-library/react'
import { WorkspaceLayout } from '../workspace-layout'

describe('WorkspaceLayout', () => {
  it('renders sidebar, header, tabs and children', () => {
    render(
      <WorkspaceLayout
        sidebar={<aside data-testid="sidebar">Side</aside>}
        header={<header data-testid="header">Head</header>}
        tabs={<button>Tab1</button>}
      >
        <main data-testid="content">Content</main>
      </WorkspaceLayout>,
    )
    expect(screen.getByTestId('sidebar')).toBeInTheDocument()
    expect(screen.getByTestId('header')).toBeInTheDocument()
    expect(screen.getByText('Tab1')).toBeInTheDocument()
    expect(screen.getByTestId('content')).toBeInTheDocument()
  })

  it('renders without tabs', () => {
    render(
      <WorkspaceLayout
        sidebar={<aside>Side</aside>}
        header={<header>Head</header>}
        tabs={null}
      >
        <div>Content</div>
      </WorkspaceLayout>,
    )
    expect(screen.getByText('Content')).toBeInTheDocument()
  })
})
