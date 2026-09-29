import { scoreEvidenceStrength } from '../evidence-engine'
import type { EvidenceItem, EvidenceKind } from '../contracts'
import goldenCases from '../evidence-engine/adr0113-golden.json'

type GoldenItem = {
  id: string
  source_id?: string
  evidence_kind?: EvidenceKind
  confidence: number
}

describe('ADR-0113 shared Python/TypeScript golden cases', () => {
  it.each(goldenCases.cases)('$name', (testCase) => {
    const items: EvidenceItem[] = (testCase.items as GoldenItem[]).map((item) => ({
      id: item.id,
      type: 'government',
      description: item.id,
      source: item.source_id ?? 'unkeyed',
      ...(item.source_id ? { sourceId: item.source_id } : {}),
      confidence: item.confidence,
      freshness: 'fresh',
      timestamp: '2026-09-20T00:00:00.000Z',
      ...(item.evidence_kind ? { evidenceKind: item.evidence_kind } : {}),
    }))

    const actual = scoreEvidenceStrength(items)
    expect(actual).toEqual({
      score: testCase.expected.score,
      uncappedScore: testCase.expected.uncapped_score,
      contradictionPresent: testCase.expected.contradiction_present,
      primarySourceCount: testCase.expected.primary_source_count,
      evidenceCount: testCase.expected.evidence_count,
    })
  })
})
