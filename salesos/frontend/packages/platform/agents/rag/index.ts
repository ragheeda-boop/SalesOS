import type { AgentContext } from '../contracts'
import * as memory from '../memory'

export function buildContext(agentId: string, context: AgentContext): string {
  const parts: string[] = []

  parts.push(`# Agent Context for ${agentId}`)
  parts.push(`Tenant: ${context.tenantId}`)
  if (context.entityId) parts.push(`Entity: ${context.entityId} (${context.entityType ?? 'unknown'})`)
  if (context.decisionId) parts.push(`Decision: ${context.decisionId}`)

  const mem = memory.getContext(agentId)
  const memKeys = Object.keys(mem)
  if (memKeys.length > 0) {
    parts.push(`\n## Memory`)
    for (const key of memKeys) {
      const value = mem[key]
      const str = typeof value === 'object' ? JSON.stringify(value, null, 2) : String(value)
      parts.push(`- ${key}: ${str}`)
    }
  }

  if (context.metadata) {
    parts.push(`\n## Metadata`)
    for (const [key, value] of Object.entries(context.metadata)) {
      parts.push(`- ${key}: ${typeof value === 'object' ? JSON.stringify(value) : String(value)}`)
    }
  }

  return parts.join('\n')
}
