import { register, get, list, unregister } from '../registry'

const makeAgent = (id: string) => ({
  id,
  name: `Agent ${id}`,
  description: '',
  capabilities: ['test'],
  tools: ['test_tool'],
  memoryConfig: { ttl: 1000, maxEntries: 10, storageType: 'memory' as const },
  maxConcurrency: 3,
})

beforeEach(() => {
  // Clear all agents before each test (NBA_AGENT is registered as module side-effect)
  list().forEach((a) => unregister(a.id))
})

describe('AgentRegistry', () => {
  it('registers and retrieves an agent', () => {
    register(makeAgent('test-agent'))
    const agent = get('test-agent')
    expect(agent).toBeDefined()
    expect(agent!.name).toBe('Agent test-agent')
  })

  it('throws when registering a duplicate agent id', () => {
    register(makeAgent('dup'))
    expect(() => register(makeAgent('dup'))).toThrow('already registered')
  })

  it('lists all registered agents', () => {
    register(makeAgent('a1'))
    register(makeAgent('a2'))
    expect(list()).toHaveLength(2)
  })

  it('filters agents by capability', () => {
    register(makeAgent('filter-me'))
    const filtered = list('test')
    expect(filtered.length).toBeGreaterThanOrEqual(1)
    expect(filtered.every((a) => a.capabilities.includes('test'))).toBe(true)
  })

  it('returns empty list for unmatched capability', () => {
    register(makeAgent('unmatched'))
    expect(list('nonexistent')).toHaveLength(0)
  })

  it('unregisters an agent', () => {
    register(makeAgent('remove-me'))
    unregister('remove-me')
    expect(get('remove-me')).toBeUndefined()
  })
})
