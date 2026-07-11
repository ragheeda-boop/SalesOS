import { renderHook, waitFor } from '@testing-library/react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import type { ReactNode } from 'react'

jest.mock('@/lib/api')
jest.mock('@/lib/hooks/useTenant')

import api from '@/lib/api'
import { getTenantId } from '@/lib/hooks/useTenant'
import {
  useDecisionEvaluate,
  useDecisionExplain,
  useDecisionHistory,
  useDecisionRecommendations,
  useDecisionScores,
  useDecisionEvidence,
  useDecisionFeedback,
  useDecisionFeedbackStats,
} from '@/lib/decisionQueries'

const mockedApi = api as jest.Mocked<typeof api>
const mockedGetTenantId = getTenantId as jest.MockedFunction<typeof getTenantId>

const sampleDecisionResult = {
  id: 'dec-1',
  recommendation: 'follow_up',
  confidence: 0.85,
  action: 'contact_decision_maker',
  reasoning: 'ارتفاع نية الشراء',
  scores: [
    { name: 'buying_intent', value: 0.85, label: 'نية الشراء', weight: 1 },
  ],
  explainability: {
    factors: [
      { name: 'signal_strength', value: 0.9, description: 'قوة الإشارة', impact: 'high' },
    ],
    summary: 'توصية بناءً على إشارات شرائية قوية',
  },
}

const sampleHistory = {
  items: [
    {
      id: 'hist-1',
      decisionId: 'dec-1',
      action: 'follow_up',
      outcome: 'accepted',
      timestamp: '2026-07-10T10:00:00Z',
    },
  ],
  total: 1,
}

const sampleRecommendations = [
  {
    id: 'rec-1',
    action: 'schedule_meeting',
    reason: 'ارتفاع نية الشراء',
    confidence: 0.85,
    priority: 'high',
  },
]

const sampleScores = [
  { name: 'buying_intent', value: 0.85, label: 'نية الشراء', weight: 1 },
  { name: 'engagement', value: 0.7, label: 'التفاعل', weight: 0.8 },
]

const sampleEvidence = [
  {
    type: 'signal',
    description: 'إشارة شرائية قوية',
    source: 'LinkedIn',
    confidence: 0.9,
    timestamp: '2026-07-10T10:00:00Z',
  },
]

const sampleFeedback = {
  id: 'fb-1',
  decisionId: 'dec-1',
  outcome: 'accepted' as const,
  revenueImpact: 50000,
  createdAt: '2026-07-10T10:00:00Z',
}

const sampleFeedbackStats = {
  totalFeedback: 10,
  acceptanceRate: 0.7,
  rejectionRate: 0.2,
  avgRevenueImpact: 45000,
  byAction: {
    follow_up: { accepted: 5, rejected: 1, ignored: 1 },
    proposal: { accepted: 2, rejected: 1, ignored: 0 },
  },
}

function createWrapper() {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false, gcTime: 0 } },
  })
  return function Wrapper({ children }: { children: ReactNode }) {
    return (
      <QueryClientProvider client={queryClient}>
        {children}
      </QueryClientProvider>
    )
  }
}

describe('useDecisionEvaluate', () => {
  beforeEach(() => {
    jest.clearAllMocks()
    mockedGetTenantId.mockReturnValue('tenant-1')
  })

  it('calls the evaluate API and returns result', async () => {
    mockedApi.post.mockResolvedValue({ data: sampleDecisionResult })
    const { result } = renderHook(() => useDecisionEvaluate(), { wrapper: createWrapper() })

    result.current.mutate({ context: { tenantId: 'tenant-1', entityType: 'opportunity' } })

    await waitFor(() => {
      expect(result.current.data).toEqual(sampleDecisionResult)
    })
    expect(mockedApi.post).toHaveBeenCalledWith(
      '/api/v1/decision/evaluate',
      { context: { tenantId: 'tenant-1', entityType: 'opportunity' } },
      { headers: { 'X-Tenant-Id': 'tenant-1' } },
    )
  })

  it('includes tenant header in request', async () => {
    mockedApi.post.mockResolvedValue({ data: sampleDecisionResult })
    const { result } = renderHook(() => useDecisionEvaluate(), { wrapper: createWrapper() })

    result.current.mutate({ context: { tenantId: 'tenant-1', entityType: 'opportunity' } })

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true)
    })
    expect(mockedApi.post.mock.calls[0][2]?.headers).toHaveProperty('X-Tenant-Id', 'tenant-1')
  })

  it('propagates errors from API', async () => {
    mockedApi.post.mockRejectedValue(new Error('API failure'))
    const { result } = renderHook(() => useDecisionEvaluate(), { wrapper: createWrapper() })

    result.current.mutate({ context: { tenantId: 'tenant-1', entityType: 'opportunity' } })

    await waitFor(() => {
      expect(result.current.isError).toBe(true)
    })
  })
})

