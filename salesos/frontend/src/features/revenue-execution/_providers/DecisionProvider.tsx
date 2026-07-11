'use client'

import { createContext, useContext, useCallback, useMemo } from 'react'
import { decisionEngine, FeedbackEngine, ScoringEngine } from '@salesos/decision-platform'
import type {
  DecisionContext,
  DecisionResult,
  DecisionHistoryItem,
  Explainability,
  Feedback,
  Score,
  ScoreType,
} from '@salesos/decision-platform'

interface DecisionContextValue {
  evaluate: (context: DecisionContext) => Promise<DecisionResult>
  evaluateBatch: (contexts: DecisionContext[]) => Promise<DecisionResult[]>
  getRecommendation: (opportunityId: string, tenantId: string, actorId: string) => Promise<DecisionResult>
  getScores: (entityId: string, entityType: DecisionContext['entityType'], tenantId: string, actorId: string) => Promise<Score[]>
  getHistory: (tenantId: string, limit?: number) => Promise<DecisionHistoryItem[]>
  getExplainability: (decisionId: string) => Promise<Explainability | null>
  submitFeedback: (feedback: Feedback) => Promise<{ id: string; accepted: boolean }>
  getFeedbackStats: (tenantId: string) => Promise<FeedbackStats>
  score: (type: ScoreType, factors: Record<string, number>, metadata?: Record<string, unknown>) => Score
}

interface FeedbackStats {
  total: number
  accepted: number
  rejected: number
  ignored: number
  acceptanceRate: number
  totalRevenueImpact: number
  averageTimeToExecution: number | null
}

const DecisionCtx = createContext<DecisionContextValue | null>(null)

const feedbackEngine = new FeedbackEngine()
const scoringEngine = new ScoringEngine()

export function DecisionProvider({ children }: { children: React.ReactNode }) {
  const evaluate = useCallback(async (context: DecisionContext) => {
    return decisionEngine.evaluate(context)
  }, [])

  const evaluateBatch = useCallback(async (contexts: DecisionContext[]) => {
    return decisionEngine.evaluateBatch(contexts)
  }, [])

  const getRecommendation = useCallback(async (
    opportunityId: string,
    tenantId: string,
    actorId: string,
  ) => {
    return decisionEngine.evaluate({
      tenantId,
      actorId,
      opportunityId,
      entityType: 'opportunity',
    })
  }, [])

  const getScores = useCallback(async (
    entityId: string,
    entityType: DecisionContext['entityType'],
    tenantId: string,
    actorId: string,
  ) => {
    const result = await decisionEngine.evaluate({
      tenantId,
      actorId,
      entityId,
      entityType,
    })
    return result.scores
  }, [])

  const getHistory = useCallback(async (tenantId: string, limit?: number) => {
    return decisionEngine.getHistory(tenantId, limit)
  }, [])

  const getExplainability = useCallback(async (decisionId: string) => {
    return decisionEngine.explain(decisionId)
  }, [])

  const submitFeedback = useCallback(async (feedback: Feedback) => {
    return feedbackEngine.submit(feedback)
  }, [])

  const getFeedbackStats = useCallback(async (tenantId: string) => {
    return feedbackEngine.getStats(tenantId)
  }, [])

  const score = useCallback((
    type: ScoreType,
    factors: Record<string, number>,
    metadata?: Record<string, unknown>,
  ) => {
    return scoringEngine.score(type, factors, metadata)
  }, [])

  const value = useMemo<DecisionContextValue>(() => ({
    evaluate,
    evaluateBatch,
    getRecommendation,
    getScores,
    getHistory,
    getExplainability,
    submitFeedback,
    getFeedbackStats,
    score,
  }), [
    evaluate,
    evaluateBatch,
    getRecommendation,
    getScores,
    getHistory,
    getExplainability,
    submitFeedback,
    getFeedbackStats,
    score,
  ])

  return (
    <DecisionCtx.Provider value={value}>
      {children}
    </DecisionCtx.Provider>
  )
}

export function useDecision(): DecisionContextValue {
  const ctx = useContext(DecisionCtx)
  if (!ctx) {
    throw new Error('useDecision must be used within a DecisionProvider')
  }
  return ctx
}
