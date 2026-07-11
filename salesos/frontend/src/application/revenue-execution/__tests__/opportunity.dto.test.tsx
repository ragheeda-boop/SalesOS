import { calculateWinProbability, STAGE_WEIGHT, STAGE_LABEL } from '../opportunity.dto'

describe('STAGE_WEIGHT', () => {
  it('has correct weights', () => {
    expect(STAGE_WEIGHT.identified).toBe(0.10)
    expect(STAGE_WEIGHT.qualifying).toBe(0.25)
    expect(STAGE_WEIGHT.developing).toBe(0.45)
    expect(STAGE_WEIGHT.proposing).toBe(0.65)
    expect(STAGE_WEIGHT.negotiating).toBe(0.80)
    expect(STAGE_WEIGHT.closing).toBe(0.90)
    expect(STAGE_WEIGHT.won).toBe(1.0)
    expect(STAGE_WEIGHT.lost).toBe(0)
  })
})

describe('STAGE_LABEL', () => {
  it('has Arabic labels for all stages', () => {
    expect(STAGE_LABEL.identified).toBe('تم التحديد')
    expect(STAGE_LABEL.won).toBe('فوز')
    expect(STAGE_LABEL.lost).toBe('خسارة')
  })
})

describe('calculateWinProbability', () => {
  it('returns 1 for max values', () => {
    const prob = calculateWinProbability({
      stage: 'won',
      buyingIntent: 1,
      relationshipStrength: 1,
      nbaConfidence: 1,
      signalActivity: 1,
    })
    expect(prob).toBe(1)
  })

  it('returns 0.30 * stage weight for zero factors', () => {
    const prob = calculateWinProbability({
      stage: 'identified',
      buyingIntent: 0,
      relationshipStrength: 0,
      nbaConfidence: 0,
      signalActivity: 0,
    })
    expect(prob).toBeCloseTo(0.30 * 0.10, 5)
  })

  it('increases probability with higher buying intent', () => {
    const low = calculateWinProbability({
      stage: 'qualifying', buyingIntent: 0.2, relationshipStrength: 0.5, nbaConfidence: 0.5, signalActivity: 0.5,
    })
    const high = calculateWinProbability({
      stage: 'qualifying', buyingIntent: 0.9, relationshipStrength: 0.5, nbaConfidence: 0.5, signalActivity: 0.5,
    })
    expect(high).toBeGreaterThan(low)
  })

  it('scales with stage progression', () => {
    const early = calculateWinProbability({
      stage: 'identified', buyingIntent: 0.5, relationshipStrength: 0.5, nbaConfidence: 0.5, signalActivity: 0.5,
    })
    const late = calculateWinProbability({
      stage: 'negotiating', buyingIntent: 0.5, relationshipStrength: 0.5, nbaConfidence: 0.5, signalActivity: 0.5,
    })
    expect(late).toBeGreaterThan(early)
  })
})
