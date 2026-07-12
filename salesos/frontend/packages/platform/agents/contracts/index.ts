import type {
  DecisionContext,
  DecisionResult,
} from '@salesos/decision-platform'

export type AgentStatus = 'idle' | 'busy' | 'error' | 'disabled'
export type TaskStatus = 'pending' | 'assigned' | 'running' | 'completed' | 'failed' | 'cancelled'
export type TaskPriority = 'low' | 'medium' | 'high' | 'critical'
export type MemoryType = 'ephemeral' | 'working' | 'long_term'

export interface ToolDefinition {
  name: string
  description: string
  schema: Record<string, unknown>
  handler: string
}

export interface MemoryConfig {
  ttl: number
  maxEntries: number
  storageType: 'memory' | 'redis'
}

export interface AgentDefinition {
  id: string
  name: string
  description: string
  capabilities: string[]
  tools: string[]
  memoryConfig: MemoryConfig
  maxConcurrency: number
}

export interface AgentContext {
  tenantId: string
  decisionId?: string
  entityId?: string
  entityType?: string
  metadata?: Record<string, unknown>
}

export interface AgentTask {
  id: string
  agentId: string
  context: AgentContext
  goal: string
  status: TaskStatus
  priority: TaskPriority
  createdAt: string
  assignedAt?: string
  completedAt?: string
  error?: string
}

export interface AgentAction {
  type: string
  name: string
  params: Record<string, unknown>
  status: 'pending' | 'running' | 'completed' | 'failed'
  result?: unknown
  error?: string
  startedAt: string
  completedAt?: string
}

export interface AgentResult {
  taskId: string
  agentId: string
  decision: DecisionResult
  actions: AgentAction[]
  summary: string
  completedAt: string
}

export interface MemoryEntry {
  id: string
  agentId: string
  type: MemoryType
  key: string
  value: unknown
  ttl: number
  timestamp: string
}
