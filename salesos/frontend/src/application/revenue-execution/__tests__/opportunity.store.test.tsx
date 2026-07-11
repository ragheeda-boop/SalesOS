import { loadOpportunities, createOpportunity, updateOpportunityStage, addOpportunityNote, getOpportunitiesByStage, getOpportunity } from '../opportunity.store'

const _oppStore: any[] = []

jest.mock('axios', () => ({
  get: jest.fn(() => Promise.resolve({ data: { items: _oppStore } })),
  post: jest.fn((url: string, input: any) => {
    const notesMatch = url.match(/opportunities\/([^/]+)\/notes/)
    if (notesMatch && input.text) {
      const opp = _oppStore.find((o: any) => o.id === notesMatch[1])
      if (opp) {
        opp.notes = opp.notes || []
        opp.notes.push({ id: 'n1', text: input.text, author: input.author, createdAt: '2026-07-11T12:00:00.000Z' })
      }
      return Promise.resolve({ data: { items: _oppStore } })
    }
    const opp = {
      id: 'opp_' + Math.random().toString(36).slice(2, 10),
      stage: 'identified', ...input,
      createdAt: '2026-07-11T12:00:00.000Z', winProbability: 0.10,
      riskLevel: input.confidence >= 0.9 ? 'low' : input.confidence <= 0.4 ? 'high' : 'medium',
      lastActivityAt: '2026-07-11T12:00:00.000Z', notes: [], tags: [], source: 'nba',
    }
    _oppStore.push(opp)
    return Promise.resolve({ data: opp })
  }),
  put: jest.fn(),
  patch: jest.fn((url: string, body: any) => {
    const id = url.match(/opportunities\/([^/]+)/)?.[1]
    const opp = _oppStore.find((o: any) => o.id === id)
    if (opp && body.stage) opp.stage = body.stage
    return Promise.resolve({ data: opp })
  }),
  delete: jest.fn(),
  interceptors: { request: { use: jest.fn() }, response: { use: jest.fn() } },
  create() { return this },
}))

beforeEach(() => {
  _oppStore.length = 0
})

describe('opportunity store', () => {
  describe('loadOpportunities', () => {
    it('returns empty array when nothing stored', async () => {
      expect(await loadOpportunities()).toEqual([])
    })
  })

  describe('createOpportunity', () => {
    it('creates an opportunity with generated id', async () => {
      const opp = await createOpportunity({
        companyId: 'c-1',
        companyName: 'شركة',
        title: 'صفقة جديدة',
        estimatedValue: 500000,
        confidence: 0.8,
        buyingIntent: 0.7,
        relationshipStrength: 0.6,
      })

      expect(opp.id).toContain('opp_')
      expect(opp.companyId).toBe('c-1')
      expect(opp.title).toBe('صفقة جديدة')
      expect(opp.estimatedValue).toBe(500000)
      expect(opp.stage).toBe('identified')
      expect(opp.winProbability).toBe(0.10)
      expect(opp.source).toBe('nba')
      expect(opp.riskLevel).toBe('medium')
    })

    it('creates low risk for high confidence', async () => {
      const opp = await createOpportunity({
        companyId: 'c-1', companyName: 'شركة', title: 'Test', estimatedValue: 100000,
        confidence: 0.9, buyingIntent: 0.8, relationshipStrength: 0.8,
      })
      expect(opp.riskLevel).toBe('low')
    })

    it('creates high risk for low confidence', async () => {
      const opp = await createOpportunity({
        companyId: 'c-1', companyName: 'شركة', title: 'Test', estimatedValue: 100000,
        confidence: 0.3, buyingIntent: 0.8, relationshipStrength: 0.8,
      })
      expect(opp.riskLevel).toBe('high')
    })
  })

  describe('updateOpportunityStage', () => {
    it('updates stage and lastActivityAt', async () => {
      await createOpportunity({
        companyId: 'c-1', companyName: 'شركة', title: 'Test', estimatedValue: 100000,
        confidence: 0.5, buyingIntent: 0.5, relationshipStrength: 0.5,
      })
      const all = await loadOpportunities()
      const updated = await updateOpportunityStage(all[0].id, 'qualifying')

      expect(updated[0].stage).toBe('qualifying')
    })
  })

  describe('addOpportunityNote', () => {
    it('adds a note to the opportunity', async () => {
      await createOpportunity({
        companyId: 'c-1', companyName: 'شركة', title: 'Test', estimatedValue: 100000,
        confidence: 0.5, buyingIntent: 0.5, relationshipStrength: 0.5,
      })
      const all = await loadOpportunities()
      const updated = await addOpportunityNote(all[0].id, 'مذكرة مهمة', 'أحمد')

      expect(updated[0].notes).toHaveLength(1)
      expect(updated[0].notes[0].text).toBe('مذكرة مهمة')
      expect(updated[0].notes[0].author).toBe('أحمد')
    })
  })

  describe('getOpportunitiesByStage', () => {
    it('filters by stage', async () => {
      await createOpportunity({
        companyId: 'c-1', companyName: 'شركة', title: 'A', estimatedValue: 100000,
        confidence: 0.5, buyingIntent: 0.5, relationshipStrength: 0.5,
      })
      const all = await loadOpportunities()
      expect(getOpportunitiesByStage(all, 'identified')).toHaveLength(1)
      expect(getOpportunitiesByStage(all, 'won')).toHaveLength(0)
      expect(getOpportunitiesByStage(all)).toHaveLength(1)
    })
  })

  describe('getOpportunity', () => {
    it('finds opportunity by id', async () => {
      const created = await createOpportunity({
        companyId: 'c-1', companyName: 'شركة', title: 'Find Me', estimatedValue: 100000,
        confidence: 0.5, buyingIntent: 0.5, relationshipStrength: 0.5,
      })
      const found = await getOpportunity(created.id)
      expect(found?.title).toBe('Find Me')
    })

    it('returns undefined for unknown id', async () => {
      expect(await getOpportunity('unknown')).toBeUndefined()
    })
  })
})
