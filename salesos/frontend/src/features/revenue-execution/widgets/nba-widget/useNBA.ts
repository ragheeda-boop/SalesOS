import { useCallback } from 'react'
import axios from 'axios'

export interface NBARecommendation {
  id: string
  opportunityId: string
  action: string
  reason: string
  confidence: number
  confidenceLabel: 'high' | 'medium' | 'low'
  source: 'rule' | 'ai' | 'hybrid'
  alternatives: { action: string; reason: string; confidence: number }[]
  evidence: { type: string; description: string; source: string; confidence: number }[]
  potentialRisks: { type: string; level: string; description: string }[]
  status: 'pending' | 'accepted' | 'dismissed' | 'completed'
  createdAt: string
  updatedAt: string
}

export function useNBA(opportunityId: string) {
  const getNBA = useCallback(async (): Promise<NBARecommendation | null> => {
    try {
      const { data } = await axios.get(`/api/v1/revenue/opportunities/${opportunityId}/nba`)
      return data
    } catch {
      return null
    }
  }, [opportunityId])

  const refreshNBA = useCallback(async (): Promise<NBARecommendation | null> => {
    try {
      const { data } = await axios.post(`/api/v1/revenue/opportunities/${opportunityId}/nba/refresh`)
      return data
    } catch {
      return null
    }
  }, [opportunityId])

  const acceptNBA = useCallback(async (nbaId: string) => {
    await axios.post(`/api/v1/revenue/opportunities/${opportunityId}/nba/feedback`, {
      nba_id: nbaId,
      action: 'accepted',
    })
  }, [opportunityId])

  const dismissNBA = useCallback(async (nbaId: string, reason?: string) => {
    await axios.post(`/api/v1/revenue/opportunities/${opportunityId}/nba/feedback`, {
      nba_id: nbaId,
      action: 'dismissed',
      reason,
    })
  }, [opportunityId])

  return { getNBA, refreshNBA, acceptNBA, dismissNBA }
}
