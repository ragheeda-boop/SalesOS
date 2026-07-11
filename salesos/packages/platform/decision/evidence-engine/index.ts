import type {
  DecisionContext,
  EvidenceItem,
  EvidenceType,
} from '../contracts/index'

export interface EvidenceProvider {
  name: string
  confidence: number
  freshnessMax: number
}

export interface EvidenceSource {
  type: EvidenceType
  provider: EvidenceProvider
  data: Record<string, unknown>[]
}

export interface EvidenceCollectionResult {
  items: EvidenceItem[]
  deduplicated: number
  totalSources: number
  averageConfidence: number
  collectionTimeMs: number
}

const BUILTIN_PROVIDERS: Record<string, EvidenceProvider> = {
  signals: { name: 'signals', confidence: 0.85, freshnessMax: 24 },
  company_dna: { name: 'company_dna', confidence: 0.90, freshnessMax: 24 },
  timeline: { name: 'timeline', confidence: 0.80, freshnessMax: 1 },
  search: { name: 'search', confidence: 0.75, freshnessMax: 1 },
  documents: { name: 'documents', confidence: 0.85, freshnessMax: 24 },
}

const EVIDENCE_TYPE_PROVIDER_MAP: Record<EvidenceType, string> = {
  signal: 'signals',
  document: 'documents',
  timeline: 'timeline',
  dna: 'company_dna',
  meeting: 'timeline',
  email: 'timeline',
  search: 'search',
  government: 'signals',
}

function generateId(): string {
  return 'evt_' + Date.now().toString(36) + Math.random().toString(36).substr(2, 9)
}

function normalizeText(text: string): string {
  return text
    .toLowerCase()
    .trim()
    .replace(/\s+/g, ' ')
}

function freshnessHours(timestamp: string): number {
  const now = Date.now()
  const then = new Date(timestamp).getTime()
  return (now - then) / (1000 * 60 * 60)
}

function freshnessLabel(hours: number): string {
  if (hours < 1) return 'fresh'
  if (hours < 24) return 'recent'
  if (hours < 168) return 'stale'
  return 'expired'
}

function computeFreshness(
  timestamp: string,
  freshnessMax: number,
): string {
  const hours = freshnessHours(timestamp)
  if (hours > freshnessMax) {
    return 'expired'
  }
  return freshnessLabel(hours)
}

function isStale(timestamp: string, freshnessMax: number): boolean {
  return freshnessHours(timestamp) > freshnessMax
}

function normalizeConfidence(confidence: number): number {
  return Math.max(0, Math.min(1, Math.round(confidence * 100) / 100))
}

function extractEvidenceFromRecord(
  record: Record<string, unknown>,
  type: EvidenceType,
  provider: EvidenceProvider,
): EvidenceItem {
  const description =
    (record.description as string) ||
    (record.summary as string) ||
    (record.title as string) ||
    (record.text as string) ||
    `${type} evidence`
  const source =
    (record.source as string) || provider.name
  const timestamp =
    (record.timestamp as string) ||
    (record.date as string) ||
    (record.created_at as string) ||
    new Date().toISOString()
  const severity =
    (record.severity as EvidenceItem['severity']) || undefined
  const url =
    (record.url as string) || (record.link as string) || undefined

  let confidence = provider.confidence
  if (record.confidence !== undefined) {
    confidence = Number(record.confidence) || provider.confidence
  }
  confidence = normalizeConfidence(confidence)

  if (isStale(timestamp, provider.freshnessMax)) {
    confidence = normalizeConfidence(confidence * 0.5)
  }

  const data: Record<string, unknown> = {}
  for (const [key, value] of Object.entries(record)) {
    if (
      key !== 'description' &&
      key !== 'summary' &&
      key !== 'title' &&
      key !== 'text' &&
      key !== 'source' &&
      key !== 'timestamp' &&
      key !== 'date' &&
      key !== 'created_at' &&
      key !== 'severity' &&
      key !== 'url' &&
      key !== 'link' &&
      key !== 'confidence'
    ) {
      data[key] = value
    }
  }

  return {
    id: generateId(),
    type,
    description,
    source,
    confidence,
    freshness: computeFreshness(timestamp, provider.freshnessMax),
    timestamp,
    ...(severity !== undefined && { severity }),
    ...(url !== undefined && { url }),
    ...(Object.keys(data).length > 0 && { data }),
  }
}

function deduplicate(items: EvidenceItem[]): {
  items: EvidenceItem[]
  removed: number
} {
  const map = new Map<string, EvidenceItem>()

  for (const item of items) {
    const key = `${item.type}::${normalizeText(item.description)}`
    const existing = map.get(key)

    if (!existing || item.confidence > existing.confidence) {
      map.set(key, item)
    }
  }

  return {
    items: Array.from(map.values()),
    removed: items.length - map.size,
  }
}

function rankByConfidence(items: EvidenceItem[]): EvidenceItem[] {
  return [...items].sort((a, b) => b.confidence - a.confidence)
}

export class EvidenceEngine {
  private store = new Map<string, EvidenceItem[]>()

  private tenantKey(tenantId: string, entityId: string): string {
    return `${tenantId}::${entityId}`
  }

  private storeItems(
    tenantId: string,
    entityId: string,
    items: EvidenceItem[],
  ): void {
    const key = this.tenantKey(tenantId, entityId)
    const existing = this.store.get(key) || []
    this.store.set(key, [...existing, ...items])
  }

  async collect(
    context: DecisionContext,
    sources?: EvidenceSource[],
  ): Promise<EvidenceCollectionResult> {
    const start = Date.now()
    const tenantId = context.tenantId
    const entityId = context.entityId || context.companyId || context.opportunityId || 'unknown'

    const allItems: EvidenceItem[] = []
    let totalSources = 0

    if (sources && sources.length > 0) {
      for (const source of sources) {
        totalSources++
        for (const record of source.data) {
          allItems.push(
            extractEvidenceFromRecord(record, source.type, source.provider),
          )
        }
      }
    } else {
      for (const [providerKey, provider] of Object.entries(BUILTIN_PROVIDERS)) {
        const matchingTypes = Object.entries(EVIDENCE_TYPE_PROVIDER_MAP)
          .filter(([, p]) => p === providerKey)
          .map(([t]) => t as EvidenceType)

        for (const evidenceType of matchingTypes) {
          const sourceRecord: Record<string, unknown> = {
            description: `${evidenceType} evidence for ${entityId}`,
            source: provider.name,
            timestamp: new Date().toISOString(),
            confidence: provider.confidence,
            ...(context.metadata || {}),
          }
          totalSources++
          allItems.push(
            extractEvidenceFromRecord(sourceRecord, evidenceType, provider),
          )
        }
      }
    }

    const { items: deduped, removed } = deduplicate(allItems)
    const ranked = rankByConfidence(deduped)

    this.storeItems(tenantId, entityId, ranked)

    const avgConfidence =
      ranked.length > 0
        ? normalizeConfidence(
            ranked.reduce((sum, item) => sum + item.confidence, 0) /
              ranked.length,
          )
        : 0

    return {
      items: ranked,
      deduplicated: removed,
      totalSources,
      averageConfidence: avgConfidence,
      collectionTimeMs: Date.now() - start,
    }
  }

  async getRecent(
    tenantId: string,
    entityId: string,
    limit: number = 50,
  ): Promise<EvidenceItem[]> {
    const key = this.tenantKey(tenantId, entityId)
    const items = this.store.get(key) || []
    const ranked = rankByConfidence(items)
    return ranked.slice(0, limit)
  }
}
