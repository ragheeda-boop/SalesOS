import { buildContext } from '../rag'
import { store, clear } from '../memory'

describe('AgentRAG', () => {
  beforeEach(() => {
    clear('rag-agent')
  })

  it('builds a basic context string', () => {
    const result = buildContext('rag-agent', { tenantId: 't1' })
    expect(result).toContain('Agent Context for rag-agent')
    expect(result).toContain('Tenant: t1')
  })

  it('includes entity information', () => {
    const result = buildContext('rag-agent', { tenantId: 't1', entityId: 'e1', entityType: 'company' })
    expect(result).toContain('Entity: e1 (company)')
  })

  it('includes decision ID', () => {
    const result = buildContext('rag-agent', { tenantId: 't1', decisionId: 'dec-1' })
    expect(result).toContain('Decision: dec-1')
  })

  it('includes memory entries', () => {
    store('rag-agent', 'last_result', { summary: 'Task completed' }, 60000)
    const result = buildContext('rag-agent', { tenantId: 't1' })
    expect(result).toContain('## Memory')
    expect(result).toContain('last_result')
    expect(result).toContain('Task completed')
  })

  it('includes metadata', () => {
    const result = buildContext('rag-agent', {
      tenantId: 't1',
      metadata: { source: 'dashboard', version: 2 },
    })
    expect(result).toContain('## Metadata')
    expect(result).toContain('source')
    expect(result).toContain('dashboard')
  })
})
