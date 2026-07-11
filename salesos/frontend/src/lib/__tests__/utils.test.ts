import { cn, formatDate, formatNumber } from '../utils'

describe('cn', () => {
  it('merges class names', () => {
    expect(cn('foo', 'bar')).toBe('foo bar')
  })

  it('handles conditional classes', () => {
    expect(cn('base', false && 'hidden', 'visible')).toBe('base visible')
  })

  it('handles undefined values', () => {
    expect(cn('a', undefined, 'b')).toBe('a b')
  })

  it('handles tailwind conflict resolution', () => {
    const result = cn('px-4', 'px-2')
    expect(result).not.toContain('px-4')
  })
})

describe('formatDate', () => {
  it('formats a date string', () => {
    const result = formatDate('2026-07-10')
    expect(result).toContain('يوليو')
    expect(result).toContain('٢٠٢٦')
  })

  it('formats a Date object', () => {
    const result = formatDate(new Date('2026-01-15'))
    expect(result).toContain('يناير')
  })
})

describe('formatNumber', () => {
  it('formats a number in Arabic locale', () => {
    const result = formatNumber(1234567)
    expect(result).toContain('١')
  })
})
