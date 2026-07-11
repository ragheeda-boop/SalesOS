import { loadOpportunities, createOpportunity, updateOpportunityStage, addOpportunityNote, getOpportunitiesByStage, getOpportunity } from '../opportunity.store'

describe('opportunity store', () => {
  beforeEach(() => {
    localStorage.clear()
    jest.useFakeTimers()
    jest.setSystemTime(new Date('2026-07-11T12:00:00Z'))
  })

  afterEach(() => {
    jest.useRealTimers()
  })

  describe('loadOpportunities', () => {
    it('returns empty array when nothing stored', () => {
      expect(loadOpportunities()).toEqual([])
    })
  })

  describe('createOpportunity', () => {
    it('creates an opportunity with generated id', () => {
      const opp = createOpportunity({
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

    it('creates low risk for high confidence', () => {
      const opp = createOpportunity({
        companyId: 'c-1', companyName: 'شركة', title: 'Test', estimatedValue: 100000,
        confidence: 0.9, buyingIntent: 0.8, relationshipStrength: 0.8,
      })
      expect(opp.riskLevel).toBe('low')
    })

    it('creates high risk for low confidence', () => {
      const opp = createOpportunity({
        companyId: 'c-1', companyName: 'شركة', title: 'Test', estimatedValue: 100000,
        confidence: 0.3, buyingIntent: 0.8, relationshipStrength: 0.8,
      })
      expect(opp.riskLevel).toBe('high')
    })
  })

  describe('updateOpportunityStage', () => {
    it('updates stage and lastActivityAt', () => {
      createOpportunity({
        companyId: 'c-1', companyName: 'شركة', title: 'Test', estimatedValue: 100000,
        confidence: 0.5, buyingIntent: 0.5, relationshipStrength: 0.5,
      })
      const opp = loadOpportunities()[0]
      const updated = updateOpportunityStage(opp.id, 'qualifying')

      expect(updated[0].stage).toBe('qualifying')
      expect(updated[0].stageChangedAt).toBe('2026-07-11T12:00:00.000Z')
      expect(updated[0].lastActivityAt).toBe('2026-07-11T12:00:00.000Z')
    })
  })

  describe('addOpportunityNote', () => {
    it('adds a note to the opportunity', () => {
      createOpportunity({
        companyId: 'c-1', companyName: 'شركة', title: 'Test', estimatedValue: 100000,
        confidence: 0.5, buyingIntent: 0.5, relationshipStrength: 0.5,
      })
      const opp = loadOpportunities()[0]
      const updated = addOpportunityNote(opp.id, 'مذكرة مهمة', 'أحمد')

      expect(updated[0].notes).toHaveLength(1)
      expect(updated[0].notes[0].text).toBe('مذكرة مهمة')
      expect(updated[0].notes[0].author).toBe('أحمد')
    })
  })

  describe('getOpportunitiesByStage', () => {
    it('filters by stage', () => {
      createOpportunity({
        companyId: 'c-1', companyName: 'شركة', title: 'A', estimatedValue: 100000,
        confidence: 0.5, buyingIntent: 0.5, relationshipStrength: 0.5,
      })
      const all = loadOpportunities()
      expect(getOpportunitiesByStage(all, 'identified')).toHaveLength(1)
      expect(getOpportunitiesByStage(all, 'won')).toHaveLength(0)
      expect(getOpportunitiesByStage(all)).toHaveLength(1)
    })
  })

  describe('getOpportunity', () => {
    it('finds opportunity by id', () => {
      const created = createOpportunity({
        companyId: 'c-1', companyName: 'شركة', title: 'Find Me', estimatedValue: 100000,
        confidence: 0.5, buyingIntent: 0.5, relationshipStrength: 0.5,
      })
      const found = getOpportunity(created.id)
      expect(found?.title).toBe('Find Me')
    })

    it('returns undefined for unknown id', () => {
      expect(getOpportunity('unknown')).toBeUndefined()
    })
  })
})