describe('useDecisionExplain', () => {
  beforeEach(() => {
    jest.clearAllMocks()
    mockedGetTenantId.mockReturnValue('tenant-1')
  })

  it('fetches explanation when decisionId is provided', async () => {
    mockedApi.get.mockResolvedValue({ data: sampleDecisionResult.explainability })
    const { result } = renderHook(() => useDecisionExplain('dec-1'), { wrapper: createWrapper() })

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true)
    })
    expect(result.current.data).toEqual(sampleDecisionResult.explainability)
    expect(mockedApi.get).toHaveBeenCalledWith(
      '/api/v1/decision/dec-1/explain',
      { headers: { 'X-Tenant-Id': 'tenant-1' } },
    )
  })

  it('does not fetch when decisionId is empty', () => {
    const { result } = renderHook(() => useDecisionExplain(''), { wrapper: createWrapper() })
    expect(result.current.fetchStatus).toBe('idle')
  })
})

describe('useDecisionHistory', () => {
  beforeEach(() => {
    jest.clearAllMocks()
    mockedGetTenantId.mockReturnValue('tenant-1')
  })

  it('fetches decision history', async () => {
    mockedApi.get.mockResolvedValue({ data: sampleHistory })
    const { result } = renderHook(() => useDecisionHistory(20), { wrapper: createWrapper() })

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true)
    })
    expect(result.current.data).toEqual(sampleHistory)
    expect(mockedApi.get).toHaveBeenCalledWith(
      '/api/v1/decision/history',
      { params: { limit: 20 }, headers: { 'X-Tenant-Id': 'tenant-1' } },
    )
  })

  it('has a refetchInterval of 60s', () => {
    const { result } = renderHook(() => useDecisionHistory(), { wrapper: createWrapper() })
    expect(result.current.data).toBeUndefined()
  })
})

describe('useDecisionRecommendations', () => {
  beforeEach(() => {
    jest.clearAllMocks()
    mockedGetTenantId.mockReturnValue('tenant-1')
  })

  it('fetches recommendations for entity', async () => {
    mockedApi.get.mockResolvedValue({ data: sampleRecommendations })
    const { result } = renderHook(
      () => useDecisionRecommendations('entity-1', 'opportunity'),
      { wrapper: createWrapper() },
    )

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true)
    })
    expect(result.current.data).toEqual(sampleRecommendations)
    expect(mockedApi.get).toHaveBeenCalledWith(
      '/api/v1/decision/recommendations',
      { params: { entity_id: 'entity-1', entity_type: 'opportunity' }, headers: { 'X-Tenant-Id': 'tenant-1' } },
    )
  })

  it('has a refetchInterval of 60s', () => {
    const { result } = renderHook(
      () => useDecisionRecommendations('entity-1', 'opportunity'),
      { wrapper: createWrapper() },
    )
    expect(result.current.data).toBeUndefined()
  })
})

