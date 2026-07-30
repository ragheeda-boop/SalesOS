import type { DashboardWidget } from"@/application/dashboard/widget.contract"

 export type WidgetId = 'missionCenter' | 'decisionQueue' | 'intelligenceFeed' | 'aiBrief' | 'marketPulse' | 'recentActivity' | 'pipeline' | 'companyHealth' | 'companyEngagement' | 'emailIntelligence' | 'calendarIntelligence' | 'followupCenter' | 'companyScoring'

export interface WidgetConfig {
 id: WidgetId
 gridColumn: string
 minHeight: string
 refreshIntervalMs: number
 staleThresholdMs: number
}

export const WIDGET_CONFIG: Record<WidgetId, WidgetConfig> = {
 missionCenter: {
 id: 'missionCenter',
 gridColumn: 'span 3',
 minHeight: '200px',
 refreshIntervalMs: 60_000,
 staleThresholdMs: 120_000,
 },
 decisionQueue: {
 id: 'decisionQueue',
 gridColumn: 'span 3',
 minHeight: '320px',
 refreshIntervalMs: 60_000,
 staleThresholdMs: 120_000,
 },
 intelligenceFeed: {
 id: 'intelligenceFeed',
 gridColumn: 'span 4',
 minHeight: '400px',
 refreshIntervalMs: 30_000,
 staleThresholdMs: 60_000,
 },
 aiBrief: {
 id: 'aiBrief',
 gridColumn: 'span 2',
 minHeight: '200px',
 refreshIntervalMs: 120_000,
 staleThresholdMs: 300_000,
 },
 marketPulse: {
 id: 'marketPulse',
 gridColumn: 'span 3',
 minHeight: '300px',
 refreshIntervalMs: 60_000,
 staleThresholdMs: 120_000,
 },
 recentActivity: {
 id: 'recentActivity',
 gridColumn: 'span 3',
 minHeight: '300px',
 refreshIntervalMs: 30_000,
 staleThresholdMs: 60_000,
 },
 pipeline: {
 id: 'pipeline',
 gridColumn: 'span 4',
 minHeight: '350px',
 refreshIntervalMs: 60_000,
 staleThresholdMs: 120_000,
 },
 companyHealth: {
  id: 'companyHealth',
  gridColumn: 'span 3',
  minHeight: '300px',
  refreshIntervalMs: 60_000,
  staleThresholdMs: 120_000,
 },
 companyEngagement: {
  id: 'companyEngagement',
  gridColumn: 'span 4',
  minHeight: '280px',
  refreshIntervalMs: 60_000,
  staleThresholdMs: 120_000,
 },
 emailIntelligence: {
  id: 'emailIntelligence',
  gridColumn: 'span 4',
  minHeight: '320px',
  refreshIntervalMs: 60_000,
  staleThresholdMs: 120_000,
 },
 calendarIntelligence: {
  id: 'calendarIntelligence',
  gridColumn: 'span 4',
  minHeight: '320px',
  refreshIntervalMs: 60_000,
  staleThresholdMs: 120_000,
 },
 followupCenter: {
  id: 'followupCenter',
  gridColumn: 'span 4',
  minHeight: '400px',
  refreshIntervalMs: 30_000,
  staleThresholdMs: 60_000,
 },
 companyScoring: {
  id: 'companyScoring',
  gridColumn: 'span 4',
  minHeight: '320px',
  refreshIntervalMs: 60_000,
  staleThresholdMs: 120_000,
 },
}

export function getWidgetConfig(id: WidgetId): WidgetConfig {
 return WIDGET_CONFIG[id]
}
