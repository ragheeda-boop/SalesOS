import type { SearchResult, SearchEntityType } from './types'

export interface RawSearchResult {
  id: string
  entity_type: string
  title: string
  subtitle: string
  description?: string
  score: number
  confidence: number
  highlights?: { field: string; text: string; snippets: string[] }[]
  badges?: { label: string; variant: string }[]
  actions?: { id: string; label: string; icon?: string; handler: string }[]
  source: string
  updated_at: string
  thumbnail?: string
  relationships?: { id: string; type: string; label: string; direction: string }[]
}

const VALID_VARIANTS = ['info', 'success', 'warning', 'danger', 'neutral'] as const
const VALID_DIRECTIONS = ['inbound', 'outbound', 'bidirectional'] as const

function sanitizeVariant(v: string): SearchResult['badges'][number]['variant'] {
  return VALID_VARIANTS.includes(v as any) ? (v as any) : 'neutral'
}

function sanitizeDirection(d: string): NonNullable<SearchResult['relationships']>[number]['direction'] {
  return VALID_DIRECTIONS.includes(d as any) ? (d as any) : 'bidirectional'
}

export function mapSearchResult(raw: RawSearchResult): SearchResult {
  return {
    id: raw.id,
    entityType: raw.entity_type as SearchEntityType,
    title: raw.title,
    subtitle: raw.subtitle,
    description: raw.description,
    score: raw.score ?? 0,
    confidence: raw.confidence ?? 0,
    highlights: (raw.highlights ?? []).map((h) => ({
      field: h.field,
      text: h.text,
      snippets: h.snippets ?? [],
    })),
    badges: (raw.badges ?? []).map((b) => ({
      label: b.label,
      variant: sanitizeVariant(b.variant),
    })),
    actions: (raw.actions ?? []).map((a) => ({
      id: a.id,
      label: a.label,
      icon: a.icon,
      handler: a.handler,
    })),
    source: raw.source,
    updatedAt: raw.updated_at,
    thumbnail: raw.thumbnail,
    relationships: (raw.relationships ?? []).map((r) => ({
      id: r.id,
      type: r.type,
      label: r.label,
      direction: sanitizeDirection(r.direction),
    })),
  }
}

export function mapSearchResults(raw: RawSearchResult[]): SearchResult[] {
  return raw.map(mapSearchResult)
}

export function groupResultsByType(results: SearchResult[]): Record<string, SearchResult[]> {
  const groups: Record<string, SearchResult[]> = {}
  for (const r of results) {
    const key = r.entityType
    if (!groups[key]) groups[key] = []
    groups[key].push(r)
  }
  return groups
}
