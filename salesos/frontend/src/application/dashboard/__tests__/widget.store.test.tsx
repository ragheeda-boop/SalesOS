import { deriveWidgets, deriveStatus } from '../widget.store'

describe('deriveStatus', () => {
  it('returns loading when isLoading and no data', () => {
    expect(deriveStatus(null, true, false)).toBe('loading')
  })

  it('returns degraded when isLoading and has data', () => {
    expect(deriveStatus({}, true, false)).toBe('degraded')
  })

  it('returns error when isError and no data', () => {
    expect(deriveStatus(null, false, true)).toBe('error')
  })

  it('returns degraded when isError and has data', () => {
    expect(deriveStatus({}, false, true)).toBe('degraded')
  })

  it('returns loading when no data and no loading/error', () => {
    expect(deriveStatus(null, false, false)).toBe('loading')
  })

  it('returns ready when data is present', () => {
    expect(deriveStatus({}, false, false)).toBe('ready')
  })
})

describe('deriveWidgets', () => {
  it('returns all six widgets with loading status', () => {
    const widgets = deriveWidgets(undefined, true, false)
    expect(Object.keys(widgets)).toEqual([
      'missionCenter', 'decisionQueue', 'intelligenceFeed', 'aiBrief', 'marketPulse', 'recentActivity',
    ])
    Object.values(widgets).forEach((w) => {
      expect(w.status).toBe('loading')
    })
  })

  it('returns all six widgets with ready status', () => {
    const dto: any = {
      missionCenter: { data: { companiesTracked: 100 }, id: 'mc', title: 'MC', status: 'ready', lastUpdated: null, actions: [] },
      decisionQueue: { data: { items: [], total: 0 }, id: 'dq', title: 'DQ', status: 'ready', lastUpdated: null, actions: [] },
      intelligenceFeed: { data: { items: [], total: 0, unseenCount: 0 }, id: 'if', title: 'IF', status: 'ready', lastUpdated: null, actions: [] },
      aiBrief: { data: { summary: '', highlights: [], generatedAt: '' }, id: 'ab', title: 'AB', status: 'ready', lastUpdated: null, actions: [] },
      marketPulse: { data: { trends: [], topMovers: [] }, id: 'mp', title: 'MP', status: 'ready', lastUpdated: null, actions: [] },
      recentActivity: { data: { items: [], total: 0 }, id: 'ra', title: 'RA', status: 'ready', lastUpdated: null, actions: [] },
    }
    const widgets = deriveWidgets(dto, false, false)
    expect(widgets.missionCenter.status).toBe('ready')
    expect(widgets.missionCenter.data?.companiesTracked).toBe(100)
  })

  it('handles null dto gracefully', () => {
    const widgets = deriveWidgets(undefined, false, true)
    Object.values(widgets).forEach((w) => {
      expect(w.status).toBe('error')
    })
  })
})
