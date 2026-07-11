jest.mock('../widget-config', () => ({
  DASHBOARD_WIDGETS: [
    { id: 'mission-center', title: 'Mission Center', component: 'MissionCenter' },
    { id: 'decision-queue', title: 'Decision Queue', component: 'DecisionQueue' },
    { id: 'intelligence-feed', title: 'Intelligence Feed', component: 'IntelligenceFeed' },
    { id: 'ai-brief', title: 'AI Brief', component: 'AIBrief' },
    { id: 'market-pulse', title: 'Market Pulse', component: 'MarketPulse' },
    { id: 'recent-activity', title: 'Recent Activity', component: 'RecentActivity' },
  ],
  getDashboardWidgets: () => ['mission-center', 'decision-queue', 'intelligence-feed', 'ai-brief', 'market-pulse', 'recent-activity'],
}))

import { DASHBOARD_WIDGETS, getDashboardWidgets } from '../widget-config'

describe('widget-config', () => {
  it('exports dashboard widgets', () => {
    expect(DASHBOARD_WIDGETS).toHaveLength(6)
  })

  it('returns widget IDs', () => {
    const ids = getDashboardWidgets()
    expect(ids).toContain('mission-center')
    expect(ids).toContain('recent-activity')
  })
})
