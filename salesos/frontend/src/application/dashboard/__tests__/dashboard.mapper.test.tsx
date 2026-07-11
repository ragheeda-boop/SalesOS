import { mapDashboard } from '../dashboard.mapper'
import type { DashboardDTO } from '../dashboard.dto'

describe('mapDashboard', () => {
  it('returns defaults for empty input', () => {
    const result = mapDashboard({})
    expect(result.generatedAt).toBeNull()
    expect(result.period).toBe('today')
    expect(result.totalTracked).toBe(0)
  })

  it('maps all widget fields', () => {
    const raw = {
      generatedAt: '2026-07-11T12:00:00Z',
      period: 'week',
      totalTracked: 42,
      missionCenter: {
        id: 'mc-1',
        title: 'Mission Center',
        status: 'ready',
        lastUpdated: '2026-07-11T12:00:00Z',
        data: { companiesTracked: 100, activeDeals: 20, pipelineValue: 5000000, signalsToday: 15, decisionsPending: 5 },
        actions: [{ id: 'a1', label: 'Refresh', type: 'refresh' as const }],
      },
      decisionQueue: {
        id: 'dq-1', title: 'Decision Queue', status: 'ready', lastUpdated: null,
        data: { items: [], total: 0 },
        actions: [],
      },
    }

    const result = mapDashboard(raw)
    expect(result.generatedAt).toBe('2026-07-11T12:00:00Z')
    expect(result.period).toBe('week')
    expect(result.totalTracked).toBe(42)
    expect(result.missionCenter?.data?.companiesTracked).toBe(100)
    expect(result.decisionQueue?.data?.total).toBe(0)
  })

  it('returns null for missing widgets', () => {
    const result = mapDashboard({})
    expect(result.missionCenter).toBeNull()
    expect(result.decisionQueue).toBeNull()
    expect(result.intelligenceFeed).toBeNull()
    expect(result.aiBrief).toBeNull()
    expect(result.marketPulse).toBeNull()
    expect(result.recentActivity).toBeNull()
  })

  it('coerces field types safely', () => {
    const result = mapDashboard({
      generatedAt: 12345,
      period: undefined,
      totalTracked: 'invalid',
    })
    expect(result.generatedAt).toBe('12345')
    expect(result.period).toBe('today')
    expect(result.totalTracked).toBe(0)
  })
})
