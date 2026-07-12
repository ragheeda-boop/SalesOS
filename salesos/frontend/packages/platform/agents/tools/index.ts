import type { ToolDefinition } from '../contracts'
import { decisionEngine } from '@salesos/decision-platform'
import type { DecisionContext } from '@salesos/decision-platform'

const tools = new Map<string, ToolDefinition>()

type ToolHandler = (params: Record<string, unknown>) => Promise<unknown>

const handlers = new Map<string, ToolHandler>()

export function register(tool: ToolDefinition): void {
  if (tools.has(tool.name)) {
    throw new Error(`Tool '${tool.name}' is already registered`)
  }
  tools.set(tool.name, tool)
}

export async function execute(toolName: string, params: Record<string, unknown>): Promise<unknown> {
  const handler = handlers.get(toolName)
  if (!handler) {
    const tool = tools.get(toolName)
    if (!tool) throw new Error(`Unknown tool: '${toolName}'`)
    throw new Error(`Tool '${toolName}' has no handler registered`)
  }
  return handler(params)
}

export function list(): ToolDefinition[] {
  return Array.from(tools.values())
}

export function registerHandler(name: string, handler: ToolHandler): void {
  handlers.set(name, handler)
}

const createOpportunityTool: ToolDefinition = {
  name: 'create_opportunity',
  description: 'Creates a new SalesOS opportunity',
  schema: {
    type: 'object',
    properties: {
      companyId: { type: 'string', description: 'Company ID' },
      name: { type: 'string', description: 'Opportunity name' },
      value: { type: 'number', description: 'Expected revenue' },
      stage: { type: 'string', description: 'Pipeline stage' },
      ownerId: { type: 'string', description: 'Owner user ID' },
    },
    required: ['companyId', 'name'],
  },
  handler: 'create_opportunity',
}

const createTaskTool: ToolDefinition = {
  name: 'create_task',
  description: 'Creates a new SalesOS task',
  schema: {
    type: 'object',
    properties: {
      title: { type: 'string', description: 'Task title' },
      description: { type: 'string', description: 'Task description' },
      assigneeId: { type: 'string', description: 'Assignee user ID' },
      dueDate: { type: 'string', description: 'Due date ISO string' },
      priority: { type: 'string', enum: ['low', 'medium', 'high', 'critical'] },
      relatedEntityId: { type: 'string', description: 'Related entity ID' },
      relatedEntityType: { type: 'string', description: 'Related entity type' },
    },
    required: ['title', 'assigneeId'],
  },
  handler: 'create_task',
}

const evaluateDecisionTool: ToolDefinition = {
  name: 'evaluate_decision',
  description: 'Evaluates a decision via the Decision Platform engine',
  schema: {
    type: 'object',
    properties: {
      tenantId: { type: 'string', description: 'Tenant ID' },
      actorId: { type: 'string', description: 'Actor ID' },
      entityId: { type: 'string', description: 'Entity ID' },
      entityType: { type: 'string', enum: ['company', 'opportunity', 'person'] },
      opportunityId: { type: 'string' },
      companyId: { type: 'string' },
      signalId: { type: 'string' },
      metadata: { type: 'object' },
    },
    required: ['tenantId', 'actorId'],
  },
  handler: 'evaluate_decision',
}

const searchCompaniesTool: ToolDefinition = {
  name: 'search_companies',
  description: 'Searches for companies (placeholder)',
  schema: {
    type: 'object',
    properties: {
      query: { type: 'string', description: 'Search query' },
      limit: { type: 'number', description: 'Max results' },
    },
    required: ['query'],
  },
  handler: 'search_companies',
}

const getRecommendationTool: ToolDefinition = {
  name: 'get_recommendation',
  description: 'Gets an NBA recommendation for a given context',
  schema: {
    type: 'object',
    properties: {
      tenantId: { type: 'string' },
      actorId: { type: 'string' },
      entityId: { type: 'string' },
      entityType: { type: 'string' },
    },
    required: ['tenantId', 'actorId'],
  },
  handler: 'get_recommendation',
}

registerHandler('create_opportunity', async (params) => {
  return {
    success: true,
    action: 'create_opportunity',
    opportunityId: crypto.randomUUID(),
    name: params.name,
    companyId: params.companyId,
    value: params.value ?? 0,
    stage: params.stage ?? 'discovery',
    ownerId: params.ownerId,
    createdAt: new Date().toISOString(),
  }
})

registerHandler('create_task', async (params) => {
  return {
    success: true,
    action: 'create_task',
    taskId: crypto.randomUUID(),
    title: params.title,
    assigneeId: params.assigneeId,
    dueDate: params.dueDate,
    priority: params.priority ?? 'medium',
    relatedEntityId: params.relatedEntityId,
    relatedEntityType: params.relatedEntityType,
    createdAt: new Date().toISOString(),
  }
})

registerHandler('evaluate_decision', async (params) => {
  const context: DecisionContext = {
    tenantId: params.tenantId as string,
    actorId: params.actorId as string,
    entityId: params.entityId as string | undefined,
    entityType: params.entityType as DecisionContext['entityType'],
    opportunityId: params.opportunityId as string | undefined,
    companyId: params.companyId as string | undefined,
    signalId: params.signalId as string | undefined,
    metadata: params.metadata as Record<string, unknown> | undefined,
  }
  return decisionEngine.evaluate(context)
})

registerHandler('search_companies', async (_params) => {
  return { success: true, results: [], message: 'Search companies placeholder — integrate Search SDK' }
})

registerHandler('get_recommendation', async (params) => {
  const context: DecisionContext = {
    tenantId: params.tenantId as string,
    actorId: params.actorId as string,
    entityId: params.entityId as string | undefined,
    entityType: params.entityType as DecisionContext['entityType'],
  }
  return decisionEngine.evaluate(context)
})

register(createOpportunityTool)
register(createTaskTool)
register(evaluateDecisionTool)
register(searchCompaniesTool)
register(getRecommendationTool)
