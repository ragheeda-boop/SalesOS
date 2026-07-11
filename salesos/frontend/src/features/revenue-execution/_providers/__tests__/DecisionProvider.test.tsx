import { render, screen, renderHook, waitFor } from '@testing-library/react'
import type { ReactNode } from 'react'

jest.mock('@salesos/decision-platform', () => {
  const mockEvaluate = jest.fn()
  const mockEvaluateBatch = jest.fn()
  const mockExplain = jest.fn()
  const mockGetHistory = jest.fn()
  const mockSubmit = jest.fn()
  const mockGetStats = jest.fn()
  const mockScore = jest.fn()

  return {
    decisionEngine: {
      evaluate: mockEvaluate,
      evaluateBatch: mockEvaluateBatch,
      explain: mockExplain,
      getHistory: mockGetHistory,
    },
    FeedbackEngine: jest.fn().mockImplementation(() => ({
      submit: mockSubmit,
      getStats: mockGetStats,
    })),
    ScoringEngine: jest.fn().mockImplementation(() => ({
      score: mockScore,
    })),
  }
})

import { DecisionProvider, useDecision } from '../DecisionProvider'

const sampleResult: DecisionResult = {
  id: 'dec-1',
  recommendation: 'follow_up',
  confidence: 0.85,
  action: 'contact_decision_maker',
  reasoning: 'ارتفاع نية الشراء',
  scores: [{ name: 'buying_intent', value: 0.85, label: 'نية الشراء', weight: 1 }],
  explainability: { factors: [{ name: 'signal', value: 0.9, description: 'قوة الإشارة', impact: 'high' }], summary: 'ملخص' },
}

const sampleContext: DecisionContext = {
  tenantId: 'tenant-1',
  actorId: 'actor-1',
  opportunityId: 'opp-1',
  entityType: 'opportunity',
}

function renderWithProvider(children: ReactNode) {
  return render(<DecisionProvider>{children}</DecisionProvider>)
}