describe('useDecisionScores', () => {
  beforeEach(() => {
    jest.clearAllMocks()
    mockedGetTenantId.mockReturnValue('tenant-1')
  })

  it('fetches scores when both entityId and entityType are provided', async () => {
    mockedApi.get.mockResolvedValue({ data: sampleScores })
    const { result } = renderHook(
      () => useDecisionScores('entity-1', 'opportunity'),
      { wrapper: createWrapper() },
    )

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true)
    })
    expect(result.current.data).toEqual(sampleScores)
  })

  it('does not fetch when entityId is empty', () => {
    const { result } = renderHook(
      () => useDecisionScores('', 'opportunity'),
      { wrapper: createWrapper() },
    )
    expect(result.current.fetchStatus).toBe('idle')
  })

  it('does not fetch when entityType is empty', () => {
    const { result } = renderHook(
      () => useDecisionScores('entity-1', ''),
      { wrapper: createWrapper() },
    )
    expect(result.current.fetchStatus).toBe('idle')
  })
})

describe('useDecisionEvidence', () => {
  beforeEach(() => {
    jest.clearAllMocks()
    mockedGetTenantId.mockReturnValue('tenant-1')
  })

  it('fetches evidence when both IDs are provided', async () => {
    mockedApi.get.mockResolvedValue({ data: sampleEvidence })
    const { result } = renderHook(
      () => useDecisionEvidence('entity-1', 'opportunity'),
      { wrapper: createWrapper() },
    )

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true)
    })
    expect(result.current.data).toEqual(sampleEvidence)
  })

  it('does not fetch when missing ID', () => {
    const { result } = renderHook(
      () => useDecisionEvidence('', 'opportunity'),
      { wrapper: createWrapper() },
    )
    expect(result.current.fetchStatus).toBe('idle')
  })
})

describe('useDecisionFeedback', () => {
  beforeEach(() => {
    jest.clearAllMocks()
    mockedGetTenantId.mockReturnValue('tenant-1')
  })

  it('submits feedback and invalidates queries on success', async () => {
    mockedApi.post.mockResolvedValue({ data: sampleFeedback })
    const { result } = renderHook(() => useDecisionFeedback(), { wrapper: createWrapper() })

    result.current.mutate({
      decisionId: 'dec-1',
      outcome: 'accepted',
      revenueImpact: 50000,
    })

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true)
    })
    expect(result.current.data).toEqual(sampleFeedback)
    expect(mockedApi.post).toHaveBeenCalledWith(
      '/api/v1/decision/feedback',
      { decision_id: 'dec-1', outcome: 'accepted', revenueImpact: 50000 },
      { headers: { 'X-Tenant-Id': 'tenant-1' } },
    )
  })

  it('includes reason and timeToExecution in payload', async () => {
    mockedApi.post.mockResolvedValue({ data: sampleFeedback })
    const { result } = renderHook(() => useDecisionFeedback(), { wrapper: createWrapper() })

    result.current.mutate({
      decisionId: 'dec-2',
      outcome: 'rejected',
      reason: 'توصية غير مناسبة',
      timeToExecution: 3600,
    })

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true)
    })
    expect(mockedApi.post).toHaveBeenCalledWith(
      '/api/v1/decision/feedback',
      { decision_id: 'dec-2', outcome: 'rejected', reason: 'توصية غير مناسبة', timeToExecution: 3600 },
      { headers: { 'X-Tenant-Id': 'tenant-1' } },
    )
  })
})

describe('useDecisionFeedbackStats', () => {
  beforeEach(() => {
    jest.clearAllMocks()
    mockedGetTenantId.mockReturnValue('tenant-1')
  })

  it('fetches feedback statistics', async () => {
    mockedApi.get.mockResolvedValue({ data: sampleFeedbackStats })
    const { result } = renderHook(() => useDecisionFeedbackStats(), { wrapper: createWrapper() })

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true)
    })
    expect(result.current.data).toEqual(sampleFeedbackStats)
    expect(mockedApi.get).toHaveBeenCalledWith(
      '/api/v1/decision/feedback/stats',
      { headers: { 'X-Tenant-Id': 'tenant-1' } },
    )
  })

  it('returns byAction breakdown', async () => {
    mockedApi.get.mockResolvedValue({ data: sampleFeedbackStats })
    const { result } = renderHook(() => useDecisionFeedbackStats(), { wrapper: createWrapper() })

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true)
    })
    expect(result.current.data?.byAction.follow_up.accepted).toBe(5)
    expect(result.current.data?.byAction.proposal.rejected).toBe(1)
  })
})
