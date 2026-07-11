import type { RelationshipNode, RelationshipEdge } from '@/application/company-intelligence/company-intelligence.dto'
export interface RelationshipGraphViewProps {
  nodes: RelationshipNode[]
  edges: RelationshipEdge[]
}
