import { render, screen, fireEvent } from '@testing-library/react'

jest.mock('@/lib/i18n', () => ({
  useTranslation: () => ({
    t: (key: string) => {
      const map: Record<string, string> = {
        'error.default_title': 'Something went wrong',
        'error.default_message': '',
        'error.retry': 'Try again',
        'error.show_details': 'Show details',
      }
      return map[key] || key
    },
  }),
}))

import { ErrorFallback } from '../error-boundary'
import { ErrorBoundary } from '../../error-boundary'

describe('ErrorFallback', () => {
  it('renders default title and message', () => {
    render(<ErrorFallback />)
    expect(screen.getByText('Something went wrong')).toBeInTheDocument()
  })

  it('renders custom title and message', () => {
    render(<ErrorFallback title="Custom Error" message="Details here" />)
    expect(screen.getByText('Custom Error')).toBeInTheDocument()
    expect(screen.getByText('Details here')).toBeInTheDocument()
  })

  it('renders retry button and fires handler', () => {
    const onRetry = jest.fn()
    render(<ErrorFallback onRetry={onRetry} />)
    fireEvent.click(screen.getByText('Try again'))
    expect(onRetry).toHaveBeenCalledTimes(1)
  })

  it('has alert role', () => {
    render(<ErrorFallback />)
    expect(screen.getByRole('alert')).toBeInTheDocument()
  })
})

describe('ErrorBoundary', () => {
  beforeEach(() => {
    jest.spyOn(console, 'error').mockImplementation(() => {})
  })

  afterEach(() => {
    jest.restoreAllMocks()
  })

  it('renders children when no error', () => {
    render(
      <ErrorBoundary>
        <div>Safe content</div>
      </ErrorBoundary>,
    )
    expect(screen.getByText('Safe content')).toBeInTheDocument()
  })

  it('renders default fallback on error', () => {
    const Bomb = () => { throw new Error('💥') }
    render(
      <ErrorBoundary>
        <Bomb />
      </ErrorBoundary>,
    )
    expect(screen.getByText('💥')).toBeInTheDocument()
  })

  it('renders custom fallback on error', () => {
    const Bomb = () => { throw new Error('Boom') }
    render(
      <ErrorBoundary fallback={<div>Custom fallback</div>}>
        <Bomb />
      </ErrorBoundary>,
    )
    expect(screen.getByText('Custom fallback')).toBeInTheDocument()
  })

  it('calls onError when error is caught', () => {
    const onError = jest.fn()
    const Bomb = () => { throw new Error('Test') }
    render(
      <ErrorBoundary onError={onError}>
        <Bomb />
      </ErrorBoundary>,
    )
    expect(onError).toHaveBeenCalled()
  })

  it('resets error state when retry is clicked', () => {
    let shouldThrow = true
    const Bomb = () => {
      if (shouldThrow) throw new Error('💥')
      return <div>Recovered</div>
    }
    render(
      <ErrorBoundary>
        <Bomb />
      </ErrorBoundary>,
    )
    expect(screen.getByText('💥')).toBeInTheDocument()

    fireEvent.click(screen.getByText('إعادة المحاولة'))
    shouldThrow = false
    fireEvent.click(screen.getByText('إعادة المحاولة'))

    expect(screen.getByText('Recovered')).toBeInTheDocument()
  })

  it('renders custom element fallback', () => {
    const Bomb = () => { throw new Error('Oops') }
    render(
      <ErrorBoundary fallback={<div>Custom fallback element</div>}>
        <Bomb />
      </ErrorBoundary>,
    )
    expect(screen.getByText('Custom fallback element')).toBeInTheDocument()
  })
})
