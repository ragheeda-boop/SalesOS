import { renderHook, act } from '@testing-library/react'
import { useDebounce, useMediaQuery, usePrevious } from '../src/use-utils'

describe('useDebounce', () => {
  beforeEach(() => {
    jest.useFakeTimers()
  })

  afterEach(() => {
    jest.useRealTimers()
  })

  it('returns initial value immediately', () => {
    const { result } = renderHook(() => useDebounce('hello', 500))
    expect(result.current).toBe('hello')
  })

  it('updates after delay', () => {
    const { result, rerender } = renderHook(
      ({ val }) => useDebounce(val, 500),
      { initialProps: { val: 'hello' } }
    )

    rerender({ val: 'world' })
    expect(result.current).toBe('hello')

    act(() => { jest.advanceTimersByTime(500) })
    expect(result.current).toBe('world')
  })

  it('cancels previous timer on rapid changes', () => {
    const { result, rerender } = renderHook(
      ({ val }) => useDebounce(val, 500),
      { initialProps: { val: 'a' } }
    )

    rerender({ val: 'b' })
    rerender({ val: 'c' })
    act(() => { jest.advanceTimersByTime(200) })
    expect(result.current).toBe('a')

    act(() => { jest.advanceTimersByTime(300) })
    expect(result.current).toBe('c')
  })
})

describe('usePrevious', () => {
  it('returns undefined on first render', () => {
    const { result } = renderHook(() => usePrevious('hello'))
    expect(result.current).toBeUndefined()
  })

  it('returns previous value after update', () => {
    const { result, rerender } = renderHook(
      ({ val }) => usePrevious(val),
      { initialProps: { val: 'first' } }
    )

    rerender({ val: 'second' })
    expect(result.current).toBe('first')
  })
})

describe('useMediaQuery', () => {
  it('returns false for non-matching query', () => {
    window.matchMedia = jest.fn().mockImplementation((q: string) => ({
      matches: false,
      media: q,
      addEventListener: jest.fn(),
      removeEventListener: jest.fn(),
    }))
    const { result } = renderHook(() => useMediaQuery('(min-width: 9999px)'))
    expect(result.current).toBe(false)
  })
})
