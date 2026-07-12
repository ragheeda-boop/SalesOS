import type { AgentDefinition } from '../contracts'

const agents = new Map<string, AgentDefinition>()

const NBA_AGENT: AgentDefinition = {
  id: 'nba-agent',
  name: 'NBA Agent',
  description: 'Consumes Next-Best-Action recommendations from the Decision Platform and creates opportunities and tasks',
  capabilities: ['nba-consumption', 'opportunity-creation', 'task-creation', 'decision-execution'],
  tools: ['create_opportunity', 'create_task', 'get_recommendation', 'evaluate_decision'],
  memoryConfig: {
    ttl: 3600000,
    maxEntries: 500,
    storageType: 'memory',
  },
  maxConcurrency: 5,
}

export function register(agent: AgentDefinition): void {
  if (agents.has(agent.id)) {
    throw new Error(`Agent '${agent.id}' is already registered`)
  }
  agents.set(agent.id, { ...agent })
}

export function get(id: string): AgentDefinition | undefined {
  return agents.get(id)
}

export function list(capability?: string): AgentDefinition[] {
  const all = Array.from(agents.values())
  if (capability) {
    return all.filter(a => a.capabilities.includes(capability))
  }
  return all
}

export function unregister(id: string): void {
  agents.delete(id)
}

register(NBA_AGENT)
