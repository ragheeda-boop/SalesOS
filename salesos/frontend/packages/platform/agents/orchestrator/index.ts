import type { AgentContext, AgentTask, AgentResult, AgentAction, TaskStatus, TaskPriority } from '../contracts'
import * as registry from '../registry'
import * as tools from '../tools'
import * as memory from '../memory'
import { decisionEngine } from '@salesos/decision-platform'
import type { DecisionContext } from '@salesos/decision-platform'

const tasks = new Map<string, AgentTask>()
const agentBusyMap = new Map<string, number>()

function generateId(): string {
  return crypto.randomUUID()
}

function now(): string {
  return new Date().toISOString()
}

function resolvePriority(context: AgentContext, goal: string): TaskPriority {
  if (context.metadata?.priority === 'critical' || context.metadata?.priority === 'high') {
    return context.metadata.priority as TaskPriority
  }
  if (goal.toLowerCase().includes('critical') || goal.toLowerCase().includes('urgent')) {
    return 'critical'
  }
  if (goal.toLowerCase().includes('high') || goal.toLowerCase().includes('important')) {
    return 'high'
  }
  return 'medium'
}

export async function assignTask(
  agentId: string,
  context: AgentContext,
  goal: string,
): Promise<AgentTask> {
  const agent = registry.get(agentId)
  if (!agent) throw new Error(`Agent '${agentId}' is not registered`)

  const task: AgentTask = {
    id: generateId(),
    agentId,
    context,
    goal,
    status: 'pending',
    priority: resolvePriority(context, goal),
    createdAt: now(),
  }

  tasks.set(task.id, task)
  return task
}

export async function executeTask(taskId: string): Promise<AgentResult> {
  const task = tasks.get(taskId)
  if (!task) throw new Error(`Task '${taskId}' not found`)

  const agent = registry.get(task.agentId)
  if (!agent) throw new Error(`Agent '${task.agentId}' is not registered`)

  const busyCount = agentBusyMap.get(task.agentId) ?? 0
  if (busyCount >= agent.maxConcurrency) {
    throw new Error(`Agent '${task.agentId}' is at max concurrency (${agent.maxConcurrency})`)
  }

  task.status = 'running'
  task.assignedAt = now()
  agentBusyMap.set(task.agentId, busyCount + 1)

  const actions: AgentAction[] = []
  const startedAt = now()

  try {
    const decContext: DecisionContext = {
      tenantId: task.context.tenantId,
      actorId: task.agentId,
      entityId: task.context.entityId,
      entityType: task.context.entityType as DecisionContext['entityType'],
      metadata: {
        ...task.context.metadata,
        agentId: task.agentId,
        taskId: task.id,
        goal: task.goal,
      },
    }

    const decision = await decisionEngine.evaluate(decContext)

    for (const toolName of agent.tools) {
      const available = tools.list().find(t => t.name === toolName)
      if (!available) continue

      const actionStart = now()
      const action: AgentAction = {
        type: 'tool',
        name: toolName,
        params: {
          tenantId: task.context.tenantId,
          entityId: task.context.entityId,
          entityType: task.context.entityType,
          decisionId: decision.decisionId,
          ...task.context.metadata,
        },
        status: 'pending',
        startedAt: actionStart,
      }

      try {
        const result = await tools.execute(toolName, action.params)
        action.status = 'completed'
        action.result = result
        action.completedAt = now()

        if (result && typeof result === 'object' && 'opportunityId' in (result as Record<string, unknown>)) {
          memory.store(task.agentId, `last_opportunity_${task.id}`, result)
        }
        if (result && typeof result === 'object' && 'taskId' in (result as Record<string, unknown>)) {
          memory.store(task.agentId, `last_task_${task.id}`, result)
        }
      } catch (err) {
        action.status = 'failed'
        action.error = err instanceof Error ? err.message : String(err)
        action.completedAt = now()
      }

      actions.push(action)
    }

    const succeeded = actions.filter(a => a.status === 'completed').length
    const failed = actions.filter(a => a.status === 'failed').length

    task.status = failed > 0 && succeeded === 0 ? 'failed' : 'completed'
    task.completedAt = now()

    const summary = [
      `Agent '${agent.name}' executed task '${task.goal}'`,
      `Decision: ${decision.recommendation.actionLabel} (${Math.round(decision.recommendation.confidence * 100)}%)`,
      `Actions: ${succeeded} succeeded, ${failed} failed`,
    ].join('. ')

    memory.store(task.agentId, `last_result_${task.id}`, { summary, decisionId: decision.decisionId })

    return {
      taskId: task.id,
      agentId: task.agentId,
      decision,
      actions,
      summary,
      completedAt: now(),
    }
  } catch (err) {
    task.status = 'failed'
    task.error = err instanceof Error ? err.message : String(err)
    task.completedAt = now()
    throw err
  } finally {
    const current = agentBusyMap.get(task.agentId) ?? 0
    agentBusyMap.set(task.agentId, Math.max(0, current - 1))
  }
}

export async function executeBatch(
  batch: { agentId: string; context: AgentContext; goal: string }[],
): Promise<AgentResult[]> {
  const assigned = await Promise.all(
    batch.map(b => assignTask(b.agentId, b.context, b.goal)),
  )
  return Promise.all(assigned.map(t => executeTask(t.id)))
}

export function getTask(taskId: string): AgentTask | undefined {
  return tasks.get(taskId)
}

export function clearTasks(): void {
  tasks.clear()
  agentBusyMap.clear()
}

export function getAgentStatus(agentId: string): { busy: boolean; taskCount: number } {
  const agentTasks = Array.from(tasks.values()).filter(t => t.agentId === agentId)
  const running = agentTasks.filter(t => t.status === 'running').length
  return {
    busy: running > 0,
    taskCount: agentTasks.length,
  }
}
