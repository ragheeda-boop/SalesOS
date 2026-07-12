jest.mock('@salesos/decision-platform', () => ({
  decisionEngine: {
    evaluate: jest.fn().mockResolvedValue({
      decisionId: 'dec-1',
      recommendation: { action: 'proceed', actionLabel: 'Proceed', confidence: 0.85 },
      scores: [],
      rulesApplied: [],
      evidence: [],
      context: { tenantId: 't1', actorId: 'a1' },
      explainability: { summary: 'OK', factors: [] },
      telemetry: { evaluationTimeMs: 10, rulesTimeMs: 2, scoringTimeMs: 3, evidenceTimeMs: 4, recommendationTimeMs: 1, totalTimeMs: 20 },
      timestamp: new Date().toISOString(),
    }),
  },
}))

import { assignTask, executeTask, executeBatch, getTask, getAgentStatus } from '../orchestrator'
import { register, unregister, get, list } from '../registry'
import { clear } from '../memory'

const makeAgent = (id: string, maxConcurrency = 5) => ({
  id,
  name: `Agent ${id}`,
  description: '',
  capabilities: ['test'],
  tools: [],
  memoryConfig: { ttl: 60000, maxEntries: 100, storageType: 'memory' as const },
  maxConcurrency,
})

beforeEach(() => {
  list().forEach((a) => unregister(a.id))
  clear('test-agent')
  register(makeAgent('test-agent'))
})

describe('AgentOrchestrator', () => {
  describe('assignTask', () => {
    it('creates a task with pending status', async () => {
      const task = await assignTask('test-agent', { tenantId: 't1' }, 'do something')
      expect(task.id).toBeDefined()
      expect(task.agentId).toBe('test-agent')
      expect(task.goal).toBe('do something')
      expect(task.status).toBe('pending')
      expect(task.createdAt).toBeDefined()
    })

    it('throws for unknown agent', async () => {
      await expect(assignTask('unknown', { tenantId: 't1' }, 'x')).rejects.toThrow('not registered')
    })

    it('resolves priority from goal keywords', async () => {
      const critical = await assignTask('test-agent', { tenantId: 't1' }, 'critical bug fix')
      expect(critical.priority).toBe('critical')

      const high = await assignTask('test-agent', { tenantId: 't1' }, 'important task')
      expect(high.priority).toBe('high')

      const normal = await assignTask('test-agent', { tenantId: 't1' }, 'routine')
      expect(normal.priority).toBe('medium')
    })

    it('resolves priority from context metadata', async () => {
      const task = await assignTask('test-agent', { tenantId: 't1', metadata: { priority: 'high' } }, 'whatever')
      expect(task.priority).toBe('high')
    })
  })

  describe('getTask', () => {
    it('returns undefined for unknown task', () => {
      expect(getTask('nonexistent')).toBeUndefined()
    })
  })

  describe('getAgentStatus', () => {
    it('returns status for an agent with no tasks', () => {
      const status = getAgentStatus('test-agent')
      expect(status.busy).toBe(false)
      expect(status.taskCount).toBe(0)
    })
  })
})
