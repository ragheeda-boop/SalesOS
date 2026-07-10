import { render, screen } from '@testing-library/react'
import { Tabs, TabsList, Tab, TabsPanel } from '../src/tabs'

describe('Tabs', () => {
  it('renders children', () => {
    render(<Tabs><TabsList><Tab value="a">Tab A</Tab></TabsList></Tabs>)
    expect(screen.getByText('Tab A')).toBeInTheDocument()
  })
})

describe('TabsPanel', () => {
  it('renders content', () => {
    const { container } = render(
      <Tabs defaultValue="a">
        <TabsList><Tab value="a">A</Tab></TabsList>
        <TabsPanel value="a">Content</TabsPanel>
      </Tabs>
    )
    expect(screen.getByText('Content')).toBeInTheDocument()
  })
})
