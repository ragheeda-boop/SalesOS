import { assignTask, getTask, getAgentStatus, clearTasks } from '../orchestrator'
import { register, unregister, list } from '../registry'
import { clear } from '../memory'

const agent = {
  id: 'test-agent',
  name: 'Test Agent',
  description: '',
  capabilities: ['test'],
  tools: [],
  memoryConfig: { ttl: 60000, maxEntries: 100, storageType: 'memory' as const },
  maxConcurrency: 5,
}

beforeEach(() => {
  clearTasks()
  list().forEach((a) => unregister(a.id))
  clear('test-agent')
  register(agent)
})

describe('AgentOrchestrator', () => {
  describe('assignTask', () => {
    it('creates a task with pending status', async () => {
      const task = await assignTask('test-agent', { tenantId: 't1' }, 'do something')
      expect(task.id).toBeDefined()
      expect(task.agentId).toBe('test-agent')
      expect(task.goal).toBe('do something')
      expect(task.status).toBe('pending')
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
  })

  describe('getTask', () => {
    it('returns undefined for unknown task', () => {
      expect(getTask('nonexistent')).toBeUndefined()
    })
  })

  describe('getAgentStatus', () => {
    it('returns zero counts for an agent with no tasks', () => {
      const status = getAgentStatus('test-agent')
      expect(status.busy).toBe(false)
      expect(status.taskCount).toBe(0)
    })

    it('reflects assigned tasks', async () => {
      await assignTask('test-agent', { tenantId: 't1' }, 'task 1')
      const status = getAgentStatus('test-agent')
      expect(status.taskCount).toBe(1)
    })
  })
})
