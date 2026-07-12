import { store, recall, forget, clear, getContext } from '../memory'

describe('AgentMemory', () => {
  beforeEach(() => {
    clear('test-agent')
    clear('other-agent')
  })

  it('stores and recalls a value', () => {
    store('test-agent', 'my-key', { hello: 'world' }, 60000)
    expect(recall('test-agent', 'my-key')).toEqual({ hello: 'world' })
  })

  it('returns undefined for unknown agent', () => {
    expect(recall('nonexistent', 'key')).toBeUndefined()
  })

  it('returns undefined for unknown key', () => {
    store('test-agent', 'existing', 'value', 60000)
    expect(recall('test-agent', 'missing')).toBeUndefined()
  })

  it('updates an existing key', () => {
    store('test-agent', 'key', 'first', 60000)
    store('test-agent', 'key', 'second', 60000)
    expect(recall('test-agent', 'key')).toBe('second')
  })

  it('forgets a specific key', () => {
    store('test-agent', 'keep', 'value', 60000)
    store('test-agent', 'remove', 'value', 60000)
    forget('test-agent', 'remove')
    expect(recall('test-agent', 'remove')).toBeUndefined()
    expect(recall('test-agent', 'keep')).toBe('value')
  })

  it('clears all memory for an agent', () => {
    store('test-agent', 'a', 1, 60000)
    store('test-agent', 'b', 2, 60000)
    clear('test-agent')
    expect(getContext('test-agent')).toEqual({})
  })

  it('isolates memory between agents', () => {
    store('test-agent', 'shared', 'agent-value', 60000)
    store('other-agent', 'shared', 'other-value', 60000)
    expect(recall('test-agent', 'shared')).toBe('agent-value')
    expect(recall('other-agent', 'shared')).toBe('other-value')
  })

  it('returns context as a flat key-value record', () => {
    store('test-agent', 'name', 'Alice', 60000)
    store('test-agent', 'score', 100, 60000)
    const ctx = getContext('test-agent')
    expect(ctx).toEqual({ name: 'Alice', score: 100 })
  })

  it('handles TTL expiry', () => {
    jest.useFakeTimers()
    store('test-agent', 'ephemeral', 'gone', 100)
    jest.advanceTimersByTime(200)
    expect(recall('test-agent', 'ephemeral')).toBeUndefined()
    jest.useRealTimers()
  })

  it('does not expire entries with TTL <= 0', () => {
    jest.useFakeTimers()
    store('test-agent', 'persistent', 'forever', 0)
    jest.advanceTimersByTime(86400000)
    expect(recall('test-agent', 'persistent')).toBe('forever')
    jest.useRealTimers()
  })
})
