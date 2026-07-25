import { screen, fireEvent, waitFor, type RenderResult } from '@testing-library/react'
import { describeWidgetContract } from './testing/WidgetContract'
import { renderWidget } from './testing/renderWidget'
import { createMockWidget } from './testing/mockWidgetContext'
import {
  mockPermissionsAll,
  mockPermissionsNone,
} from './testing/mockPermissions'
import {
  mockFeatureFlagsAll,
  mockFeatureFlagsNone,
} from './testing/mockFeatureFlags'
import type { WidgetConfig, WidgetData, WidgetStatus } from './types'

export interface ContractTestSuiteConfig<T> {
  name: string
  render: WidgetConfig<T>['render']
  metadata: WidgetConfig<T>['metadata']
  defaultData: T
  customTests?: (helpers: ContractTestHelpers<T>) => void
}

export interface ContractTestHelpers<T> {
  mock: {
    ready: (overrides?: Partial<WidgetData<T>>) => WidgetData<T>
    loading: (overrides?: Partial<WidgetData<T>>) => WidgetData<T>
    degraded: (overrides?: Partial<WidgetData<T>>) => WidgetData<T>
    error: (overrides?: Partial<WidgetData<T>>) => WidgetData<T>
  }
  renderWidget: (
    overrides?: Partial<{
      useData: () => WidgetData<T>
      fallback: React.ReactNode
    }>,
  ) => RenderResult
  screen: typeof screen
  fireEvent: typeof fireEvent
  waitFor: typeof waitFor
}

export function createWidgetContractTest<T>(cfg: ContractTestSuiteConfig<T>) {
  describeWidgetContract({
    name: cfg.name,
    config: {
      metadata: cfg.metadata,
      render: cfg.render,
    },
    defaultData: cfg.defaultData,
  })

  if (cfg.customTests) {
    const mock = createMockWidget(cfg.defaultData)

    const helpers: ContractTestHelpers<T> = {
      mock,
      renderWidget: (overrides) =>
        renderWidget(
          { metadata: cfg.metadata, render: cfg.render },
          {
            useData: overrides?.useData ?? (() => mock.ready()),
            fallback: overrides?.fallback,
          },
        ),
      screen,
      fireEvent,
      waitFor,
    }

    describe(`Widget-Specific Tests: ${cfg.name}`, () => {
      beforeEach(() => {
        mockPermissionsAll()
        mockFeatureFlagsAll()
      })

      cfg.customTests(helpers)
    })
  }
}

export { describeWidgetContract } from './testing/WidgetContract'
export { renderWidget } from './testing/renderWidget'
export { createMockWidget } from './testing/mockWidgetContext'
export {
  mockPermissionsAll,
  mockPermissionsNone,
} from './testing/mockPermissions'
export {
  mockFeatureFlagsAll,
  mockFeatureFlagsNone,
} from './testing/mockFeatureFlags'
export type {
  ContractTestConfig,
  ContractTestSuite,
} from './testing/WidgetContract'
export type { MockWidgetContext } from './testing/types'
