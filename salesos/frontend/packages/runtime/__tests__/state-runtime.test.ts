import { StateRuntime } from '../src/state-runtime'

describe('StateRuntime', () => {
  let rt: StateRuntime

  beforeEach(() => {
    rt = new StateRuntime()
  })

  it('sets and gets values by key', () => {
    rt.set('company.name', 'ACME Corp')
    expect(rt.get('company.name')).toBe('ACME Corp')
  })

  it('returns undefined for missing keys', () => {
    expect(rt.get('nonexistent')).toBeUndefined()
  })

  it('overwrites existing values', () => {
    rt.set('theme', 'light')
    rt.set('theme', 'dark')
    expect(rt.get('theme')).toBe('dark')
  })

  it('subscribes to changes', () => {
    const fn = jest.fn()
    rt.subscribe('company.name', fn)
    rt.set('company.name', 'ACME')
    expect(fn).toHaveBeenCalledWith('ACME')
  })

  it('unsubscribes listeners', () => {
    const fn = jest.fn()
    const unsub = rt.subscribe('company.name', fn)
    unsub()
    rt.set('company.name', 'ACME')
    expect(fn).not.toHaveBeenCalled()
  })

  it('notifies only matching path listeners', () => {
    const fn1 = jest.fn()
    const fn2 = jest.fn()
    rt.subscribe('company.name', fn1)
    rt.subscribe('company.city', fn2)
    rt.set('company.name', 'ACME')
    expect(fn1).toHaveBeenCalled()
    expect(fn2).not.toHaveBeenCalled()
  })

  it('supports nested objects', () => {
    rt.set('user', { name: 'Ali', role: 'admin' })
    expect(rt.get('user.name')).toBe('Ali')
    expect(rt.get('user.role')).toBe('admin')
  })

  it('clears all state', () => {
    rt.set('a', 1)
    rt.set('b', 2)
    rt.clear()
    expect(rt.get('a')).toBeUndefined()
    expect(rt.get('b')).toBeUndefined()
  })
})
