import { mapSearchResult, mapSearchResults, groupResultsByType } from '../result-mapper'
import type { RawSearchResult } from '../result-mapper'

const rawResult: RawSearchResult = {
  id: 'comp_1',
  entity_type: 'company',
  title: 'أرامكو السعودية',
  subtitle: 'شركة نفط وغاز',
  description: 'أكبر شركة نفط في العالم',
  score: 0.95,
  confidence: 0.92,
  source: 'postgresql',
  updated_at: '2026-07-10T00:00:00.000Z',
}

describe('mapSearchResult', () => {
  it('maps core fields', () => {
    const r = mapSearchResult(rawResult)
    expect(r.id).toBe('comp_1')
    expect(r.entityType).toBe('company')
    expect(r.title).toBe('أرامكو السعودية')
    expect(r.score).toBe(0.95)
  })

  it('maps highlights', () => {
    const r = mapSearchResult({ ...rawResult, highlights: [{ field: 'title', text: 'أرامكو', snippets: ['أرامكو'] }] })
    expect(r.highlights).toHaveLength(1)
    expect(r.highlights[0].field).toBe('title')
  })

  it('maps badges', () => {
    const r = mapSearchResult({ ...rawResult, badges: [{ label: 'نشط', variant: 'success' }] })
    expect(r.badges).toHaveLength(1)
    expect(r.badges[0].label).toBe('نشط')
    expect(r.badges[0].variant).toBe('success')
  })

  it('sanitizes badge variant', () => {
    const r = mapSearchResult({ ...rawResult, badges: [{ label: 'test', variant: 'invalid' }] })
    expect(r.badges[0].variant).toBe('neutral')
  })

  it('maps actions', () => {
    const r = mapSearchResult({ ...rawResult, actions: [{ id: 'view', label: 'View', handler: 'navigate' }] })
    expect(r.actions).toHaveLength(1)
  })

  it('maps relationships', () => {
    const r = mapSearchResult({ ...rawResult, relationships: [{ id: 'rel_1', type: 'supplier', label: 'مورد', direction: 'outbound' }] })
    expect(r.relationships).toHaveLength(1)
    expect(r.relationships![0].direction).toBe('outbound')
  })

  it('sanitizes relationship direction', () => {
    const r = mapSearchResult({ ...rawResult, relationships: [{ id: 'rel_1', type: 'supplier', label: 'مورد', direction: 'invalid' }] })
    expect(r.relationships![0].direction).toBe('bidirectional')
  })

  it('handles missing optional fields', () => {
    const r = mapSearchResult(rawResult)
    expect(r.highlights).toEqual([])
    expect(r.badges).toEqual([])
    expect(r.actions).toEqual([])
    expect(r.thumbnail).toBeUndefined()
  })
})

describe('mapSearchResults', () => {
  it('maps array of results', () => {
    const results = mapSearchResults([rawResult, { ...rawResult, id: 'comp_2' }])
    expect(results).toHaveLength(2)
  })
})

describe('groupResultsByType', () => {
  it('groups results by entity type', () => {
    const results = mapSearchResults([
      rawResult,
      { ...rawResult, id: 'comp_2', entity_type: 'person' },
      { ...rawResult, id: 'comp_3', entity_type: 'company' },
    ])
    const groups = groupResultsByType(results)
    expect(groups.company).toHaveLength(2)
    expect(groups.person).toHaveLength(1)
  })
})
