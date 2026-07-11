'use client'

import { useState, useCallback } from 'react'
import { cn } from '@salesos/ui'
import { Building2, User, Users, ArrowRight, ArrowLeft, ArrowUpDown } from 'lucide-react'
import type { RelationshipGraphViewProps } from './types'

const NODE_ICON = { person: <User className="h-3.5 w-3.5" />, company: <Building2 className="h-3.5 w-3.5" />, department: <Users className="h-3.5 w-3.5" /> }
const DIR_ICON = { inbound: <ArrowRight className="h-3 w-3" />, outbound: <ArrowLeft className="h-3 w-3" />, bidirectional: <ArrowUpDown className="h-3 w-3" /> }

export function RelationshipGraphView({ nodes, edges }: RelationshipGraphViewProps) {
  const [selectedNode, setSelectedNode] = useState<string | null>(null)

  const connectedEdges = edges.filter((e) => e.source === selectedNode || e.target === selectedNode)
  const connectedNodeIds = new Set(connectedEdges.flatMap((e) => [e.source, e.target]))
  const visibleNodes = selectedNode ? nodes.filter((n) => connectedNodeIds.has(n.id)) : nodes.slice(0, 6)

  if (nodes.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center py-8 text-center">
        <Building2 className="mb-2 h-8 w-8 text-[var(--text-muted)] opacity-30" />
        <p className="text-sm text-[var(--text-muted)]">لا توجد علاقات</p>
      </div>
    )
  }

  return (
    <div role="region" aria-label="العلاقات" className="space-y-1 dark:bg-neutral-900/20 dark:rounded-lg dark:p-1">
      <div className="flex flex-wrap gap-1">
        {visibleNodes.map((node) => {
          const isSelected = node.id === selectedNode
          return (
            <button
              key={node.id}
              onClick={() => setSelectedNode(isSelected ? null : node.id)}
              className={cn(
                'flex items-center gap-1.5 rounded-lg px-2 py-1.5 text-xs transition motion-reduce:transition-none',
                isSelected
                  ? 'bg-primary-50 text-primary-700 dark:bg-primary-900/20 dark:text-primary-300 ring-1 ring-primary-300'
                  : 'bg-[var(--bg-tertiary)] text-[var(--text-primary)] hover:bg-primary-50/50 dark:bg-neutral-800 dark:hover:bg-neutral-700',
              )}
            >
              {NODE_ICON[node.type]}
              <span className="truncate max-w-[100px]">{node.label}</span>
            </button>
          )
        })}
      </div>

      {selectedNode && (
        <div className="rounded-lg bg-[var(--bg-tertiary)] p-2 dark:bg-neutral-800">
          <p className="text-[10px] font-medium text-[var(--text-muted)] mb-1">العلاقات</p>
          {connectedEdges.map((edge, i) => {
            const isSource = edge.source === selectedNode
            const otherId = isSource ? edge.target : edge.source
            const other = nodes.find((n) => n.id === otherId)
            return (
              <div key={i} className="flex items-center gap-2 py-0.5 text-[10px] text-[var(--text-muted)]">
                {DIR_ICON[edge.direction]}
                <span>{edge.label}</span>
                {other && <span className="font-medium text-[var(--text-primary)]">→ {other.label}</span>}
              </div>
            )
          })}
        </div>
      )}
    </div>
  )
}
