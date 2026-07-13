import { screen, fireEvent } from '@testing-library/react'
import type { WidgetConfig, WidgetData, WidgetStatus } from '../types'
import { renderWidget } from './renderWidget'
import { createMockWidget } from './mockWidgetContext'
import { mockPermissionsAll, mockPermissionsNone } from './mockPermissions'
import { mockFeatureFlagsAll, mockFeatureFlagsNone } from './mockFeatureFlags'

interface ContractTestConfig<T> {
  name: string
  config: Pick<WidgetConfig<T>, 'metadata' | 'render'>
  defaultData: T
}

export function describeWidgetContract<T>(cfg: ContractTestConfig<T>) {
  describe(`Widget Contract: ${cfg.name}`, () => {
    const mock = createMockWidget(cfg.defaultData)
    const testCases: { label: string; status: WidgetStatus; data: WidgetData<T> }[] = [
      { label: 'loading', status: 'loading', data: mock.loading() },
      { label: 'ready', status: 'ready', data: mock.ready() },
      { label: 'degraded', status: 'degraded', data: mock.degraded() },
      { label: 'error', status: 'error', data: mock.error() },
    ]

    beforeEach(() => {
      mockPermissionsAll()
      mockFeatureFlagsAll()
    })

    describe('1. Rendering', () => {
      it('renders title', () => {
        renderWidget(cfg.config, { useData: () => mock.ready() })
        expect(screen.getByText(cfg.config.metadata.title)).toBeInTheDocument()
      })

      it('renders children in ready state', () => {
        renderWidget(cfg.config, { useData: () => mock.ready() })
        expect(screen.getAllByRole('region').length).toBeGreaterThanOrEqual(1)
      })

      it('renders with fallback when permission denied', () => {
        mockPermissionsNone()
        const fallbackText = 'no-permission'
        renderWidget(cfg.config, {
          useData: () => mock.ready(),
          fallback: <div>{fallbackText}</div>,
        })
        expect(screen.getByText(fallbackText)).toBeInTheDocument()
      })

      it('renders with fallback when feature disabled', () => {
        mockFeatureFlagsNone()
        const fallbackText = 'feature-disabled'
        renderWidget(cfg.config, {
          useData: () => mock.ready(),
          fallback: <div>{fallbackText}</div>,
        })
        expect(screen.getByText(fallbackText)).toBeInTheDocument()
      })
    })

    describe('2. Widget States', () => {
      it.each(testCases)('renders $label state', ({ data }) => {
        renderWidget(cfg.config, { useData: () => data })
        const status = data.status
        if (status === 'ready') {
          expect(screen.getAllByRole('region').length).toBeGreaterThanOrEqual(1)
        }
        if (status === 'loading') {
          expect(screen.getByRole('status')).toBeInTheDocument()
        }
        if (status === 'error') {
          expect(screen.getByRole('alert')).toBeInTheDocument()
        }
      })

      it('shows content under degraded overlay when degraded with data', () => {
        renderWidget(cfg.config, { useData: () => mock.degraded() })
        expect(screen.getAllByRole('region').length).toBeGreaterThanOrEqual(1)
      })

      it('shows loading when degraded without data', () => {
        renderWidget(cfg.config, {
          useData: () => ({ ...mock.degraded(), data: null }),
        })
        expect(screen.getByRole('status')).toBeInTheDocument()
      })
    })

    describe('3. Permissions', () => {
      it('renders when permission granted', () => {
        mockPermissionsAll()
        renderWidget(cfg.config, { useData: () => mock.ready() })
        expect(screen.getByText(cfg.config.metadata.title)).toBeInTheDocument()
      })

      it('hides content when permission denied', () => {
        mockPermissionsNone()
        renderWidget(cfg.config, { useData: () => mock.ready() })
        expect(screen.queryByRole('region')).not.toBeInTheDocument()
      })
    })

    describe('4. Feature Flags', () => {
      it('renders when feature enabled', () => {
        mockFeatureFlagsAll()
        renderWidget(cfg.config, { useData: () => mock.ready() })
        expect(screen.getByText(cfg.config.metadata.title)).toBeInTheDocument()
      })

      it('hides content when feature disabled', () => {
        mockFeatureFlagsNone()
        renderWidget(cfg.config, { useData: () => mock.ready() })
        expect(screen.queryByRole('region')).not.toBeInTheDocument()
      })
    })

    describe('5. Accessibility', () => {
      it('refresh button has aria-label', () => {
        renderWidget(cfg.config, { useData: () => mock.ready() })
        const refresh = screen.queryByLabelText('Refresh')
        expect(refresh).toBeInTheDocument()
      })

      it('loading state has role="status"', () => {
        renderWidget(cfg.config, { useData: () => mock.loading() })
        expect(screen.getByRole('status')).toBeInTheDocument()
      })

      it('error state has role="alert"', () => {
        renderWidget(cfg.config, { useData: () => mock.error() })
        expect(screen.getByRole('alert')).toBeInTheDocument()
      })

      it('error state has retry button', () => {
        renderWidget(cfg.config, { useData: () => mock.error() })
        expect(screen.getByText('إعادة المحاولة')).toBeInTheDocument()
      })
    })

    describe('6. Interaction', () => {
      it('retry button calls refetch on click', () => {
        const refetch = jest.fn()
        renderWidget(cfg.config, {
          useData: () => ({ ...mock.error(), refetch }),
        })
        fireEvent.click(screen.getByText('إعادة المحاولة'))
        expect(refetch).toHaveBeenCalledTimes(1)
      })

      it('refresh button calls refetch on click', () => {
        const refetch = jest.fn()
        renderWidget(cfg.config, {
          useData: () => ({ ...mock.ready(), refetch }),
        })
        const refresh = screen.getByLabelText('Refresh')
        fireEvent.click(refresh)
        expect(refetch).toHaveBeenCalledTimes(1)
      })
    })
  })
}
