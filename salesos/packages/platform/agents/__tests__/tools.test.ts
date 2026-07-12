jest.mock('@salesos/decision-platform', () => ({
  decisionEngine: {
    evaluate: jest.fn().mockResolvedValue({
      decisionId: 'mock-dec',
      recommendation: { action: 'evaluate', actionLabel: 'Evaluate', confidence: 0.9 },
      scores: [],
      rulesApplied: [],
      evidence: [],
      context: { tenantId: 't1', actorId: 'a1' },
      explainability: { summary: 'OK', factors: [] },
      telemetry: { evaluationTimeMs: 5, rulesTimeMs: 1, scoringTimeMs: 1, evidenceTimeMs: 1, recommendationTimeMs: 1, totalTimeMs: 9 },
      timestamp: new Date().toISOString(),
    }),
  },
}))

import { execute, list } from '../tools'

describe('AgentTools', () => {
  it('lists registered tools (from module side-effect)', () => {
    const all = list()
    expect(all.length).toBeGreaterThanOrEqual(5)
    expect(all.find((t) => t.name === 'create_opportunity')).toBeDefined()
    expect(all.find((t) => t.name === 'create_task')).toBeDefined()
    expect(all.find((t) => t.name === 'evaluate_decision')).toBeDefined()
    expect(all.find((t) => t.name === 'search_companies')).toBeDefined()
    expect(all.find((t) => t.name === 'get_recommendation')).toBeDefined()
  })

  it('executes create_opportunity handler', async () => {
    const result = await execute('create_opportunity', {
      companyId: 'c1',
      name: 'Test Opp',
      value: 50000,
    })
    expect(result).toMatchObject({
      success: true,
      action: 'create_opportunity',
      opportunityId: expect.any(String),
      name: 'Test Opp',
    })
  })

  it('executes create_task handler', async () => {
    const result = await execute('create_task', {
      title: 'Test Task',
      assigneeId: 'u1',
    })
    expect(result).toMatchObject({
      success: true,
      taskId: expect.any(String),
      title: 'Test Task',
    })
  })

  it('executes evaluate_decision handler', async () => {
    const result = await execute('evaluate_decision', {
      tenantId: 't1',
      actorId: 'a1',
      entityId: 'e1',
      entityType: 'opportunity',
    })
    expect(result).toMatchObject({
      decisionId: 'mock-dec',
      recommendation: expect.any(Object),
    })
  })

  it('executes get_recommendation handler', async () => {
    const result = await execute('get_recommendation', {
      tenantId: 't1',
      actorId: 'a1',
    })
    expect(result).toMatchObject({
      decisionId: 'mock-dec',
    })
  })

  it('executes search_companies placeholder', async () => {
    const result = await execute('search_companies', { query: 'acme' })
    expect(result).toMatchObject({
      success: true,
      results: [],
    })
  })

  it('throws for unknown tool name', async () => {
    await expect(execute('nonexistent', {})).rejects.toThrow('Unknown tool')
  })
})
