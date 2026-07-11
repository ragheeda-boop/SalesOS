import { render, screen } from '@testing-library/react'

jest.mock('../widget-registry', () => ({
  WidgetRegistry: ({ children }: { children: React.ReactNode }) => <div data-testid="widget-registry">{children}</div>,
  useWidgetRegistry: () => ({ getWidget: jest.fn(), getAllWidgets: jest.fn() }),
}))

import { WidgetRegistry, useWidgetRegistry } from '../widget-registry'

describe('WidgetRegistry', () => {
  it('renders children', () => {
    render(<WidgetRegistry><div data-testid="child">C</div></WidgetRegistry>)
    expect(screen.getByTestId('child')).toBeInTheDocument()
  })
})

describe('useWidgetRegistry', () => {
  it('returns registry methods', () => {
    const reg = useWidgetRegistry()
    expect(reg.getWidget).toBeDefined()
    expect(reg.getAllWidgets).toBeDefined()
  })
})
