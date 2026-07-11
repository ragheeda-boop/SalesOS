'use client'

import { createRegistry, type RegistryEntry } from './_registry/widget-registry'
import { MissionCenterWidget } from './widgets/mission-center'
import { DecisionQueueWidget } from './widgets/decision-queue'
import { IntelligenceFeedWidget } from './widgets/intelligence-feed'
import { AIBriefWidget } from './widgets/ai-brief'
import { MarketPulseWidget } from './widgets/market-pulse'
import { RecentActivityWidget } from './widgets/recent-activity'

export const widgetRegistry: RegistryEntry[] = createRegistry([
  { id: 'missionCenter', Container: MissionCenterWidget },
  { id: 'decisionQueue', Container: DecisionQueueWidget },
  { id: 'intelligenceFeed', Container: IntelligenceFeedWidget },
  { id: 'aiBrief', Container: AIBriefWidget },
  { id: 'marketPulse', Container: MarketPulseWidget },
  { id: 'recentActivity', Container: RecentActivityWidget },
])