describe('DecisionProvider', () => {
  beforeEach(() => {
    jest.clearAllMocks()
  })

  it('renders children', () => {
    renderWithProvider(<div data-testid="child">Hello</div>)
    expect(screen.getByTestId('child')).toHaveTextContent('Hello')
  })

  it('provides evaluate function', async () => {
    const { decisionEngine } = require('@salesos/decision-platform')
    decisionEngine.evaluate.mockResolvedValue(sampleResult)

    const { result } = renderHook(() => useDecision(), { wrapper: DecisionProvider })
    const output = await result.current.evaluate(sampleContext)

    expect(output).toEqual(sampleResult)
    expect(decisionEngine.evaluate).toHaveBeenCalledWith(sampleContext)
  })

  it('provides evaluateBatch function', async () => {
    const { decisionEngine } = require('@salesos/decision-platform')
    decisionEngine.evaluateBatch.mockResolvedValue([sampleResult])

    const { result } = renderHook(() => useDecision(), { wrapper: DecisionProvider })
    const output = await result.current.evaluateBatch([sampleContext])

    expect(output).toEqual([sampleResult])
    expect(decisionEngine.evaluateBatch).toHaveBeenCalledWith([sampleContext])
  })

  it('provides getRecommendation with correct context', async () => {
    const { decisionEngine } = require('@salesos/decision-platform')
    decisionEngine.evaluate.mockResolvedValue(sampleResult)

    const { result } = renderHook(() => useDecision(), { wrapper: DecisionProvider })
    const output = await result.current.getRecommendation('opp-1', 'tenant-1', 'actor-1')

    expect(output).toEqual(sampleResult)
    expect(decisionEngine.evaluate).toHaveBeenCalledWith({
      tenantId: 'tenant-1',
      actorId: 'actor-1',
      opportunityId: 'opp-1',
      entityType: 'opportunity',
    })
  })

  it('provides getScores extracting scores from result', async () => {
    const { decisionEngine } = require('@salesos/decision-platform')
    decisionEngine.evaluate.mockResolvedValue(sampleResult)

    const { result } = renderHook(() => useDecision(), { wrapper: DecisionProvider })
    const output = await result.current.getScores('entity-1', 'opportunity', 'tenant-1', 'actor-1')

    expect(output).toEqual(sampleResult.scores)
  })

  it('provides getHistory function', async () => {
    const { decisionEngine } = require('@salesos/decision-platform')
    const historyItems = [{ id: 'hist-1', decisionId: 'dec-1', action: 'follow_up', outcome: 'accepted', timestamp: '2026-07-10T10:00:00Z' }]
    decisionEngine.getHistory.mockResolvedValue(historyItems)

    const { result } = renderHook(() => useDecision(), { wrapper: DecisionProvider })
    const output = await result.current.getHistory('tenant-1', 10)

    expect(output).toEqual(historyItems)
    expect(decisionEngine.getHistory).toHaveBeenCalledWith('tenant-1', 10)
  })

  it('provides getExplainability function', async () => {
    const { decisionEngine } = require('@salesos/decision-platform')
    decisionEngine.explain.mockResolvedValue(sampleResult.explainability)

    const { result } = renderHook(() => useDecision(), { wrapper: DecisionProvider })
    const output = await result.current.getExplainability('dec-1')

    expect(output).toEqual(sampleResult.explainability)
    expect(decisionEngine.explain).toHaveBeenCalledWith('dec-1')
  })

  it('provides submitFeedback function', async () => {
    const { FeedbackEngine } = require('@salesos/decision-platform')
    const feedbackResponse = { id: 'fb-1', accepted: true }
    const mockInstance = FeedbackEngine.mock.instances[0]
    mockInstance.submit.mockResolvedValue(feedbackResponse)

    const { result } = renderHook(() => useDecision(), { wrapper: DecisionProvider })
    const feedback = { id: 'fb-1', decisionId: 'dec-1', outcome: 'accepted' as const, revenueImpact: 50000, createdAt: '2026-07-10T10:00:00Z' }
    const output = await result.current.submitFeedback(feedback)

    expect(output).toEqual(feedbackResponse)
    expect(mockInstance.submit).toHaveBeenCalledWith(feedback)
  })

  it('provides getFeedbackStats function', async () => {
    const { FeedbackEngine } = require('@salesos/decision-platform')
    const stats = { total: 10, accepted: 7, rejected: 2, ignored: 1, acceptanceRate: 0.7, totalRevenueImpact: 350000, averageTimeToExecution: null }
    const mockInstance = FeedbackEngine.mock.instances[0]
    mockInstance.getStats.mockResolvedValue(stats)

    const { result } = renderHook(() => useDecision(), { wrapper: DecisionProvider })
    const output = await result.current.getFeedbackStats('tenant-1')

    expect(output).toEqual(stats)
    expect(mockInstance.getStats).toHaveBeenCalledWith('tenant-1')
  })

  it('provides score function', async () => {
    const { ScoringEngine } = require('@salesos/decision-platform')
    const scoreResult = { name: 'custom', value: 0.75, label: 'مخصص', weight: 1 }
    const mockInstance = ScoringEngine.mock.instances[0]
    mockInstance.score.mockReturnValue(scoreResult)

    const { result } = renderHook(() => useDecision(), { wrapper: DecisionProvider })
    const output = result.current.score('buying_intent' as any, { signal: 0.8, engagement: 0.7 }, { source: 'test' })

    expect(output).toEqual(scoreResult)
    expect(mockInstance.score).toHaveBeenCalledWith('buying_intent', { signal: 0.8, engagement: 0.7 }, { source: 'test' })
  })

  it('provides evaluate without tenant context', async () => {
    const { decisionEngine } = require('@salesos/decision-platform')
    decisionEngine.evaluate.mockResolvedValue(sampleResult)

    const { result } = renderHook(() => useDecision(), { wrapper: DecisionProvider })
    const ctx = { entityType: 'company', actorId: 'actor-1' }
    const output = await result.current.evaluate(ctx as any)

    expect(output).toEqual(sampleResult)
    expect(decisionEngine.evaluate).toHaveBeenCalledWith(ctx)
  })
})

describe('useDecision outside provider', () => {
  it('throws error when used without DecisionProvider', () => {
    expect(() => renderHook(() => useDecision())).toThrow(
      'useDecision must be used within a DecisionProvider',
    )
  })
})
