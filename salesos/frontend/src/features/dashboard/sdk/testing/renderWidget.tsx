import { render, type RenderResult } from '@testing-library/react'
import type { WidgetConfig, WidgetData } from '../types'
import { createWidget } from '../create-widget'

export interface RenderWidgetOptions {
  useData: () => WidgetData<unknown>
  fallback?: React.ReactNode
}

export function renderWidget(
  config: Pick<WidgetConfig<unknown>, 'metadata' | 'render'>,
  options: RenderWidgetOptions,
): RenderResult {
  const Widget = createWidget({
    ...config,
    useData: options.useData,
    fallback: options.fallback,
  })
  return render(<Widget />)
}
